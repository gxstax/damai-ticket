#!/bin/bash
# 大麦抢票 - 抢票启动脚本（支持 Android & HarmonyOS）
# 使用方法: ./start_ticket_grabbing.sh

echo "========================================="
echo "  大麦抢票 - 执行脚本"
echo "========================================="
echo ""

# 检查 Appium 服务器是否运行
echo "🌐 检查 Appium 服务器..."
if ! curl -s http://127.0.0.1:4723/status > /dev/null 2>&1; then
    echo "❌ Appium 服务器未运行"
    echo "   请先启动: ./start_appium.sh"
    exit 1
fi
echo "✅ Appium 服务器运行正常"
echo ""

# 检查配置文件
if [ ! -f "damai_appium/config.jsonc" ]; then
    echo "❌ 配置文件不存在: damai_appium/config.jsonc"
    exit 1
fi
echo "✅ 配置文件存在"
echo ""

# 显示当前配置
echo "📋 当前配置:"
grep -E '"keyword"|"city"|"date"|"platformName"|"deviceName"' damai_appium/config.jsonc | head -5 | sed 's/^/   /'
echo ""

# 确认是否继续
read -p "确认开始抢票？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 1
fi

# 进入脚本目录并运行
cd damai_appium

echo ""
echo "🚀 开始抢票..."
echo "   请确保大麦 APP 已打开并进入目标演出页面"
echo ""

python3 damai_app_v2.py
