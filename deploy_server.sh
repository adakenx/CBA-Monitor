#!/bin/bash

# 服务器端部署脚本
# 在腾讯云服务器上执行

set -e

WORK_DIR="/home/ubuntu/cba-monitor"
cd $WORK_DIR

echo "=========================================="
echo "    CBA比赛监控 - 服务器部署"
echo "=========================================="

# 1. 创建虚拟环境
echo ""
echo "[1/5] 创建Python虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 2. 激活虚拟环境并安装依赖
echo ""
echo "[2/5] 安装Python依赖..."
source venv/bin/activate
pip install -r requirements.txt -q
echo "✅ 依赖安装完成"

# 3. 测试连接
echo ""
echo "[3/5] 测试连接..."
python cba_monitor.py test

# 4. 配置Cron定时任务
echo ""
echo "[4/5] 配置定时任务..."

# 移除旧的CBA监控cron（如果有）
crontab -l 2>/dev/null | grep -v "cba-monitor" | crontab - 2>/dev/null || true

# 添加定时任务
# 任务1: 每天北京时间09:00执行比赛检查（对应多伦多前一天20:00左右）
# 任务2: 每周一北京时间10:00执行赛程更新
(crontab -l 2>/dev/null; echo "# CBA比赛监控 - 每日检查") | crontab -
(crontab -l 2>/dev/null; echo "0 9 * * * cd $WORK_DIR && source venv/bin/activate && python cba_monitor.py once >> $WORK_DIR/cba.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "# CBA比赛监控 - 每周更新赛程") | crontab -
(crontab -l 2>/dev/null; echo "0 10 * * 1 cd $WORK_DIR && source venv/bin/activate && python cba_monitor.py update >> $WORK_DIR/cba.log 2>&1") | crontab -

echo "✅ Cron定时任务已配置"

# 5. 显示配置结果
echo ""
echo "[5/5] 验证配置..."
echo ""
echo "当前Cron任务:"
crontab -l | grep -A1 "cba"

echo ""
echo "=========================================="
echo "           部署完成！"
echo "=========================================="
echo ""
echo "📋 管理命令:"
echo "   查看日志: tail -f $WORK_DIR/cba.log"
echo "   手动测试: cd $WORK_DIR && source venv/bin/activate && python cba_monitor.py once"
echo "   测试通知: cd $WORK_DIR && source venv/bin/activate && python cba_monitor.py notify"
echo "   更新赛程: cd $WORK_DIR && source venv/bin/activate && python cba_monitor.py update"
echo "   编辑cron: crontab -e"
echo ""
echo "⏰ 定时任务:"
echo "   比赛提醒: 每天 09:00 (北京时间) ≈ 20:00 (多伦多前一天)"
echo "   赛程更新: 每周一 10:00 (北京时间)"
echo ""
echo "🏀 监控球队: 北京北汽、北京控股"
echo ""
