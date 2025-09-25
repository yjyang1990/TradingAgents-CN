#!/usr/bin/env python3
"""
数据源管理器
统一管理中国股票数据源的选择和切换，支持Tushare、AKShare、BaoStock等
"""

import os
import time
from typing import Dict, List, Optional, Any
from enum import Enum
import warnings
import pandas as pd

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')
warnings.filterwarnings('ignore')

# 导入统一日志系统
from tradingagents.utils.logging_init import setup_dataflow_logging
logger = setup_dataflow_logging()


class ChinaDataSource(Enum):
    """中国股票数据源枚举"""
    TUSHARE = "tushare"
    AKSHARE = "akshare"
    BAOSTOCK = "baostock"
    TDX = "tdx"  # 已弃用：建议使用Tushare替代





class DataSourceManager:
    """数据源管理器"""

    def __init__(self):
        """初始化数据源管理器"""
        self.default_source = self._get_default_source()
        self.available_sources = self._check_available_sources()
        self.current_source = self.default_source

        logger.info(f"📊 数据源管理器初始化完成")
        logger.info(f"   默认数据源: {self.default_source.value}")
        logger.info(f"   可用数据源: {[s.value for s in self.available_sources]}")

    def _get_default_source(self) -> ChinaDataSource:
        """获取默认数据源"""
        # 从环境变量获取，默认使用AKShare作为第一优先级数据源
        env_source = os.getenv('DEFAULT_CHINA_DATA_SOURCE', 'akshare').lower()

        # 映射到枚举
        source_mapping = {
            'tushare': ChinaDataSource.TUSHARE,
            'akshare': ChinaDataSource.AKSHARE,
            'baostock': ChinaDataSource.BAOSTOCK,
            'tdx': ChinaDataSource.TDX
        }

        return source_mapping.get(env_source, ChinaDataSource.AKSHARE)

    # ==================== Tushare数据接口 ====================

    def get_china_stock_data_tushare(self, symbol: str, start_date: str, end_date: str) -> str:
        """
        使用Tushare获取中国A股历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            str: 格式化的股票数据报告
        """
        # 临时切换到Tushare数据源
        original_source = self.current_source
        self.current_source = ChinaDataSource.TUSHARE

        try:
            result = self._get_tushare_data(symbol, start_date, end_date)
            return result
        finally:
            # 恢复原始数据源
            self.current_source = original_source

    def search_china_stocks_tushare(self, keyword: str) -> str:
        """
        使用Tushare搜索中国股票

        Args:
            keyword: 搜索关键词

        Returns:
            str: 搜索结果
        """
        try:
            from .tushare_adapter import get_tushare_adapter

            logger.debug(f"🔍 [Tushare] 搜索股票: {keyword}")

            adapter = get_tushare_adapter()
            results = adapter.search_stocks(keyword)

            if results is not None and not results.empty:
                result = f"搜索关键词: {keyword}\n"
                result += f"找到 {len(results)} 只股票:\n\n"

                # 显示前10个结果
                for idx, row in results.head(10).iterrows():
                    result += f"代码: {row.get('symbol', '')}\n"
                    result += f"名称: {row.get('name', '未知')}\n"
                    result += f"行业: {row.get('industry', '未知')}\n"
                    result += f"地区: {row.get('area', '未知')}\n"
                    result += f"上市日期: {row.get('list_date', '未知')}\n"
                    result += "-" * 30 + "\n"

                return result
            else:
                return f"❌ 未找到匹配'{keyword}'的股票"

        except ImportError as e:
            logger.error(f"❌ [Tushare] 模块导入失败: {e}")
            return f"❌ Tushare模块未安装或导入失败: {e}"
        except ConnectionError as e:
            logger.error(f"❌ [Tushare] 网络连接失败: {e}")
            return f"❌ Tushare网络连接失败，请检查网络: {e}"
        except KeyError as e:
            logger.error(f"❌ [Tushare] 数据字段缺失: {e}")
            return f"❌ Tushare数据格式异常: {e}"
        except ValueError as e:
            logger.error(f"❌ [Tushare] 参数错误: {e}")
            return f"❌ 搜索参数错误: {e}"

    def get_china_stock_fundamentals_tushare(self, symbol: str) -> str:
        """
        使用Tushare获取中国股票基本面数据

        Args:
            symbol: 股票代码

        Returns:
            str: 基本面分析报告
        """
        try:
            from .tushare_adapter import get_tushare_adapter

            logger.debug(f"📊 [Tushare] 获取{symbol}基本面数据...")

            adapter = get_tushare_adapter()
            fundamentals = adapter.get_fundamentals(symbol)

            if fundamentals:
                return fundamentals
            else:
                return f"❌ 未获取到{symbol}的基本面数据"

        except ImportError as e:
            logger.error(f"❌ [Tushare] 模块导入失败: {e}")
            return f"❌ Tushare模块未安装: {e}"
        except ConnectionError as e:
            logger.error(f"❌ [Tushare] 网络连接失败: {e}")
            return f"❌ 网络连接失败，请检查网络: {e}"
        except KeyError as e:
            logger.error(f"❌ [Tushare] 数据字段缺失: {e}")
            return f"❌ 基本面数据格式异常: {e}"

    def get_china_stock_info_tushare(self, symbol: str) -> str:
        """
        使用Tushare获取中国股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            str: 股票基本信息
        """
        try:
            from .tushare_adapter import get_tushare_adapter

            logger.debug(f"📊 [Tushare] 获取{symbol}股票信息...")

            adapter = get_tushare_adapter()
            stock_info = adapter.get_stock_info(symbol)

            if stock_info:
                result = f"📊 {stock_info.get('name', '未知')}({symbol}) - 股票信息\n"
                result += f"股票代码: {stock_info.get('symbol', symbol)}\n"
                result += f"股票名称: {stock_info.get('name', '未知')}\n"
                result += f"所属行业: {stock_info.get('industry', '未知')}\n"
                result += f"所属地区: {stock_info.get('area', '未知')}\n"
                result += f"上市日期: {stock_info.get('list_date', '未知')}\n"
                result += f"市场类型: {stock_info.get('market', '未知')}\n"
                result += f"交易所: {stock_info.get('exchange', '未知')}\n"
                result += f"货币单位: {stock_info.get('curr_type', 'CNY')}\n"

                return result
            else:
                return f"❌ 未获取到{symbol}的股票信息"

        except ImportError as e:
            logger.error(f"❌ [Tushare] 模块导入失败: {e}")
            return f"❌ Tushare模块未安装: {e}"
        except ConnectionError as e:
            logger.error(f"❌ [Tushare] 网络连接失败: {e}")
            return f"❌ 网络连接失败，请检查网络: {e}"
        except KeyError as e:
            logger.error(f"❌ [Tushare] 数据字段缺失: {e}")
            return f"❌ 股票信息数据格式异常: {e}"
    
    def _check_available_sources(self) -> List[ChinaDataSource]:
        """检查可用的数据源"""
        available = []
        
        # 检查Tushare
        try:
            import tushare as ts
            token = os.getenv('TUSHARE_TOKEN')
            if token:
                available.append(ChinaDataSource.TUSHARE)
                logger.info("✅ Tushare数据源可用")
            else:
                logger.warning("⚠️ Tushare数据源不可用: 未设置TUSHARE_TOKEN")
        except ImportError:
            logger.warning("⚠️ Tushare数据源不可用: 库未安装")
        
        # 检查AKShare
        try:
            import akshare as ak
            available.append(ChinaDataSource.AKSHARE)
            logger.info("✅ AKShare数据源可用")
        except ImportError:
            logger.warning("⚠️ AKShare数据源不可用: 库未安装")
        
        # 检查BaoStock
        try:
            import baostock as bs
            available.append(ChinaDataSource.BAOSTOCK)
            logger.info(f"✅ BaoStock数据源可用")
        except ImportError:
            logger.warning(f"⚠️ BaoStock数据源不可用: 库未安装")
        
        # 检查TDX (通达信)
        try:
            import pytdx
            available.append(ChinaDataSource.TDX)
            logger.warning(f"⚠️ TDX数据源可用 (将被淘汰)")
        except ImportError:
            logger.info(f"ℹ️ TDX数据源不可用: 库未安装")
        
        return available
    
    def get_current_source(self) -> ChinaDataSource:
        """获取当前数据源"""
        return self.current_source
    
    def set_current_source(self, source: ChinaDataSource) -> bool:
        """设置当前数据源"""
        if source in self.available_sources:
            self.current_source = source
            logger.info(f"✅ 数据源已切换到: {source.value}")
            return True
        else:
            logger.error(f"❌ 数据源不可用: {source.value}")
            return False
    
    def get_data_adapter(self):
        """获取当前数据源的适配器"""
        if self.current_source == ChinaDataSource.TUSHARE:
            return self._get_tushare_adapter()
        elif self.current_source == ChinaDataSource.AKSHARE:
            return self._get_akshare_adapter()
        elif self.current_source == ChinaDataSource.BAOSTOCK:
            return self._get_baostock_adapter()
        elif self.current_source == ChinaDataSource.TDX:
            return self._get_tdx_adapter()
        else:
            raise ValueError(f"不支持的数据源: {self.current_source}")
    
    def _get_tushare_adapter(self):
        """获取Tushare适配器"""
        try:
            from .tushare_adapter import get_tushare_adapter
            return get_tushare_adapter()
        except ImportError as e:
            logger.error(f"❌ Tushare适配器导入失败: {e}")
            return None
    
    def _get_akshare_adapter(self):
        """获取AKShare适配器"""
        try:
            from .akshare_utils import get_akshare_provider
            return get_akshare_provider()
        except ImportError as e:
            logger.error(f"❌ AKShare适配器导入失败: {e}")
            return None
    
    def _get_baostock_adapter(self):
        """获取BaoStock适配器"""
        try:
            from .baostock_utils import get_baostock_provider
            return get_baostock_provider()
        except ImportError as e:
            logger.error(f"❌ BaoStock适配器导入失败: {e}")
            return None
    
    def _get_tdx_adapter(self):
        """获取TDX适配器 (已弃用)"""
        logger.warning(f"⚠️ 警告: TDX数据源已弃用，将在未来版本中移除，建议迁移至Tushare数据源")
        try:
            from .tdx_utils import get_tdx_provider
            return get_tdx_provider()
        except ImportError as e:
            logger.error(f"❌ TDX适配器导入失败: {e}")
            return None
    
    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> str:
        """
        获取股票数据的统一接口

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            str: 格式化的股票数据
        """
        # 记录详细的输入参数
        logger.info(f"📊 [数据获取] 开始获取股票数据",
                   extra={
                       'symbol': symbol,
                       'start_date': start_date,
                       'end_date': end_date,
                       'data_source': self.current_source.value,
                       'event_type': 'data_fetch_start'
                   })

        # 添加详细的股票代码追踪日志
        logger.info(f"🔍 [股票代码追踪] DataSourceManager.get_stock_data 接收到的股票代码: '{symbol}' (类型: {type(symbol)})")
        logger.info(f"🔍 [股票代码追踪] 股票代码长度: {len(str(symbol))}")
        logger.info(f"🔍 [股票代码追踪] 股票代码字符: {list(str(symbol))}")
        logger.info(f"🔍 [股票代码追踪] 当前数据源: {self.current_source.value}")

        start_time = time.time()

        try:
            # 根据数据源调用相应的获取方法
            if self.current_source == ChinaDataSource.TUSHARE:
                logger.info(f"🔍 [股票代码追踪] 调用 Tushare 数据源，传入参数: symbol='{symbol}'")
                result = self._get_tushare_data(symbol, start_date, end_date)
            elif self.current_source == ChinaDataSource.AKSHARE:
                result = self._get_akshare_data(symbol, start_date, end_date)
            elif self.current_source == ChinaDataSource.BAOSTOCK:
                result = self._get_baostock_data(symbol, start_date, end_date)
            elif self.current_source == ChinaDataSource.TDX:
                result = self._get_tdx_data(symbol, start_date, end_date)
            else:
                result = f"❌ 不支持的数据源: {self.current_source.value}"

            # 记录详细的输出结果
            duration = time.time() - start_time
            result_length = len(result) if result else 0
            is_success = result and "❌" not in result and "错误" not in result

            if is_success:
                logger.info(f"✅ [数据获取] 成功获取股票数据",
                           extra={
                               'symbol': symbol,
                               'start_date': start_date,
                               'end_date': end_date,
                               'data_source': self.current_source.value,
                               'duration': duration,
                               'result_length': result_length,
                               'result_preview': result[:200] + '...' if result_length > 200 else result,
                               'event_type': 'data_fetch_success'
                           })
                return result
            else:
                logger.warning(f"⚠️ [数据获取] 数据质量异常，尝试降级到其他数据源",
                              extra={
                                  'symbol': symbol,
                                  'start_date': start_date,
                                  'end_date': end_date,
                                  'data_source': self.current_source.value,
                                  'duration': duration,
                                  'result_length': result_length,
                                  'result_preview': result[:200] + '...' if result_length > 200 else result,
                                  'event_type': 'data_fetch_warning'
                              })

                # 数据质量异常时也尝试降级到其他数据源
                fallback_result = self._try_fallback_sources(symbol, start_date, end_date)
                if fallback_result and "❌" not in fallback_result and "错误" not in fallback_result:
                    logger.info(f"✅ [数据获取] 降级成功获取数据")
                    return fallback_result
                else:
                    logger.error(f"❌ [数据获取] 所有数据源都无法获取有效数据")
                    return result  # 返回原始结果（包含错误信息）

        except ImportError as e:
            duration = time.time() - start_time
            logger.error(f"❌ [数据获取] 模块导入失败: {e}")
            return f"❌ 数据源模块未安装: {e}"
        except ConnectionError as e:
            duration = time.time() - start_time
            logger.error(f"❌ [数据获取] 网络连接失败: {e}",
                        extra={
                            'symbol': symbol,
                            'start_date': start_date,
                            'end_date': end_date,
                            'data_source': self.current_source.value,
                            'duration': duration,
                            'error': str(e),
                            'event_type': 'data_fetch_exception'
                        }, exc_info=True)
            return self._try_fallback_sources(symbol, start_date, end_date)
    
    def _get_tushare_data(self, symbol: str, start_date: str, end_date: str) -> str:
        """使用Tushare获取数据 - 直接调用适配器，避免循环调用"""
        logger.debug(f"📊 [Tushare] 调用参数: symbol={symbol}, start_date={start_date}, end_date={end_date}")

        # 添加详细的股票代码追踪日志
        logger.info(f"🔍 [股票代码追踪] _get_tushare_data 接收到的股票代码: '{symbol}' (类型: {type(symbol)})")
        logger.info(f"🔍 [股票代码追踪] 股票代码长度: {len(str(symbol))}")
        logger.info(f"🔍 [股票代码追踪] 股票代码字符: {list(str(symbol))}")
        logger.info(f"🔍 [DataSourceManager详细日志] _get_tushare_data 开始执行")
        logger.info(f"🔍 [DataSourceManager详细日志] 当前数据源: {self.current_source.value}")

        start_time = time.time()
        try:
            # 直接调用适配器，避免循环调用interface
            from .tushare_adapter import get_tushare_adapter
            logger.info(f"🔍 [股票代码追踪] 调用 tushare_adapter，传入参数: symbol='{symbol}'")
            logger.info(f"🔍 [DataSourceManager详细日志] 开始调用tushare_adapter...")

            adapter = get_tushare_adapter()
            data = adapter.get_stock_data(symbol, start_date, end_date)

            if data is not None and not data.empty:
                # 获取股票基本信息
                stock_info = adapter.get_stock_info(symbol)
                stock_name = stock_info.get('name', f'股票{symbol}') if stock_info else f'股票{symbol}'

                # 计算最新价格和涨跌幅
                latest_data = data.iloc[-1]
                latest_price = latest_data.get('close', 0)
                prev_close = data.iloc[-2].get('close', latest_price) if len(data) > 1 else latest_price
                change = latest_price - prev_close
                change_pct = (change / prev_close * 100) if prev_close != 0 else 0

                # 格式化数据报告
                result = f"📊 {stock_name}({symbol}) - Tushare数据\n"
                result += f"数据期间: {start_date} 至 {end_date}\n"
                result += f"数据条数: {len(data)}条\n\n"

                result += f"💰 最新价格: ¥{latest_price:.2f}\n"
                result += f"📈 涨跌额: {change:+.2f} ({change_pct:+.2f}%)\n\n"

                # 添加统计信息
                result += f"📊 价格统计:\n"
                result += f"   最高价: ¥{data['high'].max():.2f}\n"
                result += f"   最低价: ¥{data['low'].min():.2f}\n"
                result += f"   平均价: ¥{data['close'].mean():.2f}\n"
                # 防御性获取成交量数据
                volume_value = self._get_volume_safely(data)
                result += f"   成交量: {volume_value:,.0f}股\n"

                return result
            else:
                result = f"❌ 未获取到{symbol}的有效数据"

            duration = time.time() - start_time
            logger.info(f"🔍 [DataSourceManager详细日志] interface调用完成，耗时: {duration:.3f}秒")
            logger.info(f"🔍 [股票代码追踪] get_china_stock_data_tushare 返回结果前200字符: {result[:200] if result else 'None'}")
            logger.info(f"🔍 [DataSourceManager详细日志] 返回结果类型: {type(result)}")
            logger.info(f"🔍 [DataSourceManager详细日志] 返回结果长度: {len(result) if result else 0}")

            logger.debug(f"📊 [Tushare] 调用完成: 耗时={duration:.2f}s, 结果长度={len(result) if result else 0}")

            return result
        except ImportError as e:
            duration = time.time() - start_time
            logger.error(f"❌ [Tushare] 模块导入失败: {e}, 耗时={duration:.2f}s")
            return f"❌ Tushare模块未安装: {e}"
        except ConnectionError as e:
            duration = time.time() - start_time
            logger.error(f"❌ [Tushare] 网络连接失败: {e}, 耗时={duration:.2f}s", exc_info=True)
            return f"❌ Tushare网络连接失败: {e}"
        except KeyError as e:
            duration = time.time() - start_time
            logger.error(f"❌ [Tushare] 数据字段缺失: {e}, 耗时={duration:.2f}s")
            return f"❌ Tushare数据格式异常: {e}"
            logger.error(f"❌ [DataSourceManager详细日志] 异常信息: {str(e)}")
            import traceback
            logger.error(f"❌ [DataSourceManager详细日志] 异常堆栈: {traceback.format_exc()}")
            raise
    
    def _get_akshare_data(self, symbol: str, start_date: str, end_date: str) -> str:
        """使用AKShare获取数据"""
        logger.debug(f"📊 [AKShare] 调用参数: symbol={symbol}, start_date={start_date}, end_date={end_date}")

        start_time = time.time()
        try:
            # 这里需要实现AKShare的统一接口
            from .akshare_utils import get_akshare_provider
            provider = get_akshare_provider()
            data = provider.get_stock_data(symbol, start_date, end_date)

            duration = time.time() - start_time

            if data is not None and not data.empty:
                result = f"股票代码: {symbol}\n"
                result += f"数据期间: {start_date} 至 {end_date}\n"
                result += f"数据条数: {len(data)}条\n\n"

                # 显示最新3天数据，确保在各种显示环境下都能完整显示
                display_rows = min(3, len(data))
                result += f"最新{display_rows}天数据:\n"

                # 使用pandas选项确保显示完整数据
                with pd.option_context('display.max_rows', None,
                                     'display.max_columns', None,
                                     'display.width', None,
                                     'display.max_colwidth', None):
                    result += data.tail(display_rows).to_string(index=False)

                # 如果数据超过3天，也显示一些统计信息
                if len(data) > 3:
                    latest_price = data.iloc[-1]['收盘'] if '收盘' in data.columns else data.iloc[-1].get('close', 'N/A')
                    first_price = data.iloc[0]['收盘'] if '收盘' in data.columns else data.iloc[0].get('close', 'N/A')
                    if latest_price != 'N/A' and first_price != 'N/A':
                        try:
                            change = float(latest_price) - float(first_price)
                            change_pct = (change / float(first_price)) * 100
                            result += f"\n\n📊 期间统计:\n"
                            result += f"期间涨跌: {change:+.2f} ({change_pct:+.2f}%)\n"
                            result += f"最高价: {data['最高'].max() if '最高' in data.columns else data.get('high', pd.Series()).max():.2f}\n"
                            result += f"最低价: {data['最低'].min() if '最低' in data.columns else data.get('low', pd.Series()).min():.2f}"
                        except (ValueError, TypeError):
                            pass

                logger.debug(f"📊 [AKShare] 调用成功: 耗时={duration:.2f}s, 数据条数={len(data)}, 结果长度={len(result)}")
                return result
            else:
                result = f"❌ 未能获取{symbol}的股票数据"
                logger.warning(f"⚠️ [AKShare] 数据为空: 耗时={duration:.2f}s")
                return result

        except ImportError as e:
            duration = time.time() - start_time
            logger.error(f"❌ [AKShare] 模块导入失败: {e}, 耗时={duration:.2f}s")
            return f"❌ AKShare模块未安装: {e}"
        except ConnectionError as e:
            duration = time.time() - start_time
            logger.error(f"❌ [AKShare] 网络连接失败: {e}, 耗时={duration:.2f}s", exc_info=True)
            return f"❌ AKShare网络连接失败: {e}"
        except KeyError as e:
            duration = time.time() - start_time
            logger.error(f"❌ [AKShare] 数据字段缺失: {e}, 耗时={duration:.2f}s")
            return f"❌ AKShare数据格式异常: {e}"
    
    def _get_baostock_data(self, symbol: str, start_date: str, end_date: str) -> str:
        """使用BaoStock获取数据"""
        # 这里需要实现BaoStock的统一接口
        from .baostock_utils import get_baostock_provider
        provider = get_baostock_provider()
        data = provider.get_stock_data(symbol, start_date, end_date)
        
        if data is not None and not data.empty:
            result = f"股票代码: {symbol}\n"
            result += f"数据期间: {start_date} 至 {end_date}\n"
            result += f"数据条数: {len(data)}条\n\n"

            # 显示最新3天数据，确保在各种显示环境下都能完整显示
            display_rows = min(3, len(data))
            result += f"最新{display_rows}天数据:\n"

            # 使用pandas选项确保显示完整数据
            with pd.option_context('display.max_rows', None,
                                 'display.max_columns', None,
                                 'display.width', None,
                                 'display.max_colwidth', None):
                result += data.tail(display_rows).to_string(index=False)
            return result
        else:
            return f"❌ 未能获取{symbol}的股票数据"
    
    def _get_tdx_data(self, symbol: str, start_date: str, end_date: str) -> str:
        """使用TDX获取数据 (已弃用)"""
        logger.warning(f"⚠️ 警告: 正在使用已弃用的TDX数据源，建议切换至Tushare以获得更好的稳定性和性能")
        from .tdx_utils import get_china_stock_data
        return get_china_stock_data(symbol, start_date, end_date)
    
    def _get_volume_safely(self, data) -> float:
        """安全地获取成交量数据，支持多种列名"""
        try:
            # 支持多种可能的成交量列名
            volume_columns = ['volume', 'vol', 'turnover', 'trade_volume']

            for col in volume_columns:
                if col in data.columns:
                    logger.info(f"✅ 找到成交量列: {col}")
                    return data[col].sum()

            # 如果都没找到，记录警告并返回0
            logger.warning(f"⚠️ 未找到成交量列，可用列: {list(data.columns)}")
            return 0

        except Exception as e:
            logger.error(f"❌ 获取成交量失败: {e}")
            return 0

    def _try_fallback_sources(self, symbol: str, start_date: str, end_date: str) -> str:
        """尝试备用数据源 - 避免递归调用"""
        logger.error(f"🔄 {self.current_source.value}失败，尝试备用数据源...")

        # 备用数据源优先级: AKShare > Tushare > BaoStock > TDX
        fallback_order = [
            ChinaDataSource.AKSHARE,
            ChinaDataSource.TUSHARE,
            ChinaDataSource.BAOSTOCK,
            ChinaDataSource.TDX
        ]

        for source in fallback_order:
            if source != self.current_source and source in self.available_sources:
                try:
                    logger.info(f"🔄 尝试备用数据源: {source.value}")

                    # 直接调用具体的数据源方法，避免递归
                    if source == ChinaDataSource.TUSHARE:
                        result = self._get_tushare_data(symbol, start_date, end_date)
                    elif source == ChinaDataSource.AKSHARE:
                        result = self._get_akshare_data(symbol, start_date, end_date)
                    elif source == ChinaDataSource.BAOSTOCK:
                        result = self._get_baostock_data(symbol, start_date, end_date)
                    elif source == ChinaDataSource.TDX:
                        result = self._get_tdx_data(symbol, start_date, end_date)
                    else:
                        logger.warning(f"⚠️ 未知数据源: {source.value}")
                        continue

                    if "❌" not in result:
                        logger.info(f"✅ 备用数据源{source.value}获取成功")
                        return result
                    else:
                        logger.warning(f"⚠️ 备用数据源{source.value}返回错误结果")

                except Exception as e:
                    logger.error(f"❌ 备用数据源{source.value}也失败: {e}")
                    continue
        
        return f"❌ 所有数据源都无法获取{symbol}的数据"
    
    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票基本信息，支持降级机制"""
        logger.info(f"📊 [股票信息] 开始获取{symbol}基本信息...")

        # 首先尝试当前数据源
        try:
            if self.current_source == ChinaDataSource.TUSHARE:
                from .interface import get_china_stock_info_tushare
                info_str = get_china_stock_info_tushare(symbol)
                result = self._parse_stock_info_string(info_str, symbol)

                # 检查是否获取到有效信息
                if result.get('name') and result['name'] != f'股票{symbol}':
                    logger.info(f"✅ [股票信息] Tushare成功获取{symbol}信息")
                    return result
                else:
                    logger.warning(f"⚠️ [股票信息] Tushare返回无效信息，尝试降级...")
                    return self._try_fallback_stock_info(symbol)
            else:
                adapter = self.get_data_adapter()
                if adapter and hasattr(adapter, 'get_stock_info'):
                    result = adapter.get_stock_info(symbol)
                    if result.get('name') and result['name'] != f'股票{symbol}':
                        logger.info(f"✅ [股票信息] {self.current_source.value}成功获取{symbol}信息")
                        return result
                    else:
                        logger.warning(f"⚠️ [股票信息] {self.current_source.value}返回无效信息，尝试降级...")
                        return self._try_fallback_stock_info(symbol)
                else:
                    logger.warning(f"⚠️ [股票信息] {self.current_source.value}不支持股票信息获取，尝试降级...")
                    return self._try_fallback_stock_info(symbol)

        except Exception as e:
            logger.error(f"❌ [股票信息] {self.current_source.value}获取失败: {e}")
            return self._try_fallback_stock_info(symbol)

    def _try_fallback_stock_info(self, symbol: str) -> Dict:
        """尝试使用备用数据源获取股票基本信息"""
        logger.info(f"🔄 [股票信息] {self.current_source.value}失败，尝试备用数据源...")

        # 获取所有可用数据源
        available_sources = self.available_sources.copy()

        # 移除当前数据源
        if self.current_source.value in available_sources:
            available_sources.remove(self.current_source.value)

        # 尝试所有备用数据源
        for source_name in available_sources:
            try:
                source = ChinaDataSource(source_name)
                logger.info(f"🔄 [股票信息] 尝试备用数据源: {source_name}")

                # 根据数据源类型获取股票信息
                if source == ChinaDataSource.TUSHARE:
                    from .interface import get_china_stock_info_tushare
                    info_str = get_china_stock_info_tushare(symbol)
                    result = self._parse_stock_info_string(info_str, symbol)
                elif source == ChinaDataSource.AKSHARE:
                    result = self._get_akshare_stock_info(symbol)
                elif source == ChinaDataSource.BAOSTOCK:
                    result = self._get_baostock_stock_info(symbol)
                else:
                    # 尝试通用适配器
                    original_source = self.current_source
                    self.current_source = source
                    adapter = self.get_data_adapter()
                    self.current_source = original_source

                    if adapter and hasattr(adapter, 'get_stock_info'):
                        result = adapter.get_stock_info(symbol)
                    else:
                        logger.warning(f"⚠️ [股票信息] {source_name}不支持股票信息获取")
                        continue

                # 检查是否获取到有效信息
                if result.get('name') and result['name'] != f'股票{symbol}':
                    logger.info(f"✅ [股票信息] 备用数据源{source_name}成功获取{symbol}信息")
                    return result
                else:
                    logger.warning(f"⚠️ [股票信息] 备用数据源{source_name}返回无效信息")

            except Exception as e:
                logger.error(f"❌ [股票信息] 备用数据源{source_name}失败: {e}")
                continue

        # 所有数据源都失败，返回默认值
        logger.error(f"❌ [股票信息] 所有数据源都无法获取{symbol}的基本信息")
        return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'unknown'}

    def _get_akshare_stock_info(self, symbol: str) -> Dict:
        """使用AKShare获取股票基本信息"""
        try:
            import akshare as ak

            # 尝试获取个股信息
            stock_info = ak.stock_individual_info_em(symbol=symbol)

            if stock_info is not None and not stock_info.empty:
                # 转换为字典格式
                info = {'symbol': symbol, 'source': 'akshare'}

                # 提取股票名称
                name_row = stock_info[stock_info['item'] == '股票简称']
                if not name_row.empty:
                    info['name'] = name_row['value'].iloc[0]
                else:
                    info['name'] = f'股票{symbol}'

                # 提取其他信息
                info['area'] = '未知'  # AKShare没有地区信息
                info['industry'] = '未知'  # 可以通过其他API获取
                info['market'] = '未知'  # 可以根据股票代码推断
                info['list_date'] = '未知'  # 可以通过其他API获取

                return info
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare'}

        except Exception as e:
            logger.error(f"❌ [股票信息] AKShare获取失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare', 'error': str(e)}

    def _get_baostock_stock_info(self, symbol: str) -> Dict:
        """使用BaoStock获取股票基本信息"""
        try:
            import baostock as bs

            # 转换股票代码格式
            if symbol.startswith('6'):
                bs_code = f"sh.{symbol}"
            else:
                bs_code = f"sz.{symbol}"

            # 登录BaoStock
            lg = bs.login()
            if lg.error_code != '0':
                logger.error(f"❌ [股票信息] BaoStock登录失败: {lg.error_msg}")
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'baostock'}

            # 查询股票基本信息
            rs = bs.query_stock_basic(code=bs_code)
            if rs.error_code != '0':
                bs.logout()
                logger.error(f"❌ [股票信息] BaoStock查询失败: {rs.error_msg}")
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'baostock'}

            # 解析结果
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            # 登出
            bs.logout()

            if data_list:
                # BaoStock返回格式: [code, code_name, ipoDate, outDate, type, status]
                info = {'symbol': symbol, 'source': 'baostock'}
                info['name'] = data_list[0][1]  # code_name
                info['area'] = '未知'  # BaoStock没有地区信息
                info['industry'] = '未知'  # BaoStock没有行业信息
                info['market'] = '未知'  # 可以根据股票代码推断
                info['list_date'] = data_list[0][2]  # ipoDate

                return info
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'baostock'}

        except Exception as e:
            logger.error(f"❌ [股票信息] BaoStock获取失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'baostock', 'error': str(e)}

    def _parse_stock_info_string(self, info_str: str, symbol: str) -> Dict:
        """解析股票信息字符串为字典"""
        try:
            info = {'symbol': symbol, 'source': self.current_source.value}
            lines = info_str.split('\n')
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if '股票名称' in key:
                        info['name'] = value
                    elif '所属行业' in key:
                        info['industry'] = value
                    elif '所属地区' in key:
                        info['area'] = value
                    elif '上市市场' in key:
                        info['market'] = value
                    elif '上市日期' in key:
                        info['list_date'] = value
            
            return info
            
        except Exception as e:
            logger.error(f"⚠️ 解析股票信息失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': self.current_source.value}

    # ==================== 资金流向数据接口 ====================

    def get_capital_flow_realtime(self, symbol: str, use_cache: bool = True) -> str:
        """
        获取个股实时资金流向数据，支持多数据源降级

        Args:
            symbol: 股票代码，如 '002115'
            use_cache: 是否使用缓存

        Returns:
            str: 格式化的资金流向数据报告
        """
        logger.info(f"💰 [资金流向] 获取{symbol}实时资金流向数据...")

        try:
            # 导入资金流向提供器
            from .market_data_capital_flow_utils import get_capital_flow_provider

            provider = get_capital_flow_provider()
            df = provider.get_capital_flow_realtime(symbol, use_cache=use_cache)

            if df is not None and not df.empty:
                # 格式化输出
                result = f"💰 {symbol} - 实时资金流向数据\n"
                result += f"数据时间: {df.iloc[-1]['trade_time'] if 'trade_time' in df.columns else '最新'}\n"
                result += f"数据条数: {len(df)}条\n\n"

                # 显示最新资金流向
                if not df.empty:
                    latest = df.iloc[-1]
                    result += "📊 最新资金流向:\n"
                    if 'main_net_inflow' in latest:
                        result += f"   主力净流入: {latest['main_net_inflow']:+,.2f}万元\n"
                    if 'large_net_inflow' in latest:
                        result += f"   大单净流入: {latest['large_net_inflow']:+,.2f}万元\n"
                    if 'medium_net_inflow' in latest:
                        result += f"   中单净流入: {latest['medium_net_inflow']:+,.2f}万元\n"
                    if 'small_net_inflow' in latest:
                        result += f"   小单净流入: {latest['small_net_inflow']:+,.2f}万元\n"
                    if 'super_large_net_inflow' in latest:
                        result += f"   超大单净流入: {latest['super_large_net_inflow']:+,.2f}万元\n"

                # 计算总净流入
                if len(df) > 0:
                    total_main = df['main_net_inflow'].sum() if 'main_net_inflow' in df.columns else 0
                    result += f"\n💡 今日主力净流入总计: {total_main:+,.2f}万元\n"

                logger.info(f"✅ [资金流向] 成功获取{symbol}实时资金流向，共{len(df)}条记录")
                return result
            else:
                result = f"❌ 未获取到{symbol}的实时资金流向数据"
                logger.warning(f"⚠️ [资金流向] {result}")
                return result

        except ImportError as e:
            error_msg = f"❌ 资金流向模块未安装或导入失败: {e}"
            logger.error(f"❌ [资金流向] 模块导入失败: {e}")
            return error_msg
        except Exception as e:
            error_msg = f"❌ 获取{symbol}实时资金流向数据失败: {e}"
            logger.error(f"❌ [资金流向] 获取失败: {e}", exc_info=True)
            return error_msg

    def get_capital_flow_daily(self, symbol: str, start_date: str = None, end_date: str = None,
                             use_cache: bool = True) -> str:
        """
        获取个股日度资金流向数据，支持多数据源降级

        Args:
            symbol: 股票代码，如 '002115'
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'
            use_cache: 是否使用缓存

        Returns:
            str: 格式化的资金流向数据报告
        """
        logger.info(f"💰 [资金流向] 获取{symbol}日度资金流向数据...")

        try:
            # 导入资金流向提供器
            from .market_data_capital_flow_utils import get_capital_flow_provider

            provider = get_capital_flow_provider()
            df = provider.get_capital_flow_daily(symbol, start_date=start_date,
                                               end_date=end_date, use_cache=use_cache)

            if df is not None and not df.empty:
                # 格式化输出
                result = f"💰 {symbol} - 日度资金流向数据\n"
                result += f"数据期间: {start_date or '最早'} 至 {end_date or '最新'}\n"
                result += f"数据条数: {len(df)}条\n\n"

                # 显示最近几日资金流向
                recent_days = min(5, len(df))
                result += f"📊 最近{recent_days}日资金流向:\n"
                for i in range(recent_days):
                    row = df.iloc[-(i+1)]  # 倒序显示最新的
                    result += f"   {row['trade_date']}: 主力净流入 {row.get('main_net_inflow', 0):+,.2f}万元\n"

                # 计算统计数据
                if len(df) > 0:
                    total_main = df['main_net_inflow'].sum() if 'main_net_inflow' in df.columns else 0
                    avg_main = df['main_net_inflow'].mean() if 'main_net_inflow' in df.columns else 0
                    max_inflow = df['main_net_inflow'].max() if 'main_net_inflow' in df.columns else 0
                    min_inflow = df['main_net_inflow'].min() if 'main_net_inflow' in df.columns else 0

                    result += f"\n📈 统计数据:\n"
                    result += f"   累计主力净流入: {total_main:+,.2f}万元\n"
                    result += f"   平均每日净流入: {avg_main:+,.2f}万元\n"
                    result += f"   最大单日流入: {max_inflow:+,.2f}万元\n"
                    result += f"   最大单日流出: {min_inflow:+,.2f}万元\n"

                logger.info(f"✅ [资金流向] 成功获取{symbol}日度资金流向，共{len(df)}条记录")
                return result
            else:
                result = f"❌ 未获取到{symbol}的日度资金流向数据"
                logger.warning(f"⚠️ [资金流向] {result}")
                return result

        except ImportError as e:
            error_msg = f"❌ 资金流向模块未安装或导入失败: {e}"
            logger.error(f"❌ [资金流向] 模块导入失败: {e}")
            return error_msg
        except Exception as e:
            error_msg = f"❌ 获取{symbol}日度资金流向数据失败: {e}"
            logger.error(f"❌ [资金流向] 获取失败: {e}", exc_info=True)
            return error_msg

    def get_concept_capital_flow(self, concept_code: str, use_cache: bool = True) -> str:
        """
        获取概念板块资金流向数据（待实现）

        Args:
            concept_code: 概念代码
            use_cache: 是否使用缓存

        Returns:
            str: 格式化的概念资金流向数据报告
        """
        logger.info(f"💰 [资金流向] 获取概念{concept_code}资金流向数据...")

        try:
            # 导入资金流向提供器
            from .market_data_capital_flow_utils import get_capital_flow_provider

            provider = get_capital_flow_provider()
            df = provider.get_concept_capital_flow(concept_code, use_cache=use_cache)

            if df is not None and not df.empty:
                # 格式化输出（待实现）
                result = f"💰 概念{concept_code} - 资金流向数据\n"
                result += f"数据条数: {len(df)}条\n"
                result += "⚠️ 概念资金流向功能正在开发中...\n"
                return result
            else:
                result = f"⚠️ 概念{concept_code}资金流向功能待实现"
                logger.warning(f"⚠️ [资金流向] {result}")
                return result

        except Exception as e:
            error_msg = f"❌ 获取概念{concept_code}资金流向数据失败: {e}"
            logger.error(f"❌ [资金流向] 获取失败: {e}", exc_info=True)
            return error_msg

    def get_concept_list(self, use_cache: bool = True) -> str:
        """
        获取概念板块列表
        Args:
            use_cache: 是否使用缓存
        Returns:
            str: 格式化的概念板块列表报告
        """
        logger.info("📊 [概念板块] 获取概念板块列表...")
        try:
            from .market_data_concept_utils import get_concept_provider
            provider = get_concept_provider()
            df = provider.get_concept_list(use_cache=use_cache)

            if df is not None and not df.empty:
                # 格式化返回结果
                result = f"📊 概念板块数据汇总 (共{len(df)}个概念)\n"
                result += "=" * 60 + "\n"

                # 显示前10个概念板块的基本信息
                top_concepts = df.head(10)
                for _, row in top_concepts.iterrows():
                    concept_name = row.get('concept_name', '未知')
                    change_pct = row.get('change_pct', 0)
                    price = row.get('price', 0)
                    volume = row.get('volume', 0)
                    turnover = row.get('turnover', 0)

                    result += f"📈 {concept_name}\n"
                    result += f"   价格: {price:.2f}  涨跌幅: {change_pct:.2f}%\n"
                    result += f"   成交量: {volume}  成交额: {turnover:.2f}万\n"
                    result += "-" * 40 + "\n"

                result += f"\n💡 数据来源: 东方财富  更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                logger.info(f"✅ [概念板块] 成功获取{len(df)}个概念板块数据")
                return result
            else:
                error_msg = "❌ 未获取到概念板块数据"
                logger.warning(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ 获取概念板块列表失败: {e}"
            logger.error(f"❌ [概念板块] 获取失败: {e}", exc_info=True)
            return error_msg

    def get_concept_stocks(self, concept_code: str, use_cache: bool = True) -> str:
        """
        获取概念板块成分股
        Args:
            concept_code: 概念代码
            use_cache: 是否使用缓存
        Returns:
            str: 格式化的概念成分股报告
        """
        logger.info(f"📊 [概念成分股] 获取概念{concept_code}成分股...")
        try:
            from .market_data_concept_utils import get_concept_provider
            provider = get_concept_provider()
            df = provider.get_concept_stocks(concept_code, use_cache=use_cache)

            if df is not None and not df.empty:
                # 格式化返回结果
                result = f"📊 概念{concept_code}成分股数据 (共{len(df)}只股票)\n"
                result += "=" * 60 + "\n"

                # 按涨跌幅排序，显示前15只成分股
                sorted_stocks = df.sort_values('change_pct', ascending=False).head(15)
                for _, row in sorted_stocks.iterrows():
                    stock_code = row.get('stock_code', '')
                    stock_name = row.get('stock_name', '未知')
                    price = row.get('price', 0)
                    change_pct = row.get('change_pct', 0)
                    change_amount = row.get('change_amount', 0)
                    volume = row.get('volume', 0)
                    turnover = row.get('turnover', 0)

                    result += f"📈 {stock_name} ({stock_code})\n"
                    result += f"   价格: {price:.2f}  涨跌: {change_amount:+.2f} ({change_pct:+.2f}%)\n"
                    result += f"   成交量: {volume}  成交额: {turnover:.2f}万\n"
                    result += "-" * 40 + "\n"

                result += f"\n💡 数据来源: 东方财富  更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                logger.info(f"✅ [概念成分股] 成功获取概念{concept_code}的{len(df)}只成分股")
                return result
            else:
                error_msg = f"❌ 未获取到概念{concept_code}的成分股数据"
                logger.warning(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ 获取概念{concept_code}成分股失败: {e}"
            logger.error(f"❌ [概念成分股] 获取失败: {e}", exc_info=True)
            return error_msg

    def get_top_concepts(self, sort_by: str = "change_pct", ascending: bool = False, limit: int = 20) -> str:
        """
        获取概念板块排行榜
        Args:
            sort_by: 排序字段 (change_pct, volume, turnover, market_cap等)
            ascending: 是否升序排列
            limit: 返回数量限制
        Returns:
            str: 格式化的概念板块排行榜
        """
        logger.info(f"📊 [概念排行] 获取概念板块排行榜 (按{sort_by}排序)...")
        try:
            from .market_data_concept_utils import get_concept_provider
            provider = get_concept_provider()
            df = provider.get_top_concepts(sort_by=sort_by, ascending=ascending, limit=limit)

            if df is not None and not df.empty:
                # 格式化返回结果
                sort_name_map = {
                    'change_pct': '涨跌幅',
                    'volume': '成交量',
                    'turnover': '成交额',
                    'market_cap': '市值',
                    'amplitude': '振幅'
                }
                sort_display = sort_name_map.get(sort_by, sort_by)

                result = f"📊 概念板块排行榜 (按{sort_display}排序，前{len(df)}名)\n"
                result += "=" * 60 + "\n"

                for i, (_, row) in enumerate(df.iterrows(), 1):
                    concept_name = row.get('concept_name', '未知')
                    change_pct = row.get('change_pct', 0)
                    price = row.get('price', 0)
                    volume = row.get('volume', 0)
                    turnover = row.get('turnover', 0)
                    sort_value = row.get(sort_by, 0)

                    result += f"🏆 第{i}名: {concept_name}\n"
                    result += f"   {sort_display}: {sort_value:.2f}  价格: {price:.2f}  涨跌幅: {change_pct:+.2f}%\n"
                    result += f"   成交量: {volume}  成交额: {turnover:.2f}万\n"
                    result += "-" * 40 + "\n"

                result += f"\n💡 数据来源: 东方财富  更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                logger.info(f"✅ [概念排行] 成功获取{len(df)}个概念排行数据")
                return result
            else:
                error_msg = "❌ 未获取到概念板块排行数据"
                logger.warning(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ 获取概念板块排行失败: {e}"
            logger.error(f"❌ [概念排行] 获取失败: {e}", exc_info=True)
            return error_msg

    def get_dividend_history(self, symbol: str, start_year: int = None, end_year: int = None, use_cache: bool = True) -> str:
        """
        获取股票历史分红数据
        Args:
            symbol: 股票代码
            start_year: 开始年份
            end_year: 结束年份
            use_cache: 是否使用缓存
        Returns:
            str: 格式化的分红历史报告
        """
        logger.info(f"💰 [分红历史] 获取股票{symbol}分红历史数据...")
        try:
            from .market_data_dividend_utils import get_dividend_provider
            provider = get_dividend_provider()
            df = provider.get_dividend_history(symbol, start_year=start_year, end_year=end_year, use_cache=use_cache)

            if df is not None and not df.empty:
                # 格式化返回结果
                result = f"💰 股票{symbol}分红历史数据 (共{len(df)}条记录)\n"
                result += "=" * 60 + "\n"

                # 按公告日期排序，显示最近的分红记录
                sorted_dividends = df.sort_values('notice_date', ascending=False).head(10)
                for _, row in sorted_dividends.iterrows():
                    notice_date = row.get('notice_date', '未知')[:10] if row.get('notice_date') else '未知'
                    ex_dividend_date = row.get('ex_dividend_date', '未知')[:10] if row.get('ex_dividend_date') else '未知'
                    dividend_ratio = row.get('dividend_ratio', 0)
                    plan_explain = row.get('plan_explain', '未知')
                    year = row.get('year', '未知')
                    progress = row.get('progress', '未知')

                    result += f"📅 分红年度: {year}\n"
                    result += f"   派息方案: {plan_explain}\n"
                    result += f"   每股派息: {dividend_ratio:.4f}元\n"
                    result += f"   公告日期: {notice_date}\n"
                    result += f"   除息日期: {ex_dividend_date}\n"
                    result += f"   实施进度: {progress}\n"
                    result += "-" * 40 + "\n"

                result += f"\n💡 数据来源: 东方财富  更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                logger.info(f"✅ [分红历史] 成功获取{symbol}的{len(df)}条分红记录")
                return result
            else:
                error_msg = f"❌ 未获取到股票{symbol}的分红历史数据"
                logger.warning(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ 获取股票{symbol}分红历史失败: {e}"
            logger.error(f"❌ [分红历史] 获取失败: {e}", exc_info=True)
            return error_msg

    def get_dividend_summary(self, symbol: str, use_cache: bool = True) -> str:
        """
        获取股票分红汇总信息
        Args:
            symbol: 股票代码
            use_cache: 是否使用缓存
        Returns:
            str: 格式化的分红汇总报告
        """
        logger.info(f"💰 [分红汇总] 获取股票{symbol}分红汇总信息...")
        try:
            from .market_data_dividend_utils import get_dividend_provider
            provider = get_dividend_provider()
            summary = provider.get_dividend_summary(symbol, use_cache=use_cache)

            if summary:
                # 格式化返回结果
                result = f"💰 股票{symbol}分红汇总分析\n"
                result += "=" * 60 + "\n"

                # 基本统计信息
                result += "📊 分红统计概况\n"
                result += f"   总分红次数: {summary.get('total_dividend_count', 0)}次\n"
                result += f"   累计分红总额: {summary.get('total_dividend_amount', 0):.4f}元/股\n"
                result += f"   平均每次分红: {summary.get('avg_dividend_ratio', 0):.4f}元/股\n"
                result += f"   分红稳定性: {summary.get('dividend_stability', 0):.2f} (0-1分)\n"
                result += "-" * 40 + "\n"

                # 最近一次分红信息
                latest = summary.get('latest_dividend', {})
                if latest:
                    result += "📅 最近分红信息\n"
                    result += f"   公告日期: {latest.get('notice_date', '未知')[:10] if latest.get('notice_date') else '未知'}\n"
                    result += f"   除息日期: {latest.get('ex_dividend_date', '未知')[:10] if latest.get('ex_dividend_date') else '未知'}\n"
                    result += f"   派息金额: {latest.get('dividend_ratio', 0):.4f}元/股\n"
                    result += f"   分红方案: {latest.get('plan_explain', '未知')}\n"
                    result += f"   实施进度: {latest.get('progress', '未知')}\n"
                    result += "-" * 40 + "\n"

                # 年度分红分布
                yearly_dividends = summary.get('yearly_dividends', {})
                if yearly_dividends:
                    result += "📈 年度分红分布\n"
                    for year, amount in sorted(yearly_dividends.items(), reverse=True):
                        result += f"   {year}年: {amount:.4f}元/股\n"
                    result += "-" * 40 + "\n"

                result += f"\n💡 数据来源: 东方财富  更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                logger.info(f"✅ [分红汇总] 成功获取{symbol}分红汇总数据")
                return result
            else:
                error_msg = f"❌ 未获取到股票{symbol}的分红汇总数据"
                logger.warning(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ 获取股票{symbol}分红汇总失败: {e}"
            logger.error(f"❌ [分红汇总] 获取失败: {e}", exc_info=True)
            return error_msg

    def calculate_dividend_yield(self, symbol: str, current_price: float = None, use_cache: bool = True) -> str:
        """
        计算股票股息率
        Args:
            symbol: 股票代码
            current_price: 当前股价
            use_cache: 是否使用缓存
        Returns:
            str: 格式化的股息率报告
        """
        logger.info(f"💰 [股息率] 计算股票{symbol}股息率...")
        try:
            from .market_data_dividend_utils import get_dividend_provider
            provider = get_dividend_provider()
            result_data = provider.calculate_dividend_yield(symbol, current_price=current_price, use_cache=use_cache)

            if result_data and 'dividend_yield' in result_data:
                # 格式化返回结果
                result = f"💰 股票{symbol}股息率分析\n"
                result += "=" * 60 + "\n"

                dividend_yield = result_data.get('dividend_yield', 0)
                annual_dividend = result_data.get('annual_dividend', 0)
                price = result_data.get('current_price', current_price)
                calc_date = result_data.get('calculation_date', time.strftime('%Y-%m-%d'))

                # 股息率信息
                result += "📊 股息率计算结果\n"
                result += f"   股息率: {dividend_yield:.2f}%\n"
                result += f"   年度分红: {annual_dividend:.4f}元/股\n"
                if price:
                    result += f"   参考股价: {price:.2f}元\n"
                result += f"   计算日期: {calc_date}\n"
                result += "-" * 40 + "\n"

                # 股息率评估
                result += "📈 股息率评估\n"
                if dividend_yield >= 5.0:
                    result += "   评级: ⭐⭐⭐⭐⭐ 优秀 (股息率≥5%)\n"
                    result += "   说明: 股息率较高，适合追求稳定收益的投资者\n"
                elif dividend_yield >= 3.0:
                    result += "   评级: ⭐⭐⭐⭐ 良好 (股息率3-5%)\n"
                    result += "   说明: 股息率适中，有一定分红收益\n"
                elif dividend_yield >= 1.0:
                    result += "   评级: ⭐⭐⭐ 一般 (股息率1-3%)\n"
                    result += "   说明: 股息率偏低，分红收益有限\n"
                else:
                    result += "   评级: ⭐⭐ 较低 (股息率<1%)\n"
                    result += "   说明: 股息率很低或无分红，不适合追求分红收益的投资者\n"

                # 错误信息处理
                if 'error' in result_data:
                    result += f"\n⚠️ 注意事项: {result_data['error']}\n"

                result += f"\n💡 数据来源: 东方财富  更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                logger.info(f"✅ [股息率] 成功计算{symbol}股息率: {dividend_yield:.2f}%")
                return result
            else:
                error_msg = f"❌ 无法计算股票{symbol}的股息率"
                if result_data and 'error' in result_data:
                    error_msg += f": {result_data['error']}"
                logger.warning(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ 计算股票{symbol}股息率失败: {e}"
            logger.error(f"❌ [股息率] 计算失败: {e}", exc_info=True)
            return error_msg


# 全局数据源管理器实例
_data_source_manager = None

def get_data_source_manager() -> DataSourceManager:
    """获取全局数据源管理器实例"""
    global _data_source_manager
    if _data_source_manager is None:
        _data_source_manager = DataSourceManager()
    return _data_source_manager


def get_china_stock_data_unified(symbol: str, start_date: str, end_date: str) -> str:
    """
    统一的中国股票数据获取接口
    自动使用配置的数据源，支持备用数据源

    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        str: 格式化的股票数据
    """
    from tradingagents.utils.logging_init import get_logger


    # 添加详细的股票代码追踪日志
    logger.info(f"🔍 [股票代码追踪] data_source_manager.get_china_stock_data_unified 接收到的股票代码: '{symbol}' (类型: {type(symbol)})")
    logger.info(f"🔍 [股票代码追踪] 股票代码长度: {len(str(symbol))}")
    logger.info(f"🔍 [股票代码追踪] 股票代码字符: {list(str(symbol))}")

    manager = get_data_source_manager()
    logger.info(f"🔍 [股票代码追踪] 调用 manager.get_stock_data，传入参数: symbol='{symbol}', start_date='{start_date}', end_date='{end_date}'")
    result = manager.get_stock_data(symbol, start_date, end_date)
    # 分析返回结果的详细信息
    if result:
        lines = result.split('\n')
        data_lines = [line for line in lines if '2025-' in line and symbol in line]
        logger.info(f"🔍 [股票代码追踪] 返回结果统计: 总行数={len(lines)}, 数据行数={len(data_lines)}, 结果长度={len(result)}字符")
        logger.info(f"🔍 [股票代码追踪] 返回结果前500字符: {result[:500]}")
        if len(data_lines) > 0:
            logger.info(f"🔍 [股票代码追踪] 数据行示例: 第1行='{data_lines[0][:100]}', 最后1行='{data_lines[-1][:100]}'")
    else:
        logger.info(f"🔍 [股票代码追踪] 返回结果: None")
    return result


def get_china_stock_info_unified(symbol: str) -> Dict:
    """
    统一的中国股票信息获取接口
    
    Args:
        symbol: 股票代码
        
    Returns:
        Dict: 股票基本信息
    """
    manager = get_data_source_manager()
    return manager.get_stock_info(symbol)


# 全局数据源管理器实例
_data_source_manager = None

def get_data_source_manager() -> DataSourceManager:
    """获取全局数据源管理器实例"""
    global _data_source_manager
    if _data_source_manager is None:
        _data_source_manager = DataSourceManager()
    return _data_source_manager
