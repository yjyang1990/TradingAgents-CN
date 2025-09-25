"""
概念板块数据提供器模块

基于adata架构设计，提供概念板块和成分股相关的数据获取功能
- 概念板块列表获取
- 板块涨跌幅排行
- 成分股查询
- 板块资金流向

参考文件: /Users/yyj/GitProject/adata/adata/stock/market 模块
"""

import pandas as pd
import requests
import json
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import time
import asyncio
import aiohttp

try:
    from tradingagents.utils.unified_cache_manager import UnifiedCacheManager
    cache_manager = UnifiedCacheManager()
except ImportError:
    cache_manager = None

try:
    from tradingagents.utils.logging_manager import get_logger
    logger = get_logger('concept_utils')
except ImportError:
    logger = None


class EastMoneyConceptData:
    """东方财富概念板块数据源"""

    BASE_URL = "https://push2.eastmoney.com/api/qt"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://quote.eastmoney.com/',
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        })

    def get_concept_list(self) -> pd.DataFrame:
        """获取概念板块列表"""
        url = f"{self.BASE_URL}/clist/get"
        params = {
            'cb': 'jQuery112406389542653718456_1640754174808',
            'pn': '1',
            'pz': '2000',
            'po': '1',
            'np': '1',
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': '2',
            'invt': '2',
            'fid': 'f3',
            'fs': 'm:90+t:3+f:!50',
            'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f11,f62,f128,f136,f115,f152',
            '_': str(int(time.time() * 1000))
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            # 解析JSONP响应
            text = response.text
            start = text.find('(') + 1
            end = text.rfind(')')
            json_str = text[start:end]

            data = json.loads(json_str)

            if not data.get('data') or not data['data'].get('diff'):
                return pd.DataFrame()

            concepts = []
            for item in data['data']['diff']:
                concept = {
                    'concept_code': item.get('f12', ''),
                    'concept_name': item.get('f14', ''),
                    'price': item.get('f2', 0),
                    'change_pct': item.get('f3', 0),
                    'change_amount': item.get('f4', 0),
                    'volume': item.get('f5', 0),
                    'turnover': item.get('f6', 0),
                    'amplitude': item.get('f7', 0),
                    'high': item.get('f15', 0),
                    'low': item.get('f16', 0),
                    'open': item.get('f17', 0),
                    'prev_close': item.get('f18', 0),
                    'volume_ratio': item.get('f10', 0),
                    'pe_ratio': item.get('f9', 0),
                    'market_cap': item.get('f20', 0),
                    'float_market_cap': item.get('f21', 0),
                    'total_shares': item.get('f8', 0)
                }
                concepts.append(concept)

            return pd.DataFrame(concepts)

        except Exception as e:
            if logger:
                logger.error(f"获取概念板块列表失败: {e}")
            return pd.DataFrame()

    def get_concept_stocks(self, concept_code: str) -> pd.DataFrame:
        """获取概念板块成分股"""
        url = f"{self.BASE_URL}/clist/get"
        params = {
            'cb': 'jQuery112406389542653718456_1640754174808',
            'pn': '1',
            'pz': '1000',
            'po': '1',
            'np': '1',
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': '2',
            'invt': '2',
            'fid': 'f3',
            'fs': f'm:0+t:6+f:!2,m:0+t:13+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2,m:1+t:23+f:!2,m:0+t:81+s:2048',
            'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152',
            '_': str(int(time.time() * 1000))
        }

        # 需要加上概念代码过滤
        params['fs'] = f"b:{concept_code}+f:!50"

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            # 解析JSONP响应
            text = response.text
            start = text.find('(') + 1
            end = text.rfind(')')
            json_str = text[start:end]

            data = json.loads(json_str)

            if not data.get('data') or not data['data'].get('diff'):
                return pd.DataFrame()

            stocks = []
            for item in data['data']['diff']:
                stock = {
                    'stock_code': item.get('f12', ''),
                    'stock_name': item.get('f14', ''),
                    'price': item.get('f2', 0),
                    'change_pct': item.get('f3', 0),
                    'change_amount': item.get('f4', 0),
                    'volume': item.get('f5', 0),
                    'turnover': item.get('f6', 0),
                    'amplitude': item.get('f7', 0),
                    'high': item.get('f15', 0),
                    'low': item.get('f16', 0),
                    'open': item.get('f17', 0),
                    'prev_close': item.get('f18', 0),
                    'volume_ratio': item.get('f10', 0),
                    'pe_ratio': item.get('f9', 0),
                    'market_cap': item.get('f20', 0),
                    'float_market_cap': item.get('f21', 0),
                    'total_shares': item.get('f8', 0),
                    'concept_code': concept_code
                }
                stocks.append(stock)

            return pd.DataFrame(stocks)

        except Exception as e:
            if logger:
                logger.error(f"获取概念板块成分股失败 {concept_code}: {e}")
            return pd.DataFrame()


class BaiduConceptData:
    """百度概念板块数据源（备用）"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })

    def get_concept_list(self) -> pd.DataFrame:
        """获取概念板块列表（简化版本）"""
        try:
            # 这里可以实现百度数据源的概念板块获取
            # 目前返回空DataFrame作为占位
            if logger:
                logger.info("使用百度数据源获取概念板块列表")
            return pd.DataFrame()
        except Exception as e:
            if logger:
                logger.error(f"百度数据源获取概念板块列表失败: {e}")
            return pd.DataFrame()

    def get_concept_stocks(self, concept_code: str) -> pd.DataFrame:
        """获取概念板块成分股（简化版本）"""
        try:
            # 这里可以实现百度数据源的成分股获取
            # 目前返回空DataFrame作为占位
            if logger:
                logger.info(f"使用百度数据源获取概念成分股: {concept_code}")
            return pd.DataFrame()
        except Exception as e:
            if logger:
                logger.error(f"百度数据源获取概念成分股失败 {concept_code}: {e}")
            return pd.DataFrame()


class ConceptProvider:
    """概念板块数据提供器 - 智能降级机制"""

    def __init__(self):
        self.primary_source = EastMoneyConceptData()
        self.fallback_source = BaiduConceptData()
        self.cache_prefix = "concept_data"

    def get_concept_list(self, use_cache: bool = True) -> pd.DataFrame:
        """获取概念板块列表，支持智能降级"""
        cache_key = f"{self.cache_prefix}_concept_list"

        # 检查缓存
        if use_cache and cache_manager:
            cached_data = cache_manager.get('concept_data', cache_key)
            if cached_data is not None:
                if logger:
                    logger.info("从缓存获取概念板块列表")
                return cached_data

        # 尝试主数据源
        try:
            data = self.primary_source.get_concept_list()
            if not data.empty:
                if use_cache and cache_manager:
                    cache_manager.set('concept_data', cache_key, data)
                if logger:
                    logger.info(f"从东方财富获取到 {len(data)} 个概念板块")
                return data
        except Exception as e:
            if logger:
                logger.warning(f"主数据源获取概念板块失败，尝试备用源: {e}")

        # 降级到备用数据源
        try:
            data = self.fallback_source.get_concept_list()
            if not data.empty:
                if use_cache and cache_manager:
                    cache_manager.set('concept_data', cache_key, data)
                if logger:
                    logger.info(f"从备用数据源获取到 {len(data)} 个概念板块")
                return data
        except Exception as e:
            if logger:
                logger.error(f"备用数据源也获取概念板块失败: {e}")

        # 返回空DataFrame
        return pd.DataFrame()

    def get_concept_stocks(self, concept_code: str, use_cache: bool = True) -> pd.DataFrame:
        """获取概念板块成分股，支持智能降级"""
        cache_key = f"{self.cache_prefix}_stocks_{concept_code}"

        # 检查缓存
        if use_cache and cache_manager:
            cached_data = cache_manager.get('concept_data', cache_key)
            if cached_data is not None:
                if logger:
                    logger.info(f"从缓存获取概念成分股: {concept_code}")
                return cached_data

        # 尝试主数据源
        try:
            data = self.primary_source.get_concept_stocks(concept_code)
            if not data.empty:
                if use_cache and cache_manager:
                    cache_manager.set('concept_data', cache_key, data)
                if logger:
                    logger.info(f"从东方财富获取到概念 {concept_code} 的 {len(data)} 只成分股")
                return data
        except Exception as e:
            if logger:
                logger.warning(f"主数据源获取概念成分股失败，尝试备用源: {e}")

        # 降级到备用数据源
        try:
            data = self.fallback_source.get_concept_stocks(concept_code)
            if not data.empty:
                if use_cache and cache_manager:
                    cache_manager.set('concept_data', cache_key, data)
                if logger:
                    logger.info(f"从备用数据源获取到概念 {concept_code} 的 {len(data)} 只成分股")
                return data
        except Exception as e:
            if logger:
                logger.error(f"备用数据源也获取概念成分股失败: {e}")

        # 返回空DataFrame
        return pd.DataFrame()

    def get_top_concepts(self, sort_by: str = "change_pct", ascending: bool = False, limit: int = 20) -> pd.DataFrame:
        """获取概念板块排行榜"""
        try:
            data = self.get_concept_list()
            if data.empty:
                return pd.DataFrame()

            # 按指定字段排序
            if sort_by in data.columns:
                sorted_data = data.sort_values(by=sort_by, ascending=ascending).head(limit)
                if logger:
                    logger.info(f"获取概念板块排行榜: {sort_by} 前{limit}名")
                return sorted_data
            else:
                if logger:
                    logger.warning(f"排序字段 {sort_by} 不存在")
                return data.head(limit)

        except Exception as e:
            if logger:
                logger.error(f"获取概念板块排行榜失败: {e}")
            return pd.DataFrame()


# 全局概念数据提供器实例
_concept_provider = None

def get_concept_provider() -> ConceptProvider:
    """获取概念数据提供器实例"""
    global _concept_provider
    if _concept_provider is None:
        _concept_provider = ConceptProvider()
    return _concept_provider


# 便捷函数
def get_concept_list(use_cache: bool = True) -> pd.DataFrame:
    """获取概念板块列表"""
    provider = get_concept_provider()
    return provider.get_concept_list(use_cache=use_cache)


def get_concept_stocks(concept_code: str, use_cache: bool = True) -> pd.DataFrame:
    """获取概念板块成分股"""
    provider = get_concept_provider()
    return provider.get_concept_stocks(concept_code, use_cache=use_cache)


def get_top_concepts(sort_by: str = "change_pct", ascending: bool = False, limit: int = 20) -> pd.DataFrame:
    """获取概念板块排行榜"""
    provider = get_concept_provider()
    return provider.get_top_concepts(sort_by=sort_by, ascending=ascending, limit=limit)