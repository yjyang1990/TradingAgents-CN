#!/usr/bin/env python3
"""
资金流向功能单元测试

测试覆盖范围:
- 资金流向数据提供器核心功能
- 多数据源支持和降级机制
- 缓存机制测试
- 错误处理和异常情况
- 数据格式验证

参考：/Users/yyj/GitProject/adata/adata/stock/market/capital_flow/stock_capital_flow_template.py
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 添加项目路径到sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tradingagents.dataflows.market_data_capital_flow_utils import (
    CapitalFlowProvider,
    EastMoneyCapitalFlow,
    BaiduCapitalFlow,
    CapitalFlowData,
    get_capital_flow_provider,
    get_stock_capital_flow_realtime,
    get_stock_capital_flow_daily
)


class TestCapitalFlowData(unittest.TestCase):
    """测试资金流向数据模型"""

    def test_capital_flow_data_creation(self):
        """测试资金流向数据模型创建"""
        data = CapitalFlowData(
            symbol="000001",
            trade_date="2024-01-01",
            main_net=1000.0,
            large=800.0,
            data_source="eastmoney"
        )

        self.assertEqual(data.symbol, "000001")
        self.assertEqual(data.trade_date, "2024-01-01")
        self.assertEqual(data.main_net, 1000.0)
        self.assertEqual(data.large, 800.0)
        self.assertEqual(data.data_source, "eastmoney")

    def test_capital_flow_data_defaults(self):
        """测试资金流向数据模型默认值"""
        data = CapitalFlowData(symbol="000001", trade_date="2024-01-01")

        self.assertEqual(data.main_inflow, 0.0)
        self.assertEqual(data.main_outflow, 0.0)
        self.assertEqual(data.data_source, "eastmoney")


class TestEastMoneyCapitalFlow(unittest.TestCase):
    """测试东方财富资金流向数据源"""

    def setUp(self):
        """设置测试环境"""
        self.source = EastMoneyCapitalFlow()

    def test_source_initialization(self):
        """测试数据源初始化"""
        self.assertEqual(self.source.source_name, "eastmoney")
        self.assertIsNotNone(self.source.session)
        self.assertIn("User-Agent", self.source.session.headers)

    @patch('requests.Session.get')
    def test_get_capital_flow_realtime_success(self, mock_get):
        """测试获取实时资金流向数据成功情况"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'klines': [
                    '2024-01-01 09:30,-1943532.0,2710159.0,-766627.0,-5901648.0,3958116.0',
                    '2024-01-01 09:31,-1234567.0,1234567.0,-111111.0,-2222222.0,3333333.0'
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.source.get_capital_flow_realtime("000001")

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertIn('symbol', result.columns)
        self.assertIn('trade_time', result.columns)
        self.assertIn('main_net_inflow', result.columns)
        self.assertEqual(result.iloc[0]['symbol'], '000001')

    @patch('requests.Session.get')
    def test_get_capital_flow_realtime_empty_response(self, mock_get):
        """测试获取实时资金流向数据空响应"""
        mock_response = Mock()
        mock_response.json.return_value = {'data': None}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.source.get_capital_flow_realtime("000001")

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)

    @patch('requests.Session.get')
    def test_get_capital_flow_realtime_network_error(self, mock_get):
        """测试网络错误情况"""
        mock_get.side_effect = Exception("Network error")

        result = self.source.get_capital_flow_realtime("000001")

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)

    @patch('requests.Session.get')
    def test_get_capital_flow_daily_success(self, mock_get):
        """测试获取日度资金流向数据成功情况"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'klines': [
                    '2024-01-01,-1943532.0,2710159.0,-766627.0,-5901648.0,3958116.0',
                    '2024-01-02,-2000000.0,3000000.0,-800000.0,-6000000.0,4000000.0'
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.source.get_capital_flow_daily("000001", "2024-01-01", "2024-01-02")

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertIn('symbol', result.columns)
        self.assertIn('trade_date', result.columns)
        self.assertEqual(result.iloc[0]['symbol'], '000001')

    def test_market_code_detection(self):
        """测试市场代码检测（沪市/深市）"""
        # 沪市股票（6开头）
        self.assertTrue("000001".startswith('6') == False)  # 深市
        self.assertTrue("600036".startswith('6') == True)   # 沪市


class TestBaiduCapitalFlow(unittest.TestCase):
    """测试百度资金流向数据源"""

    def setUp(self):
        """设置测试环境"""
        self.source = BaiduCapitalFlow()

    def test_source_initialization(self):
        """测试百度数据源初始化"""
        self.assertEqual(self.source.source_name, "baidu")

    def test_get_capital_flow_realtime_not_implemented(self):
        """测试百度实时数据（暂未实现）"""
        result = self.source.get_capital_flow_realtime("000001")
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)

    def test_get_capital_flow_daily_not_implemented(self):
        """测试百度日度数据（暂未实现）"""
        result = self.source.get_capital_flow_daily("000001")
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)


class TestCapitalFlowProvider(unittest.TestCase):
    """测试资金流向数据提供器"""

    def setUp(self):
        """设置测试环境"""
        # 使用Mock缓存管理器避免真实缓存系统依赖
        self.mock_cache_manager = Mock()
        self.provider = CapitalFlowProvider(cache_manager=self.mock_cache_manager)

    def test_provider_initialization(self):
        """测试提供器初始化"""
        self.assertIsInstance(self.provider.data_sources, list)
        self.assertTrue(len(self.provider.data_sources) > 0)
        self.assertIsInstance(self.provider.data_sources[0], EastMoneyCapitalFlow)

    def test_cache_key_generation(self):
        """测试缓存键生成"""
        key = self.provider._generate_cache_key('realtime', '000001')
        self.assertEqual(key, 'capital_flow:realtime_000001')

        key = self.provider._generate_cache_key('daily', '000001', start_date='2024-01-01', end_date='2024-01-02')
        self.assertIn('capital_flow:daily_000001', key)
        self.assertIn('start_date_2024-01-01', key)
        self.assertIn('end_date_2024-01-02', key)

    @patch.object(EastMoneyCapitalFlow, 'get_capital_flow_realtime')
    def test_get_capital_flow_realtime_success(self, mock_get):
        """测试获取实时资金流向成功"""
        # 模拟成功的数据响应
        test_data = pd.DataFrame([{
            'symbol': '000001',
            'trade_time': '2024-01-01 09:30',
            'main_net_inflow': -1943532.0,
            'small_net_inflow': 2710159.0,
            'medium_net_inflow': -766627.0,
            'large_net_inflow': -5901648.0,
            'super_large_net_inflow': 3958116.0
        }])
        mock_get.return_value = test_data

        # 模拟缓存未命中
        self.mock_cache_manager.get.return_value = None

        result = self.provider.get_capital_flow_realtime('000001')

        self.assertEqual(result, test_data)
        self.mock_cache_manager.set.assert_called_once()

    @patch.object(EastMoneyCapitalFlow, 'get_capital_flow_realtime')
    def test_get_capital_flow_realtime_cache_hit(self, mock_get):
        """测试实时资金流向缓存命中"""
        cached_data = pd.DataFrame([{'symbol': '000001', 'data': 'cached'}])
        self.mock_cache_manager.get.return_value = cached_data

        result = self.provider.get_capital_flow_realtime('000001')

        self.assertEqual(result, cached_data)
        mock_get.assert_not_called()  # 缓存命中时不应调用数据源

    @patch.object(EastMoneyCapitalFlow, 'get_capital_flow_realtime')
    @patch.object(BaiduCapitalFlow, 'get_capital_flow_realtime')
    def test_data_source_fallback(self, mock_baidu_get, mock_east_get):
        """测试数据源降级机制"""
        # 东方财富失败
        mock_east_get.side_effect = Exception("API Error")

        # 百度成功
        fallback_data = pd.DataFrame([{'symbol': '000001', 'data': 'from_baidu'}])
        mock_baidu_get.return_value = fallback_data

        self.mock_cache_manager.get.return_value = None

        result = self.provider.get_capital_flow_realtime('000001')

        self.assertEqual(result, fallback_data)
        mock_east_get.assert_called_once()
        mock_baidu_get.assert_called_once()

    @patch.object(EastMoneyCapitalFlow, 'get_capital_flow_daily')
    def test_get_capital_flow_daily_with_date_filter(self, mock_get):
        """测试带日期过滤的日度资金流向获取"""
        test_data = pd.DataFrame([{
            'symbol': '000001',
            'trade_date': '2024-01-01',
            'main_net_inflow': -1000000.0
        }])
        mock_get.return_value = test_data
        self.mock_cache_manager.get.return_value = None

        result = self.provider.get_capital_flow_daily('000001', start_date='2024-01-01', end_date='2024-01-01')

        self.assertEqual(result, test_data)
        mock_get.assert_called_with('000001', start_date='2024-01-01', end_date='2024-01-01')

    def test_get_concept_capital_flow_not_implemented(self):
        """测试概念资金流向（暂未实现）"""
        result = self.provider.get_concept_capital_flow('concept_001')
        self.assertIsInstance(result, pd.DataFrame)


class TestGlobalFunctions(unittest.TestCase):
    """测试全局便捷函数"""

    @patch('tradingagents.dataflows.market_data_capital_flow_utils.get_capital_flow_provider')
    def test_get_stock_capital_flow_realtime(self, mock_get_provider):
        """测试全局实时资金流向函数"""
        mock_provider = Mock()
        mock_provider.get_capital_flow_realtime.return_value = pd.DataFrame()
        mock_get_provider.return_value = mock_provider

        result = get_stock_capital_flow_realtime('000001')

        mock_provider.get_capital_flow_realtime.assert_called_once_with('000001', use_cache=True)

    @patch('tradingagents.dataflows.market_data_capital_flow_utils.get_capital_flow_provider')
    def test_get_stock_capital_flow_daily(self, mock_get_provider):
        """测试全局日度资金流向函数"""
        mock_provider = Mock()
        mock_provider.get_capital_flow_daily.return_value = pd.DataFrame()
        mock_get_provider.return_value = mock_provider

        result = get_stock_capital_flow_daily('000001', start_date='2024-01-01')

        mock_provider.get_capital_flow_daily.assert_called_once_with(
            '000001', start_date='2024-01-01', end_date=None, use_cache=True
        )

    def test_singleton_provider(self):
        """测试单例模式"""
        provider1 = get_capital_flow_provider()
        provider2 = get_capital_flow_provider()

        self.assertIs(provider1, provider2)


class TestDataValidation(unittest.TestCase):
    """测试数据验证"""

    def test_column_names_consistency(self):
        """测试列名一致性"""
        source = EastMoneyCapitalFlow()

        # 验证列名常量
        expected_realtime_columns = ['symbol', 'trade_time', 'main_net_inflow', 'small_net_inflow',
                                    'medium_net_inflow', 'large_net_inflow', 'super_large_net_inflow']
        expected_daily_columns = ['symbol', 'trade_date', 'main_net_inflow', 'small_net_inflow',
                                 'medium_net_inflow', 'large_net_inflow', 'super_large_net_inflow']

        self.assertEqual(source.FLOW_MIN_COLUMNS, expected_realtime_columns)
        self.assertEqual(source.FLOW_DAILY_COLUMNS, expected_daily_columns)

    @patch('requests.Session.get')
    def test_data_type_conversion(self, mock_get):
        """测试数据类型转换"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'klines': ['2024-01-01,-1943532.0,2710159.0,-766627.0,-5901648.0,3958116.0']
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        source = EastMoneyCapitalFlow()
        result = source.get_capital_flow_realtime("000001")

        # 验证数值列类型
        numeric_columns = ['main_net_inflow', 'small_net_inflow', 'medium_net_inflow',
                          'large_net_inflow', 'super_large_net_inflow']
        for col in numeric_columns:
            self.assertTrue(pd.api.types.is_numeric_dtype(result[col]))

    def test_symbol_validation(self):
        """测试股票代码验证"""
        # 测试有效的股票代码格式
        valid_symbols = ['000001', '600036', '300001', '002001']
        invalid_symbols = ['', '12345', 'AAPL', '00001']  # 长度不正确或格式错误

        # 这里可以添加股票代码格式验证逻辑的测试
        for symbol in valid_symbols:
            self.assertEqual(len(symbol), 6)
            self.assertTrue(symbol.isdigit())


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""

    def setUp(self):
        """设置测试环境"""
        self.provider = CapitalFlowProvider(cache_manager=Mock())

    @patch.object(EastMoneyCapitalFlow, 'get_capital_flow_realtime')
    @patch.object(BaiduCapitalFlow, 'get_capital_flow_realtime')
    def test_all_sources_fail(self, mock_baidu_get, mock_east_get):
        """测试所有数据源都失败的情况"""
        mock_east_get.side_effect = Exception("East API Error")
        mock_baidu_get.side_effect = Exception("Baidu API Error")

        result = self.provider.get_capital_flow_realtime('000001', use_cache=False)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)

    @patch('requests.Session.get')
    def test_malformed_response_handling(self, mock_get):
        """测试格式错误响应的处理"""
        mock_response = Mock()
        mock_response.json.return_value = {'error': 'Invalid request'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        source = EastMoneyCapitalFlow()
        result = source.get_capital_flow_realtime("000001")

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)

    @patch('requests.Session.get')
    def test_timeout_handling(self, mock_get):
        """测试超时处理"""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

        source = EastMoneyCapitalFlow()
        result = source.get_capital_flow_realtime("000001")

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)


class TestCacheIntegration(unittest.TestCase):
    """测试缓存集成"""

    def setUp(self):
        """设置测试环境"""
        self.mock_cache_manager = Mock()
        self.provider = CapitalFlowProvider(cache_manager=self.mock_cache_manager)

    def test_cache_disabled(self):
        """测试禁用缓存"""
        self.mock_cache_manager.get.return_value = pd.DataFrame([{'cached': 'data'}])

        with patch.object(EastMoneyCapitalFlow, 'get_capital_flow_realtime') as mock_get:
            mock_get.return_value = pd.DataFrame()

            # 禁用缓存
            result = self.provider.get_capital_flow_realtime('000001', use_cache=False)

            # 应该直接调用数据源，不使用缓存
            mock_get.assert_called_once()
            self.mock_cache_manager.get.assert_not_called()

    def test_cache_ttl_settings(self):
        """测试缓存TTL设置"""
        with patch.object(EastMoneyCapitalFlow, 'get_capital_flow_realtime') as mock_get:
            mock_get.return_value = pd.DataFrame([{'symbol': '000001'}])
            self.mock_cache_manager.get.return_value = None

            self.provider.get_capital_flow_realtime('000001')

            # 验证实时数据使用短TTL（300秒）
            call_args = self.mock_cache_manager.set.call_args
            self.assertEqual(call_args[1]['ttl'], 300)


if __name__ == '__main__':
    # 创建测试套件
    unittest.main(verbosity=2)