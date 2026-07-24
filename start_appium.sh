#!/bin/bash
# 大麦抢票 - Appium启动脚本（支持 Android & HarmonyOS）
# 使用方法: ./start_appium.sh

echo "========================================="
echo "  大麦抢票 - Appium 启动脚本"
echo "========================================="

# 检测 ADB 路径
detect_adb() {
    if command -v adb &> /dev/null; then
        ADB_CMD=$(which adb)
    elif [ -f "$HOME/Library/Android/sdk/platform-tools/adb" ]; then
        ADB_CMD="$HOME/Library/Android/sdk/platform-tools/adb"
        export PATH="$HOME/Library/Android/sdk/platform-tools:$PATH"
    elif [ -d "$HOME/Android/Sdk/platform-tools" ]; then
        ADB_CMD="$HOME/Android/Sdk/platform-tools/adb"
        export PATH="$HOME/Android/Sdk/platform-tools:$PATH"
    else
        echo "⚠️  未找到 ADB，请安装 Android SDK 平台工具"
        echo "   macOS: brew install android-platform-tools"
        echo "   或: https://developer.android.com/studio/releases/platform-tools"
        return 1
    fi
    echo "✅ ADB: $ADB_CMD"
    return 0
}

# 检测设备
check_device() {
    echo ""
    echo "📱 检查设备连接..."
    if ! command -v adb &> /dev/null; then
        if [ -z "$ADB_CMD" ]; then
            echo "❌ ADB 不可用，跳过设备检测"
            return 1
        fi
        DEVICES=$($ADB_CMD devices | grep -c "device$")
    else
        DEVICES=$(adb devices | grep -c "device$")
    fi

    if [ "$DEVICES" -eq 0 ]; then
        echo "⚠️  未检测到设备"
        echo ""
        echo "🔔 HarmonyOS 设备连接指南:"
        echo "   1. 打开「设置」→「关于手机」→ 连续点击「版本号」7 次开启开发者模式"
        echo "   2. 返回「设置」→「系统和更新」→「开发人员选项」"
        echo "   3. 开启「USB 调试」"
        echo "   4. HarmonyOS 4.x+ 还需开启「USB 调试（安全设置）」"
        echo "   5. 用 USB 线连接电脑，在手机上确认「允许 USB 调试」"
        echo ""
        echo "   验证连接: adb devices"
        echo "   如 adb 无法识别，尝试使用 hdc: hdc list targets"
        return 1
    else
        echo "✅ 检测到 $DEVICES 个设备"

        # 获取设备信息
        if command -v adb &> /dev/null; then
            DEVICE_MODEL=$(adb shell getprop ro.product.model 2>/dev/null | tr -d '\r')
            HW_SDK=$(adb shell getprop ro.hw.build.version.sdk 2>/dev/null | tr -d '\r')
            if [ -n "$HW_SDK" ]; then
                echo "📱 设备: $DEVICE_MODEL (HarmonyOS)"
            else
                ANDROID_VERSION=$(adb shell getprop ro.build.version.release 2>/dev/null | tr -d '\r')
                echo "📱 设备: $DEVICE_MODEL (Android $ANDROID_VERSION)"
            fi
        fi
    fi
    return 0
}

# 检查大麦 APP 是否安装
check_app() {
    if command -v adb &> /dev/null; then
        if adb shell pm list packages 2>/dev/null | grep -q "cn.damai"; then
            echo "✅ 大麦 APP 已安装"
            return 0
        fi
    elif [ -n "$ADB_CMD" ]; then
        if $ADB_CMD shell pm list packages 2>/dev/null | grep -q "cn.damai"; then
            echo "✅ 大麦 APP 已安装"
            return 0
        fi
    fi
    echo "⚠️  大麦 APP 未安装，请在设备上安装大麦 APP"
    return 1
}

# 检查 Node.js
check_node() {
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js 未安装，请先安装 Node.js"
        exit 1
    fi
    echo "📦 Node.js: $(node --version)"
}

# 检查 Appium
check_appium() {
    if ! command -v appium &> /dev/null; then
        echo "❌ Appium 未安装"
        echo "   运行: npm install -g appium"
        echo "   安装 UiAutomator2 驱动: appium driver install uiautomator2"
        exit 1
    fi
    echo "🤖 Appium: $(appium --version)"

    # 检查 uiautomator2 驱动
    APPIUM_DRIVERS=$(appium driver list --installed 2>/dev/null || appium driver list 2>/dev/null)
    if ! echo "$APPIUM_DRIVERS" | grep -q "uiautomator2"; then
        echo "⚠️  UiAutomator2 驱动未安装"
        echo "   运行: appium driver install uiautomator2"
        exit 1
    fi
}

# ===== 主流程 =====
check_node
check_appium
detect_adb
check_device
check_app

echo ""
echo "========================================="
echo "  启动 Appium 服务器..."
echo "  地址: http://127.0.0.1:4723"
echo "  按 Ctrl+C 停止"
echo "========================================="
echo ""

appium --address 0.0.0.0 --port 4723 --relaxed-security
