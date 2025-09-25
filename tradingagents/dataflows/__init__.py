# 使用延迟导入优化启动性能
import sys
from typing import TYPE_CHECKING

# 导入日志模块（轻量级模块，保持立即导入）
try:
    from tradingagents.utils.logging_manager import get_logger
    logger = get_logger('agents')
except ImportError:
    logger = None

# 延迟导入检查和缓存
_import_cache = {}
_availability_cache = {}

def _get_module_availability(module_name, import_path):
    """检查模块可用性并缓存结果"""
    if module_name not in _availability_cache:
        try:
            __import__(import_path)
            _availability_cache[module_name] = True
            if logger:
                logger.info(f"✅ {module_name}模块可用")
        except ImportError as e:
            _availability_cache[module_name] = False
            if logger:
                logger.warning(f"⚠️ {module_name}模块不可用: {e}")
    return _availability_cache[module_name]

# 全局可用性检查（延迟执行）
def _get_yfinance_availability():
    return _get_module_availability('yfinance', 'tradingagents.dataflows.yfin_utils')

def _get_stockstats_availability():
    return _get_module_availability('stockstats', 'tradingagents.dataflows.stockstats_utils')

# 模块级别的可用性变量
YFINANCE_AVAILABLE = None
STOCKSTATS_AVAILABLE = None

def __getattr__(name):
    """动态导入数据流模块，只在首次访问时加载"""
    global YFINANCE_AVAILABLE, STOCKSTATS_AVAILABLE

    # 处理可用性检查
    if name == 'YFINANCE_AVAILABLE':
        if YFINANCE_AVAILABLE is None:
            YFINANCE_AVAILABLE = _get_yfinance_availability()
        return YFINANCE_AVAILABLE

    if name == 'STOCKSTATS_AVAILABLE':
        if STOCKSTATS_AVAILABLE is None:
            STOCKSTATS_AVAILABLE = _get_stockstats_availability()
        return STOCKSTATS_AVAILABLE
    # 基础模块映射
    base_modules = {
        'get_data_in_range': ('tradingagents.dataflows.finnhub_utils', 'get_data_in_range'),
        'getNewsData': ('tradingagents.dataflows.googlenews_utils', 'getNewsData'),
        'fetch_top_from_category': ('tradingagents.dataflows.reddit_utils', 'fetch_top_from_category'),
    }

    # 可选模块映射
    optional_modules = {
        'YFinanceUtils': ('tradingagents.dataflows.yfin_utils', 'YFinanceUtils'),
        'StockstatsUtils': ('tradingagents.dataflows.stockstats_utils', 'StockstatsUtils'),
    }

    # Interface模块的函数映射
    interface_functions = {
        'get_finnhub_news': 'get_finnhub_news',
        'get_finnhub_company_insider_sentiment': 'get_finnhub_company_insider_sentiment',
        'get_finnhub_company_insider_transactions': 'get_finnhub_company_insider_transactions',
        'get_google_news': 'get_google_news',
        'get_reddit_global_news': 'get_reddit_global_news',
        'get_reddit_company_news': 'get_reddit_company_news',
        'get_simfin_balance_sheet': 'get_simfin_balance_sheet',
        'get_simfin_cashflow': 'get_simfin_cashflow',
        'get_simfin_income_statements': 'get_simfin_income_statements',
        'get_stock_stats_indicators_window': 'get_stock_stats_indicators_window',
        'get_stockstats_indicator': 'get_stockstats_indicator',
        'get_YFin_data_window': 'get_YFin_data_window',
        'get_YFin_data': 'get_YFin_data',
        'get_china_stock_data_tushare': 'get_china_stock_data_tushare',
        'search_china_stocks_tushare': 'search_china_stocks_tushare',
        'get_china_stock_fundamentals_tushare': 'get_china_stock_fundamentals_tushare',
        'get_china_stock_info_tushare': 'get_china_stock_info_tushare',
        'get_china_stock_data_unified': 'get_china_stock_data_unified',
        'get_china_stock_info_unified': 'get_china_stock_info_unified',
        'switch_china_data_source': 'switch_china_data_source',
        'get_current_china_data_source': 'get_current_china_data_source',
        'get_hk_stock_data_unified': 'get_hk_stock_data_unified',
        'get_hk_stock_info_unified': 'get_hk_stock_info_unified',
        'get_stock_data_by_market': 'get_stock_data_by_market',
    }

    # 使用缓存避免重复导入
    if name in _import_cache:
        return _import_cache[name]

    # 基础模块导入
    if name in base_modules:
        module_path, attr_name = base_modules[name]
        try:
            module = __import__(module_path, fromlist=[attr_name])
            result = getattr(module, attr_name)
            _import_cache[name] = result
            return result
        except ImportError as e:
            if logger:
                logger.error(f"导入基础模块失败 {name}: {e}")
            raise

    # 可选模块导入
    if name in optional_modules:
        module_path, attr_name = optional_modules[name]
        try:
            module = __import__(module_path, fromlist=[attr_name])
            result = getattr(module, attr_name)
            _import_cache[name] = result
            return result
        except ImportError as e:
            if logger:
                logger.warning(f"可选模块 {name} 不可用: {e}")
            return None

    # Interface函数导入
    if name in interface_functions:
        try:
            from tradingagents.dataflows import interface
            result = getattr(interface, interface_functions[name])
            _import_cache[name] = result
            return result
        except (ImportError, AttributeError) as e:
            if logger:
                logger.error(f"导入interface函数失败 {name}: {e}")
            raise ImportError(f"无法导入 {name}: {e}")

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    # News and sentiment functions
    "get_finnhub_news",
    "get_finnhub_company_insider_sentiment",
    "get_finnhub_company_insider_transactions",
    "get_google_news",
    "get_reddit_global_news",
    "get_reddit_company_news",
    # Financial statements functions
    "get_simfin_balance_sheet",
    "get_simfin_cashflow",
    "get_simfin_income_statements",
    # Technical analysis functions
    "get_stock_stats_indicators_window",
    "get_stockstats_indicator",
    # Market data functions
    "get_YFin_data_window",
    "get_YFin_data",
    # Tushare data functions
    "get_china_stock_data_tushare",
    "search_china_stocks_tushare",
    "get_china_stock_fundamentals_tushare",
    "get_china_stock_info_tushare",
    # Unified China data functions
    "get_china_stock_data_unified",
    "get_china_stock_info_unified",
    "switch_china_data_source",
    "get_current_china_data_source",
    # Hong Kong stock functions
    "get_hk_stock_data_unified",
    "get_hk_stock_info_unified",
    "get_stock_data_by_market",
]
