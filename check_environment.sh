#!/bin/bash
# 大麦抢票 - 环境检查脚本（支持 Android & HarmonyOS）
# 使用方法: ./check_environment.sh

echo "========================================="
echo "  大麦抢票 - 环境检查"
echo "========================================="
echo ""

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
        echo "   ⚠️ 未找到 ADB"
        echo "   安装: brew install android-platform-tools"
        return 1
    fi
    echo "   ✅ $ADB_CMD"
    return 0
}

# 检查 Python
echo "🐍 Python 环境..."
if command -v python3 &> /dev/null; then
    echo "   ✅ $(python3 --version)"
else
    echo "   ❌ Python3 未安装"
    exit 1
fi
echo ""

# 检查 Node.js
echo "📦 Node.js 环境..."
if command -v node &> /dev/null; then
    echo "   ✅ Node.js: $(node --version)"
    NODE_MAJOR=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_MAJOR" -ge 18 ]; then
        echo "   ✅ Node.js 版本兼容"
    else
        echo "   ⚠️ Node.js 版本可能不兼容，建议升级到 18+"
    fi
else
    echo "   ❌ Node.js 未安装"
    exit 1
fi
echo ""

# 检查 Appium
echo "🤖 Appium..."
if command -v appium &> /dev/null; then
    echo "   ✅ Appium: $(appium --version)"
    APPIUM_DRIVERS=$(appium driver list --installed 2>/dev/null || appium driver list 2>/dev/null)
    if echo "$APPIUM_DRIVERS" | grep -q "uiautomator2"; then
        echo "   ✅ UiAutomator2 驱动已安装"
    else
        echo "   ⚠️ UiAutomator2 驱动未安装"
        echo "   运行: appium driver install uiautomator2"
    fi
else
    echo "   ❌ Appium 未安装"
    echo "   安装: npm install -g appium"
fi
echo ""

# 检查 ADB
echo "🔧 ADB..."
detect_adb
echo ""

# 检查设备
echo "📱 设备连接..."
if command -v adb &> /dev/null; then
    ADB_TOOL="adb"
elif [ -n "$ADB_CMD" ]; then
    ADB_TOOL="$ADB_CMD"
else
    ADB_TOOL=""
fi

if [ -n "$ADB_TOOL" ]; then
    DEVICES=$($ADB_TOOL devices 2>/dev/null | grep -c "device$")
    if [ "$DEVICES" -eq 0 ]; then
        echo "   ⚠️ 未检测到设备"
        echo ""
        echo "   🔔 HarmonyOS 设备连接步骤:"
        echo "   1. 「设置」→「关于手机」→ 连续点击「版本号」7 次"
        echo "   2. 「设置」→「系统和更新」→「开发人员选项」→ 开启「USB 调试」"
        echo "   3. HarmonyOS 4.x+ 需开启「USB 调试（安全设置）」"
        echo "   4. 连接 USB 线并在手机上授权"
        echo "   5. 验证: adb devices"
    else
        echo "   ✅ 检测到 $DEVICES 个设备"

        # 逐个显示设备信息
        for SERIAL in $($ADB_TOOL devices 2>/dev/null | grep "device$" | cut -f1); do
            MODEL=$($ADB_TOOL -s "$SERIAL" shell getprop ro.product.model 2>/dev/null | tr -d '\r')
            VERSION=$($ADB_TOOL -s "$SERIAL" shell getprop ro.build.version.release 2>/dev/null | tr -d '\r')
            HW_SDK=$($ADB_TOOL -s "$SERIAL" shell getprop ro.hw.build.version.sdk 2>/dev/null | tr -d '\r')

            if [ -n "$HW_SDK" ]; then
                echo "      ├─ $MODEL (HarmonyOS $VERSION)"
            else
                echo "      ├─ $MODEL (Android $VERSION)"
            fi
            echo "      └─ 序列号: $SERIAL"
        done

        # 检查大麦 APP
        echo ""
        echo "📱 大麦 APP..."
        if $ADB_TOOL shell pm list packages 2>/dev/null | grep -q "cn.damai"; then
            echo "   ✅ 大麦 APP 已安装"
        else
            echo "   ❌ 大麦 APP 未安装"
            echo "   请在设备上安装大麦 APP"
        fi
    fi
else
    echo "   ⚠️ ADB 不可用，无法检测设备"
fi
echo ""

# 检查 Appium 服务器
echo "🌐 Appium 服务器..."
if curl -s http://127.0.0.1:4723/status > /dev/null 2>&1; then
    echo "   ✅ Appium 服务器正在运行 (http://127.0.0.1:4723)"
else
    echo "   ⚠️ Appium 服务器未运行"
    echo "   启动: ./start_appium.sh"
fi
echo ""

# 检查配置文件
echo "📋 配置文件..."
if [ -f "damai_appium/config.jsonc" ]; then
    echo "   ✅ 配置文件存在"
    echo "   当前配置:"
    grep -E '"keyword"|"city"|"users"|"platformName"|"deviceName"' damai_appium/config.jsonc | head -5 | sed 's/^/     /'
else
    echo "   ❌ 配置文件不存在"
fi
echo ""

echo "========================================="
echo "  环境检查完成！"
echo "========================================="
echo ""
echo "使用说明:"
echo "  1. 启动 Appium:  ./start_appium.sh"
echo "  2. 开始抢票:    cd damai_appium && python damai_app_v2.py"
echo ""
