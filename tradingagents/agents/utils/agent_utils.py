from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from typing import List
from typing import Annotated
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import RemoveMessage
from langchain_core.tools import tool
from datetime import date, timedelta, datetime
import functools
import pandas as pd
import os
from dateutil.relativedelta import relativedelta
from langchain_openai import ChatOpenAI
import tradingagents.dataflows.interface as interface
from tradingagents.default_config import DEFAULT_CONFIG
from langchain_core.messages import HumanMessage

# 导入统一日志系统和工具日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_tool_call, log_analysis_step

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')


def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]
        
        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        
        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")
        
        return {"messages": removal_operations + [placeholder]}
    
    return delete_messages


class Toolkit:
    _config = DEFAULT_CONFIG.copy()

    @classmethod
    def update_config(cls, config):
        """Update the class-level configuration."""
        cls._config.update(config)

    @property
    def config(self):
        """Access the configuration."""
        return self._config

    def __init__(self, config=None):
        if config:
            self.update_config(config)

    @staticmethod
    @tool
    def get_reddit_news(
        curr_date: Annotated[str, "Date you want to get news for in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve global news from Reddit within a specified time frame.
        Args:
            curr_date (str): Date you want to get news for in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the latest global news from Reddit in the specified time frame.
        """
        
        global_news_result = interface.get_reddit_global_news(curr_date, 7, 5)

        return global_news_result

    @staticmethod
    @tool
    def get_finnhub_news(
        ticker: Annotated[
            str,
            "Search query of a company, e.g. 'AAPL, TSM, etc.",
        ],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news about a given stock from Finnhub within a date range
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing news about the company within the date range from start_date to end_date
        """

        end_date_str = end_date

        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        look_back_days = (end_date - start_date).days

        finnhub_news_result = interface.get_finnhub_news(
            ticker, end_date_str, look_back_days
        )

        return finnhub_news_result

    @staticmethod
    @tool
    def get_reddit_stock_info(
        ticker: Annotated[
            str,
            "Ticker of a company. e.g. AAPL, TSM",
        ],
        curr_date: Annotated[str, "Current date you want to get news for"],
    ) -> str:
        """
        Retrieve the latest news about a given stock from Reddit, given the current date.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): current date in yyyy-mm-dd format to get news for
        Returns:
            str: A formatted dataframe containing the latest news about the company on the given date
        """

        stock_news_results = interface.get_reddit_company_news(ticker, curr_date, 7, 5)

        return stock_news_results

    @staticmethod
    @tool
    def get_chinese_social_sentiment(
        ticker: Annotated[str, "Ticker of a company. e.g. AAPL, TSM"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ) -> str:
        """
        获取中国社交媒体和财经平台上关于特定股票的情绪分析和讨论热度。
        整合雪球、东方财富股吧、新浪财经等中国本土平台的数据。
        Args:
            ticker (str): 股票代码，如 AAPL, TSM
            curr_date (str): 当前日期，格式为 yyyy-mm-dd
        Returns:
            str: 包含中国投资者情绪分析、讨论热度、关键观点的格式化报告
        """
        try:
            # 这里可以集成多个中国平台的数据
            chinese_sentiment_results = interface.get_chinese_social_sentiment(ticker, curr_date)
            return chinese_sentiment_results
        except Exception as e:
            # 如果中国平台数据获取失败，回退到原有的Reddit数据
            return interface.get_reddit_company_news(ticker, curr_date, 7, 5)

    @staticmethod
    # @tool  # 已移除：请使用 get_stock_fundamentals_unified 或 get_stock_market_data_unified
    def get_china_stock_data(
        stock_code: Annotated[str, "中国股票代码，如 002115(平安银行), 600519(贵州茅台)"],
        start_date: Annotated[str, "开始日期，格式 yyyy-mm-dd"],
        end_date: Annotated[str, "结束日期，格式 yyyy-mm-dd"],
    ) -> str:
        """
        获取中国A股实时和历史数据，通过Tushare等高质量数据源提供专业的股票数据。
        支持实时行情、历史K线、技术指标等全面数据，自动使用最佳数据源。
        Args:
            stock_code (str): 中国股票代码，如 002115(平安银行), 600519(贵州茅台)
            start_date (str): 开始日期，格式 yyyy-mm-dd
            end_date (str): 结束日期，格式 yyyy-mm-dd
        Returns:
            str: 包含实时行情、历史数据、技术指标的完整股票分析报告
        """
        try:
            logger.debug(f"📊 [DEBUG] ===== agent_utils.get_china_stock_data 开始调用 =====")
            logger.debug(f"📊 [DEBUG] 参数: stock_code={stock_code}, start_date={start_date}, end_date={end_date}")

            from tradingagents.dataflows.interface import get_china_stock_data_unified
            logger.debug(f"📊 [DEBUG] 成功导入统一数据源接口")

            logger.debug(f"📊 [DEBUG] 正在调用统一数据源接口...")
            result = get_china_stock_data_unified(stock_code, start_date, end_date)

            logger.debug(f"📊 [DEBUG] 统一数据源接口调用完成")
            logger.debug(f"📊 [DEBUG] 返回结果类型: {type(result)}")
            logger.debug(f"📊 [DEBUG] 返回结果长度: {len(result) if result else 0}")
            logger.debug(f"📊 [DEBUG] 返回结果前200字符: {str(result)[:200]}...")
            logger.debug(f"📊 [DEBUG] ===== agent_utils.get_china_stock_data 调用结束 =====")

            return result
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"❌ [DEBUG] ===== agent_utils.get_china_stock_data 异常 =====")
            logger.error(f"❌ [DEBUG] 错误类型: {type(e).__name__}")
            logger.error(f"❌ [DEBUG] 错误信息: {str(e)}")
            logger.error(f"❌ [DEBUG] 详细堆栈:")
            print(error_details)
            logger.error(f"❌ [DEBUG] ===== 异常处理结束 =====")
            return f"中国股票数据获取失败: {str(e)}。建议安装pytdx库: pip install pytdx"

    @staticmethod
    @tool
    def get_china_market_overview(
        curr_date: Annotated[str, "当前日期，格式 yyyy-mm-dd"],
    ) -> str:
        """
        获取中国股市整体概览，包括主要指数的实时行情。
        涵盖上证指数、深证成指、创业板指、科创50等主要指数。
        Args:
            curr_date (str): 当前日期，格式 yyyy-mm-dd
        Returns:
            str: 包含主要指数实时行情的市场概览报告
        """
        try:
            # 使用Tushare获取主要指数数据
            from tradingagents.dataflows.tushare_adapter import get_tushare_adapter

            adapter = get_tushare_adapter()
            if not adapter.provider or not adapter.provider.connected:
                # 如果Tushare不可用，回退到TDX
                logger.warning(f"⚠️ Tushare不可用，回退到TDX获取市场概览")
                from tradingagents.dataflows.tdx_utils import get_china_market_overview
                return get_china_market_overview()

            # 使用Tushare获取主要指数信息
            # 这里可以扩展为获取具体的指数数据
            return f"""# 中国股市概览 - {curr_date}

## 📊 主要指数
- 上证指数: 数据获取中...
- 深证成指: 数据获取中...
- 创业板指: 数据获取中...
- 科创50: 数据获取中...

## 💡 说明
市场概览功能正在从TDX迁移到Tushare，完整功能即将推出。
当前可以使用股票数据获取功能分析个股。

数据来源: Tushare专业数据源
更新时间: {curr_date}
"""

        except Exception as e:
            return f"中国市场概览获取失败: {str(e)}。正在从TDX迁移到Tushare数据源。"

    @staticmethod
    @tool
    def get_YFin_data(
        symbol: Annotated[str, "ticker symbol of the company"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve the stock price data for a given ticker symbol from Yahoo Finance.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
        """

        result_data = interface.get_YFin_data(symbol, start_date, end_date)

        return result_data

    @staticmethod
    @tool
    def get_YFin_data_online(
        symbol: Annotated[str, "ticker symbol of the company"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve the stock price data for a given ticker symbol from Yahoo Finance.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
        """

        result_data = interface.get_YFin_data_online(symbol, start_date, end_date)

        return result_data

    @staticmethod
    @tool
    def get_stockstats_indicators_report(
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[
            str, "technical indicator to get the analysis and report of"
        ],
        curr_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """

        result_stockstats = interface.get_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days, False
        )

        return result_stockstats

    @staticmethod
    @tool
    def get_stockstats_indicators_report_online(
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[
            str, "technical indicator to get the analysis and report of"
        ],
        curr_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """

        result_stockstats = interface.get_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days, True
        )

        return result_stockstats

    @staticmethod
    @tool
    def get_finnhub_company_insider_sentiment(
        ticker: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[
            str,
            "current date of you are trading at, yyyy-mm-dd",
        ],
    ):
        """
        Retrieve insider sentiment information about a company (retrieved from public SEC information) for the past 30 days
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the sentiment in the past 30 days starting at curr_date
        """

        data_sentiment = interface.get_finnhub_company_insider_sentiment(
            ticker, curr_date, 30
        )

        return data_sentiment

    @staticmethod
    @tool
    def get_finnhub_company_insider_transactions(
        ticker: Annotated[str, "ticker symbol"],
        curr_date: Annotated[
            str,
            "current date you are trading at, yyyy-mm-dd",
        ],
    ):
        """
        Retrieve insider transaction information about a company (retrieved from public SEC information) for the past 30 days
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the company's insider transactions/trading information in the past 30 days
        """

        data_trans = interface.get_finnhub_company_insider_transactions(
            ticker, curr_date, 30
        )

        return data_trans

    @staticmethod
    @tool
    def get_simfin_balance_sheet(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent balance sheet of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the company's most recent balance sheet
        """

        data_balance_sheet = interface.get_simfin_balance_sheet(ticker, freq, curr_date)

        return data_balance_sheet

    @staticmethod
    @tool
    def get_simfin_cashflow(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent cash flow statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent cash flow statement
        """

        data_cashflow = interface.get_simfin_cashflow(ticker, freq, curr_date)

        return data_cashflow

    @staticmethod
    @tool
    def get_simfin_income_stmt(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent income statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent income statement
        """

        data_income_stmt = interface.get_simfin_income_statements(
            ticker, freq, curr_date
        )

        return data_income_stmt

    @staticmethod
    @tool
    def get_google_news(
        query: Annotated[str, "Query to search with"],
        curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news from Google News based on a query and date range.
        Args:
            query (str): Query to search with
            curr_date (str): Current date in yyyy-mm-dd format
            look_back_days (int): How many days to look back
        Returns:
            str: A formatted string containing the latest news from Google News based on the query and date range.
        """

        google_news_results = interface.get_google_news(query, curr_date, 7)

        return google_news_results

    @staticmethod
    @tool
    def get_realtime_stock_news(
        ticker: Annotated[str, "Ticker of a company. e.g. AAPL, TSM"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ) -> str:
        """
        获取股票的实时新闻分析，解决传统新闻源的滞后性问题。
        整合多个专业财经API，提供15-30分钟内的最新新闻。
        支持多种新闻源轮询机制，优先使用实时新闻聚合器，失败时自动尝试备用新闻源。
        对于A股和港股，会优先使用中文财经新闻源（如东方财富）。
        
        Args:
            ticker (str): 股票代码，如 AAPL, TSM, 600036.SH
            curr_date (str): 当前日期，格式为 yyyy-mm-dd
        Returns:
            str: 包含实时新闻分析、紧急程度评估、时效性说明的格式化报告
        """
        from tradingagents.dataflows.realtime_news_utils import get_realtime_stock_news
        return get_realtime_stock_news(ticker, curr_date, hours_back=6)

    @staticmethod
    @tool
    def get_stock_news_openai(
        ticker: Annotated[str, "the company's ticker"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news about a given stock by using OpenAI's news API.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest news about the company on the given date.
        """

        openai_news_results = interface.get_stock_news_openai(ticker, curr_date)

        return openai_news_results

    @staticmethod
    @tool
    def get_global_news_openai(
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest macroeconomics news on a given date using OpenAI's macroeconomics news API.
        Args:
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest macroeconomic news on the given date.
        """

        openai_news_results = interface.get_global_news_openai(curr_date)

        return openai_news_results

    @staticmethod
    # @tool  # 已移除：请使用 get_stock_fundamentals_unified
    def get_fundamentals_openai(
        ticker: Annotated[str, "the company's ticker"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest fundamental information about a given stock on a given date by using OpenAI's news API.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest fundamental information about the company on the given date.
        """
        logger.debug(f"📊 [DEBUG] get_fundamentals_openai 被调用: ticker={ticker}, date={curr_date}")

        # 检查是否为中国股票
        import re
        if re.match(r'^\d{6}$', str(ticker)):
            logger.debug(f"📊 [DEBUG] 检测到中国A股代码: {ticker}")
            # 使用统一接口获取中国股票名称
            try:
                from tradingagents.dataflows.interface import get_china_stock_info_unified
                stock_info = get_china_stock_info_unified(ticker)

                # 解析股票名称
                if "股票名称:" in stock_info:
                    company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                else:
                    company_name = f"股票代码{ticker}"

                logger.debug(f"📊 [DEBUG] 中国股票名称映射: {ticker} -> {company_name}")
            except Exception as e:
                logger.error(f"⚠️ [DEBUG] 从统一接口获取股票名称失败: {e}")
                company_name = f"股票代码{ticker}"

            # 修改查询以包含正确的公司名称
            modified_query = f"{company_name}({ticker})"
            logger.debug(f"📊 [DEBUG] 修改后的查询: {modified_query}")
        else:
            logger.debug(f"📊 [DEBUG] 检测到非中国股票: {ticker}")
            modified_query = ticker

        try:
            openai_fundamentals_results = interface.get_fundamentals_openai(
                modified_query, curr_date
            )
            logger.debug(f"📊 [DEBUG] OpenAI基本面分析结果长度: {len(openai_fundamentals_results) if openai_fundamentals_results else 0}")
            return openai_fundamentals_results
        except Exception as e:
            logger.error(f"❌ [DEBUG] OpenAI基本面分析失败: {str(e)}")
            return f"基本面分析失败: {str(e)}"

    @staticmethod
    # @tool  # 已移除：请使用 get_stock_fundamentals_unified
    def get_china_fundamentals(
        ticker: Annotated[str, "中国A股股票代码，如600036"],
        curr_date: Annotated[str, "当前日期，格式为yyyy-mm-dd"],
    ):
        """
        获取中国A股股票的基本面信息，使用中国股票数据源。
        Args:
            ticker (str): 中国A股股票代码，如600036, 002115
            curr_date (str): 当前日期，格式为yyyy-mm-dd
        Returns:
            str: 包含股票基本面信息的格式化字符串
        """
        logger.debug(f"📊 [DEBUG] get_china_fundamentals 被调用: ticker={ticker}, date={curr_date}")

        # 检查是否为中国股票
        import re
        if not re.match(r'^\d{6}$', str(ticker)):
            return f"错误：{ticker} 不是有效的中国A股代码格式"

        try:
            # 使用统一数据源接口获取股票数据（默认Tushare，支持备用数据源）
            from tradingagents.dataflows.interface import get_china_stock_data_unified
            logger.debug(f"📊 [DEBUG] 正在获取 {ticker} 的股票数据...")

            # 获取最近30天的数据用于基本面分析
            from datetime import datetime, timedelta
            end_date = datetime.strptime(curr_date, '%Y-%m-%d')
            start_date = end_date - timedelta(days=30)

            stock_data = get_china_stock_data_unified(
                ticker,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )

            logger.debug(f"📊 [DEBUG] 股票数据获取完成，长度: {len(stock_data) if stock_data else 0}")

            if not stock_data or "获取失败" in stock_data or "❌" in stock_data:
                return f"无法获取股票 {ticker} 的基本面数据：{stock_data}"

            # 调用真正的基本面分析
            from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider

            # 创建分析器实例
            analyzer = OptimizedChinaDataProvider()

            # 生成真正的基本面分析报告
            fundamentals_report = analyzer._generate_fundamentals_report(ticker, stock_data)

            logger.debug(f"📊 [DEBUG] 中国基本面分析报告生成完成")
            logger.debug(f"📊 [DEBUG] get_china_fundamentals 结果长度: {len(fundamentals_report)}")

            return fundamentals_report

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"❌ [DEBUG] get_china_fundamentals 失败:")
            logger.error(f"❌ [DEBUG] 错误: {str(e)}")
            logger.error(f"❌ [DEBUG] 堆栈: {error_details}")
            return f"中国股票基本面分析失败: {str(e)}"

    @staticmethod
    # @tool  # 已移除：请使用 get_stock_fundamentals_unified 或 get_stock_market_data_unified
    def get_hk_stock_data_unified(
        symbol: Annotated[str, "港股代码，如：0700.HK、9988.HK等"],
        start_date: Annotated[str, "开始日期，格式：YYYY-MM-DD"],
        end_date: Annotated[str, "结束日期，格式：YYYY-MM-DD"]
    ) -> str:
        """
        获取港股数据的统一接口，优先使用AKShare数据源，备用Yahoo Finance

        Args:
            symbol: 港股代码 (如: 0700.HK)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            str: 格式化的港股数据
        """
        logger.debug(f"🇭🇰 [DEBUG] get_hk_stock_data_unified 被调用: symbol={symbol}, start_date={start_date}, end_date={end_date}")

        try:
            from tradingagents.dataflows.interface import get_hk_stock_data_unified

            result = get_hk_stock_data_unified(symbol, start_date, end_date)

            logger.debug(f"🇭🇰 [DEBUG] 港股数据获取完成，长度: {len(result) if result else 0}")

            return result

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"❌ [DEBUG] get_hk_stock_data_unified 失败:")
            logger.error(f"❌ [DEBUG] 错误: {str(e)}")
            logger.error(f"❌ [DEBUG] 堆栈: {error_details}")
            return f"港股数据获取失败: {str(e)}"

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_stock_fundamentals_unified", log_args=True)
    def get_stock_fundamentals_unified(
        ticker: Annotated[str, "股票代码（支持A股、港股、美股）"],
        start_date: Annotated[str, "开始日期，格式：YYYY-MM-DD"] = None,
        end_date: Annotated[str, "结束日期，格式：YYYY-MM-DD"] = None,
        curr_date: Annotated[str, "当前日期，格式：YYYY-MM-DD"] = None
    ) -> str:
        """
        统一的股票基本面分析工具
        自动识别股票类型（A股、港股、美股）并调用相应的数据源

        Args:
            ticker: 股票代码（如：002115、0700.HK、AAPL）
            start_date: 开始日期（可选，格式：YYYY-MM-DD）
            end_date: 结束日期（可选，格式：YYYY-MM-DD）
            curr_date: 当前日期（可选，格式：YYYY-MM-DD）

        Returns:
            str: 基本面分析数据和报告
        """
        logger.info(f"📊 [统一基本面工具] 分析股票: {ticker}")

        # 添加详细的股票代码追踪日志
        logger.info(f"🔍 [股票代码追踪] 统一基本面工具接收到的原始股票代码: '{ticker}' (类型: {type(ticker)})")
        logger.info(f"🔍 [股票代码追踪] 股票代码长度: {len(str(ticker))}")
        logger.info(f"🔍 [股票代码追踪] 股票代码字符: {list(str(ticker))}")

        # 保存原始ticker用于对比
        original_ticker = ticker

        try:
            from tradingagents.utils.stock_utils import StockUtils
            from datetime import datetime, timedelta

            # 自动识别股票类型
            market_info = StockUtils.get_market_info(ticker)
            is_china = market_info['is_china']
            is_hk = market_info['is_hk']
            is_us = market_info['is_us']

            logger.info(f"🔍 [股票代码追踪] StockUtils.get_market_info 返回的市场信息: {market_info}")
            logger.info(f"📊 [统一基本面工具] 股票类型: {market_info['market_name']}")
            logger.info(f"📊 [统一基本面工具] 货币: {market_info['currency_name']} ({market_info['currency_symbol']})")

            # 检查ticker是否在处理过程中发生了变化
            if str(ticker) != str(original_ticker):
                logger.warning(f"🔍 [股票代码追踪] 警告：股票代码发生了变化！原始: '{original_ticker}' -> 当前: '{ticker}'")

            # 设置默认日期
            if not curr_date:
                curr_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = curr_date

            result_data = []

            if is_china:
                # 中国A股：获取股票数据 + 增强的东方财富基本面数据
                logger.info(f"🇨🇳 [统一基本面工具] 处理A股数据...")
                logger.info(f"🔍 [股票代码追踪] 进入A股处理分支，ticker: '{ticker}'")

                try:
                    # 获取股票价格数据
                    from tradingagents.dataflows.interface import get_china_stock_data_unified
                    logger.info(f"🔍 [股票代码追踪] 调用 get_china_stock_data_unified，传入参数: ticker='{ticker}', start_date='{start_date}', end_date='{end_date}'")
                    stock_data = get_china_stock_data_unified(ticker, start_date, end_date)
                    logger.info(f"🔍 [股票代码追踪] get_china_stock_data_unified 返回结果前200字符: {stock_data[:200] if stock_data else 'None'}")
                    result_data.append(f"## A股价格数据\n{stock_data}")
                except Exception as e:
                    logger.error(f"🔍 [股票代码追踪] get_china_stock_data_unified 调用失败: {e}")
                    result_data.append(f"## A股价格数据\n获取失败: {e}")

                # 优先使用东方财富增强数据
                try:
                    from tradingagents.dataflows.eastmoney_core import generate_stock_analysis_report
                    logger.info(f"🔍 [股票代码追踪] 调用东方财富核心数据，ticker: '{ticker}'")

                    # 提取纯股票代码（去除交易所后缀）
                    clean_ticker = ticker.replace('.SZ', '').replace('.SH', '').replace('.SS', '').replace('.XSHE', '').replace('.XSHG', '')

                    eastmoney_data = generate_stock_analysis_report(clean_ticker)
                    logger.info(f"🔍 [股票代码追踪] 东方财富数据获取成功，长度: {len(eastmoney_data)}")
                    result_data.append(f"## A股东方财富核心指标\n{eastmoney_data}")

                except Exception as e:
                    logger.warning(f"🔍 [股票代码追踪] 东方财富数据获取失败，使用备用方案: {e}")

                    # 备用方案：使用原有基本面数据
                    try:
                        from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
                        analyzer = OptimizedChinaDataProvider()
                        logger.info(f"🔍 [股票代码追踪] 调用 OptimizedChinaDataProvider._generate_fundamentals_report，传入参数: ticker='{ticker}'")
                        fundamentals_data = analyzer._generate_fundamentals_report(ticker, stock_data if 'stock_data' in locals() else "")
                        logger.info(f"🔍 [股票代码追踪] _generate_fundamentals_report 返回结果前200字符: {fundamentals_data[:200] if fundamentals_data else 'None'}")
                        result_data.append(f"## A股基本面数据（备用）\n{fundamentals_data}")
                    except Exception as e2:
                        logger.error(f"🔍 [股票代码追踪] 备用基本面数据获取也失败: {e2}")
                        result_data.append(f"## A股基本面数据\n获取失败: {e2}")

            elif is_hk:
                # 港股：使用AKShare数据源，支持多重备用方案
                logger.info(f"🇭🇰 [统一基本面工具] 处理港股数据...")

                hk_data_success = False

                # 主要数据源：AKShare
                try:
                    from tradingagents.dataflows.interface import get_hk_stock_data_unified
                    hk_data = get_hk_stock_data_unified(ticker, start_date, end_date)

                    # 检查数据质量
                    if hk_data and len(hk_data) > 100 and "❌" not in hk_data:
                        result_data.append(f"## 港股数据\n{hk_data}")
                        hk_data_success = True
                        logger.info(f"✅ [统一基本面工具] 港股主要数据源成功")
                    else:
                        logger.warning(f"⚠️ [统一基本面工具] 港股主要数据源质量不佳")

                except Exception as e:
                    logger.error(f"⚠️ [统一基本面工具] 港股主要数据源失败: {e}")

                # 备用方案：基础港股信息
                if not hk_data_success:
                    try:
                        from tradingagents.dataflows.interface import get_hk_stock_info_unified
                        hk_info = get_hk_stock_info_unified(ticker)

                        basic_info = f"""## 港股基础信息

**股票代码**: {ticker}
**股票名称**: {hk_info.get('name', f'港股{ticker}')}
**交易货币**: 港币 (HK$)
**交易所**: 香港交易所 (HKG)
**数据源**: {hk_info.get('source', '基础信息')}

⚠️ 注意：详细的价格和财务数据暂时无法获取，建议稍后重试或使用其他数据源。

**基本面分析建议**：
- 建议查看公司最新财报
- 关注港股市场整体走势
- 考虑汇率因素对投资的影响
"""
                        result_data.append(basic_info)
                        logger.info(f"✅ [统一基本面工具] 港股备用信息成功")

                    except Exception as e2:
                        # 最终备用方案
                        fallback_info = f"""## 港股信息（备用）

**股票代码**: {ticker}
**股票类型**: 港股
**交易货币**: 港币 (HK$)
**交易所**: 香港交易所 (HKG)

❌ 数据获取遇到问题: {str(e2)}

**建议**：
1. 检查网络连接
2. 稍后重试分析
3. 使用其他港股数据源
4. 查看公司官方财报
"""
                        result_data.append(fallback_info)
                        logger.warning(f"⚠️ [统一基本面工具] 港股使用最终备用方案")

            else:
                # 美股：使用OpenAI/Finnhub数据源
                logger.info(f"🇺🇸 [统一基本面工具] 处理美股数据...")

                try:
                    from tradingagents.dataflows.interface import get_fundamentals_openai
                    us_data = get_fundamentals_openai(ticker, curr_date)
                    result_data.append(f"## 美股基本面数据\n{us_data}")
                except Exception as e:
                    result_data.append(f"## 美股基本面数据\n获取失败: {e}")

            # 组合所有数据
            combined_result = f"""# {ticker} 基本面分析数据

**股票类型**: {market_info['market_name']}
**货币**: {market_info['currency_name']} ({market_info['currency_symbol']})
**分析日期**: {curr_date}

{chr(10).join(result_data)}

---
*数据来源: 根据股票类型自动选择最适合的数据源*
"""

            logger.info(f"📊 [统一基本面工具] 数据获取完成，总长度: {len(combined_result)}")
            return combined_result

        except Exception as e:
            error_msg = f"统一基本面分析工具执行失败: {str(e)}"
            logger.error(f"❌ [统一基本面工具] {error_msg}")
            return error_msg

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_stock_market_data_unified", log_args=True)
    def get_stock_market_data_unified(
        ticker: Annotated[str, "股票代码（支持A股、港股、美股）"],
        start_date: Annotated[str, "开始日期，格式：YYYY-MM-DD"],
        end_date: Annotated[str, "结束日期，格式：YYYY-MM-DD"]
    ) -> str:
        """
        统一的股票市场数据工具
        自动识别股票类型（A股、港股、美股）并调用相应的数据源获取价格和技术指标数据

        Args:
            ticker: 股票代码（如：002115、0700.HK、AAPL）
            start_date: 开始日期（格式：YYYY-MM-DD）
            end_date: 结束日期（格式：YYYY-MM-DD）

        Returns:
            str: 市场数据和技术分析报告
        """
        logger.info(f"📈 [统一市场工具] 分析股票: {ticker}")

        try:
            from tradingagents.utils.stock_utils import StockUtils

            # 自动识别股票类型
            market_info = StockUtils.get_market_info(ticker)
            is_china = market_info['is_china']
            is_hk = market_info['is_hk']
            is_us = market_info['is_us']

            logger.info(f"📈 [统一市场工具] 股票类型: {market_info['market_name']}")
            logger.info(f"📈 [统一市场工具] 货币: {market_info['currency_name']} ({market_info['currency_symbol']}")

            result_data = []

            if is_china:
                # 中国A股：使用中国股票数据源
                logger.info(f"🇨🇳 [统一市场工具] 处理A股市场数据...")

                try:
                    from tradingagents.dataflows.interface import get_china_stock_data_unified
                    stock_data = get_china_stock_data_unified(ticker, start_date, end_date)
                    result_data.append(f"## A股市场数据\n{stock_data}")
                except Exception as e:
                    result_data.append(f"## A股市场数据\n获取失败: {e}")

            elif is_hk:
                # 港股：使用AKShare数据源
                logger.info(f"🇭🇰 [统一市场工具] 处理港股市场数据...")

                try:
                    from tradingagents.dataflows.interface import get_hk_stock_data_unified
                    hk_data = get_hk_stock_data_unified(ticker, start_date, end_date)
                    result_data.append(f"## 港股市场数据\n{hk_data}")
                except Exception as e:
                    result_data.append(f"## 港股市场数据\n获取失败: {e}")

            else:
                # 美股：优先使用FINNHUB API数据源
                logger.info(f"🇺🇸 [统一市场工具] 处理美股市场数据...")

                try:
                    from tradingagents.dataflows.optimized_us_data import get_us_stock_data_cached
                    us_data = get_us_stock_data_cached(ticker, start_date, end_date)
                    result_data.append(f"## 美股市场数据\n{us_data}")
                except Exception as e:
                    result_data.append(f"## 美股市场数据\n获取失败: {e}")

            # 组合所有数据
            combined_result = f"""# {ticker} 市场数据分析

**股票类型**: {market_info['market_name']}
**货币**: {market_info['currency_name']} ({market_info['currency_symbol']})
**分析期间**: {start_date} 至 {end_date}

{chr(10).join(result_data)}

---
*数据来源: 根据股票类型自动选择最适合的数据源*
"""

            logger.info(f"📈 [统一市场工具] 数据获取完成，总长度: {len(combined_result)}")
            return combined_result

        except Exception as e:
            error_msg = f"统一市场数据工具执行失败: {str(e)}"
            logger.error(f"❌ [统一市场工具] {error_msg}")
            return error_msg

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_stock_news_unified", log_args=True)
    def get_stock_news_unified(
        ticker: Annotated[str, "股票代码（支持A股、港股、美股）"],
        curr_date: Annotated[str, "当前日期，格式：YYYY-MM-DD"]
    ) -> str:
        """
        统一的股票新闻工具
        自动识别股票类型（A股、港股、美股）并调用相应的新闻数据源

        Args:
            ticker: 股票代码（如：002115、0700.HK、AAPL）
            curr_date: 当前日期（格式：YYYY-MM-DD）

        Returns:
            str: 新闻分析报告
        """
        logger.info(f"📰 [统一新闻工具] 分析股票: {ticker}")

        try:
            from tradingagents.utils.stock_utils import StockUtils
            from datetime import datetime, timedelta

            # 自动识别股票类型
            market_info = StockUtils.get_market_info(ticker)
            is_china = market_info['is_china']
            is_hk = market_info['is_hk']
            is_us = market_info['is_us']

            logger.info(f"📰 [统一新闻工具] 股票类型: {market_info['market_name']}")

            # 计算新闻查询的日期范围
            end_date = datetime.strptime(curr_date, '%Y-%m-%d')
            start_date = end_date - timedelta(days=7)
            start_date_str = start_date.strftime('%Y-%m-%d')

            result_data = []

            if is_china or is_hk:
                # 中国A股和港股：使用AKShare东方财富新闻和Google新闻（中文搜索）
                logger.info(f"🇨🇳🇭🇰 [统一新闻工具] 处理中文新闻...")

                # 1. 尝试获取AKShare东方财富新闻
                try:
                    # 处理股票代码
                    clean_ticker = ticker.replace('.SH', '').replace('.SZ', '').replace('.SS', '')\
                                   .replace('.HK', '').replace('.XSHE', '').replace('.XSHG', '')
                    
                    logger.info(f"🇨🇳🇭🇰 [统一新闻工具] 尝试获取东方财富新闻: {clean_ticker}")
                    
                    # 导入AKShare新闻获取函数
                    from tradingagents.dataflows.akshare_utils import get_stock_news_em
                    
                    # 获取东方财富新闻
                    news_df = get_stock_news_em(clean_ticker)
                    
                    if not news_df.empty:
                        # 格式化东方财富新闻
                        em_news_items = []
                        for _, row in news_df.iterrows():
                            news_title = row.get('标题', '')
                            news_time = row.get('时间', '')
                            news_url = row.get('链接', '')
                            
                            news_item = f"- **{news_title}** [{news_time}]({news_url})"
                            em_news_items.append(news_item)
                        
                        # 添加到结果中
                        if em_news_items:
                            em_news_text = "\n".join(em_news_items)
                            result_data.append(f"## 东方财富新闻\n{em_news_text}")
                            logger.info(f"🇨🇳🇭🇰 [统一新闻工具] 成功获取{len(em_news_items)}条东方财富新闻")
                except Exception as em_e:
                    logger.error(f"❌ [统一新闻工具] 东方财富新闻获取失败: {em_e}")
                    result_data.append(f"## 东方财富新闻\n获取失败: {em_e}")

                # 2. 获取Google新闻作为补充
                try:
                    # 获取公司中文名称用于搜索
                    if is_china:
                        # A股使用股票代码搜索，添加更多中文关键词
                        clean_ticker = ticker.replace('.SH', '').replace('.SZ', '').replace('.SS', '')\
                                       .replace('.XSHE', '').replace('.XSHG', '')
                        search_query = f"{clean_ticker} 股票 公司 财报 新闻"
                        logger.info(f"🇨🇳 [统一新闻工具] A股Google新闻搜索关键词: {search_query}")
                    else:
                        # 港股使用代码搜索
                        search_query = f"{ticker} 港股"
                        logger.info(f"🇭🇰 [统一新闻工具] 港股Google新闻搜索关键词: {search_query}")

                    from tradingagents.dataflows.interface import get_google_news
                    news_data = get_google_news(search_query, curr_date)
                    result_data.append(f"## Google新闻\n{news_data}")
                    logger.info(f"🇨🇳🇭🇰 [统一新闻工具] 成功获取Google新闻")
                except Exception as google_e:
                    logger.error(f"❌ [统一新闻工具] Google新闻获取失败: {google_e}")
                    result_data.append(f"## Google新闻\n获取失败: {google_e}")

            else:
                # 美股：使用Finnhub新闻
                logger.info(f"🇺🇸 [统一新闻工具] 处理美股新闻...")

                try:
                    from tradingagents.dataflows.interface import get_finnhub_news
                    news_data = get_finnhub_news(ticker, start_date_str, curr_date)
                    result_data.append(f"## 美股新闻\n{news_data}")
                except Exception as e:
                    result_data.append(f"## 美股新闻\n获取失败: {e}")

            # 组合所有数据
            combined_result = f"""# {ticker} 新闻分析

**股票类型**: {market_info['market_name']}
**分析日期**: {curr_date}
**新闻时间范围**: {start_date_str} 至 {curr_date}

{chr(10).join(result_data)}

---
*数据来源: 根据股票类型自动选择最适合的新闻源*
"""

            logger.info(f"📰 [统一新闻工具] 数据获取完成，总长度: {len(combined_result)}")
            return combined_result

        except Exception as e:
            error_msg = f"统一新闻工具执行失败: {str(e)}"
            logger.error(f"❌ [统一新闻工具] {error_msg}")
            return error_msg

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_stock_sentiment_unified", log_args=True)
    def get_stock_sentiment_unified(
        ticker: Annotated[str, "股票代码（支持A股、港股、美股）"],
        curr_date: Annotated[str, "当前日期，格式：YYYY-MM-DD"]
    ) -> str:
        """
        统一的股票情绪分析工具
        自动识别股票类型（A股、港股、美股）并调用相应的情绪数据源

        Args:
            ticker: 股票代码（如：002115、0700.HK、AAPL）
            curr_date: 当前日期（格式：YYYY-MM-DD）

        Returns:
            str: 情绪分析报告
        """
        logger.info(f"😊 [统一情绪工具] 分析股票: {ticker}")

        try:
            from tradingagents.utils.stock_utils import StockUtils

            # 自动识别股票类型
            market_info = StockUtils.get_market_info(ticker)
            is_china = market_info['is_china']
            is_hk = market_info['is_hk']
            is_us = market_info['is_us']

            logger.info(f"😊 [统一情绪工具] 股票类型: {market_info['market_name']}")

            result_data = []

            if is_china or is_hk:
                # 中国A股和港股：使用社交媒体情绪分析
                logger.info(f"🇨🇳🇭🇰 [统一情绪工具] 处理中文市场情绪...")

                try:
                    # 可以集成微博、雪球、东方财富等中文社交媒体情绪
                    # 目前使用基础的情绪分析
                    sentiment_summary = f"""
## 中文市场情绪分析

**股票**: {ticker} ({market_info['market_name']})
**分析日期**: {curr_date}

### 市场情绪概况
- 由于中文社交媒体情绪数据源暂未完全集成，当前提供基础分析
- 建议关注雪球、东方财富、同花顺等平台的讨论热度
- 港股市场还需关注香港本地财经媒体情绪

### 情绪指标
- 整体情绪: 中性
- 讨论热度: 待分析
- 投资者信心: 待评估

*注：完整的中文社交媒体情绪分析功能正在开发中*
"""
                    result_data.append(sentiment_summary)
                except Exception as e:
                    result_data.append(f"## 中文市场情绪\n获取失败: {e}")

            else:
                # 美股：使用Reddit情绪分析
                logger.info(f"🇺🇸 [统一情绪工具] 处理美股情绪...")

                try:
                    from tradingagents.dataflows.interface import get_reddit_sentiment

                    sentiment_data = get_reddit_sentiment(ticker, curr_date)
                    result_data.append(f"## 美股Reddit情绪\n{sentiment_data}")
                except Exception as e:
                    result_data.append(f"## 美股Reddit情绪\n获取失败: {e}")

            # 组合所有数据
            combined_result = f"""# {ticker} 情绪分析

**股票类型**: {market_info['market_name']}
**分析日期**: {curr_date}

{chr(10).join(result_data)}

---
*数据来源: 根据股票类型自动选择最适合的情绪数据源*
"""

            logger.info(f"😊 [统一情绪工具] 数据获取完成，总长度: {len(combined_result)}")
            return combined_result

        except Exception as e:
            error_msg = f"统一情绪分析工具执行失败: {str(e)}"
            logger.error(f"❌ [统一情绪工具] {error_msg}")
            return error_msg

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_capital_flow_analysis", log_args=True)
    def get_capital_flow_analysis(
        symbol: Annotated[str, "股票代码"],
        analysis_days: Annotated[int, "分析天数"] = 5
    ) -> str:
        """
        获取股票资金流向分析，为技术分析师提供资金面的洞察

        Args:
            symbol: 股票代码
            analysis_days: 分析天数，默认5天

        Returns:
            str: 资金流向分析报告
        """
        try:
            logger.info(f"💰 [资金流向工具] 开始分析股票 {symbol} 的资金流向")

            # 获取实时资金流向数据
            realtime_flow = interface.get_capital_flow_realtime(symbol)
            logger.debug(f"💰 [资金流向工具] 获取实时数据: {len(realtime_flow)} 字符")

            # 获取历史资金流向数据
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=analysis_days)).strftime('%Y-%m-%d')

            historical_flow = interface.get_capital_flow_data(symbol, start_date, end_date)
            logger.debug(f"💰 [资金流向工具] 获取历史数据: {len(historical_flow)} 字符")

            # 组合分析报告
            analysis_report = f"""# {symbol} 资金流向技术分析

    ## 实时资金流向情况
    {realtime_flow}

    ## 近{analysis_days}日资金流向趋势
    {historical_flow}

    ## 技术分析要点

    ### 资金流向指标说明：
    - **主力净流入**: 大资金(>50万)的净流入情况，正值表示资金流入，负值表示流出
    - **超大单净流入**: 特大资金(>100万)流向，通常代表机构资金动向
    - **大单净流入**: 大额交易(20-50万)资金流向
    - **中单净流入**: 中等资金(5-20万)流向，往往反映游资活动
    - **小单净流入**: 散户资金(<5万)流向

    ### 分析维度：
    1. **资金性质分析**: 从资金规模判断是机构资金还是散户资金
    2. **资金流向趋势**: 连续几日的资金净流入/流出趋势
    3. **资金流向强度**: 资金流入/流出的绝对数量和相对比例
    4. **主力控盘度**: 主力资金与散户资金的对比

    ### 技术分析建议：
    - 主力资金持续流入通常是股价上涨的先行指标
    - 超大单资金流入常预示着重要的价格变化
    - 资金流向与股价走势的背离需要特别关注
    - 连续多日的资金净流出可能预示调整压力

    ---
    *分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
    *数据来源: 东方财富等多数据源智能融合*
    """

            logger.info(f"💰 [资金流向工具] 分析完成，报告长度: {len(analysis_report)}")
            return analysis_report

        except Exception as e:
            error_msg = f"资金流向分析失败: {str(e)}"
            logger.error(f"❌ [资金流向工具] {error_msg}")
            return f"❌ 获取{symbol}资金流向分析失败: {error_msg}"

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_concept_capital_flow_analysis", log_args=True)
    def get_concept_capital_flow_analysis(
        concept_code: Annotated[str, "概念板块代码"],
    ) -> str:
        """
        获取概念板块资金流向分析，帮助技术分析师识别板块轮动和热点

        Args:
            concept_code: 概念板块代码

        Returns:
            str: 概念板块资金流向分析报告
        """
        try:
            logger.info(f"📊 [概念资金流向] 开始分析概念板块 {concept_code}")

            # 获取概念资金流向数据
            concept_flow = interface.get_concept_capital_flow(concept_code)

            # 获取概念成分股信息
            concept_stocks = interface.get_concept_stocks(concept_code)

            # 组合分析报告
            analysis_report = f"""# 概念板块 {concept_code} 资金流向分析

    ## 概念板块资金流向
    {concept_flow}

    ## 概念成分股表现
    {concept_stocks}

    ## 板块技术分析要点

    ### 板块资金流向意义：
    - **板块资金净流入**: 反映市场对该概念主题的关注度和资金偏好
    - **成分股资金分化**: 分析板块内部资金流向的差异化表现
    - **龙头股资金集中度**: 识别板块内的资金集中股票

    ### 技术分析应用：
    1. **板块轮动识别**: 通过资金流向变化识别热点板块切换
    2. **概念炒作周期**: 判断概念主题的资金流入阶段
    3. **个股选择参考**: 在强势板块中选择资金流入最多的个股
    4. **风险控制**: 板块资金流出时及时规避相关个股风险

    ### 操作建议：
    - 板块资金持续流入时，重点关注龙头股机会
    - 板块资金分化严重时，谨慎参与概念炒作
    - 结合板块资金流向和个股技术形态，提高胜率

    ---
    *分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
    *数据来源: 概念板块多维度资金流向监控*
    """

            logger.info(f"📊 [概念资金流向] 分析完成")
            return analysis_report

        except Exception as e:
            error_msg = f"概念板块资金流向分析失败: {str(e)}"
            logger.error(f"❌ [概念资金流向] {error_msg}")
            return f"❌ 获取概念板块{concept_code}资金流向分析失败: {error_msg}"

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_market_capital_flow_overview", log_args=True)
    def get_market_capital_flow_overview() -> str:
        """
        获取市场整体资金流向概览，为技术分析师提供市场资金面的宏观视角

        Returns:
            str: 市场资金流向概览报告
        """
        try:
            logger.info(f"🌐 [市场资金流向] 开始获取市场整体资金流向概览")

            # 获取热门概念的资金流向
            concept_ranking = interface.get_concept_ranking(sort_by="change_pct", limit=10)

            # 组合市场资金流向概览
            overview_report = f"""# 市场资金流向概览

    ## 热门概念板块排行 (按涨跌幅)
    {concept_ranking}

    ## 市场资金流向技术分析

    ### 市场资金面分析要点：
    1. **热点板块识别**: 资金集中流入的概念板块往往是短期热点
    2. **市场情绪判断**: 通过板块资金流向强度判断市场风险偏好
    3. **轮动周期把握**: 识别不同概念板块之间的资金轮动规律
    4. **系统性风险**: 当所有板块资金同时流出时，需警惕市场系统性风险

    ### 技术分析策略：
    - **追涨策略**: 重点关注资金流入强劲的概念板块龙头
    - **轮动策略**: 在资金从一个板块流向另一个板块时把握机会
    - **防守策略**: 当市场整体资金流出时，降低仓位或选择防守性板块

    ### 风险提示：
    - 概念板块炒作具有阶段性，注意及时止盈
    - 资金流向数据需要结合基本面和技术面综合判断
    - 短期资金流向可能存在噪音，建议关注趋势性变化

    ---
    *分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
    *覆盖范围: 主要概念板块和市场热点追踪*
    """

            logger.info(f"🌐 [市场资金流向] 概览分析完成")
            return overview_report

        except Exception as e:
            error_msg = f"市场资金流向概览获取失败: {str(e)}"
            logger.error(f"❌ [市场资金流向] {error_msg}")
            return f"❌ 获取市场资金流向概览失败: {error_msg}"

        # ============ 基本面分析工具 (概念板块 + 股息分析) ============

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_concept_fundamentals_analysis", log_args=True)
    def get_concept_fundamentals_analysis(
        concept_code: Annotated[str, "概念板块代码"]
    ) -> str:
        """
        获取概念板块基本面分析，帮助基本面分析师识别有价值的投资主题

        Args:
            concept_code: 概念板块代码

        Returns:
            str: 概念板块基本面分析报告
        """
        try:
            logger.info(f"📈 [概念基本面] 开始分析概念板块 {concept_code} 的基本面")

            # 获取概念板块列表和成分股
            concept_stocks = interface.get_concept_stocks(concept_code)
            concept_ranking = interface.get_concept_ranking(sort_by="market_cap", limit=5)

            # 组合基本面分析报告
            analysis_report = f"""# 概念板块 {concept_code} 基本面投资分析

    ## 概念板块成分股分析
    {concept_stocks}

    ## 相关概念板块市值排名 (前5名)
    {concept_ranking}

    ## 基本面投资分析框架

    ### 概念投资价值评估：
    1. **行业前景分析**: 评估概念所代表的行业或主题的长期发展潜力
    2. **政策支持度**: 分析相关政策对概念板块的支持力度和持续性
    3. **技术成熟度**: 判断概念涉及的技术或商业模式的成熟程度
    4. **市场空间**: 评估概念板块的总体市场规模和增长潜力

    ### 成分股基本面筛选：
    - **财务健康度**: 关注成分股的盈利能力、现金流和负债情况
    - **竞争优势**: 识别在概念主题中具有核心竞争力的公司
    - **估值合理性**: 评估股票当前估值是否合理，避免概念溢价过高
    - **管理层质量**: 考察公司管理层的执行力和战略规划能力

    ### 投资建议框架：
    1. **长期投资视角**: 关注具有长期成长性的概念主题
    2. **分散投资**: 在概念板块内选择多只优质股票分散风险
    3. **估值纪律**: 严格控制买入价格，避免追高
    4. **定期评估**: 定期评估概念的发展情况和投资逻辑变化

    ### 风险控制：
    - 概念炒作风险：避免在概念高峰期盲目追高
    - 政策变化风险：关注相关政策的变化对概念的影响
    - 基本面变化：及时跟踪成分股基本面变化

    ---
    *分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
    *分析维度: 概念价值评估 + 成分股基本面筛选*
    """

            logger.info(f"📈 [概念基本面] 分析完成")
            return analysis_report

        except Exception as e:
            error_msg = f"概念板块基本面分析失败: {str(e)}"
            logger.error(f"❌ [概念基本面] {error_msg}")
            return f"❌ 概念板块{concept_code}基本面分析失败: {error_msg}"

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_dividend_investment_analysis", log_args=True)
    def get_dividend_investment_analysis(
        symbol: Annotated[str, "股票代码"],
        current_price: Annotated[float, "当前股价"] = None
    ) -> str:
        """
        获取股票股息投资分析，为基本面分析师提供价值投资和收益评估

        Args:
            symbol: 股票代码
            current_price: 当前股价(可选)

        Returns:
            str: 股息投资分析报告
        """
        try:
            logger.info(f"💎 [股息投资分析] 开始分析股票 {symbol} 的股息投资价值")

            # 获取股息历史数据
            dividend_history = interface.get_dividend_history(symbol, use_cache=True)

            # 获取股息汇总信息
            dividend_summary = interface.get_dividend_summary(symbol, use_cache=True)

            # 计算股息率
            dividend_yield = interface.calculate_dividend_yield(symbol, current_price, use_cache=True)

            # 组合股息投资分析报告
            analysis_report = f"""# {symbol} 股息投资价值分析

    ## 股息历史表现
    {dividend_history}

    ## 股息汇总统计
    {dividend_summary}

    ## 股息率评估
    {dividend_yield}

    ## 股息投资价值评估框架

    ### 股息投资优势分析：
    1. **稳定现金收益**: 定期股息提供稳定的现金流收入
    2. **抗通胀能力**: 优质分红股的股息增长通常能跑赢通胀
    3. **风险控制**: 分红能力强的公司通常财务稳健，风险相对较低
    4. **复利效应**: 长期持有并再投资股息，实现复利增长

    ### 股息质量评估维度：
    - **分红稳定性**: 历史分红的连续性和稳定性
    - **分红增长性**: 股息的增长趋势和可持续性
    - **派息率适中**: 避免派息率过高影响公司发展
    - **现金流支撑**: 分红是否有足够的自由现金流支撑

    ### 股息投资策略：
    1. **股息增长投资**: 选择股息持续增长的优质公司
    2. **高股息价值投资**: 关注股息率较高且基本面良好的股票
    3. **股息再投资**: 将获得的股息继续投资，实现复利效应
    4. **组合配置**: 构建多元化的股息股票组合

    ### 投资建议：
    - **买入时机**: 在股息率相对较高时买入，获得更好的收益率
    - **长期持有**: 股息投资适合长期投资者，短期波动不必过度关注
    - **定期评估**: 关注公司基本面变化，确保分红的可持续性
    - **税收考虑**: 了解股息税收政策，优化投资收益

    ### 风险提示：
    - 股息削减风险：经济下行时公司可能削减或暂停分红
    - 利率敏感性：利率上升时高股息股票可能面临估值压力
    - 增长性权衡：高股息股票的资本增值潜力可能相对有限

    ---
    *分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
    *投资理念: 价值投资 + 现金流收益 + 长期持有*
    """

            logger.info(f"💎 [股息投资分析] 分析完成")
            return analysis_report

        except Exception as e:
            error_msg = f"股息投资分析失败: {str(e)}"
            logger.error(f"❌ [股息投资分析] {error_msg}")
            return f"❌ 股票{symbol}股息投资分析失败: {error_msg}"

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_sector_rotation_analysis", log_args=True)
    def get_sector_rotation_analysis() -> str:
        """
        获取行业板块轮动分析，帮助基本面分析师把握市场轮动机会

        Returns:
            str: 行业板块轮动分析报告
        """
        try:
            logger.info(f"🔄 [板块轮动] 开始分析行业板块轮动情况")

            # 获取概念板块排名数据
            top_concepts_by_change = interface.get_concept_ranking(sort_by="change_pct", limit=10)
            top_concepts_by_volume = interface.get_concept_ranking(sort_by="volume", limit=8)
            top_concepts_by_market_cap = interface.get_concept_ranking(sort_by="market_cap", limit=8)

            # 组合板块轮动分析报告
            rotation_report = f"""# 行业板块轮动基本面分析

    ## 当前热门板块 (按涨跌幅排序)
    {top_concepts_by_change}

    ## 活跃交易板块 (按成交量排序)
    {top_concepts_by_volume}

    ## 大市值板块 (按市值排序)
    {top_concepts_by_market_cap}

    ## 板块轮动投资策略框架

    ### 板块轮动分析逻辑：
    1. **经济周期分析**: 不同经济周期阶段，不同板块的表现差异显著
    2. **政策导向跟踪**: 政策扶持的行业往往成为阶段性热点
    3. **基本面拐点**: 关注行业基本面出现向上拐点的板块
    4. **估值比较**: 寻找基本面良好但估值相对较低的板块

    ### 板块投资机会识别：
    - **成长性板块**: 关注新兴产业和高成长行业的投资机会
    - **价值修复板块**: 寻找被错杀但基本面稳定的传统行业
    - **周期性板块**: 把握经济周期带来的周期性行业机会
    - **防御性板块**: 经济不确定时期的避险选择

    ### 基本面分析要点：
    1. **行业景气度**: 评估行业整体的景气程度和发展趋势
    2. **供需关系**: 分析行业供需平衡状况及未来变化
    3. **技术进步**: 关注技术创新对行业格局的影响
    4. **监管环境**: 评估监管政策对行业发展的影响

    ### 投资策略建议：
    - **分阶段配置**: 根据经济周期和市场阶段调整板块配置
    - **龙头优选**: 在优势板块中选择龙头企业进行配置
    - **估值纪律**: 严格控制买入估值，避免高位追涨
    - **动态调整**: 根据基本面变化及时调整板块配置

    ### 风险管控：
    - 板块集中风险：避免过度集中在单一板块
    - 择时风险：板块轮动存在一定的择时难度
    - 基本面变化：密切跟踪板块基本面的变化

    ---
    *分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
    *分析范围: 全市场主要概念板块轮动监控*
    """

            logger.info(f"🔄 [板块轮动] 分析完成")
            return rotation_report

        except Exception as e:
            error_msg = f"板块轮动分析失败: {str(e)}"
            logger.error(f"❌ [板块轮动] {error_msg}")
            return f"❌ 板块轮动分析失败: {error_msg}"
