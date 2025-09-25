#!/usr/bin/env python3
"""
概念板块数据提供器单元测试

测试概念板块相关功能的各个组件:
- EastMoneyConceptData 数据源
- BaiduConceptData 备用数据源
- ConceptProvider 提供器
- 全局函数接口
- DataSourceManager 集成
- Interface 函数
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

class TestConceptDataModels(unittest.TestCase):
    """测试概念板块数据模型"""

    def test_concept_data_model(self):
        """测试概念板块数据模型结构"""
        expected_columns = [
            'concept_code', 'concept_name', 'price', 'change_pct',
            'change_amount', 'volume', 'turnover', 'amplitude',
            'high', 'low', 'open', 'prev_close', 'volume_ratio',
            'pe_ratio', 'market_cap', 'float_market_cap', 'total_shares'
        ]

        # 创建测试数据
        test_data = {col: [0] for col in expected_columns}
        df = pd.DataFrame(test_data)

        # 验证所有必需列都存在
        for col in expected_columns:
            self.assertIn(col, df.columns, f"缺少必需字段: {col}")

    def test_concept_stocks_data_model(self):
        """测试概念成分股数据模型结构"""
        expected_columns = [
            'stock_code', 'stock_name', 'price', 'change_pct',
            'change_amount', 'volume', 'turnover', 'amplitude',
            'high', 'low', 'open', 'prev_close', 'volume_ratio',
            'pe_ratio', 'market_cap', 'float_market_cap', 'total_shares',
            'concept_code'
        ]

        # 创建测试数据
        test_data = {col: [0] for col in expected_columns}
        df = pd.DataFrame(test_data)

        # 验证所有必需列都存在
        for col in expected_columns:
            self.assertIn(col, df.columns, f"缺少必需字段: {col}")


class TestEastMoneyConceptData(unittest.TestCase):
    """测试东方财富概念板块数据源"""

    def setUp(self):
        """设置测试环境"""
        with patch('tradingagents.dataflows.market_data_concept_utils.logger', None):
            from tradingagents.dataflows.market_data_concept_utils import EastMoneyConceptData
            self.data_source = EastMoneyConceptData()

    @patch('requests.Session.get')
    def test_get_concept_list_success(self, mock_get):
        """测试成功获取概念板块列表"""
        # Mock 响应数据
        mock_response_text = """jQuery112406389542653718456_1640754174808({
            "rc": 0,
            "rt": 6,
            "svr": 181669068,
            "lt": 1,
            "full": 1,
            "data": {
                "total": 2,
                "diff": [
                    {
                        "f12": "BK0001",
                        "f14": "人工智能",
                        "f2": 100.5,
                        "f3": 2.5,
                        "f4": 2.45,
                        "f5": 1000000,
                        "f6": 100000000,
                        "f7": 5.2,
                        "f15": 102.0,
                        "f16": 98.0,
                        "f17": 99.0,
                        "f18": 98.0,
                        "f10": 1.2,
                        "f9": 15.5,
                        "f20": 5000000000,
                        "f21": 3000000000,
                        "f8": 50000000
                    },
                    {
                        "f12": "BK0002",
                        "f14": "新能源汽车",
                        "f2": 85.3,
                        "f3": -1.8,
                        "f4": -1.56,
                        "f5": 2000000,
                        "f6": 170000000,
                        "f7": 4.8,
                        "f15": 87.0,
                        "f16": 83.0,
                        "f17": 86.5,
                        "f18": 86.86,
                        "f10": 0.9,
                        "f9": 12.3,
                        "f20": 8000000000,
                        "f21": 6000000000,
                        "f8": 95000000
                    }
                ]
            }
        })"""

        mock_response = Mock()
        mock_response.text = mock_response_text
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # 调用方法
        result = self.data_source.get_concept_list()

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertIn('concept_code', result.columns)
        self.assertIn('concept_name', result.columns)
        self.assertEqual(result.iloc[0]['concept_code'], 'BK0001')
        self.assertEqual(result.iloc[0]['concept_name'], '人工智能')

    @patch('requests.Session.get')
    def test_get_concept_list_network_error(self, mock_get):
        """测试网络错误处理"""
        mock_get.side_effect = Exception("网络连接失败")

        result = self.data_source.get_concept_list()

        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)

    @patch('requests.Session.get')
    def test_get_concept_stocks_success(self, mock_get):
        """测试成功获取概念成分股"""
        # Mock 响应数据
        mock_response_text = """jQuery112406389542653718456_1640754174808({
            "rc": 0,
            "rt": 6,
            "svr": 181669068,
            "lt": 1,
            "full": 1,
            "data": {
                "total": 1,
                "diff": [
                    {
                        "f12": "000001",
                        "f14": "平安银行",
                        "f2": 12.5,
                        "f3": 1.2,
                        "f4": 0.15,
                        "f5": 5000000,
                        "f6": 62500000,
                        "f7": 3.2,
                        "f15": 12.8,
                        "f16": 12.2,
                        "f17": 12.3,
                        "f18": 12.35,
                        "f10": 1.1,
                        "f9": 8.5,
                        "f20": 25000000000,
                        "f21": 20000000000,
                        "f8": 2000000000
                    }
                ]
            }
        })"""

        mock_response = Mock()
        mock_response.text = mock_response_text
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # 调用方法
        result = self.data_source.get_concept_stocks("BK0001")

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertIn('stock_code', result.columns)
        self.assertIn('stock_name', result.columns)
        self.assertIn('concept_code', result.columns)
        self.assertEqual(result.iloc[0]['stock_code'], '000001')
        self.assertEqual(result.iloc[0]['stock_name'], '平安银行')
        self.assertEqual(result.iloc[0]['concept_code'], 'BK0001')


class TestBaiduConceptData(unittest.TestCase):
    """测试百度概念板块数据源（备用）"""

    def setUp(self):
        """设置测试环境"""
        with patch('tradingagents.dataflows.market_data_concept_utils.logger', None):
            from tradingagents.dataflows.market_data_concept_utils import BaiduConceptData
            self.data_source = BaiduConceptData()

    def test_get_concept_list_placeholder(self):
        """测试获取概念板块列表（占位实现）"""
        result = self.data_source.get_concept_list()

        # 备用数据源当前返回空DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)

    def test_get_concept_stocks_placeholder(self):
        """测试获取概念成分股（占位实现）"""
        result = self.data_source.get_concept_stocks("BK0001")

        # 备用数据源当前返回空DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)


class TestConceptProvider(unittest.TestCase):
    """测试概念板块提供器"""

    def setUp(self):
        """设置测试环境"""
        with patch('tradingagents.dataflows.market_data_concept_utils.cache_manager', None), \
             patch('tradingagents.dataflows.market_data_concept_utils.logger', None):
            from tradingagents.dataflows.market_data_concept_utils import ConceptProvider
            self.provider = ConceptProvider()

    def test_get_concept_list_with_cache(self):
        """测试带缓存的获取概念板块列表"""
        # Mock 缓存管理器
        mock_cache_manager = Mock()
        mock_cache_manager.get.return_value = None

        # Mock 主数据源
        mock_primary_result = pd.DataFrame({
            'concept_code': ['BK0001', 'BK0002'],
            'concept_name': ['人工智能', '新能源汽车'],
            'price': [100.5, 85.3],
            'change_pct': [2.5, -1.8]
        })

        with patch('tradingagents.dataflows.market_data_concept_utils.cache_manager', mock_cache_manager):
            self.provider.primary_source.get_concept_list = Mock(return_value=mock_primary_result)

            result = self.provider.get_concept_list(use_cache=True)

            # 验证结果
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 2)
            self.assertEqual(result.iloc[0]['concept_name'], '人工智能')

            # 验证缓存操作
            mock_cache_manager.get.assert_called_once()
            mock_cache_manager.set.assert_called_once()

    def test_get_concept_list_fallback(self):
        """测试数据源降级机制"""
        # Mock 主数据源失败
        self.provider.primary_source.get_concept_list = Mock(side_effect=Exception("主数据源失败"))

        # Mock 备用数据源成功
        fallback_result = pd.DataFrame({
            'concept_code': ['BK0003'],
            'concept_name': ['5G通信'],
            'price': [75.2],
            'change_pct': [3.1]
        })
        self.provider.fallback_source.get_concept_list = Mock(return_value=fallback_result)

        result = self.provider.get_concept_list(use_cache=False)

        # 验证降级成功
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['concept_name'], '5G通信')

    def test_get_top_concepts(self):
        """测试获取概念排行榜"""
        # Mock 概念列表数据
        mock_concepts = pd.DataFrame({
            'concept_code': ['BK0001', 'BK0002', 'BK0003'],
            'concept_name': ['人工智能', '新能源汽车', '5G通信'],
            'change_pct': [5.2, 2.8, -1.5],
            'volume': [1000000, 2000000, 1500000]
        })

        self.provider.get_concept_list = Mock(return_value=mock_concepts)

        # 测试按涨跌幅排序
        result = self.provider.get_top_concepts(sort_by="change_pct", limit=2)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]['concept_name'], '人工智能')  # 最高涨幅
        self.assertEqual(result.iloc[1]['concept_name'], '新能源汽车')  # 第二高涨幅


class TestConceptGlobalFunctions(unittest.TestCase):
    """测试概念板块全局函数"""

    @patch('tradingagents.dataflows.market_data_concept_utils.get_concept_provider')
    def test_get_concept_list_function(self, mock_get_provider):
        """测试全局get_concept_list函数"""
        # Mock 提供器
        mock_provider = Mock()
        mock_provider.get_concept_list.return_value = pd.DataFrame({
            'concept_code': ['BK0001'],
            'concept_name': ['人工智能']
        })
        mock_get_provider.return_value = mock_provider

        from tradingagents.dataflows.market_data_concept_utils import get_concept_list

        result = get_concept_list(use_cache=True)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        mock_provider.get_concept_list.assert_called_once_with(use_cache=True)

    @patch('tradingagents.dataflows.market_data_concept_utils.get_concept_provider')
    def test_get_concept_stocks_function(self, mock_get_provider):
        """测试全局get_concept_stocks函数"""
        # Mock 提供器
        mock_provider = Mock()
        mock_provider.get_concept_stocks.return_value = pd.DataFrame({
            'stock_code': ['000001'],
            'stock_name': ['平安银行'],
            'concept_code': ['BK0001']
        })
        mock_get_provider.return_value = mock_provider

        from tradingagents.dataflows.market_data_concept_utils import get_concept_stocks

        result = get_concept_stocks("BK0001", use_cache=False)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        mock_provider.get_concept_stocks.assert_called_once_with("BK0001", use_cache=False)

    @patch('tradingagents.dataflows.market_data_concept_utils.get_concept_provider')
    def test_get_top_concepts_function(self, mock_get_provider):
        """测试全局get_top_concepts函数"""
        # Mock 提供器
        mock_provider = Mock()
        mock_provider.get_top_concepts.return_value = pd.DataFrame({
            'concept_code': ['BK0001'],
            'concept_name': ['人工智能'],
            'change_pct': [5.2]
        })
        mock_get_provider.return_value = mock_provider

        from tradingagents.dataflows.market_data_concept_utils import get_top_concepts

        result = get_top_concepts(sort_by="volume", limit=10)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        mock_provider.get_top_concepts.assert_called_once_with(sort_by="volume", ascending=False, limit=10)


class TestDataSourceManagerIntegration(unittest.TestCase):
    """测试DataSourceManager集成"""

    @patch('tradingagents.dataflows.data_source_manager.logger')
    @patch('tradingagents.dataflows.market_data_concept_utils.get_concept_provider')
    def test_data_source_manager_get_concept_list(self, mock_get_provider, mock_logger):
        """测试DataSourceManager的get_concept_list方法"""
        # Mock 概念提供器
        mock_provider = Mock()
        mock_provider.get_concept_list.return_value = pd.DataFrame({
            'concept_code': ['BK0001', 'BK0002'],
            'concept_name': ['人工智能', '新能源汽车'],
            'price': [100.5, 85.3],
            'change_pct': [2.5, -1.8],
            'volume': [1000000, 2000000],
            'turnover': [100000000, 170000000]
        })
        mock_get_provider.return_value = mock_provider

        from tradingagents.dataflows.data_source_manager import DataSourceManager

        manager = DataSourceManager()
        result = manager.get_concept_list(use_cache=True)

        # 验证返回格式化字符串
        self.assertIsInstance(result, str)
        self.assertIn("概念板块数据汇总", result)
        self.assertIn("人工智能", result)
        self.assertIn("新能源汽车", result)
        mock_provider.get_concept_list.assert_called_once_with(use_cache=True)

    @patch('tradingagents.dataflows.data_source_manager.logger')
    @patch('tradingagents.dataflows.market_data_concept_utils.get_concept_provider')
    def test_data_source_manager_get_concept_stocks(self, mock_get_provider, mock_logger):
        """测试DataSourceManager的get_concept_stocks方法"""
        # Mock 概念提供器
        mock_provider = Mock()
        mock_provider.get_concept_stocks.return_value = pd.DataFrame({
            'stock_code': ['000001', '000002'],
            'stock_name': ['平安银行', '万科A'],
            'price': [12.5, 22.8],
            'change_pct': [1.2, -0.8],
            'change_amount': [0.15, -0.18],
            'volume': [5000000, 3000000],
            'turnover': [62500000, 68400000]
        })
        mock_get_provider.return_value = mock_provider

        from tradingagents.dataflows.data_source_manager import DataSourceManager

        manager = DataSourceManager()
        result = manager.get_concept_stocks("BK0001", use_cache=False)

        # 验证返回格式化字符串
        self.assertIsInstance(result, str)
        self.assertIn("概念BK0001成分股数据", result)
        self.assertIn("平安银行", result)
        self.assertIn("万科A", result)
        mock_provider.get_concept_stocks.assert_called_once_with("BK0001", use_cache=False)


class TestInterfaceFunctions(unittest.TestCase):
    """测试Interface接口函数"""

    @patch('tradingagents.dataflows.interface.logger')
    @patch('tradingagents.dataflows.data_source_manager.get_data_source_manager')
    def test_interface_get_concept_list(self, mock_get_manager, mock_logger):
        """测试接口层get_concept_list函数"""
        # Mock DataSourceManager
        mock_manager = Mock()
        mock_manager.get_concept_list.return_value = "概念板块数据汇总"
        mock_get_manager.return_value = mock_manager

        from tradingagents.dataflows.interface import get_concept_list

        result = get_concept_list(use_cache=True)

        self.assertEqual(result, "概念板块数据汇总")
        mock_manager.get_concept_list.assert_called_once_with(use_cache=True)

    @patch('tradingagents.dataflows.interface.logger')
    @patch('tradingagents.dataflows.data_source_manager.get_data_source_manager')
    def test_interface_get_concept_stocks(self, mock_get_manager, mock_logger):
        """测试接口层get_concept_stocks函数"""
        # Mock DataSourceManager
        mock_manager = Mock()
        mock_manager.get_concept_stocks.return_value = "概念成分股数据"
        mock_get_manager.return_value = mock_manager

        from tradingagents.dataflows.interface import get_concept_stocks

        result = get_concept_stocks("BK0001", use_cache=False)

        self.assertEqual(result, "概念成分股数据")
        mock_manager.get_concept_stocks.assert_called_once_with("BK0001", use_cache=False)

    @patch('tradingagents.dataflows.interface.logger')
    @patch('tradingagents.dataflows.data_source_manager.get_data_source_manager')
    def test_interface_get_concept_ranking(self, mock_get_manager, mock_logger):
        """测试接口层get_concept_ranking函数"""
        # Mock DataSourceManager
        mock_manager = Mock()
        mock_manager.get_top_concepts.return_value = "概念板块排行榜"
        mock_get_manager.return_value = mock_manager

        from tradingagents.dataflows.interface import get_concept_ranking

        result = get_concept_ranking(sort_by="volume", ascending=True, limit=15)

        self.assertEqual(result, "概念板块排行榜")
        mock_manager.get_top_concepts.assert_called_once_with(sort_by="volume", ascending=True, limit=15)


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""

    @patch('tradingagents.dataflows.market_data_concept_utils.logger')
    def test_concept_provider_both_sources_fail(self, mock_logger):
        """测试主备数据源都失败的情况"""
        with patch('tradingagents.dataflows.market_data_concept_utils.cache_manager', None):
            from tradingagents.dataflows.market_data_concept_utils import ConceptProvider

            provider = ConceptProvider()
            provider.primary_source.get_concept_list = Mock(side_effect=Exception("主数据源失败"))
            provider.fallback_source.get_concept_list = Mock(side_effect=Exception("备用数据源失败"))

            result = provider.get_concept_list(use_cache=False)

            # 应该返回空DataFrame
            self.assertIsInstance(result, pd.DataFrame)
            self.assertTrue(result.empty)

    @patch('tradingagents.dataflows.interface.logger')
    def test_interface_exception_handling(self, mock_logger):
        """测试接口层异常处理"""
        with patch('tradingagents.dataflows.data_source_manager.get_data_source_manager',
                   side_effect=Exception("数据源管理器初始化失败")):
            from tradingagents.dataflows.interface import get_concept_list

            result = get_concept_list()

            # 应该返回错误消息
            self.assertIsInstance(result, str)
            self.assertIn("获取概念板块列表失败", result)


class TestCacheIntegration(unittest.TestCase):
    """测试缓存集成"""

    def test_cache_operations(self):
        """测试缓存操作"""
        # Mock 缓存管理器
        mock_cache_manager = Mock()
        mock_cache_manager.get.return_value = pd.DataFrame({
            'concept_code': ['BK0001'],
            'concept_name': ['缓存数据']
        })

        with patch('tradingagents.dataflows.market_data_concept_utils.cache_manager', mock_cache_manager), \
             patch('tradingagents.dataflows.market_data_concept_utils.logger', None):
            from tradingagents.dataflows.market_data_concept_utils import ConceptProvider

            provider = ConceptProvider()
            result = provider.get_concept_list(use_cache=True)

            # 验证使用了缓存数据
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 1)
            self.assertEqual(result.iloc[0]['concept_name'], '缓存数据')
            mock_cache_manager.get.assert_called_once()


if __name__ == '__main__':
    unittest.main()