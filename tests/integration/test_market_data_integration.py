"""
Market Data Integration Tests - 市场数据集成测试

端到端集成测试，验证AI分析师与新市场数据源的协作能力。
测试覆盖资金流向、概念板块、股息数据的完整业务流程。

Author: Claude (Opus 4.1)
Created: 2025-09-25
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch

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

from tradingagents.agents.utils.agent_utils import (
    get_capital_flow_analysis,
    get_concept_capital_flow_analysis,
    get_market_capital_flow_overview,
    get_concept_fundamentals_analysis,
    get_dividend_investment_analysis,
    get_sector_rotation_analysis
)


class TestMarketDataIntegration:
    """市场数据集成测试主类"""

    @pytest.fixture
    def setup_test_data(self):
        """设置测试数据"""
        return {
            'test_stocks': ['002115', '000002', '600000', '600519'],
            'test_concepts': ['人工智能', '新能源汽车', '半导体', '医药生物'],
            'test_date_range': {
                'start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d')
            }
        }

    @pytest.mark.integration
    def test_capital_flow_data_pipeline(self, setup_test_data):
        """测试资金流向数据管道完整性"""
        test_stock = setup_test_data['test_stocks'][0]

        # 1. 测试历史资金流向数据获取
        historical_data = get_capital_flow_data(
            ticker=test_stock,
            period=30,
            use_cache=False
        )
        assert historical_data is not None
        assert "主力资金" in historical_data or "capital_flow" in historical_data.lower()

        # 2. 测试实时资金流向数据获取
        realtime_data = get_capital_flow_realtime(
            ticker=test_stock,
            use_cache=False
        )
        assert realtime_data is not None

        # 3. 测试AI分析师资金流向分析工具
        analysis_result = get_capital_flow_analysis(
            symbol=test_stock,
            analysis_days=5
        )
        assert analysis_result is not None
        assert len(analysis_result) > 100  # 分析结果应该足够详细

    @pytest.mark.integration
    def test_concept_data_pipeline(self, setup_test_data):
        """测试概念板块数据管道完整性"""
        test_concept = setup_test_data['test_concepts'][0]

        # 1. 测试概念列表获取
        concept_list = get_concept_list(use_cache=False)
        assert concept_list is not None
        assert len(concept_list) > 50  # 应该有足够多的概念

        # 2. 测试概念成分股查询
        concept_stocks = get_concept_stocks(
            concept_name=test_concept,
            use_cache=False
        )
        assert concept_stocks is not None

        # 3. 测试概念排行
        concept_ranking = get_concept_ranking(
            sort_by="change_pct",
            ascending=False,
            limit=20,
            use_cache=False
        )
        assert concept_ranking is not None

        # 4. 测试概念资金流向
        concept_capital_flow = get_concept_capital_flow(
            concept_name=test_concept,
            use_cache=False
        )
        assert concept_capital_flow is not None

        # 5. 测试AI分析师概念分析工具
        concept_analysis = get_concept_fundamentals_analysis(
            concept_name=test_concept
        )
        assert concept_analysis is not None
        assert len(concept_analysis) > 100

    @pytest.mark.integration
    def test_dividend_data_pipeline(self, setup_test_data):
        """测试股息数据管道完整性"""
        test_stock = setup_test_data['test_stocks'][3]  # 使用贵州茅台测试分红数据

        # 1. 测试历史分红数据获取
        dividend_history = get_dividend_history(
            ticker=test_stock,
            start_year=2020,
            end_year=2024,
            use_cache=False
        )
        assert dividend_history is not None
        assert "分红" in dividend_history or "dividend" in dividend_history.lower()

        # 2. 测试分红总结
        dividend_summary = get_dividend_summary(
            ticker=test_stock,
            use_cache=False
        )
        assert dividend_summary is not None

        # 3. 测试股息率计算
        dividend_yield = calculate_dividend_yield(
            ticker=test_stock,
            current_price=1800.0,  # 假设当前价格
            use_cache=False
        )
        assert dividend_yield is not None
        assert "股息率" in dividend_yield or "yield" in dividend_yield.lower()

        # 4. 测试AI分析师股息投资分析工具
        investment_analysis = get_dividend_investment_analysis(
            symbol=test_stock,
            current_price=1800.0
        )
        assert investment_analysis is not None
        assert len(investment_analysis) > 100

    @pytest.mark.integration
    def test_ai_analyst_tools_integration(self, setup_test_data):
        """测试AI分析师工具集成度"""
        test_stock = setup_test_data['test_stocks'][0]

        # 1. 测试市场资金流向概览
        market_overview = get_market_capital_flow_overview()
        assert market_overview is not None
        assert len(market_overview) > 200

        # 2. 测试概念资金流向分析
        concept_cf_analysis = get_concept_capital_flow_analysis(
            concept_name=setup_test_data['test_concepts'][0]
        )
        assert concept_cf_analysis is not None
        assert len(concept_cf_analysis) > 100

        # 3. 测试板块轮动分析
        sector_rotation = get_sector_rotation_analysis()
        assert sector_rotation is not None
        assert len(sector_rotation) > 150

    @pytest.mark.integration
    def test_multi_source_fallback(self, setup_test_data):
        """测试多数据源降级机制"""
        test_stock = setup_test_data['test_stocks'][0]

        # 模拟主数据源失败，测试降级机制
        with patch('tradingagents.dataflows.market_data_capital_flow_utils.EastMoneyCapitalFlow.get_capital_flow_realtime') as mock_primary:
            mock_primary.side_effect = Exception("主数据源异常")

            # 应该自动降级到备用数据源
            result = get_capital_flow_realtime(
                ticker=test_stock,
                use_cache=False
            )
            # 即使主数据源失败，也应该有结果（来自备用数据源）
            assert result is not None or "暂无数据" in str(result)

    @pytest.mark.integration
    def test_cache_performance(self, setup_test_data):
        """测试缓存性能"""
        test_stock = setup_test_data['test_stocks'][0]

        # 第一次调用（无缓存）
        start_time = time.time()
        result1 = get_capital_flow_data(
            ticker=test_stock,
            period=30,
            use_cache=True
        )
        first_call_time = time.time() - start_time

        # 第二次调用（有缓存）
        start_time = time.time()
        result2 = get_capital_flow_data(
            ticker=test_stock,
            period=30,
            use_cache=True
        )
        second_call_time = time.time() - start_time

        # 缓存应该显著提升性能
        assert second_call_time < first_call_time * 0.5
        assert result1 is not None
        assert result2 is not None

    @pytest.mark.integration
    def test_error_handling_robustness(self, setup_test_data):
        """测试错误处理健壮性"""
        # 1. 测试无效股票代码
        invalid_result = get_capital_flow_data(
            ticker="INVALID_CODE",
            period=30,
            use_cache=False
        )
        assert invalid_result is not None  # 应该返回错误信息而不是崩溃

        # 2. 测试无效概念名称
        invalid_concept = get_concept_stocks(
            concept_name="不存在的概念",
            use_cache=False
        )
        assert invalid_concept is not None

        # 3. 测试极端参数
        extreme_result = get_dividend_history(
            ticker=setup_test_data['test_stocks'][0],
            start_year=1990,  # 极早的年份
            end_year=2025,    # 未来年份
            use_cache=False
        )
        assert extreme_result is not None

    @pytest.mark.integration
    def test_data_consistency(self, setup_test_data):
        """测试数据一致性"""
        test_stock = setup_test_data['test_stocks'][0]

        # 多次调用同一接口，验证数据一致性
        results = []
        for _ in range(3):
            result = get_capital_flow_realtime(
                ticker=test_stock,
                use_cache=False
            )
            results.append(result)
            time.sleep(1)  # 间隔1秒

        # 短时间内的数据应该保持相对稳定
        assert len(set(results)) <= 2  # 允许少量变化

    @pytest.mark.integration
    def test_batch_operations(self, setup_test_data):
        """测试批量操作性能"""
        test_stocks = setup_test_data['test_stocks']

        start_time = time.time()

        # 批量获取多个股票的资金流向数据
        results = []
        for stock in test_stocks:
            result = get_capital_flow_analysis(
                symbol=stock,
                analysis_days=3
            )
            results.append(result)

        batch_time = time.time() - start_time

        # 验证所有结果都成功获取
        assert len(results) == len(test_stocks)
        assert all(r is not None for r in results)

        # 批量操作应该在合理时间内完成
        assert batch_time < 60  # 60秒内完成

    @pytest.mark.integration
    def test_real_time_data_freshness(self, setup_test_data):
        """测试实时数据新鲜度"""
        test_stock = setup_test_data['test_stocks'][0]

        # 获取实时数据
        realtime_data = get_capital_flow_realtime(
            ticker=test_stock,
            use_cache=False
        )

        # 验证数据包含时间信息且相对较新
        assert realtime_data is not None
        current_date = datetime.now().strftime('%Y-%m-%d')
        assert current_date in realtime_data or "实时" in realtime_data

    @pytest.mark.integration
    def test_end_to_end_analyst_workflow(self, setup_test_data):
        """测试端到端分析师工作流"""
        test_stock = setup_test_data['test_stocks'][3]  # 贵州茅台
        test_concept = setup_test_data['test_concepts'][0]

        # 模拟技术分析师工作流
        print(f"\n=== 技术分析师工作流测试 ===")

        # 1. 获取市场资金流向概览
        market_overview = get_market_capital_flow_overview()
        assert market_overview is not None
        print(f"市场概览获取成功: {len(market_overview)} 字符")

        # 2. 分析特定股票资金流向
        stock_analysis = get_capital_flow_analysis(
            symbol=test_stock,
            analysis_days=5
        )
        assert stock_analysis is not None
        print(f"股票资金流向分析成功: {len(stock_analysis)} 字符")

        # 3. 分析概念板块资金流向
        concept_analysis = get_concept_capital_flow_analysis(
            concept_name=test_concept
        )
        assert concept_analysis is not None
        print(f"概念资金流向分析成功: {len(concept_analysis)} 字符")

        # 模拟基本面分析师工作流
        print(f"\n=== 基本面分析师工作流测试 ===")

        # 1. 概念基本面分析
        concept_fundamentals = get_concept_fundamentals_analysis(
            concept_name=test_concept
        )
        assert concept_fundamentals is not None
        print(f"概念基本面分析成功: {len(concept_fundamentals)} 字符")

        # 2. 股息投资分析
        dividend_analysis = get_dividend_investment_analysis(
            symbol=test_stock,
            current_price=1800.0
        )
        assert dividend_analysis is not None
        print(f"股息投资分析成功: {len(dividend_analysis)} 字符")

        # 3. 板块轮动分析
        rotation_analysis = get_sector_rotation_analysis()
        assert rotation_analysis is not None
        print(f"板块轮动分析成功: {len(rotation_analysis)} 字符")

        print(f"\n=== 端到端工作流测试完成 ===")


class TestMarketDataPerformance:
    """性能测试专用类"""

    @pytest.mark.performance
    def test_concurrent_requests(self, setup_test_data):
        """测试并发请求性能"""
        import threading
        import concurrent.futures

        test_stocks = setup_test_data['test_stocks']
        results = []
        errors = []

        def fetch_data(stock):
            try:
                result = get_capital_flow_analysis(symbol=stock, analysis_days=3)
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        # 并发执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(fetch_data, stock) for stock in test_stocks]
            concurrent.futures.wait(futures)

        # 验证结果
        assert len(results) >= len(test_stocks) * 0.8  # 至少80%成功率
        assert len(errors) < len(test_stocks) * 0.2   # 错误率低于20%

    @pytest.mark.performance
    def test_memory_usage(self, setup_test_data):
        """测试内存使用情况"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 执行多个数据获取操作
        for stock in setup_test_data['test_stocks']:
            get_capital_flow_analysis(symbol=stock, analysis_days=5)
            get_dividend_investment_analysis(symbol=stock, current_price=100.0)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 内存增长应该控制在合理范围内
        assert memory_increase < 100  # 增长不超过100MB


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "integration"
    ])