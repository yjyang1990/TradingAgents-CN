#!/bin/bash
# 设置每日股票分析定时任务

# 获取项目路径
PROJECT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)

echo "🚀 设置每日股票分析定时任务"
echo "项目路径: $PROJECT_PATH"
echo "Python路径: $PYTHON_PATH"

# 检查crontab是否可用
if ! command -v crontab &> /dev/null; then
    echo "❌ crontab 命令不可用，请先安装cron服务"
    exit 1
fi

# 创建cron任务内容
CRON_COMMAND="0 6 * * * cd $PROJECT_PATH && $PYTHON_PATH daily_stock_report.py >> logs/daily_report.log 2>&1"

# 备份现有crontab
echo "📋 备份现有crontab..."
crontab -l > crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || echo "没有现有crontab"

# 添加新的cron任务
echo "➕ 添加新的定时任务..."
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

# 验证任务添加成功
if crontab -l | grep -q "daily_stock_report.py"; then
    echo "✅ 定时任务添加成功!"
    echo "📅 任务将在每天早上6:00执行"
    echo "📝 日志文件: $PROJECT_PATH/logs/daily_report.log"
    echo ""
    echo "当前crontab内容:"
    crontab -l | grep "daily_stock_report.py"
else
    echo "❌ 定时任务添加失败"
    exit 1
fi

# 创建日志目录
mkdir -p "$PROJECT_PATH/logs"

# 创建测试脚本
cat > "$PROJECT_PATH/test_daily_report.py" << 'EOF'
#!/usr/bin/env python3
"""
测试每日股票分析报告
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from daily_stock_report import DailyStockReporter

def main():
    print("🧪 测试每日股票分析报告...")

    # 创建报告生成器
    reporter = DailyStockReporter()

    # 只生成报告，不发送微信（避免测试时打扰）
    reporter.run_daily_report(save_file=True, send_wechat=False)

    print("✅ 测试完成！检查 reports/ 目录下的报告文件")

if __name__ == "__main__":
    main()
EOF

chmod +x "$PROJECT_PATH/test_daily_report.py"

echo ""
echo "🧪 测试脚本已创建: $PROJECT_PATH/test_daily_report.py"
echo "运行测试: python3 test_daily_report.py"
echo ""
echo "📚 使用说明:"
echo "1. 修改股票列表: 编辑 config/stock_watchlist.json"
echo "2. 查看日志: tail -f logs/daily_report.log"
echo "3. 删除定时任务: crontab -e"
echo "4. 手动运行: python3 daily_stock_report.py"