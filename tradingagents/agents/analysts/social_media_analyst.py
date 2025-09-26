from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json

# 导入统一日志系统和分析模块日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_analyst_module
logger = get_logger("analysts.social_media")

# 导入Google工具调用处理器
from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler


def _get_company_name_for_social_media(ticker: str, market_info: dict) -> str:
    """
    为社交媒体分析师获取公司名称

    Args:
        ticker: 股票代码
        market_info: 市场信息字典

    Returns:
        str: 公司名称
    """
    try:
        if market_info['is_china']:
            # 中国A股：使用统一接口获取股票信息
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            stock_info = get_china_stock_info_unified(ticker)

            # 解析股票名称
            if "股票名称:" in stock_info:
                company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                logger.debug(f"📊 [社交媒体分析师] 从统一接口获取中国股票名称: {ticker} -> {company_name}")
                return company_name
            else:
                logger.warning(f"⚠️ [社交媒体分析师] 无法从统一接口解析股票名称: {ticker}")
                return f"股票代码{ticker}"

        elif market_info['is_hk']:
            # 港股：使用改进的港股工具
            try:
                from tradingagents.dataflows.improved_hk_utils import get_hk_company_name_improved
                company_name = get_hk_company_name_improved(ticker)
                logger.debug(f"📊 [社交媒体分析师] 使用改进港股工具获取名称: {ticker} -> {company_name}")
                return company_name
            except Exception as e:
                logger.debug(f"📊 [社交媒体分析师] 改进港股工具获取名称失败: {e}")
                # 降级方案：生成友好的默认名称
                clean_ticker = ticker.replace('.HK', '').replace('.hk', '')
                return f"港股{clean_ticker}"

        elif market_info['is_us']:
            # 美股：使用简单映射或返回代码
            us_stock_names = {
                'AAPL': '苹果公司',
                'TSLA': '特斯拉',
                'NVDA': '英伟达',
                'MSFT': '微软',
                'GOOGL': '谷歌',
                'AMZN': '亚马逊',
                'META': 'Meta',
                'NFLX': '奈飞'
            }

            company_name = us_stock_names.get(ticker.upper(), f"美股{ticker}")
            logger.debug(f"📊 [社交媒体分析师] 美股名称映射: {ticker} -> {company_name}")
            return company_name

        else:
            return f"股票{ticker}"

    except Exception as e:
        logger.error(f"❌ [社交媒体分析师] 获取公司名称失败: {e}")
        return f"股票{ticker}"


def create_social_media_analyst(llm, toolkit):
    @log_analyst_module("social_media")
    def social_media_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        # 获取股票市场信息
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(ticker)
        
        # 获取公司名称
        company_name = _get_company_name_for_social_media(ticker, market_info)
        logger.info(f"[社交媒体分析师] 公司名称: {company_name}")

        if toolkit.config["online_tools"]:
            # 在线模式：使用完整的情绪分析工具集，与ToolNode同步
            tools = [
                toolkit.get_stock_sentiment_unified,   # 统一情绪分析工具（主要选择）
                toolkit.get_chinese_social_sentiment,  # 中国社交媒体情绪（地区化增强）
                toolkit.get_stock_news_openai,         # 在线新闻工具（备用）
                toolkit.get_reddit_stock_info,         # Reddit数据（备用）
            ]
        else:
            # 离线模式：使用统一工具和地区化工具
            tools = [
                toolkit.get_stock_sentiment_unified,   # 统一情绪分析工具（主要选择）
                toolkit.get_chinese_social_sentiment,  # 中国社交媒体情绪（地区化）
                toolkit.get_reddit_stock_info,         # Reddit数据（备用）
            ]

        logger.info(f"[社交媒体分析师] 已绑定 {len(tools)} 个工具，与ToolNode同步完成")

        system_message = f"""您是一位专业的跨市场社交媒体和投资情绪分析师。

**股票分析对象**：
- 公司名称：{company_name}
- 股票代码：{ticker}
- 所属市场：{market_info['market_name']}
- 计价货币：{market_info['currency_name']} ({market_info['currency_symbol']})

**优先工具选择策略**：
1. 🎯 **主要工具**: get_stock_sentiment_unified - 统一情绪分析工具，自动识别股票类型并调用适合的数据源
2. 🇨🇳 **中国市场增强**: get_chinese_social_sentiment - 专门分析中国本土社交媒体情绪
3. 🌍 **备用工具**: get_reddit_stock_info, get_stock_news_openai - 作为补充数据源

**智能分析策略**：
- 自动适配{market_info['market_name']}股票的特点和投资者行为
- 整合多平台情绪数据（雪球、Reddit、微博、东方财富股吧等）
- 根据股票类型调整分析重点和情绪指标权重

**核心职责**：
1. 📊 **跨平台情绪监控**: 整合各大投资社区和社交媒体的情绪数据
2. 🔍 **热点事件识别**: 捕捉影响股价的关键事件和市场传言
3. 💭 **投资者行为分析**: 评估散户与机构投资者的观点差异
4. 📈 **情绪量化评估**: 提供具体的情绪指标和价格影响预测
5. ⏰ **交易时机建议**: 基于情绪变化给出买入/卖出时机

**分析重点**（根据市场类型）：
- **A股市场**: 重点关注政策情绪、雪球讨论、东方财富股吧
- **港股市场**: 关注国际投资者情绪、本地财经媒体
- **美股市场**: 重点关注Reddit、Twitter、机构情绪

**必须输出**：
- 情绪指数评分（1-10分，10为极度乐观）
- 预期价格波动幅度（以{market_info['currency_symbol']}计价）
- 基于情绪的具体交易建议
- 情绪风险提示

请使用统一工具优先获取情绪数据，然后生成详细的中文分析报告。"""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "您是一位有用的AI助手，与其他助手协作。"
                    " 使用提供的工具来推进回答问题。"
                    " 如果您无法完全回答，没关系；具有不同工具的其他助手"
                    " 将从您停下的地方继续帮助。执行您能做的以取得进展。"
                    " 如果您或任何其他助手有最终交易提案：**买入/持有/卖出**或可交付成果，"
                    " 请在您的回应前加上最终交易提案：**买入/持有/卖出**，以便团队知道停止。"
                    " 您可以访问以下工具：{tool_names}。\n{system_message}"
                    "供您参考，当前日期是{current_date}。我们要分析的当前公司是{ticker}。请用中文撰写所有分析内容。",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        # 安全地获取工具名称，处理函数和工具对象
        tool_names = []
        for tool in tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(tool))

        prompt = prompt.partial(tool_names=", ".join(tool_names))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        # 使用统一的Google工具调用处理器
        if GoogleToolCallHandler.is_google_model(llm):
            logger.info(f"📊 [社交媒体分析师] 检测到Google模型，使用统一工具调用处理器")
            
            # 创建分析提示词
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=company_name,
                analyst_type="社交媒体情绪分析",
                specific_requirements="重点关注投资者情绪、社交媒体讨论热度、舆论影响等。"
            )
            
            # 处理Google模型工具调用
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="社交媒体分析师"
            )
        else:
            # 非Google模型的处理逻辑
            logger.debug(f"📊 [DEBUG] 非Google模型 ({llm.__class__.__name__})，使用标准处理逻辑")
            
            report = ""
            if len(result.tool_calls) == 0:
                report = result.content

        return {
            "messages": [result],
            "sentiment_report": report,
        }

    return social_media_analyst_node
