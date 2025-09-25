"""
概念板块数据提供器模块

基于adata架构设计，提供概念板块和成分股相关的数据获取功能
- 概念板块列表获取
- 板块涨跌幅排行
- 成分股查询
- 概念行情数据(历史K线、分时、实时)

参考文件: /Users/yyj/GitProject/adata/adata/stock/market 模块
"""

import pandas as pd
import requests
import json
import datetime
from datetime import datetime
import time

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


# 缓存配置
CACHE_CONFIG = {
    'concept_list_ttl': 3600,    # 概念列表1小时缓存
    'concept_stocks_ttl': 1800,  # 成分股30分钟缓存
    'market_ttl': 300,           # 行情数据5分钟缓存
    'realtime_ttl': 300,         # 实时数据5分钟缓存
    'capital_flow_ttl': 300,     # 概念资金流向5分钟缓存
}

# AData标准列定义
_MARKET_COLUMNS = ['index_code', 'trade_time', 'trade_date', 'open', 'high', 'low', 'close', 'volume',
                   'amount', 'change', 'change_pct']
_MARKET_CONCEPT_MIN_COLUMNS = ['index_code', 'trade_time', 'trade_date', 'price', 'avg_price', 'volume',
                               'amount', 'change', 'change_pct']
_MARKET_CONCEPT_CURRENT_COLUMNS = ['index_code', 'trade_time', 'trade_date', 'open', 'high', 'low', 'price',
                                   'volume', 'amount', 'change', 'change_pct']

# 概念资金流向列定义（参考东方财富API字段）
_CONCEPT_CAPITAL_FLOW_COLUMNS = ['index_code', 'index_name', 'change_pct', 'main_net_inflow', 'main_net_inflow_rate',
                                 'max_net_inflow', 'max_net_inflow_rate', 'lg_net_inflow', 'lg_net_inflow_rate',
                                 'mid_net_inflow', 'mid_net_inflow_rate', 'sm_net_inflow', 'sm_net_inflow_rate',
                                 'stock_code', 'stock_name']

# API配置
EASTMONEY_API_CONFIG = {
    'base_urls': {
        'clist': 'https://push2.eastmoney.com/api/qt/clist/get',
        'stock_kline': 'https://push2his.eastmoney.com/api/qt/stock/kline/get',
        'stock_trends': 'https://push2his.eastmoney.com/api/qt/stock/trends2/get',
        'stock_realtime': 'https://push2.eastmoney.com/api/qt/stock/get'
    },
    'common_params': {
        'cb': 'jQuery112406389542653718456_1640754174808',
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': '2',
        'invt': '2'
    }
}

# 会话配置
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'http://quote.eastmoney.com/',
    'Accept': 'application/json, text/javascript, */*; q=0.01'
})


def _get_cached_data(cache_key: str, use_cache: bool = True):
    """获取缓存数据"""
    if use_cache and cache_manager:
        cached_data = cache_manager.get('concept_data', cache_key)
        if cached_data is not None:
            return cached_data
    return None


def _set_cached_data(cache_key: str, data, ttl: int, use_cache: bool = True):
    """设置缓存数据"""
    if use_cache and cache_manager and not data.empty:
        cache_manager.set('concept_data', cache_key, data, ttl=ttl)


def _make_eastmoney_request(api_type: str, additional_params: dict) -> dict:
    """
    统一的东方财富API请求函数

    Args:
        api_type: API类型 ('clist', 'stock_kline', 'stock_trends', 'stock_realtime')
        additional_params: 额外的请求参数

    Returns:
        dict: 解析后的JSON数据
    """
    url = EASTMONEY_API_CONFIG['base_urls'].get(api_type)
    if not url:
        raise ValueError(f"不支持的API类型: {api_type}")

    # 合并基础参数和额外参数
    params = {**EASTMONEY_API_CONFIG['common_params'], **additional_params}

    # 动态更新cb参数（时间戳）
    params['cb'] = f"jQuery112309367957412610306_{int(time.time() * 1000)}"
    params['_'] = str(int(time.time() * 1000))

    try:
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()

        # 解析JSONP响应
        text = response.text
        start = text.find('(') + 1
        end = text.rfind(')')
        json_str = text[start:end]

        return json.loads(json_str)
    except Exception as e:
        if logger:
            logger.error(f"❌ 东方财富API请求失败 ({api_type}): {str(e)}")
        raise


def get_concept_list(use_cache: bool = True) -> pd.DataFrame:
    """获取概念板块列表"""
    cache_key = "concept_data_concept_list"

    # 检查缓存
    cached_data = _get_cached_data(cache_key, use_cache)
    if cached_data is not None:
        if logger:
            logger.info("从缓存获取概念板块列表")
        return cached_data

    # 构造请求参数
    params = {
        'pn': '1',
        'pz': '2000',
        'po': '1',
        'np': '1',
        'fid': 'f3',
        'fs': 'm:90+t:3+f:!50',
        'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f11,f62,f128,f136,f115,f152'
    }

    try:
        # 使用统一API请求函数
        data = _make_eastmoney_request('clist', params)

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

        result_df = pd.DataFrame(concepts)

        # 设置缓存
        _set_cached_data(cache_key, result_df, CACHE_CONFIG['concept_list_ttl'], use_cache)

        if logger:
            logger.info(f"从东方财富获取到 {len(result_df)} 个概念板块")

        return result_df

    except Exception as e:
        if logger:
            logger.error(f"获取概念板块列表失败: {e}")
        return pd.DataFrame()


def get_concept_stocks(concept_code: str, use_cache: bool = True) -> pd.DataFrame:
    """获取概念板块成分股"""
    cache_key = f"concept_data_stocks_{concept_code}"

    # 检查缓存
    cached_data = _get_cached_data(cache_key, use_cache)
    if cached_data is not None:
        if logger:
            logger.info(f"从缓存获取概念成分股: {concept_code}")
        return cached_data

    # 获取数据
    url = "https://push2.eastmoney.com/api/qt/clist/get"
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
        'fs': f"b:{concept_code}+f:!50",
        'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152',
        '_': str(int(time.time() * 1000))
    }

    try:
        response = session.get(url, params=params, timeout=10)
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

        result_df = pd.DataFrame(stocks)

        # 设置缓存
        _set_cached_data(cache_key, result_df, CACHE_CONFIG['concept_stocks_ttl'], use_cache)

        if logger:
            logger.info(f"从东方财富获取到概念 {concept_code} 的 {len(result_df)} 只成分股")

        return result_df

    except Exception as e:
        if logger:
            logger.error(f"获取概念板块成分股失败 {concept_code}: {e}")
        return pd.DataFrame()


def get_top_concepts(sort_by: str = "change_pct", ascending: bool = False, limit: int = 20) -> pd.DataFrame:
    """获取概念板块排行榜"""
    data = get_concept_list()
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


def get_market_concept_east(index_code: str = 'BK0612', k_type: int = 1) -> pd.DataFrame:
    """
    获取东方财富的概念的历史行情数据（基于AData参考实现）

    Args:
        index_code: 东方财富概念指数代码：BK开头，如'BK0612'
        k_type: k线类型：1.日；2.周；3.月 默认：1 日k

    Returns:
        DataFrame: k线行情数据 [日期，开，高，低，收,成交量，成交额]
    """
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?" \
          f"secid=90.{index_code}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61" \
          f"&klt=10{k_type}&fqt=1&end=20500101&lmt=1000000"

    res_json = session.get(url, timeout=30).json()

    # 解析数据
    code = res_json['data']['code']
    if code != index_code:
        return pd.DataFrame()

    res_data = res_json['data']['klines']
    data = []
    for _ in res_data:
        row = str(_).split(',')
        data.append(
            {'trade_date': row[0], 'open': row[1], 'close': row[2], 'high': row[3], 'low': row[4], 'volume': row[5],
             'amount': row[6], 'change': row[9], 'change_pct': row[8], 'index_code': index_code})
    result_df = pd.DataFrame(data=data, columns=_MARKET_COLUMNS)

    # 清洗数据
    result_df[['open', 'high', 'low', 'close', 'volume', 'amount', 'change', 'change_pct']] = \
        result_df[['open', 'high', 'low', 'close', 'volume', 'amount', 'change', 'change_pct']].astype(float)
    result_df['trade_time'] = pd.to_datetime(result_df['trade_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
    result_df = result_df.round(2)
    return result_df


def get_market_concept_min_east(index_code: str = 'BK0612') -> pd.DataFrame:
    """
    获取概念行情当日分时（基于AData参考实现）

    Args:
        index_code: 概念指数代码，如'BK0612'

    Returns:
        DataFrame: 时间，现价，成交额（元），均价，成交量（股） 涨跌额，涨跌幅
    """
    url = f"https://push2his.eastmoney.com/api/qt/stock/trends2/get?" \
          f"fields2=f51,f52,f53,f54,f55,f56,f57,f58&secid=90.{index_code}&" \
          f"ndays=1&iscr=0&fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13"

    res_json = session.get(url, timeout=30).json()

    # 解析数据
    code = res_json['data']['code']
    pre_price = res_json['data']['prePrice']
    if code != index_code:
        return pd.DataFrame()

    res_data = res_json['data']['trends']
    data = []
    for _ in res_data:
        row = str(_).split(',')
        data.append(
            {'trade_date': row[0], 'open': row[1], 'price': row[2], 'high': row[3], 'low': row[4],
             'volume': row[5], 'amount': row[6], 'avg_price': row[7], 'index_code': index_code})
    result_df = pd.DataFrame(data=data, columns=_MARKET_CONCEPT_MIN_COLUMNS)

    # 清洗数据
    result_df[['price', 'volume', 'amount', 'avg_price']] = \
        result_df[['price', 'volume', 'amount', 'avg_price']].astype(float)
    result_df['trade_time'] = pd.to_datetime(result_df['trade_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
    result_df['trade_date'] = pd.to_datetime(result_df['trade_date']).dt.strftime('%Y-%m-%d')
    result_df['change'] = result_df['price'] - pre_price
    result_df['change_pct'] = result_df['change'] / pre_price * 100
    result_df = result_df.round(2)
    return result_df


def get_market_concept_current_east(index_code: str = 'BK0612') -> pd.DataFrame:
    """
    获取概念当前行情数据（基于AData参考实现）

    Args:
        index_code: 东方财富指数代码，如'BK0612'

    Returns:
        DataFrame: k线行情数据 [概念代码,交易时间，交易日期，开，高，低，当前价格,成交量，成交额]
    """
    url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=90.{index_code}&" \
          f"fields=f57,f58,f106,f59,f43,f46,f60,f44,f45,f47,f48,f49,f113,f114,f115,f117,f85,f50,f119,f120," \
          f"f121,f122,f135,f136,f137,f138,f139,f140,f141,f142,f143,f144,f145,f146,f147,f148,f149"

    res_json = session.get(url, timeout=30).json()

    # 解析数据
    j = res_json['data']
    if not j:
        return pd.DataFrame(data=[], columns=_MARKET_CONCEPT_CURRENT_COLUMNS)

    code = j['f57']
    if code != index_code:
        return pd.DataFrame(data=[], columns=_MARKET_CONCEPT_CURRENT_COLUMNS)

    pre_close = j['f60']
    data = [{'open': j['f46'], 'high': j['f44'], 'low': j['f45'], 'price': j['f43'], 'volume': j['f47'],
             'amount': j['f48'], 'index_code': index_code}]
    result_df = pd.DataFrame(data=data, columns=_MARKET_CONCEPT_CURRENT_COLUMNS)

    # 清洗数据
    result_df[['open', 'high', 'low', 'price', 'volume', 'amount']] = \
        result_df[['open', 'high', 'low', 'price', 'volume', 'amount']].astype(float)
    result_df['change'] = result_df['price'] - pre_close
    result_df['change_pct'] = result_df['change'] / pre_close * 100
    result_df = result_df.round(2)
    result_df['trade_time'] = datetime.now()
    result_df['trade_date'] = datetime.now().strftime('%Y-%m-%d')
    return result_df


def get_concept_market_data(index_code: str = 'BK0612', k_type: int = 1, use_cache: bool = True) -> pd.DataFrame:
    """获取概念历史行情数据

    Args:
        index_code: 概念指数代码，如'BK0612'
        k_type: k线类型：1.日；2.周；3.月 默认：1 日k
        use_cache: 是否使用缓存

    Returns:
        DataFrame: 历史行情数据，包含开高低收、成交量成交额等信息
    """
    cache_key = f"concept_data_market_{index_code}_{k_type}"

    # 检查缓存
    cached_data = _get_cached_data(cache_key, use_cache)
    if cached_data is not None:
        if logger:
            logger.info(f"✅ 从缓存获取{index_code}概念历史行情数据")
        return cached_data

    # 获取数据
    df = get_market_concept_east(index_code, k_type)

    # 设置缓存
    _set_cached_data(cache_key, df, CACHE_CONFIG['market_ttl'], use_cache)

    return df


def get_concept_market_realtime(index_code: str = 'BK0612', use_cache: bool = True) -> pd.DataFrame:
    """获取概念分时行情数据

    Args:
        index_code: 概念指数代码，如'BK0612'
        use_cache: 是否使用缓存

    Returns:
        DataFrame: 分时行情数据，包含时间、价格、成交量等信息
    """
    cache_key = f"concept_data_realtime_{index_code}"

    # 检查缓存
    cached_data = _get_cached_data(cache_key, use_cache)
    if cached_data is not None:
        if logger:
            logger.info(f"✅ 从缓存获取{index_code}概念分时行情数据")
        return cached_data

    # 获取数据
    df = get_market_concept_min_east(index_code)

    # 设置缓存
    _set_cached_data(cache_key, df, CACHE_CONFIG['realtime_ttl'], use_cache)

    return df


def get_concept_market_current(index_code: str = 'BK0612', use_cache: bool = True) -> pd.DataFrame:
    """获取概念当前行情数据

    Args:
        index_code: 概念指数代码，如'BK0612'
        use_cache: 是否使用缓存

    Returns:
        DataFrame: 当前行情数据，包含最新价格、涨跌幅等信息
    """
    cache_key = f"concept_data_current_{index_code}"

    # 检查缓存
    cached_data = _get_cached_data(cache_key, use_cache)
    if cached_data is not None:
        if logger:
            logger.info(f"✅ 从缓存获取{index_code}概念当前行情数据")
        return cached_data

    # 获取数据
    df = get_market_concept_current_east(index_code)

    # 设置缓存
    _set_cached_data(cache_key, df, CACHE_CONFIG['realtime_ttl'], use_cache)

    return df


def get_all_concept_capital_flow_east(days_type: int = 1) -> pd.DataFrame:
    """
    获取全部概念板块资金流向数据（基于东方财富）

    Args:
        days_type: 天数类型：1.当天，5.最近5日；10.最近十日

    Returns:
        DataFrame: 概念板块资金流向数据
    """
    # 字段映射配置（参考 /Users/yyj/GitProject/adata/adata/stock/market/concept_capital_flow/capital_flow_east.py）
    fid = {
        1: 'f62',
        5: 'f164',
        10: 'f174'
    }.get(days_type, 'f62')

    fields = {
        1: 'f12,f14,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205',
        5: 'f12,f14,f109,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f257,f258',
        10: 'f12,f14,f160,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183,f260,f261'
    }.get(days_type, 'f12,f14,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205')

    # 分页循环获取数据
    curr_page = 1
    all_data = []

    try:
        while curr_page < 50:  # 防止无限循环
            url = f"https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                'cb': f'jQuery112309367957412610306_{int(time.time() * 1000)}',
                'fid': fid,
                'po': '1',
                'pz': '50',
                'pn': str(curr_page),
                'np': '1',
                'fltt': '2',
                'invt': '2',
                'fs': 'm:90 t:3',  # 概念板块筛选条件
                'fields': fields
            }

            response = session.get(url, params=params, timeout=10)
            response.raise_for_status()

            # 解析JSONP响应
            text = response.text
            start = text.find('(') + 1
            end = text.rfind(')')
            json_str = text[start:end]

            data = json.loads(json_str).get('data')
            if not data or not data.get('diff'):
                break

            # 解析数据字段
            field_list = fields.split(',')
            for item in data['diff']:
                row_data = {}
                for i, col_name in enumerate(_CONCEPT_CAPITAL_FLOW_COLUMNS):
                    field_val = item.get(field_list[i], None)
                    if field_val == '-' or field_val is None:
                        continue
                    row_data[col_name] = field_val

                # 只添加完整的数据记录
                if len(row_data) == len(_CONCEPT_CAPITAL_FLOW_COLUMNS):
                    all_data.append(row_data)

            curr_page += 1

        # 构建DataFrame
        if not all_data:
            return pd.DataFrame(columns=_CONCEPT_CAPITAL_FLOW_COLUMNS)

        result_df = pd.DataFrame(all_data)

        # 数据类型转换
        numeric_columns = ['change_pct', 'main_net_inflow', 'sm_net_inflow', 'mid_net_inflow',
                          'lg_net_inflow', 'max_net_inflow', 'main_net_inflow_rate',
                          'sm_net_inflow_rate', 'mid_net_inflow_rate', 'lg_net_inflow_rate',
                          'max_net_inflow_rate']

        for col in numeric_columns:
            if col in result_df.columns:
                result_df[col] = pd.to_numeric(result_df[col], errors='coerce')

        if logger:
            logger.info(f"✅ 成功获取概念板块资金流向数据，共{len(result_df)}条记录（{days_type}日类型）")

        return result_df

    except Exception as e:
        if logger:
            logger.error(f"❌ 获取概念板块资金流向数据失败: {str(e)}")
        return pd.DataFrame(columns=_CONCEPT_CAPITAL_FLOW_COLUMNS)


def get_concept_capital_flow(days_type: int = 1, use_cache: bool = True) -> pd.DataFrame:
    """
    获取概念板块资金流向数据（带缓存）

    Args:
        days_type: 天数类型：1.当天，5.最近5日；10.最近十日
        use_cache: 是否使用缓存

    Returns:
        DataFrame: 概念板块资金流向数据
    """
    cache_key = f"concept_capital_flow_{days_type}"

    # 检查缓存
    cached_data = _get_cached_data(cache_key, use_cache)
    if cached_data is not None:
        if logger:
            logger.info(f"✅ 从缓存获取概念板块资金流向数据（{days_type}日类型）")
        return cached_data

    # 获取数据
    df = get_all_concept_capital_flow_east(days_type)

    # 设置缓存
    _set_cached_data(cache_key, df, CACHE_CONFIG['capital_flow_ttl'], use_cache)

    return df


def get_top_concept_capital_flow(days_type: int = 1, sort_by: str = "main_net_inflow",
                                ascending: bool = False, limit: int = 20) -> pd.DataFrame:
    """
    获取概念板块资金流向排行榜

    Args:
        days_type: 天数类型：1.当天，5.最近5日；10.最近十日
        sort_by: 排序字段（main_net_inflow, main_net_inflow_rate, change_pct等）
        ascending: 是否升序排列
        limit: 返回记录数量

    Returns:
        DataFrame: 排序后的概念板块资金流向数据
    """
    df = get_concept_capital_flow(days_type)

    if df.empty:
        return pd.DataFrame()

    # 按指定字段排序
    if sort_by in df.columns:
        sorted_df = df.sort_values(by=sort_by, ascending=ascending).head(limit)
        if logger:
            logger.info(f"✅ 获取概念板块资金流向排行榜: {sort_by} 前{limit}名（{days_type}日类型）")
        return sorted_df
    else:
        if logger:
            logger.warning(f"⚠️ 排序字段 {sort_by} 不存在，返回前{limit}条数据")
        return df.head(limit)


def get_concept_capital_flow_summary(days_type: int = 1) -> dict:
    """
    获取概念板块资金流向汇总统计

    Args:
        days_type: 天数类型：1.当天，5.最近5日；10.最近十日

    Returns:
        dict: 汇总统计信息
    """
    df = get_concept_capital_flow(days_type)

    if df.empty:
        return {}

    # 统计汇总信息
    summary = {
        'total_concepts': len(df),
        'net_inflow_positive': len(df[df['main_net_inflow'] > 0]),
        'net_inflow_negative': len(df[df['main_net_inflow'] < 0]),
        'total_main_net_inflow': df['main_net_inflow'].sum(),
        'avg_main_net_inflow': df['main_net_inflow'].mean(),
        'max_main_net_inflow': df['main_net_inflow'].max(),
        'min_main_net_inflow': df['main_net_inflow'].min(),
        'avg_change_pct': df['change_pct'].mean(),
        'max_change_pct': df['change_pct'].max(),
        'min_change_pct': df['change_pct'].min(),
        'days_type': days_type
    }

    if logger:
        logger.info(f"✅ 生成概念板块资金流向汇总统计（{days_type}日类型）")

    return summary


class ConceptDataProvider:
    """概念数据提供器类"""

    def __init__(self):
        self.logger = logger

    def get_concept_list(self, use_cache: bool = True) -> pd.DataFrame:
        """获取概念板块列表"""
        return get_concept_list(use_cache=use_cache)

    def get_concept_stocks(self, concept_code: str, use_cache: bool = True) -> pd.DataFrame:
        """获取概念成分股"""
        return get_concept_stocks(concept_code=concept_code, use_cache=use_cache)

    def get_top_concepts(self, sort_by: str = "change_pct", ascending: bool = False, limit: int = 20) -> pd.DataFrame:
        """获取概念排行榜"""
        return get_top_concepts(sort_by=sort_by, ascending=ascending, limit=limit)

    def get_concept_capital_flow(self, days_type: int = 1, use_cache: bool = True) -> pd.DataFrame:
        """获取概念资金流向"""
        return get_concept_capital_flow(days_type=days_type, use_cache=use_cache)


def get_concept_provider() -> ConceptDataProvider:
    """获取概念数据提供器实例"""
    return ConceptDataProvider()


if __name__ == '__main__':
    # 测试概念市场行情功能（基于AData实现）
    print("=== 测试概念市场行情功能（基于AData架构）===")

    # 测试历史行情数据
    print("\n=== 测试概念历史行情数据 ===")
    result = get_market_concept_east(index_code='BK0612')
    print(f"获取数据条数: {len(result)}")
    if not result.empty:
        print("数据列:")
        print(result.columns.tolist())
        print("最近5条数据:")
        print(result.tail())

    # 测试分时行情数据
    print("\n=== 测试概念分时行情数据 ===")
    result_min = get_market_concept_min_east(index_code='BK0612')
    print(f"获取数据条数: {len(result_min)}")
    if not result_min.empty:
        print("数据列:")
        print(result_min.columns.tolist())
        print("最近5条数据:")
        print(result_min.tail())

    # 测试当前行情数据
    print("\n=== 测试概念当前行情数据 ===")
    result_current = get_market_concept_current_east(index_code='BK0612')
    print(f"获取数据条数: {len(result_current)}")
    if not result_current.empty:
        print("数据列:")
        print(result_current.columns.tolist())
        print("数据内容:")
        print(result_current)

    print("\n=== 综合测试 ===")

    # 测试概念列表
    print("\n=== 测试概念板块列表 ===")
    concepts = get_concept_list()
    print(f"获取到 {len(concepts)} 个概念板块")
    if not concepts.empty:
        print("前5个概念:")
        print(concepts.head())

    # 测试概念成分股
    if not concepts.empty:
        sample_code = concepts.iloc[0]['concept_code']
        print(f"\n=== 测试概念成分股 ({sample_code}) ===")
        stocks = get_concept_stocks(sample_code)
        print(f"概念 {sample_code} 包含 {len(stocks)} 只成分股")
        if not stocks.empty:
            print("前5只成分股:")
            print(stocks.head())

    # 测试概念排行榜
    print("\n=== 测试概念板块排行榜 ===")
    top_concepts = get_top_concepts(sort_by="change_pct", limit=10)
    print(f"涨幅前10的概念板块:")
    if not top_concepts.empty:
        print(top_concepts[['concept_code', 'concept_name', 'change_pct', 'price']].head())

    # 测试概念历史行情（带缓存）
    print("\n=== 测试概念历史行情数据（带缓存） ===")
    df_concept_market = get_concept_market_data('BK0612', k_type=1)
    print(f"概念历史行情数据条数: {len(df_concept_market)}")
    if not df_concept_market.empty:
        print(f"数据列: {df_concept_market.columns.tolist()}")
        print("前5条数据:")
        print(df_concept_market.head())

    # 测试概念分时行情（带缓存）
    print("\n=== 测试概念分时行情数据（带缓存） ===")
    df_concept_realtime = get_concept_market_realtime('BK0612')
    print(f"概念分时行情数据条数: {len(df_concept_realtime)}")
    if not df_concept_realtime.empty:
        print(f"数据列: {df_concept_realtime.columns.tolist()}")
        print("前5条数据:")
        print(df_concept_realtime.head())

    # 测试概念当前行情（带缓存）
    print("\n=== 测试概念当前行情数据（带缓存） ===")
    df_concept_current = get_concept_market_current('BK0612')
    print(f"概念当前行情数据条数: {len(df_concept_current)}")
    if not df_concept_current.empty:
        print(f"数据列: {df_concept_current.columns.tolist()}")
        print("数据内容:")
        print(df_concept_current)

    print("\n" + "="*60)
    print("=== 测试概念板块资金流向功能 ===")

    # 测试当日概念板块资金流向
    print("\n=== 测试当日概念板块资金流向 ===")
    df_concept_flow = get_concept_capital_flow(days_type=1)
    print(f"当日概念板块资金流向数据条数: {len(df_concept_flow)}")
    if not df_concept_flow.empty:
        print(f"数据列: {df_concept_flow.columns.tolist()}")
        print("前5条数据:")
        print(df_concept_flow.head())

    # 测试5日概念板块资金流向
    print("\n=== 测试5日概念板块资金流向 ===")
    df_concept_flow_5d = get_concept_capital_flow(days_type=5)
    print(f"5日概念板块资金流向数据条数: {len(df_concept_flow_5d)}")
    if not df_concept_flow_5d.empty:
        print("前3条数据:")
        print(df_concept_flow_5d.head(3))

    # 测试10日概念板块资金流向
    print("\n=== 测试10日概念板块资金流向 ===")
    df_concept_flow_10d = get_concept_capital_flow(days_type=10)
    print(f"10日概念板块资金流向数据条数: {len(df_concept_flow_10d)}")

    # 测试概念板块资金流向排行榜
    print("\n=== 测试概念板块资金流向排行榜 ===")
    top_inflow = get_top_concept_capital_flow(days_type=1, sort_by="main_net_inflow", limit=10)
    print(f"主力净流入前10的概念板块:")
    if not top_inflow.empty:
        print(top_inflow[['index_code', 'index_name', 'main_net_inflow', 'main_net_inflow_rate', 'change_pct']].head())

    top_rate = get_top_concept_capital_flow(days_type=1, sort_by="main_net_inflow_rate", limit=5)
    print(f"\n主力净流入率前5的概念板块:")
    if not top_rate.empty:
        print(top_rate[['index_code', 'index_name', 'main_net_inflow', 'main_net_inflow_rate', 'change_pct']].head())

    # 测试概念板块资金流向汇总统计
    print("\n=== 测试概念板块资金流向汇总统计 ===")
    summary_1d = get_concept_capital_flow_summary(days_type=1)
    print(f"当日概念板块资金流向汇总:")
    for key, value in summary_1d.items():
        print(f"  {key}: {value}")

    summary_5d = get_concept_capital_flow_summary(days_type=5)
    print(f"\n5日概念板块资金流向汇总:")
    for key, value in summary_5d.items():
        print(f"  {key}: {value}")