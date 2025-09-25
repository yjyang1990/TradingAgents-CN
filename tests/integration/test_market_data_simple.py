"""
简化版市场数据集成测试

直接测试数据接口功能，避免工具装饰器问题
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tradingagents.dataflows.interface import (
    get_capital_flow_data,
    get_capital_flow_realtime,
    get_concept_capital_flow,
    get_concept_list,
    get_concept_stocks,
    get_concept_ranking,
    get_dividend_history,
    get_dividend_summary,
    calculate_dividend_yield
)


@pytest.mark.integration
class TestMarketDataIntegration:
    """市场数据集成测试"""

    def test_capital_flow_interface(self):
        """测试资金流向接口"""
        test_stock = '000001'

        # 测试实时资金流向
        result = get_capital_flow_realtime(ticker=test_stock)
        assert result is not None
        assert len(str(result)) > 10
        print(f"✅ 实时资金流向测试通过: {len(str(result))} 字符")

        # 测试历史资金流向
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')

        result = get_capital_flow_data(
            ticker=test_stock,
            start_date=start_date,
            end_date=end_date
        )
        assert result is not None
        assert len(str(result)) > 10
        print(f"✅ 历史资金流向测试通过: {len(str(result))} 字符")

    def test_concept_interface(self):
        """测试概念板块接口"""
        # 测试概念列表
        concepts = get_concept_list()
        assert concepts is not None
        assert len(str(concepts)) > 100
        print(f"✅ 概念列表测试通过: {len(str(concepts))} 字符")

        # 测试概念排行
        ranking = get_concept_ranking(
            sort_by="change_pct",
            limit=5
        )
        assert ranking is not None
        assert len(str(ranking)) > 50
        print(f"✅ 概念排行测试通过: {len(str(ranking))} 字符")

        # 测试概念成分股
        concept_name = "人工智能"
        stocks = get_concept_stocks(
            concept_code=concept_name
        )
        assert stocks is not None
        print(f"✅ 概念成分股测试通过: {len(str(stocks))} 字符")

    def test_dividend_interface(self):
        """测试股息数据接口"""
        test_stock = '600519'  # 贵州茅台

        # 测试分红历史
        history = get_dividend_history(
            ticker=test_stock,
            start_year=2022,
            end_year=2024
        )
        assert history is not None
        assert len(str(history)) > 50
        print(f"✅ 分红历史测试通过: {len(str(history))} 字符")

        # 测试分红汇总
        summary = get_dividend_summary(
            ticker=test_stock
        )
        assert summary is not None
        assert len(str(summary)) > 20
        print(f"✅ 分红汇总测试通过: {len(str(summary))} 字符")

        # 测试股息率计算
        yield_data = calculate_dividend_yield(
            ticker=test_stock,
            current_price=1800.0
        )
        assert yield_data is not None
        assert len(str(yield_data)) > 20
        print(f"✅ 股息率计算测试通过: {len(str(yield_data))} 字符")

    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效股票代码
        result = get_capital_flow_realtime(
            ticker="INVALID_CODE"
        )
        # 应该不会抛出异常，而是返回错误信息
        assert result is not None
        print(f"✅ 错误处理测试通过")

    def test_cache_functionality(self):
        """测试缓存功能"""
        import time

        test_stock = '000001'

        # 第一次调用（无缓存）
        start_time = time.time()
        result1 = get_capital_flow_realtime(ticker=test_stock)
        first_time = time.time() - start_time

        # 第二次调用（有缓存）
        start_time = time.time()
        result2 = get_capital_flow_realtime(ticker=test_stock)
        second_time = time.time() - start_time

        # 缓存应该提升性能
        assert result1 is not None
        assert result2 is not None
        assert second_time <= first_time  # 缓存调用应该更快或相等
        print(f"✅ 缓存功能测试通过: {first_time:.3f}s -> {second_time:.3f}s")

    def test_batch_operations(self):
        """测试批量操作"""
        test_stocks = ['000001', '000002', '600000']
        results = []

        for stock in test_stocks:
            result = get_capital_flow_realtime(ticker=stock)
            results.append(result)

        # 验证所有结果
        assert len(results) == len(test_stocks)
        assert all(r is not None for r in results)
        print(f"✅ 批量操作测试通过: {len(results)} 个结果")

    def test_data_consistency(self):
        """测试数据一致性"""
        test_stock = '000001'

        # 多次获取相同数据
        results = []
        for _ in range(3):
            result = get_capital_flow_realtime(ticker=test_stock)
            results.append(str(result))

        # 缓存数据应该保持一致
        assert len(set(results)) == 1  # 所有结果应该相同（使用缓存）
        print(f"✅ 数据一致性测试通过")


if __name__ == "__main__":
    # 直接运行测试
    test = TestMarketDataIntegration()

    print("🚀 开始市场数据集成测试")

    try:
        test.test_capital_flow_interface()
        test.test_concept_interface()
        test.test_dividend_interface()
        test.test_error_handling()
        test.test_cache_functionality()
        test.test_batch_operations()
        test.test_data_consistency()

        print("\n🎉 所有集成测试通过!")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        raise