#!/usr/bin/env python3
"""
市场数据 - 资金流向数据提供器

基于AData项目的市场数据模块，提供个股和概念的资金流向数据获取功能。
支持多数据源（东方财富、百度等）、智能降级和统一缓存机制。

集成到TradingAgents-CN的数据流架构中，为AI分析师提供资金流向分析能力。

参考：/Users/yyj/GitProject/adata/adata/stock/market/capital_flow/
"""

import pandas as pd
import requests
import json
from typing import Optional, Dict, Any, Union, List
from datetime import datetime, timedelta
import warnings
from dataclasses import dataclass

# 导入项目组件
from tradingagents.utils.logging_manager import get_logger
from tradingagents.utils.unified_cache_manager import UnifiedCacheManager, CacheBackend

logger = get_logger('market_data')
warnings.filterwarnings('ignore')


@dataclass
class CapitalFlowData:
    """资金流向数据模型"""
    symbol: str
    trade_date: str
    main_inflow: float = 0.0          # 主力资金流入
    main_outflow: float = 0.0         # 主力资金流出
    main_net: float = 0.0             # 主力资金净额
    retail_inflow: float = 0.0        # 散户资金流入
    retail_outflow: float = 0.0       # 散户资金流出
    retail_net: float = 0.0           # 散户资金净额
    super_large: float = 0.0          # 超大单净额
    large: float = 0.0                # 大单净额
    medium: float = 0.0               # 中单净额
    small: float = 0.0                # 小单净额
    data_source: str = "eastmoney"    # 数据源标识


class CapitalFlowDataSource:
    """资金流向数据源基类"""

    # 标准化的列名映射
    FLOW_MIN_COLUMNS = ['symbol', 'trade_time', 'main_net_inflow', 'small_net_inflow',
                        'medium_net_inflow', 'large_net_inflow', 'super_large_net_inflow']

    FLOW_DAILY_COLUMNS = ['symbol', 'trade_date', 'main_net_inflow', 'small_net_inflow',
                          'medium_net_inflow', 'large_net_inflow', 'super_large_net_inflow']

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_capital_flow_realtime(self, symbol: str) -> pd.DataFrame:
        """获取实时资金流向数据（分时数据）"""
        raise NotImplementedError("子类需要实现此方法")

    def get_capital_flow_daily(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取日度资金流向数据"""
        raise NotImplementedError("子类需要实现此方法")


class EastMoneyCapitalFlow(CapitalFlowDataSource):
    """东方财富资金流向数据源"""

    def __init__(self):
        super().__init__("eastmoney")
        self.base_url = "https://push2.eastmoney.com/api/qt/stock/fflow"

    def get_capital_flow_realtime(self, symbol: str) -> pd.DataFrame:
        """获取实时资金流向数据（分时数据）"""
        try:
            # 确定市场代码
            market_code = 1 if symbol.startswith('6') else 0

            # 构造URL
            url = f"{self.base_url}/kline/get"
            params = {
                'lmt': 0,
                'klt': 1,
                'fields1': 'f1,f2,f3,f7',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65',
                'secid': f'{market_code}.{symbol}'
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json().get('data', {})
            if not data or 'klines' not in data:
                logger.warning(f"东方财富API返回空数据: {symbol}")
                return pd.DataFrame([], columns=self.FLOW_MIN_COLUMNS)

            # 解析数据
            lines = data['klines']
            rows = []
            for line in lines:
                parts = line.split(',')
                if len(parts) >= 6:
                    rows.append([
                        symbol,
                        parts[0],  # trade_time
                        float(parts[1]) if parts[1] else 0.0,  # main_net_inflow
                        float(parts[2]) if parts[2] else 0.0,  # small_net_inflow
                        float(parts[3]) if parts[3] else 0.0,  # medium_net_inflow
                        float(parts[4]) if parts[4] else 0.0,  # large_net_inflow
                        float(parts[5]) if parts[5] else 0.0,  # super_large_net_inflow
                    ])

            if not rows:
                return pd.DataFrame([], columns=self.FLOW_MIN_COLUMNS)

            df = pd.DataFrame(rows, columns=self.FLOW_MIN_COLUMNS)
            df['trade_time'] = pd.to_datetime(df['trade_time'])

            # 数值列转换为float
            numeric_columns = ['main_net_inflow', 'small_net_inflow', 'medium_net_inflow',
                             'large_net_inflow', 'super_large_net_inflow']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

            logger.info(f"✅ 成功获取{symbol}实时资金流向数据，共{len(df)}条记录")
            return df

        except Exception as e:
            logger.error(f"❌ 获取{symbol}实时资金流向数据失败: {str(e)}")
            return pd.DataFrame([], columns=self.FLOW_MIN_COLUMNS)

    def get_capital_flow_daily(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取日度资金流向数据"""
        try:
            # 确定市场代码
            market_code = 1 if symbol.startswith('6') else 0

            # 构造URL - 日度数据
            url = f"{self.base_url}/daykline/get"
            params = {
                'lmt': 0,
                'klt': 101,  # 日度数据
                'fields1': 'f1,f2,f3,f7',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65',
                'ut': 'b2884a393a59ad64002292a3e90d46a5',
                'secid': f'{market_code}.{symbol}'
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json().get('data', {})
            if not data or 'klines' not in data:
                logger.warning(f"东方财富API返回空数据: {symbol}")
                return pd.DataFrame([], columns=self.FLOW_DAILY_COLUMNS)

            # 解析数据
            lines = data['klines']
            rows = []
            for line in lines:
                parts = line.split(',')
                if len(parts) >= 6:
                    rows.append([
                        symbol,
                        parts[0],  # trade_date
                        float(parts[1]) if parts[1] else 0.0,  # main_net_inflow
                        float(parts[2]) if parts[2] else 0.0,  # small_net_inflow
                        float(parts[3]) if parts[3] else 0.0,  # medium_net_inflow
                        float(parts[4]) if parts[4] else 0.0,  # large_net_inflow
                        float(parts[5]) if parts[5] else 0.0,  # super_large_net_inflow
                    ])

            if not rows:
                return pd.DataFrame([], columns=self.FLOW_DAILY_COLUMNS)

            df = pd.DataFrame(rows, columns=self.FLOW_DAILY_COLUMNS)
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')

            # 数值列转换为float
            numeric_columns = ['main_net_inflow', 'small_net_inflow', 'medium_net_inflow',
                             'large_net_inflow', 'super_large_net_inflow']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

            # 日期过滤
            if start_date or end_date:
                df_filtered = df.copy()
                if start_date:
                    df_filtered = df_filtered[df_filtered['trade_date'] >= start_date]
                if end_date:
                    df_filtered = df_filtered[df_filtered['trade_date'] <= end_date]
                df = df_filtered

            logger.info(f"✅ 成功获取{symbol}日度资金流向数据，共{len(df)}条记录")
            return df

        except Exception as e:
            logger.error(f"❌ 获取{symbol}日度资金流向数据失败: {str(e)}")
            return pd.DataFrame([], columns=self.FLOW_DAILY_COLUMNS)


class BaiduCapitalFlow(CapitalFlowDataSource):
    """百度资金流向数据源（备用）"""

    def __init__(self):
        super().__init__("baidu")
        self.base_url = "https://gushitong.baidu.com"

    def get_capital_flow_realtime(self, symbol: str) -> pd.DataFrame:
        """获取实时资金流向数据"""
        try:
            # 百度资金流向API实现
            # 这里可以添加百度数据源的具体实现
            logger.warning("百度资金流向数据源暂未实现")
            return pd.DataFrame([], columns=self.FLOW_MIN_COLUMNS)
        except Exception as e:
            logger.error(f"❌ 百度数据源获取{symbol}实时资金流向失败: {str(e)}")
            return pd.DataFrame([], columns=self.FLOW_MIN_COLUMNS)

    def get_capital_flow_daily(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取日度资金流向数据"""
        try:
            # 百度资金流向API实现
            logger.warning("百度资金流向数据源暂未实现")
            return pd.DataFrame([], columns=self.FLOW_DAILY_COLUMNS)
        except Exception as e:
            logger.error(f"❌ 百度数据源获取{symbol}日度资金流向失败: {str(e)}")
            return pd.DataFrame([], columns=self.FLOW_DAILY_COLUMNS)


class CapitalFlowProvider:
    """资金流向数据提供器

    整合多个数据源，提供智能降级和统一缓存机制
    """

    def __init__(self, cache_manager: Optional[UnifiedCacheManager] = None):
        """初始化资金流向提供器"""
        self.cache_manager = cache_manager or UnifiedCacheManager()

        # 初始化数据源（按优先级排序）
        self.data_sources = [
            EastMoneyCapitalFlow(),
            BaiduCapitalFlow(),
        ]

        # 缓存配置
        self.cache_config = {
            'realtime_ttl': 300,  # 实时数据5分钟缓存
            'daily_ttl': 3600,    # 日度数据1小时缓存
        }

        logger.info("✅ 资金流向数据提供器初始化完成")

    def _generate_cache_key(self, method: str, symbol: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [method, symbol]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}_{v}")
        return f"capital_flow:{'_'.join(key_parts)}"

    def _try_data_sources(self, method_name: str, symbol: str, **kwargs) -> pd.DataFrame:
        """尝试多个数据源获取数据"""
        for source in self.data_sources:
            try:
                method = getattr(source, method_name)
                df = method(symbol, **kwargs)
                if not df.empty:
                    logger.info(f"✅ 通过{source.source_name}成功获取{symbol}数据")
                    return df
            except Exception as e:
                logger.warning(f"⚠️ 数据源{source.source_name}获取{symbol}失败: {str(e)}")
                continue

        logger.error(f"❌ 所有数据源均获取{symbol}失败")
        return pd.DataFrame()

    def get_capital_flow_realtime(self, symbol: str, use_cache: bool = True) -> pd.DataFrame:
        """获取实时资金流向数据

        Args:
            symbol: 股票代码，如 '000001'
            use_cache: 是否使用缓存

        Returns:
            DataFrame: 实时资金流向数据
        """
        # 检查缓存
        cache_key = self._generate_cache_key('realtime', symbol)
        if use_cache:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data is not None:
                logger.info(f"✅ 从缓存获取{symbol}实时资金流向数据")
                return cached_data

        # 从数据源获取
        df = self._try_data_sources('get_capital_flow_realtime', symbol)

        # 缓存结果
        if use_cache and not df.empty:
            self.cache_manager.set(
                cache_key,
                df,
                ttl=self.cache_config['realtime_ttl'],
                metadata={'symbol': symbol, 'type': 'realtime'}
            )

        return df

    def get_capital_flow_daily(self, symbol: str, start_date: str = None, end_date: str = None,
                             use_cache: bool = True) -> pd.DataFrame:
        """获取日度资金流向数据

        Args:
            symbol: 股票代码，如 '000001'
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'
            use_cache: 是否使用缓存

        Returns:
            DataFrame: 日度资金流向数据
        """
        # 检查缓存
        cache_key = self._generate_cache_key('daily', symbol, start_date=start_date, end_date=end_date)
        if use_cache:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data is not None:
                logger.info(f"✅ 从缓存获取{symbol}日度资金流向数据")
                return cached_data

        # 从数据源获取
        df = self._try_data_sources('get_capital_flow_daily', symbol, start_date=start_date, end_date=end_date)

        # 缓存结果
        if use_cache and not df.empty:
            self.cache_manager.set(
                cache_key,
                df,
                ttl=self.cache_config['daily_ttl'],
                metadata={'symbol': symbol, 'type': 'daily', 'start_date': start_date, 'end_date': end_date}
            )

        return df

    def get_concept_capital_flow(self, concept_code: str, use_cache: bool = True) -> pd.DataFrame:
        """获取概念资金流向数据（待实现）

        Args:
            concept_code: 概念代码
            use_cache: 是否使用缓存

        Returns:
            DataFrame: 概念资金流向数据
        """
        logger.warning("概念资金流向数据获取功能待实现")
        return pd.DataFrame()


# 全局实例
_capital_flow_provider = None

def get_capital_flow_provider() -> CapitalFlowProvider:
    """获取资金流向提供器单例"""
    global _capital_flow_provider
    if _capital_flow_provider is None:
        _capital_flow_provider = CapitalFlowProvider()
    return _capital_flow_provider


# 便捷函数
def get_stock_capital_flow_realtime(symbol: str, use_cache: bool = True) -> pd.DataFrame:
    """获取个股实时资金流向数据"""
    return get_capital_flow_provider().get_capital_flow_realtime(symbol, use_cache=use_cache)


def get_stock_capital_flow_daily(symbol: str, start_date: str = None, end_date: str = None,
                                use_cache: bool = True) -> pd.DataFrame:
    """获取个股日度资金流向数据"""
    return get_capital_flow_provider().get_capital_flow_daily(
        symbol, start_date=start_date, end_date=end_date, use_cache=use_cache
    )


if __name__ == '__main__':
    # 测试代码
    provider = get_capital_flow_provider()

    # 测试实时数据
    print("=== 测试实时资金流向数据 ===")
    df_realtime = provider.get_capital_flow_realtime('000001')
    print(f"实时数据条数: {len(df_realtime)}")
    if not df_realtime.empty:
        print(df_realtime.head())

    # 测试日度数据
    print("\n=== 测试日度资金流向数据 ===")
    df_daily = provider.get_capital_flow_daily('000001', start_date='2024-01-01')
    print(f"日度数据条数: {len(df_daily)}")
    if not df_daily.empty:
        print(df_daily.head())