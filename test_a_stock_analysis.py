#!/usr/bin/env python3
"""
测试A股分析功能
只测试一只股票，不发送微信通知
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from daily_stock_report import DailyStockReporter

def test_single_stock():
    """测试单只股票分析"""

    print("🧪 测试A股分析功能...")
    print("=" * 50)

    # 创建报告生成器
    reporter = DailyStockReporter()

    if not reporter.watchlist:
        print("❌ 没有配置股票列表")
        return

    # 测试第一只股票
    test_symbol = reporter.watchlist[0]
    print(f"🔍 测试股票: {test_symbol}")

    # 获取股票名称
    stock_name = reporter.get_stock_name(test_symbol)
    print(f"📊 股票名称: {stock_name}")

    # 分析股票
    print(f"\n⏳ 正在分析 {test_symbol}({stock_name})...")
    result = reporter.analyze_stock(test_symbol)

    if result.get('success'):
        print("✅ 分析成功!")
        print(f"   操作建议: {result.get('action', '观察')}")
        print(f"   分析理由: {result.get('reasoning', '继续观察')[:200]}...")
        print(f"   信心度: {result.get('confidence', 'N/A')}")
    else:
        print("❌ 分析失败!")
        print(f"   错误: {result.get('error', '未知错误')}")

    print("\n" + "=" * 50)
    print("🎉 A股分析测试完成!")

if __name__ == "__main__":
    test_single_stock()