#!/usr/bin/env python3
"""
市场数据 - 资金流向数据提供器

基于AData项目的市场数据模块，提供个股和概念的资金流向数据获取功能。
基于东方财富数据源，提供统一缓存机制。

集成到TradingAgents-CN的数据流架构中，为AI分析师提供资金流向分析能力。

参考：/Users/yyj/GitProject/adata/adata/stock/market/capital_flow/
"""

import pandas as pd
import requests
from typing import Optional
import warnings
from dataclasses import dataclass

# 导入项目组件
from tradingagents.utils.logging_manager import get_logger
from tradingagents.utils.unified_cache_manager import UnifiedCacheManager

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

    # 标准化的列名映射（参考AData格式）
    FLOW_MIN_COLUMNS = ['stock_code', 'trade_time', 'main_net_inflow', 'sm_net_inflow',
                        'mid_net_inflow', 'lg_net_inflow', 'max_net_inflow']

    FLOW_DAILY_COLUMNS = ['stock_code', 'trade_date', 'main_net_inflow', 'sm_net_inflow',
                          'mid_net_inflow', 'lg_net_inflow', 'max_net_inflow']

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_capital_flow_realtime(self, stock_code: str) -> pd.DataFrame:
        """获取实时资金流向数据（分时数据）"""
        raise NotImplementedError("子类需要实现此方法")

    def get_capital_flow_daily(self, stock_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取日度资金流向数据"""
        raise NotImplementedError("子类需要实现此方法")


class EastMoneyCapitalFlow(CapitalFlowDataSource):
    """东方财富资金流向数据源"""

    def __init__(self):
        super().__init__("eastmoney")

    def get_capital_flow_realtime(self, stock_code: str) -> pd.DataFrame:
        """获取单个股票的今日分时资金流向"""
        try:
            # 1. 请求接口 url
            cid = 1 if stock_code.startswith('6') else 0
            url = f"https://push2.eastmoney.com/api/qt/stock/fflow/kline/get?lmt=0&klt=1&fields1=f1,f2,f3,f7&" \
                  f"fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65&" \
                  f"secid={cid}.{stock_code}"  # cspell:disable-line

            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()['data']

            # 2. 解析数据
            if not data:
                return pd.DataFrame([], columns=self.FLOW_MIN_COLUMNS)
            lines = data['klines']  # cspell:disable-line

            # 3. 数据 etl
            # 2024-06-19 09:31,-1943532.0,2710159.0,-766627.0,-5901648.0,3958116.0
            data_list = [[stock_code] + line.split(',') for line in lines]
            df = pd.DataFrame(data_list, columns=self.FLOW_MIN_COLUMNS)
            df = df.astype({'trade_time': 'datetime64[ns]', 'main_net_inflow': 'float64', 'sm_net_inflow': 'float64',
                            'mid_net_inflow': 'float64', 'lg_net_inflow': 'float64', 'max_net_inflow': 'float64'})

            logger.info(f"✅ 成功获取{stock_code}实时资金流向数据，共{len(df)}条记录")
            return df

        except Exception as e:
            logger.error(f"❌ 获取{stock_code}实时资金流向数据失败: {str(e)}")
            return pd.DataFrame([], columns=self.FLOW_MIN_COLUMNS)

    def get_capital_flow_daily(self, stock_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取单个股票的资金流向-日度
        目前只有120天的数据
        """
        try:
            # 1. 请求接口 url
            cid = 1 if stock_code.startswith('6') else 0
            url = f"https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?" \
                  f"lmt=0&klt=101&fields1=f1,f2,f3,f7&" \
                  f"fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&" \
                  f"secid={cid}.{stock_code}"  # cspell:disable-line

            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()['data']

            # 2. 解析数据
            if not data:
                return pd.DataFrame([], columns=self.FLOW_DAILY_COLUMNS)
            lines = data['klines']  # cspell:disable-line

            # 3. 数据 etl
            # '2023-12-18,-58234405.0,47874618.0,10359788.0,-13362003.0,-44872402.0,-9.72,7.99,1.73,-2.23,-7.49,8.41,-0.94,0.00,0.00'
            data_list = [[stock_code] + line.split(',')[0:6] for line in lines]
            df = pd.DataFrame(data_list, columns=self.FLOW_DAILY_COLUMNS)
            df = df.astype({'main_net_inflow': 'float64', 'sm_net_inflow': 'float64',
                            'mid_net_inflow': 'float64', 'lg_net_inflow': 'float64', 'max_net_inflow': 'float64'
                            })

            # 4. 范围筛选
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            if start_date is not None:
                start_date = pd.to_datetime(start_date)
                df = df[df['trade_date'] >= start_date]
            if end_date is not None:
                end_date = pd.to_datetime(end_date)
                df = df[df['trade_date'] <= end_date]
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')

            logger.info(f"✅ 成功获取{stock_code}日度资金流向数据，共{len(df)}条记录")
            return df

        except Exception as e:
            logger.error(f"❌ 获取{stock_code}日度资金流向数据失败: {str(e)}")
            return pd.DataFrame([], columns=self.FLOW_DAILY_COLUMNS)


class CapitalFlowProvider:
    """资金流向数据提供器

    整合多个数据源，提供智能降级和统一缓存机制
    """

    def __init__(self, cache_manager: Optional[UnifiedCacheManager] = None):
        """初始化资金流向提供器"""
        self.cache_manager = cache_manager or UnifiedCacheManager()

        # 初始化数据源
        self.data_sources = [
            EastMoneyCapitalFlow(),
        ]

        # 缓存配置
        self.cache_config = {
            'realtime_ttl': 300,  # 实时数据5分钟缓存
            'daily_ttl': 3600,    # 日度数据1小时缓存
        }

        logger.info("✅ 资金流向数据提供器初始化完成")

    def _generate_cache_key(self, method: str, stock_code: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [method, stock_code]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}_{v}")
        return f"capital_flow:{'_'.join(key_parts)}"

    def _try_data_sources(self, method_name: str, stock_code: str, **kwargs) -> pd.DataFrame:
        """尝试多个数据源获取数据"""
        for source in self.data_sources:
            try:
                method = getattr(source, method_name)
                df = method(stock_code, **kwargs)
                if not df.empty:
                    logger.info(f"✅ 通过{source.source_name}成功获取{stock_code}数据")
                    return df
            except Exception as e:
                logger.warning(f"⚠️ 数据源{source.source_name}获取{stock_code}失败: {str(e)}")
                continue

        logger.error(f"❌ 所有数据源均获取{stock_code}失败")
        return pd.DataFrame()

    def get_capital_flow_realtime(self, stock_code: str, use_cache: bool = True) -> pd.DataFrame:
        """获取实时资金流向数据

        Args:
            stock_code: 股票代码，如 '002115'
            use_cache: 是否使用缓存

        Returns:
            DataFrame: 实时资金流向数据
        """
        # 检查缓存
        cache_key = self._generate_cache_key('realtime', stock_code)
        if use_cache:
            cached_data = self.cache_manager.get('capital_flow', cache_key)
            if cached_data is not None:
                logger.info(f"✅ 从缓存获取{stock_code}实时资金流向数据")
                return cached_data

        # 从数据源获取
        df = self._try_data_sources('get_capital_flow_realtime', stock_code)

        # 缓存结果
        if use_cache and not df.empty:
            self.cache_manager.set(
                'capital_flow',
                cache_key,
                df
            )

        return df

    def get_capital_flow_daily(self, stock_code: str, start_date: str = None, end_date: str = None,
                             use_cache: bool = True) -> pd.DataFrame:
        """获取日度资金流向数据

        Args:
            stock_code: 股票代码，如 '002115'
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'
            use_cache: 是否使用缓存

        Returns:
            DataFrame: 日度资金流向数据
        """
        # 检查缓存
        cache_key = self._generate_cache_key('daily', stock_code, start_date=start_date, end_date=end_date)
        if use_cache:
            cached_data = self.cache_manager.get('capital_flow', cache_key)
            if cached_data is not None:
                logger.info(f"✅ 从缓存获取{stock_code}日度资金流向数据")
                return cached_data

        # 从数据源获取
        df = self._try_data_sources('get_capital_flow_daily', stock_code, start_date=start_date, end_date=end_date)

        # 缓存结果
        if use_cache and not df.empty:
            self.cache_manager.set(
                'capital_flow',
                cache_key,
                df
            )

        return df

    def get_concept_capital_flow(self, concept_code: str) -> pd.DataFrame:
        """获取概念资金流向数据（待实现）

        Args:
            concept_code: 概念代码

        Returns:
            DataFrame: 概念资金流向数据
        """
        logger.warning(f"概念资金流向数据获取功能待实现，概念代码: {concept_code}")
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
def get_stock_capital_flow_realtime(stock_code: str, use_cache: bool = True) -> pd.DataFrame:
    """获取个股实时资金流向数据"""
    return get_capital_flow_provider().get_capital_flow_realtime(stock_code, use_cache=use_cache)


def get_stock_capital_flow_daily(stock_code: str, start_date: str = None, end_date: str = None,
                                use_cache: bool = True) -> pd.DataFrame:
    """获取个股日度资金流向数据"""
    return get_capital_flow_provider().get_capital_flow_daily(
        stock_code, start_date=start_date, end_date=end_date, use_cache=use_cache
    )


if __name__ == '__main__':
    # 测试代码
    provider = get_capital_flow_provider()

    # 测试实时数据
    print("=== 测试实时资金流向数据 ===")
    df_realtime = provider.get_capital_flow_realtime('002115')
    print(f"实时数据条数: {len(df_realtime)}")
    if not df_realtime.empty:
        print(df_realtime.head())

    # 测试日度数据
    print("\n=== 测试日度资金流向数据 ===")
    df_daily = provider.get_capital_flow_daily('002115', start_date='2024-01-01')
    print(f"日度数据条数: {len(df_daily)}")
    if not df_daily.empty:
        print(df_daily.head())

    # 测试便捷函数
    print("\n=== 测试便捷函数 ===")
    df_realtime_func = get_stock_capital_flow_realtime('300059')
    print(f"300059实时数据条数: {len(df_realtime_func)}")

    df_daily_func = get_stock_capital_flow_daily('002115', start_date='2024-12-01')
    print(f"002115日度数据条数: {len(df_daily_func)}")