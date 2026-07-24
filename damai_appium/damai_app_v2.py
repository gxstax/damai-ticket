# -*- coding: UTF-8 -*-
"""
__Author__ = "BlueCestbon"
__Version__ = "2.1.0"
__Description__ = "大麦app抢票自动化 - 优化版（支持 HarmonyOS）"
__Created__ = 2025/09/13 19:27
"""

import subprocess
import time
from appium import webdriver
from appium.options.common.base import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import Config


def detect_device():
    """
    通过 ADB 自动检测已连接的设备信息。
    支持 Android 和 HarmonyOS 设备。

    Returns:
        dict: 包含 deviceName 和 platformVersion 的字典，检测失败返回 None
    """
    try:
        # 获取设备列表
        result = subprocess.run(
            ['adb', 'devices'],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split('\n')
        devices = []
        for line in lines[1:]:
            line = line.strip()
            if line and 'device' in line and 'offline' not in line:
                parts = line.split('\t')
                if len(parts) >= 1 and parts[0]:
                    devices.append(parts[0])

        if not devices:
            print("⚠️  未检测到已连接的设备")
            return None

        device_serial = devices[0]
        if len(devices) > 1:
            print(f"ℹ️  检测到多个设备，将使用第一个: {device_serial}")

        # 获取系统版本
        version_result = subprocess.run(
            ['adb', '-s', device_serial, 'shell', 'getprop', 'ro.build.version.release'],
            capture_output=True, text=True, timeout=5
        )
        platform_version = version_result.stdout.strip()

        # 获取设备型号
        model_result = subprocess.run(
            ['adb', '-s', device_serial, 'shell', 'getprop', 'ro.product.model'],
            capture_output=True, text=True, timeout=5
        )
        device_model = model_result.stdout.strip()

        # 检测是否为 HarmonyOS
        hmos_result = subprocess.run(
            ['adb', '-s', device_serial, 'shell', 'getprop', 'ro.hw.build.version.sdk'],
            capture_output=True, text=True, timeout=5
        )
        is_harmonyos = hmos_result.stdout.strip() != ''

        os_type = "HarmonyOS" if is_harmonyos else "Android"
        print(f"📱 检测到设备: {device_model} ({os_type} v{platform_version})")
        print(f"   设备序列号: {device_serial}")

        return {
            'deviceName': device_serial,
            'platformVersion': platform_version,
            'deviceModel': device_model,
            'isHarmonyOS': is_harmonyos
        }
    except FileNotFoundError:
        print("❌ 未找到 adb 命令，请确保已安装 Android SDK 平台工具")
        print("   macOS: brew install android-platform-tools")
        print("   或下载: https://developer.android.com/studio/releases/platform-tools")
    except subprocess.TimeoutExpired:
        print("⚠️  ADB 命令超时，请检查设备连接")
    except Exception as e:
        print(f"⚠️  设备检测失败: {e}")

    return None


class DamaiBot:
    def __init__(self):
        self.config = Config.load_config()
        self.driver = None
        self.wait = None
        self._setup_driver()

    def _get_capabilities(self):
        """构建 capabilities，优先使用配置文件，缺失字段自动检测"""
        caps = {}
        device_info = None

        # 1. platformName - 优先使用配置文件
        platform_name = self.config.device.platformName
        if not platform_name or platform_name == "Android":
            # 尝试检测是否为 HarmonyOS
            device_info = detect_device()
            if device_info and device_info['isHarmonyOS']:
                print("💡 检测到 HarmonyOS 设备，platformName 设为 'Android'（UiAutomator2 兼容模式）")
                print("   如需尝试 HarmonyOS 原生模式，请在 config.jsonc 中将 device.platformName 改为 'HarmonyOS'")
            platform_name = "Android"  # UiAutomator2 需要 Android
        caps["platformName"] = platform_name

        # 2. platformVersion - 自动检测
        platform_version = self.config.device.platformVersion
        if not platform_version:
            if device_info is None:
                device_info = detect_device()
            if device_info:
                platform_version = device_info['platformVersion']
            else:
                platform_version = "12"  # 默认值
                print(f"⚠️  无法检测系统版本，使用默认值: {platform_version}")
        caps["platformVersion"] = platform_version

        # 3. deviceName - 自动检测
        device_name = self.config.device.deviceName
        if not device_name:
            if device_info is None:
                device_info = detect_device()
            if device_info:
                device_name = device_info['deviceName']
            else:
                device_name = "emulator-5554"
                print("⚠️  无法检测设备，使用默认名称: emulator-5554")
        caps["deviceName"] = device_name

        if device_info and device_info['isHarmonyOS']:
            print("\n🔔 HarmonyOS 设备连接提示:")
            print("   1. 确保已开启「开发者模式」和「USB 调试」")
            print("   2. HarmonyOS 4.x 需额外开启「USB 调试（安全设置）」")
            print("   3. 如连接不稳定，尝试: adb kill-server && adb start-server && adb devices")
            print("   4. 部分 HarmonyOS 版本需安装 hdc 工具代替 adb")
            print()

        # 4. 固定配置
        caps["appPackage"] = "cn.damai"
        caps["appActivity"] = ".launcher.splash.SplashMainActivity"
        caps["unicodeKeyboard"] = True
        caps["resetKeyboard"] = True
        caps["noReset"] = self.config.device.noReset
        caps["newCommandTimeout"] = 6000
        caps["automationName"] = self.config.device.automationName
        caps["skipServerInstallation"] = self.config.device.skipServerInstallation
        caps["ignoreHiddenApiPolicyError"] = True
        caps["disableWindowAnimation"] = True
        caps["mjpegServerFramerate"] = 1
        caps["shouldTerminateApp"] = False
        caps["adbExecTimeout"] = self.config.device.adbExecTimeout
        caps["uiautomator2ServerInstallTimeout"] = self.config.device.uiautomator2ServerInstallTimeout

        # 如果是模拟器，添加额外的 Chromedriver 配置
        if "emulator" in device_name.lower():
            caps["avd"] = device_name

        return caps

    def _setup_driver(self):
        """初始化驱动配置"""
        capabilities = self._get_capabilities()

        device_app_info = AppiumOptions()
        device_app_info.load_capabilities(capabilities)

        print(f"🚀 连接 Appium 服务器: {self.config.server_url}")
        print(f"📱 设备: {capabilities['deviceName']} | 系统: {capabilities['platformName']} v{capabilities['platformVersion']}")
        try:
            self.driver = webdriver.Remote(self.config.server_url, options=device_app_info)
        except Exception as e:
            print(f"❌ 连接 Appium 服务器失败: {e}")
            print("\n📋 排查步骤:")
            print("   1. 确认 Appium 已启动: appium --address 0.0.0.0 --port 4723 --relaxed-security")
            print("   2. 确认设备已连接: adb devices")
            print("   3. 确认大麦 APP 已安装: adb shell pm list packages | grep cn.damai")
            if 'HarmonyOS' in capabilities.get('platformName', ''):
                print("   4. HarmonyOS 设备建议将 platformName 改为 'Android'")
            raise

        # 激进的性能优化设置
        self.driver.update_settings({
            "waitForIdleTimeout": 0,
            "actionAcknowledgmentTimeout": 0,
            "keyInjectionDelay": 0,
            "waitForSelectorTimeout": 300,
            "ignoreUnimportantViews": False,
            "allowInvisibleElements": True,
            "enableNotificationListener": False,
        })

        # 极短的显式等待
        self.wait = WebDriverWait(self.driver, 2)

    def ultra_fast_click(self, by, value, timeout=1.5):
        """超快速点击 - 适合抢票场景"""
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            rect = el.rect
            x = rect['x'] + rect['width'] // 2
            y = rect['y'] + rect['height'] // 2
            self.driver.execute_script("mobile: clickGesture", {
                "x": x,
                "y": y,
                "duration": 50
            })
            return True
        except TimeoutException:
            return False

    def batch_click(self, elements_info, delay=0.1):
        """批量点击操作"""
        for by, value in elements_info:
            if self.ultra_fast_click(by, value):
                if delay > 0:
                    time.sleep(delay)
            else:
                print(f"点击失败: {value}")

    def ultra_batch_click(self, elements_info, timeout=2):
        """超快批量点击 - 带等待机制"""
        coordinates = []
        for by, value in elements_info:
            try:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                rect = el.rect
                x = rect['x'] + rect['width'] // 2
                y = rect['y'] + rect['height'] // 2
                coordinates.append((x, y, value))
            except TimeoutException:
                print(f"超时未找到用户: {value}")
            except Exception as e:
                print(f"查找用户失败 {value}: {e}")
        print(f"成功找到 {len(coordinates)} 个用户")
        for i, (x, y, value) in enumerate(coordinates):
            self.driver.execute_script("mobile: clickGesture", {
                "x": x,
                "y": y,
                "duration": 30
            })
            if i < len(coordinates) - 1:
                time.sleep(0.01)
            print(f"点击用户: {value}")

    def smart_wait_and_click(self, by, value, backup_selectors=None, timeout=1.5):
        """智能等待和点击 - 支持备用选择器"""
        selectors = [(by, value)]
        if backup_selectors:
            selectors.extend(backup_selectors)

        for selector_by, selector_value in selectors:
            try:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((selector_by, selector_value))
                )
                rect = el.rect
                x = rect['x'] + rect['width'] // 2
                y = rect['y'] + rect['height'] // 2
                self.driver.execute_script("mobile: clickGesture", {"x": x, "y": y, "duration": 50})
                return True
            except TimeoutException:
                continue
        return False

    def run_ticket_grabbing(self):
        """执行抢票主流程"""
        try:
            print("开始抢票流程...")
            start_time = time.time()

            # 1. 城市选择
            print("选择城市...")
            city_selectors = [
                (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{self.config.city}")'),
                (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().textContains("{self.config.city}")'),
                (By.XPATH, f'//*[@text="{self.config.city}"]')
            ]
            if not self.smart_wait_and_click(*city_selectors[0], city_selectors[1:]):
                print("城市选择失败")
                return False

            # 2. 点击预约按钮
            print("点击预约按钮...")
            book_selectors = [
                (By.ID, "cn.damai:id/trade_project_detail_purchase_status_bar_container_fl"),
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*预约.*|.*购买.*|.*立即.*")'),
                (By.XPATH, '//*[contains(@text,"预约") or contains(@text,"购买")]')
            ]
            if not self.smart_wait_and_click(*book_selectors[0], book_selectors[1:]):
                print("预约按钮点击失败")
                return False

            # 3. 票价选择
            print("选择票价...")
            try:
                price_container = self.driver.find_element(By.ID, 'cn.damai:id/project_detail_perform_price_flowlayout')
                target_price = price_container.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().className("android.widget.FrameLayout").index({self.config.price_index}).clickable(true)'
                )
                self.driver.execute_script('mobile: clickGesture', {'elementId': target_price.id})
            except Exception as e:
                print(f"票价选择失败，启动备用方案: {e}")
                price_container = self.wait.until(
                    EC.presence_of_element_located((By.ID, 'cn.damai:id/project_detail_perform_price_flowlayout')))
                target_price = price_container.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().className("android.widget.FrameLayout").index({self.config.price_index}).clickable(true)'
                )
                self.driver.execute_script('mobile: clickGesture', {'elementId': target_price.id})

            # 4. 数量选择
            print("选择数量...")
            if self.driver.find_elements(by=By.ID, value='layout_num'):
                clicks_needed = len(self.config.users) - 1
                if clicks_needed > 0:
                    try:
                        plus_button = self.driver.find_element(By.ID, 'img_jia')
                        for i in range(clicks_needed):
                            rect = plus_button.rect
                            x = rect['x'] + rect['width'] // 2
                            y = rect['y'] + rect['height'] // 2
                            self.driver.execute_script("mobile: clickGesture", {
                                "x": x,
                                "y": y,
                                "duration": 50
                            })
                            time.sleep(0.02)
                    except Exception as e:
                        print(f"快速点击加号失败: {e}")

            # 5. 确定购买
            print("确定购买...")
            if not self.ultra_fast_click(By.ID, "btn_buy_view"):
                self.ultra_fast_click(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*确定.*|.*购买.*")')

            # 6. 批量选择用户
            print("选择用户...")
            user_clicks = [(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{user}")') for user in
                           self.config.users]
            self.ultra_batch_click(user_clicks)

            # 7. 提交订单
            print("提交订单...")
            submit_selectors = [
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("立即提交")'),
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*提交.*|.*确认.*")'),
                (By.XPATH, '//*[contains(@text,"提交")]')
            ]
            self.smart_wait_and_click(*submit_selectors[0], submit_selectors[1:])

            end_time = time.time()
            print(f"抢票流程完成，耗时: {end_time - start_time:.2f}秒")
            return True

        except Exception as e:
            print(f"抢票过程发生错误: {e}")
            return False
        finally:
            time.sleep(1)
            self.driver.quit()

    def run_with_retry(self, max_retries=3):
        """带重试机制的抢票"""
        for attempt in range(max_retries):
            print(f"第 {attempt + 1} 次尝试...")
            if self.run_ticket_grabbing():
                print("抢票成功！")
                return True
            else:
                print(f"第 {attempt + 1} 次尝试失败")
                if attempt < max_retries - 1:
                    print("2秒后重试...")
                    time.sleep(2)
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self._setup_driver()

        print("所有尝试均失败")
        return False


if __name__ == "__main__":
    bot = DamaiBot()
    bot.run_with_retry(max_retries=3)
