#!/usr/bin/env python3
"""
股息数据提供器单元测试

测试股息数据相关功能的各个组件:
- EastMoneyDividendData 数据源
- TushareDividendData 备用数据源
- DividendProvider 提供器
- 全局函数接口
- DataSourceManager 集成
- Interface 函数
- 股息率计算
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

class TestDividendDataModels(unittest.TestCase):
    """测试股息数据模型"""

    def test_dividend_history_data_model(self):
        """测试分红历史数据模型结构"""
        expected_columns = [
            'stock_code', 'notice_date', 'ex_dividend_date', 'record_date',
            'dividend_date', 'plan_explain', 'dividend_ratio', 'transfer_ratio',
            'bonus_ratio', 'impl_plan_profile', 'year', 'dividend_year', 'progress'
        ]

        # 创建测试数据
        test_data = {}
        for col in expected_columns:
            if col in ['dividend_ratio', 'transfer_ratio', 'bonus_ratio']:
                test_data[col] = [0.0]
            else:
                test_data[col] = ['test_value']

        df = pd.DataFrame(test_data)

        # 验证所有必需列都存在
        for col in expected_columns:
            self.assertIn(col, df.columns, f"缺少必需字段: {col}")

    def test_dividend_summary_data_model(self):
        """测试分红汇总数据模型结构"""
        expected_fields = [
            'stock_code', 'total_dividend_count', 'total_dividend_amount',
            'avg_dividend_ratio', 'latest_dividend', 'yearly_dividends', 'dividend_stability'
        ]

        # 创建测试数据
        test_data = {
            'stock_code': '000001',
            'total_dividend_count': 5,
            'total_dividend_amount': 1.25,
            'avg_dividend_ratio': 0.25,
            'latest_dividend': {
                'notice_date': '2023-05-15',
                'ex_dividend_date': '2023-06-01',
                'dividend_ratio': 0.30,
                'plan_explain': '每股派息0.3元',
                'progress': '实施'
            },
            'yearly_dividends': {'2023': 0.30, '2022': 0.25, '2021': 0.20},
            'dividend_stability': 1.0
        }

        # 验证所有必需字段都存在
        for field in expected_fields:
            self.assertIn(field, test_data, f"缺少必需字段: {field}")

    def test_dividend_yield_data_model(self):
        """测试股息率数据模型结构"""
        expected_fields = ['dividend_yield', 'annual_dividend', 'current_price', 'calculation_date']

        # 创建测试数据
        test_data = {
            'dividend_yield': 3.5,
            'annual_dividend': 0.35,
            'current_price': 10.0,
            'calculation_date': '2023-12-25'
        }

        # 验证所有必需字段都存在
        for field in expected_fields:
            self.assertIn(field, test_data, f"缺少必需字段: {field}")


class TestEastMoneyDividendData(unittest.TestCase):
    """测试东方财富股息数据源"""

    def setUp(self):
        """设置测试环境"""
        with patch('tradingagents.dataflows.market_data_dividend_utils.logger', None):
            from tradingagents.dataflows.market_data_dividend_utils import EastMoneyDividendData
            self.data_source = EastMoneyDividendData()

    @patch('requests.Session.get')
    def test_get_dividend_history_success(self, mock_get):
        """测试成功获取分红历史"""
        # Mock 响应数据
        mock_response_text = """YCdyyrYdMu({"result": {"data": [
            {
                "NOTICE_DATE": "2023-05-15",
                "EX_DIVIDEND_DATE": "2023-06-01",
                "RECORD_DATE": "2023-05-31",
                "DIVIDEND_DATE": "2023-06-05",
                "PLAN_EXPLAIN": "每股派息0.30元",
                "DIVIDEND_RATIO": 0.30,
                "TRANSFER_RATIO": 0.0,
                "BONUS_RATIO": 0.0,
                "IMPL_PLAN_PROFILE": "每股派息0.30元",
                "YEAR": "2023",
                "DIVIDEND_YEAR": "2022",
                "PROGRESS": "实施"
            },
            {
                "NOTICE_DATE": "2022-05-15",
                "EX_DIVIDEND_DATE": "2022-06-01",
                "RECORD_DATE": "2022-05-31",
                "DIVIDEND_DATE": "2022-06-05",
                "PLAN_EXPLAIN": "每股派息0.25元",
                "DIVIDEND_RATIO": 0.25,
                "TRANSFER_RATIO": 0.0,
                "BONUS_RATIO": 0.0,
                "IMPL_PLAN_PROFILE": "每股派息0.25元",
                "YEAR": "2022",
                "DIVIDEND_YEAR": "2021",
                "PROGRESS": "实施"
            }
        ]}, "success": true});"""

        mock_response = Mock()
        mock_response.text = mock_response_text
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # 调用方法
        result = self.data_source.get_dividend_history("000001")

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertIn('stock_code', result.columns)
        self.assertIn('dividend_ratio', result.columns)
        self.assertEqual(result.iloc[0]['dividend_ratio'], 0.30)
        self.assertEqual(result.iloc[1]['dividend_ratio'], 0.25)

    @patch('requests.Session.get')
    def test_get_dividend_history_network_error(self, mock_get):
        """测试网络错误处理"""
        mock_get.side_effect = Exception("网络连接失败")

        result = self.data_source.get_dividend_history("000001")

        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)

    def test_get_dividend_summary_with_data(self):
        """测试分红汇总计算"""
        # Mock get_dividend_history方法
        mock_df = pd.DataFrame({
            'stock_code': ['000001.SZ', '000001.SZ', '000001.SZ'],
            'dividend_ratio': [0.30, 0.25, 0.20],
            'year': ['2023', '2022', '2021'],
            'notice_date': ['2023-05-15', '2022-05-15', '2021-05-15'],
            'ex_dividend_date': ['2023-06-01', '2022-06-01', '2021-06-01'],
            'plan_explain': ['每股派息0.30元', '每股派息0.25元', '每股派息0.20元'],
            'progress': ['实施', '实施', '实施']
        })

        with patch.object(self.data_source, 'get_dividend_history', return_value=mock_df):
            result = self.data_source.get_dividend_summary("000001")

        self.assertIsInstance(result, dict)
        self.assertEqual(result['total_dividend_count'], 3)
        self.assertEqual(result['total_dividend_amount'], 0.75)
        self.assertEqual(result['avg_dividend_ratio'], 0.25)
        self.assertIn('latest_dividend', result)
        self.assertIn('yearly_dividends', result)

    def test_calculate_dividend_yield_with_price(self):
        """测试股息率计算（提供股价）"""
        # Mock get_dividend_history方法
        mock_df = pd.DataFrame({
            'dividend_ratio': [0.30]
        })

        with patch.object(self.data_source, 'get_dividend_history', return_value=mock_df):
            result = self.data_source.calculate_dividend_yield("000001", current_price=10.0)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['dividend_yield'], 3.0)  # 0.30 / 10.0 * 100
        self.assertEqual(result['annual_dividend'], 0.30)
        self.assertEqual(result['current_price'], 10.0)

    def test_calculate_dividend_yield_without_price(self):
        """测试股息率计算（未提供股价）"""
        # Mock get_dividend_history方法
        mock_df = pd.DataFrame({
            'dividend_ratio': [0.30]
        })

        with patch.object(self.data_source, 'get_dividend_history', return_value=mock_df):
            result = self.data_source.calculate_dividend_yield("000001")

        self.assertIsInstance(result, dict)
        self.assertEqual(result['dividend_yield'], 0.0)
        self.assertEqual(result['annual_dividend'], 0.30)
        self.assertIn('error', result)


class TestTushareDividendData(unittest.TestCase):
    """测试Tushare股息数据源（备用）"""

    def setUp(self):
        """设置测试环境"""
        with patch('tradingagents.dataflows.market_data_dividend_utils.logger', None):
            from tradingagents.dataflows.market_data_dividend_utils import TushareDividendData
            self.data_source = TushareDividendData()

    def test_get_dividend_history_placeholder(self):
        """测试获取分红历史（占位实现）"""
        result = self.data_source.get_dividend_history("000001")

        # 备用数据源当前返回空DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)

    def test_get_dividend_summary_placeholder(self):
        """测试获取分红汇总（占位实现）"""
        result = self.data_source.get_dividend_summary("000001")

        # 备用数据源当前返回空字典
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_calculate_dividend_yield_placeholder(self):
        """测试股息率计算（占位实现）"""
        result = self.data_source.calculate_dividend_yield("000001", 10.0)

        # 备用数据源返回默认值
        self.assertIsInstance(result, dict)
        self.assertEqual(result['dividend_yield'], 0.0)
        self.assertEqual(result['annual_dividend'], 0.0)
        self.assertIn('error', result)


class TestDividendProvider(unittest.TestCase):
    """测试股息数据提供器"""

    def setUp(self):
        """设置测试环境"""
        with patch('tradingagents.dataflows.market_data_dividend_utils.cache_manager', None), \
             patch('tradingagents.dataflows.market_data_dividend_utils.logger', None):
            from tradingagents.dataflows.market_data_dividend_utils import DividendProvider
            self.provider = DividendProvider()

    def test_get_dividend_history_with_cache(self):
        """测试带缓存的获取分红历史"""
        # Mock 缓存管理器
        mock_cache_manager = Mock()
        mock_cache_manager.get.return_value = None

        # Mock 主数据源
        mock_primary_result = pd.DataFrame({
            'stock_code': ['000001', '000001'],
            'dividend_ratio': [0.30, 0.25],
            'year': ['2023', '2022'],
            'notice_date': ['2023-05-15', '2022-05-15']
        })

        with patch('tradingagents.dataflows.market_data_dividend_utils.cache_manager', mock_cache_manager):
            self.provider.primary_source.get_dividend_history = Mock(return_value=mock_primary_result)

            result = self.provider.get_dividend_history("000001", use_cache=True)

            # 验证结果
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 2)
            self.assertEqual(result.iloc[0]['dividend_ratio'], 0.30)

            # 验证缓存操作
            mock_cache_manager.get.assert_called_once()
            mock_cache_manager.set.assert_called_once()

    def test_get_dividend_history_fallback(self):
        """测试数据源降级机制"""
        # Mock 主数据源失败
        self.provider.primary_source.get_dividend_history = Mock(side_effect=Exception("主数据源失败"))

        # Mock 备用数据源成功
        fallback_result = pd.DataFrame({
            'stock_code': ['000001'],
            'dividend_ratio': [0.20],
            'year': ['2021']
        })
        self.provider.fallback_source.get_dividend_history = Mock(return_value=fallback_result)

        result = self.provider.get_dividend_history("000001", use_cache=False)

        # 验证降级成功
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['dividend_ratio'], 0.20)

    def test_get_dividend_summary_with_cache(self):
        """测试带缓存的获取分红汇总"""
        # Mock 缓存管理器
        mock_cache_manager = Mock()
        mock_cache_manager.get.return_value = None

        # Mock 主数据源
        mock_summary = {
            'stock_code': '000001',
            'total_dividend_count': 3,
            'total_dividend_amount': 0.75,
            'avg_dividend_ratio': 0.25
        }

        with patch('tradingagents.dataflows.market_data_dividend_utils.cache_manager', mock_cache_manager):
            self.provider.primary_source.get_dividend_summary = Mock(return_value=mock_summary)

            result = self.provider.get_dividend_summary("000001", use_cache=True)

            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertEqual(result['total_dividend_count'], 3)
            self.assertEqual(result['total_dividend_amount'], 0.75)

            # 验证缓存操作
            mock_cache_manager.get.assert_called_once()
            mock_cache_manager.set.assert_called_once()

    def test_calculate_dividend_yield_with_cache(self):
        """测试带缓存的股息率计算"""
        # Mock 缓存管理器
        mock_cache_manager = Mock()
        mock_cache_manager.get.return_value = None

        # Mock 主数据源
        mock_yield_result = {
            'dividend_yield': 3.0,
            'annual_dividend': 0.30,
            'current_price': 10.0,
            'calculation_date': '2023-12-25'
        }

        with patch('tradingagents.dataflows.market_data_dividend_utils.cache_manager', mock_cache_manager):
            self.provider.primary_source.calculate_dividend_yield = Mock(return_value=mock_yield_result)

            result = self.provider.calculate_dividend_yield("000001", current_price=10.0, use_cache=True)

            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertEqual(result['dividend_yield'], 3.0)
            self.assertEqual(result['annual_dividend'], 0.30)

            # 验证缓存操作
            mock_cache_manager.get.assert_called_once()
            mock_cache_manager.set.assert_called_once()


class TestDividendGlobalFunctions(unittest.TestCase):
    """测试股息数据全局函数"""

    @patch('tradingagents.dataflows.market_data_dividend_utils.get_dividend_provider')
    def test_get_dividend_history_function(self, mock_get_provider):
        """测试全局get_dividend_history函数"""
        # Mock 提供器
        mock_provider = Mock()
        mock_provider.get_dividend_history.return_value = pd.DataFrame({
            'stock_code': ['000001'],
            'dividend_ratio': [0.30]
        })
        mock_get_provider.return_value = mock_provider

        from tradingagents.dataflows.market_data_dividend_utils import get_dividend_history

        result = get_dividend_history("000001", start_year=2020, end_year=2023, use_cache=True)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        mock_provider.get_dividend_history.assert_called_once_with("000001", start_year=2020, end_year=2023, use_cache=True)

    @patch('tradingagents.dataflows.market_data_dividend_utils.get_dividend_provider')
    def test_get_dividend_summary_function(self, mock_get_provider):
        """测试全局get_dividend_summary函数"""
        # Mock 提供器
        mock_provider = Mock()
        mock_provider.get_dividend_summary.return_value = {
            'stock_code': '000001',
            'total_dividend_count': 3
        }
        mock_get_provider.return_value = mock_provider

        from tradingagents.dataflows.market_data_dividend_utils import get_dividend_summary

        result = get_dividend_summary("000001", use_cache=False)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['total_dividend_count'], 3)
        mock_provider.get_dividend_summary.assert_called_once_with("000001", use_cache=False)

    @patch('tradingagents.dataflows.market_data_dividend_utils.get_dividend_provider')
    def test_calculate_dividend_yield_function(self, mock_get_provider):
        """测试全局calculate_dividend_yield函数"""
        # Mock 提供器
        mock_provider = Mock()
        mock_provider.calculate_dividend_yield.return_value = {
            'dividend_yield': 4.0,
            'annual_dividend': 0.40,
            'current_price': 10.0
        }
        mock_get_provider.return_value = mock_provider

        from tradingagents.dataflows.market_data_dividend_utils import calculate_dividend_yield

        result = calculate_dividend_yield("000001", current_price=10.0, use_cache=True)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['dividend_yield'], 4.0)
        mock_provider.calculate_dividend_yield.assert_called_once_with("000001", current_price=10.0, use_cache=True)


class TestDataSourceManagerIntegration(unittest.TestCase):
    """测试DataSourceManager集成"""

    @patch('tradingagents.dataflows.data_source_manager.logger')
    @patch('tradingagents.dataflows.market_data_dividend_utils.get_dividend_provider')
    def test_data_source_manager_get_dividend_history(self, mock_get_provider, mock_logger):
        """测试DataSourceManager的get_dividend_history方法"""
        # Mock 股息提供器
        mock_provider = Mock()
        mock_provider.get_dividend_history.return_value = pd.DataFrame({
            'stock_code': ['000001', '000001'],
            'dividend_ratio': [0.30, 0.25],
            'year': ['2023', '2022'],
            'notice_date': ['2023-05-15', '2022-05-15'],
            'ex_dividend_date': ['2023-06-01', '2022-06-01'],
            'plan_explain': ['每股派息0.30元', '每股派息0.25元'],
            'progress': ['实施', '实施']
        })
        mock_get_provider.return_value = mock_provider

        from tradingagents.dataflows.data_source_manager import DataSourceManager

        manager = DataSourceManager()
        result = manager.get_dividend_history("000001", start_year=2020, end_year=2023, use_cache=True)

        # 验证返回格式化字符串
        self.assertIsInstance(result, str)
        self.assertIn("分红历史数据", result)
        self.assertIn("每股派息0.30元", result)
        self.assertIn("每股派息0.25元", result)
        mock_provider.get_dividend_history.assert_called_once_with("000001", start_year=2020, end_year=2023, use_cache=True)

    @patch('tradingagents.dataflows.data_source_manager.logger')
    @patch('tradingagents.dataflows.market_data_dividend_utils.get_dividend_provider')
    def test_data_source_manager_get_dividend_summary(self, mock_get_provider, mock_logger):
        """测试DataSourceManager的get_dividend_summary方法"""
        # Mock 股息提供器
        mock_provider = Mock()
        mock_provider.get_dividend_summary.return_value = {
            'stock_code': '000001',
            'total_dividend_count': 3,
            'total_dividend_amount': 0.75,
            'avg_dividend_ratio': 0.25,
            'latest_dividend': {
                'notice_date': '2023-05-15',
                'ex_dividend_date': '2023-06-01',
                'dividend_ratio': 0.30,
                'plan_explain': '每股派息0.30元',
                'progress': '实施'
            },
            'yearly_dividends': {'2023': 0.30, '2022': 0.25, '2021': 0.20},
            'dividend_stability': 1.0
        }
        mock_get_provider.return_value = mock_provider

        from tradingagents.dataflows.data_source_manager import DataSourceManager

        manager = DataSourceManager()
        result = manager.get_dividend_summary("000001", use_cache=False)

        # 验证返回格式化字符串
        self.assertIsInstance(result, str)
        self.assertIn("分红汇总分析", result)
        self.assertIn("总分红次数: 3次", result)
        self.assertIn("每股派息0.30元", result)
        mock_provider.get_dividend_summary.assert_called_once_with("000001", use_cache=False)

    @patch('tradingagents.dataflows.data_source_manager.logger')
    @patch('tradingagents.dataflows.market_data_dividend_utils.get_dividend_provider')
    def test_data_source_manager_calculate_dividend_yield(self, mock_get_provider, mock_logger):
        """测试DataSourceManager的calculate_dividend_yield方法"""
        # Mock 股息提供器
        mock_provider = Mock()
        mock_provider.calculate_dividend_yield.return_value = {
            'dividend_yield': 4.5,
            'annual_dividend': 0.45,
            'current_price': 10.0,
            'calculation_date': '2023-12-25'
        }
        mock_get_provider.return_value = mock_provider

        from tradingagents.dataflows.data_source_manager import DataSourceManager

        manager = DataSourceManager()
        result = manager.calculate_dividend_yield("000001", current_price=10.0, use_cache=True)

        # 验证返回格式化字符串
        self.assertIsInstance(result, str)
        self.assertIn("股息率分析", result)
        self.assertIn("股息率: 4.50%", result)
        self.assertIn("良好", result)  # 4.5%应该被评为良好
        mock_provider.calculate_dividend_yield.assert_called_once_with("000001", current_price=10.0, use_cache=True)


class TestInterfaceFunctions(unittest.TestCase):
    """测试Interface接口函数"""

    @patch('tradingagents.dataflows.interface.logger')
    @patch('tradingagents.dataflows.data_source_manager.get_data_source_manager')
    def test_interface_get_dividend_history(self, mock_get_manager, mock_logger):
        """测试接口层get_dividend_history函数"""
        # Mock DataSourceManager
        mock_manager = Mock()
        mock_manager.get_dividend_history.return_value = "分红历史数据报告"
        mock_get_manager.return_value = mock_manager

        from tradingagents.dataflows.interface import get_dividend_history

        result = get_dividend_history("000001", start_year=2020, end_year=2023, use_cache=True)

        self.assertEqual(result, "分红历史数据报告")
        mock_manager.get_dividend_history.assert_called_once_with("000001", start_year=2020, end_year=2023, use_cache=True)

    @patch('tradingagents.dataflows.interface.logger')
    @patch('tradingagents.dataflows.data_source_manager.get_data_source_manager')
    def test_interface_get_dividend_summary(self, mock_get_manager, mock_logger):
        """测试接口层get_dividend_summary函数"""
        # Mock DataSourceManager
        mock_manager = Mock()
        mock_manager.get_dividend_summary.return_value = "分红汇总分析报告"
        mock_get_manager.return_value = mock_manager

        from tradingagents.dataflows.interface import get_dividend_summary

        result = get_dividend_summary("000001", use_cache=False)

        self.assertEqual(result, "分红汇总分析报告")
        mock_manager.get_dividend_summary.assert_called_once_with("000001", use_cache=False)

    @patch('tradingagents.dataflows.interface.logger')
    @patch('tradingagents.dataflows.data_source_manager.get_data_source_manager')
    def test_interface_calculate_dividend_yield(self, mock_get_manager, mock_logger):
        """测试接口层calculate_dividend_yield函数"""
        # Mock DataSourceManager
        mock_manager = Mock()
        mock_manager.calculate_dividend_yield.return_value = "股息率分析报告"
        mock_get_manager.return_value = mock_manager

        from tradingagents.dataflows.interface import calculate_dividend_yield

        result = calculate_dividend_yield("000001", current_price=10.0, use_cache=True)

        self.assertEqual(result, "股息率分析报告")
        mock_manager.calculate_dividend_yield.assert_called_once_with("000001", current_price=10.0, use_cache=True)


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""

    @patch('tradingagents.dataflows.market_data_dividend_utils.logger')
    def test_dividend_provider_both_sources_fail(self, mock_logger):
        """测试主备数据源都失败的情况"""
        with patch('tradingagents.dataflows.market_data_dividend_utils.cache_manager', None):
            from tradingagents.dataflows.market_data_dividend_utils import DividendProvider

            provider = DividendProvider()
            provider.primary_source.get_dividend_history = Mock(side_effect=Exception("主数据源失败"))
            provider.fallback_source.get_dividend_history = Mock(side_effect=Exception("备用数据源失败"))

            result = provider.get_dividend_history("000001", use_cache=False)

            # 应该返回空DataFrame
            self.assertIsInstance(result, pd.DataFrame)
            self.assertTrue(result.empty)

    @patch('tradingagents.dataflows.interface.logger')
    def test_interface_exception_handling(self, mock_logger):
        """测试接口层异常处理"""
        with patch('tradingagents.dataflows.data_source_manager.get_data_source_manager',
                   side_effect=Exception("数据源管理器初始化失败")):
            from tradingagents.dataflows.interface import get_dividend_history

            result = get_dividend_history("000001")

            # 应该返回错误消息
            self.assertIsInstance(result, str)
            self.assertIn("获取股票000001分红历史失败", result)


class TestDividendYieldCalculation(unittest.TestCase):
    """测试股息率计算逻辑"""

    def test_dividend_yield_calculation_accuracy(self):
        """测试股息率计算准确性"""
        # 测试场景：年度分红0.50元，当前股价10.00元
        annual_dividend = 0.50
        current_price = 10.00
        expected_yield = (annual_dividend / current_price) * 100  # 5.0%

        # Mock 东方财富数据源
        with patch('tradingagents.dataflows.market_data_dividend_utils.logger', None):
            from tradingagents.dataflows.market_data_dividend_utils import EastMoneyDividendData

            data_source = EastMoneyDividendData()

            # Mock get_dividend_history返回测试数据
            mock_df = pd.DataFrame({
                'dividend_ratio': [annual_dividend]
            })

            with patch.object(data_source, 'get_dividend_history', return_value=mock_df):
                result = data_source.calculate_dividend_yield("000001", current_price)

            self.assertEqual(result['dividend_yield'], expected_yield)
            self.assertEqual(result['annual_dividend'], annual_dividend)
            self.assertEqual(result['current_price'], current_price)

    def test_dividend_yield_edge_cases(self):
        """测试股息率计算边界情况"""
        with patch('tradingagents.dataflows.market_data_dividend_utils.logger', None):
            from tradingagents.dataflows.market_data_dividend_utils import EastMoneyDividendData

            data_source = EastMoneyDividendData()

            # 测试股价为0的情况
            mock_df = pd.DataFrame({'dividend_ratio': [0.30]})
            with patch.object(data_source, 'get_dividend_history', return_value=mock_df):
                result = data_source.calculate_dividend_yield("000001", 0.0)

            self.assertEqual(result['dividend_yield'], 0.0)

            # 测试无分红数据的情况
            empty_df = pd.DataFrame()
            with patch.object(data_source, 'get_dividend_history', return_value=empty_df):
                result = data_source.calculate_dividend_yield("000001", 10.0)

            self.assertEqual(result['dividend_yield'], 0.0)
            self.assertIn('error', result)


class TestCacheIntegration(unittest.TestCase):
    """测试缓存集成"""

    def test_cache_operations(self):
        """测试缓存操作"""
        # Mock 缓存管理器
        mock_cache_manager = Mock()
        mock_cache_manager.get.return_value = pd.DataFrame({
            'stock_code': ['000001'],
            'dividend_ratio': [0.25],
            'year': ['2023']
        })

        with patch('tradingagents.dataflows.market_data_dividend_utils.cache_manager', mock_cache_manager), \
             patch('tradingagents.dataflows.market_data_dividend_utils.logger', None):
            from tradingagents.dataflows.market_data_dividend_utils import DividendProvider

            provider = DividendProvider()
            result = provider.get_dividend_history("000001", use_cache=True)

            # 验证使用了缓存数据
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 1)
            self.assertEqual(result.iloc[0]['dividend_ratio'], 0.25)
            mock_cache_manager.get.assert_called_once()

    def test_cache_ttl_settings(self):
        """测试缓存TTL设置"""
        mock_cache_manager = Mock()
        mock_cache_manager.get.return_value = None

        # Mock 主数据源返回数据
        mock_df = pd.DataFrame({
            'stock_code': ['000001'],
            'dividend_ratio': [0.30]
        })

        with patch('tradingagents.dataflows.market_data_dividend_utils.cache_manager', mock_cache_manager), \
             patch('tradingagents.dataflows.market_data_dividend_utils.logger', None):
            from tradingagents.dataflows.market_data_dividend_utils import DividendProvider

            provider = DividendProvider()
            provider.primary_source.get_dividend_history = Mock(return_value=mock_df)

            # 调用方法
            provider.get_dividend_history("000001", use_cache=True)

            # 验证缓存设置时使用了正确的TTL（3600秒）
            mock_cache_manager.set.assert_called_once()
            args = mock_cache_manager.set.call_args
            self.assertEqual(args[1]['ttl'], 3600)  # 1小时缓存


if __name__ == '__main__':
    unittest.main()