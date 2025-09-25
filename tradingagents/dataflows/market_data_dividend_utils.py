"""
股息数据提供器模块

基于adata架构设计，提供股息和分红相关的数据获取功能
- 历史分红数据获取
- 股息率计算
- 分红派息公告
- 除权除息日期查询

参考文件: /Users/yyj/GitProject/adata/adata/stock/market/stock_dividend.py
"""

import pandas as pd
import requests
import json
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import time

try:
    from tradingagents.utils.unified_cache_manager import UnifiedCacheManager
    cache_manager = UnifiedCacheManager()
except ImportError:
    cache_manager = None

try:
    from tradingagents.utils.logging_manager import get_logger
    logger = get_logger('dividend_utils')
except ImportError:
    logger = None


class EastMoneyDividendData:
    """东方财富股息数据源"""

    BASE_URL = "https://datacenter-web.eastmoney.com/api/data"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://data.eastmoney.com/',
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        })

    def get_dividend_history(self, symbol: str, start_year: int = None, end_year: int = None) -> pd.DataFrame:
        """获取股票历史分红数据"""
        # 处理股票代码格式
        if '.' not in symbol:
            if symbol.startswith('6'):
                symbol = f"{symbol}.SH"
            else:
                symbol = f"{symbol}.SZ"

        url = f"{self.BASE_URL}/get"

        # 默认查询最近5年数据
        if not start_year:
            start_year = datetime.now().year - 5
        if not end_year:
            end_year = datetime.now().year

        params = {
            'type': 'RPT_SHAREBONUS_DET',
            'sty': 'ALL',
            'source': 'WEB',
            'p': '1',
            'ps': '200',
            'st': 'NOTICE_DATE',
            'sr': '-1',
            'var': 'YCdyyrYdMu',
            'rt': 'jsonp',
            'filter': f'(SECURITY_CODE="{symbol.split(".")[0]}")'
        }

        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()

            # 解析JSONP响应
            text = response.text
            if 'YCdyyrYdMu(' in text:
                start = text.find('YCdyyrYdMu(') + len('YCdyyrYdMu(')
                end = text.rfind(');')
                json_str = text[start:end]
            else:
                return pd.DataFrame()

            data = json.loads(json_str)

            if not data.get('result') or not data['result'].get('data'):
                return pd.DataFrame()

            dividends = []
            for item in data['result']['data']:
                dividend = {
                    'stock_code': symbol,
                    'notice_date': item.get('NOTICE_DATE', ''),  # 公告日期
                    'ex_dividend_date': item.get('EX_DIVIDEND_DATE', ''),  # 除息日
                    'record_date': item.get('RECORD_DATE', ''),  # 股权登记日
                    'dividend_date': item.get('DIVIDEND_DATE', ''),  # 派息日
                    'plan_explain': item.get('PLAN_EXPLAIN', ''),  # 分红方案说明
                    'dividend_ratio': item.get('DIVIDEND_RATIO', 0.0),  # 现金分红比例(每股派息)
                    'transfer_ratio': item.get('TRANSFER_RATIO', 0.0),  # 送股比例
                    'bonus_ratio': item.get('BONUS_RATIO', 0.0),  # 转增比例
                    'impl_plan_profile': item.get('IMPL_PLAN_PROFILE', ''),  # 实施方案概况
                    'year': item.get('YEAR', ''),  # 分红年度
                    'dividend_year': item.get('DIVIDEND_YEAR', ''),  # 分红送配年度
                    'progress': item.get('PROGRESS', ''),  # 实施进度
                }

                # 过滤年度范围
                if dividend['year'] and dividend['year'].isdigit():
                    year = int(dividend['year'])
                    if start_year <= year <= end_year:
                        dividends.append(dividend)
                else:
                    dividends.append(dividend)

            return pd.DataFrame(dividends)

        except Exception as e:
            if logger:
                logger.error(f"获取股票{symbol}分红数据失败: {e}")
            return pd.DataFrame()

    def get_dividend_summary(self, symbol: str) -> Dict:
        """获取股票分红汇总信息"""
        # 获取近3年分红数据进行汇总
        df = self.get_dividend_history(symbol, start_year=datetime.now().year - 3)

        if df.empty:
            return {}

        try:
            # 计算分红统计信息
            total_dividends = len(df)
            total_dividend_amount = df['dividend_ratio'].sum()
            avg_dividend_ratio = df['dividend_ratio'].mean() if total_dividends > 0 else 0

            # 最近一次分红信息
            latest_dividend = df.iloc[0] if not df.empty else {}

            # 分红频率分析
            yearly_dividends = df.groupby('year')['dividend_ratio'].sum().to_dict()

            summary = {
                'stock_code': symbol,
                'total_dividend_count': total_dividends,
                'total_dividend_amount': float(total_dividend_amount),
                'avg_dividend_ratio': float(avg_dividend_ratio),
                'latest_dividend': {
                    'notice_date': latest_dividend.get('notice_date', ''),
                    'ex_dividend_date': latest_dividend.get('ex_dividend_date', ''),
                    'dividend_ratio': latest_dividend.get('dividend_ratio', 0),
                    'plan_explain': latest_dividend.get('plan_explain', ''),
                    'progress': latest_dividend.get('progress', '')
                } if latest_dividend else {},
                'yearly_dividends': yearly_dividends,
                'dividend_stability': len(yearly_dividends) / 3.0 if yearly_dividends else 0  # 分红稳定性指标
            }

            return summary

        except Exception as e:
            if logger:
                logger.error(f"计算股票{symbol}分红汇总失败: {e}")
            return {}

    def calculate_dividend_yield(self, symbol: str, current_price: float = None) -> Dict:
        """计算股息率"""
        # 获取最近一年的分红数据
        current_year = datetime.now().year
        df = self.get_dividend_history(symbol, start_year=current_year - 1, end_year=current_year)

        if df.empty:
            return {'dividend_yield': 0.0, 'annual_dividend': 0.0, 'error': '无分红数据'}

        try:
            # 计算年度分红总额
            annual_dividend = df['dividend_ratio'].sum()

            if not current_price:
                # 如果没有提供当前价格，尝试获取最近的股价（这里简化处理）
                # 实际应用中可以集成股价获取功能
                if logger:
                    logger.warning(f"未提供{symbol}当前股价，无法计算准确股息率")
                return {
                    'dividend_yield': 0.0,
                    'annual_dividend': float(annual_dividend),
                    'error': '需要提供当前股价'
                }

            # 计算股息率 (年度分红 / 当前股价 * 100%)
            dividend_yield = (annual_dividend / current_price * 100) if current_price > 0 else 0.0

            return {
                'dividend_yield': float(dividend_yield),
                'annual_dividend': float(annual_dividend),
                'current_price': current_price,
                'calculation_date': datetime.now().strftime('%Y-%m-%d')
            }

        except Exception as e:
            if logger:
                logger.error(f"计算股票{symbol}股息率失败: {e}")
            return {'dividend_yield': 0.0, 'annual_dividend': 0.0, 'error': str(e)}


class TushareDividendData:
    """Tushare股息数据源（备用）"""

    def __init__(self):
        self.session = requests.Session()

    def get_dividend_history(self, symbol: str, start_year: int = None, end_year: int = None) -> pd.DataFrame:
        """获取股票历史分红数据（备用实现）"""
        try:
            # 这里可以实现Tushare API的分红数据获取
            # 目前返回空DataFrame作为占位
            if logger:
                logger.info(f"使用Tushare数据源获取{symbol}分红数据")
            return pd.DataFrame()
        except Exception as e:
            if logger:
                logger.error(f"Tushare获取{symbol}分红数据失败: {e}")
            return pd.DataFrame()

    def get_dividend_summary(self, symbol: str) -> Dict:
        """获取股票分红汇总信息（备用实现）"""
        try:
            if logger:
                logger.info(f"使用Tushare数据源获取{symbol}分红汇总")
            return {}
        except Exception as e:
            if logger:
                logger.error(f"Tushare获取{symbol}分红汇总失败: {e}")
            return {}

    def calculate_dividend_yield(self, symbol: str, current_price: float = None) -> Dict:
        """计算股息率（备用实现）"""
        try:
            if logger:
                logger.info(f"使用Tushare数据源计算{symbol}股息率")
            return {'dividend_yield': 0.0, 'annual_dividend': 0.0, 'error': '备用数据源暂未实现'}
        except Exception as e:
            if logger:
                logger.error(f"Tushare计算{symbol}股息率失败: {e}")
            return {'dividend_yield': 0.0, 'annual_dividend': 0.0, 'error': str(e)}


class DividendProvider:
    """股息数据提供器 - 智能降级机制"""

    def __init__(self):
        self.primary_source = EastMoneyDividendData()
        self.fallback_source = TushareDividendData()
        self.cache_prefix = "dividend_data"

    def get_dividend_history(self, symbol: str, start_year: int = None, end_year: int = None, use_cache: bool = True) -> pd.DataFrame:
        """获取股票历史分红数据，支持智能降级"""
        cache_key = f"{self.cache_prefix}_history_{symbol}_{start_year}_{end_year}"

        # 检查缓存
        if use_cache and cache_manager:
            cached_data = cache_manager.get('dividend_data', cache_key)
            if cached_data is not None:
                if logger:
                    logger.info(f"从缓存获取{symbol}分红历史数据")
                return cached_data

        # 尝试主数据源
        try:
            data = self.primary_source.get_dividend_history(symbol, start_year, end_year)
            if not data.empty:
                if use_cache and cache_manager:
                    cache_manager.set('dividend_data', cache_key, data)
                if logger:
                    logger.info(f"从东方财富获取到{symbol}的{len(data)}条分红记录")
                return data
        except Exception as e:
            if logger:
                logger.warning(f"主数据源获取{symbol}分红数据失败，尝试备用源: {e}")

        # 降级到备用数据源
        try:
            data = self.fallback_source.get_dividend_history(symbol, start_year, end_year)
            if not data.empty:
                if use_cache and cache_manager:
                    cache_manager.set('dividend_data', cache_key, data)
                if logger:
                    logger.info(f"从备用数据源获取到{symbol}的{len(data)}条分红记录")
                return data
        except Exception as e:
            if logger:
                logger.error(f"备用数据源也获取{symbol}分红数据失败: {e}")

        # 返回空DataFrame
        return pd.DataFrame()

    def get_dividend_summary(self, symbol: str, use_cache: bool = True) -> Dict:
        """获取股票分红汇总信息，支持智能降级"""
        cache_key = f"{self.cache_prefix}_summary_{symbol}"

        # 检查缓存
        if use_cache and cache_manager:
            cached_data = cache_manager.get('dividend_data', cache_key)
            if cached_data is not None:
                if logger:
                    logger.info(f"从缓存获取{symbol}分红汇总数据")
                return cached_data

        # 尝试主数据源
        try:
            data = self.primary_source.get_dividend_summary(symbol)
            if data:
                if use_cache and cache_manager:
                    cache_manager.set('dividend_data', cache_key, data)
                if logger:
                    logger.info(f"从东方财富获取到{symbol}分红汇总数据")
                return data
        except Exception as e:
            if logger:
                logger.warning(f"主数据源获取{symbol}分红汇总失败，尝试备用源: {e}")

        # 降级到备用数据源
        try:
            data = self.fallback_source.get_dividend_summary(symbol)
            if data:
                if use_cache and cache_manager:
                    cache_manager.set('dividend_data', cache_key, data)
                if logger:
                    logger.info(f"从备用数据源获取到{symbol}分红汇总数据")
                return data
        except Exception as e:
            if logger:
                logger.error(f"备用数据源也获取{symbol}分红汇总失败: {e}")

        # 返回空字典
        return {}

    def calculate_dividend_yield(self, symbol: str, current_price: float = None, use_cache: bool = True) -> Dict:
        """计算股息率，支持智能降级"""
        cache_key = f"{self.cache_prefix}_yield_{symbol}_{current_price}"

        # 检查缓存（股息率缓存时间较短，因为依赖股价变化）
        if use_cache and cache_manager:
            cached_data = cache_manager.get('dividend_data', cache_key)
            if cached_data is not None:
                if logger:
                    logger.info(f"从缓存获取{symbol}股息率数据")
                return cached_data

        # 尝试主数据源
        try:
            data = self.primary_source.calculate_dividend_yield(symbol, current_price)
            if data and 'dividend_yield' in data:
                if use_cache and cache_manager:
                    cache_manager.set('dividend_data', cache_key, data)
                if logger:
                    logger.info(f"从东方财富计算{symbol}股息率: {data.get('dividend_yield', 0):.2f}%")
                return data
        except Exception as e:
            if logger:
                logger.warning(f"主数据源计算{symbol}股息率失败，尝试备用源: {e}")

        # 降级到备用数据源
        try:
            data = self.fallback_source.calculate_dividend_yield(symbol, current_price)
            if data:
                if use_cache and cache_manager:
                    cache_manager.set('dividend_data', cache_key, data)
                if logger:
                    logger.info(f"从备用数据源计算{symbol}股息率")
                return data
        except Exception as e:
            if logger:
                logger.error(f"备用数据源也计算{symbol}股息率失败: {e}")

        # 返回默认值
        return {'dividend_yield': 0.0, 'annual_dividend': 0.0, 'error': '无法获取股息数据'}


# 全局股息数据提供器实例
_dividend_provider = None

def get_dividend_provider() -> DividendProvider:
    """获取股息数据提供器实例"""
    global _dividend_provider
    if _dividend_provider is None:
        _dividend_provider = DividendProvider()
    return _dividend_provider


# 便捷函数
def get_dividend_history(symbol: str, start_year: int = None, end_year: int = None, use_cache: bool = True) -> pd.DataFrame:
    """获取股票历史分红数据"""
    provider = get_dividend_provider()
    return provider.get_dividend_history(symbol, start_year=start_year, end_year=end_year, use_cache=use_cache)


def get_dividend_summary(symbol: str, use_cache: bool = True) -> Dict:
    """获取股票分红汇总信息"""
    provider = get_dividend_provider()
    return provider.get_dividend_summary(symbol, use_cache=use_cache)


def calculate_dividend_yield(symbol: str, current_price: float = None, use_cache: bool = True) -> Dict:
    """计算股息率"""
    provider = get_dividend_provider()
    return provider.calculate_dividend_yield(symbol, current_price=current_price, use_cache=use_cache)