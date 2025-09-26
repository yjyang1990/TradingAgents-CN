from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from datetime import datetime

# 导入统一日志系统和分析模块日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_analyst_module
# 导入统一新闻工具
from tradingagents.tools.unified_news_tool import create_unified_news_tool
# 导入股票工具类
from tradingagents.utils.stock_utils import StockUtils
# 导入Google工具调用处理器
from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler

logger = get_logger("analysts.news")


def create_news_analyst(llm, toolkit):
    @log_analyst_module("news")
    def news_analyst_node(state):
        start_time = datetime.now()
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        logger.info(f"[新闻分析师] 开始分析 {ticker} 的新闻，交易日期: {current_date}")
        session_id = state.get("session_id", "未知会话")
        logger.info(f"[新闻分析师] 会话ID: {session_id}，开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取市场信息
        market_info = StockUtils.get_market_info(ticker)
        logger.info(f"[新闻分析师] 股票类型: {market_info['market_name']}")
        
        # 获取公司名称
        def _get_company_name(ticker: str, market_info: dict) -> str:
            """根据股票代码获取公司名称"""
            try:
                if market_info['is_china']:
                    # 中国A股：使用统一接口获取股票信息
                    from tradingagents.dataflows.interface import get_china_stock_info_unified
                    stock_info = get_china_stock_info_unified(ticker)
                    
                    # 解析股票名称
                    if "股票名称:" in stock_info:
                        company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                        logger.debug(f"📊 [DEBUG] 从统一接口获取中国股票名称: {ticker} -> {company_name}")
                        return company_name
                    else:
                        logger.warning(f"⚠️ [DEBUG] 无法从统一接口解析股票名称: {ticker}")
                        return f"股票代码{ticker}"
                        
                elif market_info['is_hk']:
                    # 港股：使用改进的港股工具
                    try:
                        from tradingagents.dataflows.improved_hk_utils import get_hk_company_name_improved
                        company_name = get_hk_company_name_improved(ticker)
                        logger.debug(f"📊 [DEBUG] 使用改进港股工具获取名称: {ticker} -> {company_name}")
                        return company_name
                    except Exception as e:
                        logger.debug(f"📊 [DEBUG] 改进港股工具获取名称失败: {e}")
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
                    logger.debug(f"📊 [DEBUG] 美股名称映射: {ticker} -> {company_name}")
                    return company_name
                    
                else:
                    return f"股票{ticker}"
                    
            except Exception as e:
                logger.error(f"❌ [DEBUG] 获取公司名称失败: {e}")
                return f"股票{ticker}"
        
        company_name = _get_company_name(ticker, market_info)
        logger.info(f"[新闻分析师] 公司名称: {company_name}")
        
        # 🔧 使用增强的新闻工具组合，包括统一工具和实时新闻
        logger.info(f"[新闻分析师] 使用统一新闻工具和实时新闻工具，提供全面的新闻分析")

        if toolkit.config["online_tools"]:
            # 在线模式：使用完整的新闻分析工具集，与ToolNode同步
            tools = [
                toolkit.get_stock_news_unified,    # 统一新闻工具（主要选择）
                toolkit.get_realtime_stock_news,   # 实时新闻工具（新增）
                toolkit.get_global_news_openai,    # 全球宏观新闻（备用）
                toolkit.get_google_news,           # Google新闻（备用）
                toolkit.get_finnhub_news,          # Finnhub新闻（备用）
                toolkit.get_reddit_news,           # Reddit新闻（备用）
            ]
        else:
            # 离线模式：创建统一新闻工具 + 备用工具
            unified_news_tool = create_unified_news_tool(toolkit)
            unified_news_tool.name = "get_stock_news_unified"

            tools = [
                unified_news_tool,                 # 统一新闻工具
                toolkit.get_finnhub_news,          # Finnhub新闻（备用）
                toolkit.get_google_news,           # Google新闻（备用）
                toolkit.get_reddit_news,           # Reddit新闻（备用）
            ]

        logger.info(f"[新闻分析师] 已加载 {len(tools)} 个新闻分析工具")

        system_message = f"""您是一位专业的跨市场财经新闻分析师，专门分析市场新闻对股票价格的影响。

**分析对象**：
- 公司名称：{company_name}
- 股票代码：{ticker}
- 所属市场：{market_info['market_name']}
- 计价货币：{market_info['currency_name']} ({market_info['currency_symbol']})

**工具使用策略**（按优先级排序）：
1. 🎯 **主要工具**: get_stock_news_unified - 统一新闻工具，自动适配{market_info['market_name']}新闻源
2. ⚡ **实时增强**: get_realtime_stock_news - 获取15-30分钟内最新消息，解决传统新闻滞后性
3. 🌍 **宏观视角**: get_global_news_openai - 全球宏观经济新闻和政策动态
4. 🔍 **备用数据源**: get_finnhub_news, get_google_news - 多源交叉验证

**智能分析策略**：
- 🕒 **时效性优先**: 优先使用实时新闻工具，获取最新市场动态
- 🎭 **多源整合**: 结合统一工具和实时工具，提供全面新闻覆盖
- 🎯 **市场适配**: 根据{market_info['market_name']}特点，重点关注相关新闻源

**核心职责**：
1. 📰 **实时新闻监控**: 优先获取15-30分钟内的最新新闻
2. 🔍 **关键事件识别**: 筛选出对{ticker}有重大影响的新闻事件
3. ⚖️ **影响评估**: 量化分析新闻对股价的潜在影响
4. ⏱️ **时效性分析**: 评估新闻的时间敏感性和紧急程度
5. 💡 **投资建议**: 基于新闻分析提供具体的交易时机建议

**市场特定关注点**：
- **A股市场**: 政策动态、监管变化、财报季、中美关系
- **港股市场**: 国际资金流向、汇率变化、中概股动态
- **美股市场**: 美联储政策、财报季、行业轮动、地缘政治

**必须输出**：
- 新闻时效性评估（发布时间 vs 当前时间）
- 价格影响程度（1-10分，10为极高影响）
- 预期价格波动幅度（以{market_info['currency_symbol']}计价）
- 基于新闻的具体交易建议和时机
- 新闻风险等级评估

**分析要求**：
- 优先使用实时新闻工具获取最新消息
- 如新闻滞后超过2小时，必须在分析中明确标注时效性限制
- 提供量化的价格影响评估和具体预期
- 结合多个新闻源进行交叉验证

请使用可用工具获取新闻数据，然后生成详细的中文分析报告。"""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "您是一位专业的财经新闻分析师。"
                    "\n🚨 CRITICAL REQUIREMENT - 绝对强制要求："
                    "\n"
                    "\n❌ 禁止行为："
                    "\n- 绝对禁止在没有调用工具的情况下直接回答"
                    "\n- 绝对禁止基于推测或假设生成任何分析内容"
                    "\n- 绝对禁止跳过工具调用步骤"
                    "\n- 绝对禁止说'我无法获取实时数据'等借口"
                    "\n"
                    "\n✅ 强制执行步骤："
                    "\n1. 您的第一个动作必须是调用 get_stock_news_unified 工具"
                    "\n2. 该工具会自动识别股票类型（A股、港股、美股）并获取相应新闻"
                    "\n3. 只有在成功获取新闻数据后，才能开始分析"
                    "\n4. 您的回答必须基于工具返回的真实数据"
                    "\n"
                    "\n🔧 工具调用格式示例："
                    "\n调用: get_stock_news_unified(stock_code='{ticker}', max_news=10)"
                    "\n"
                    "\n⚠️ 如果您不调用工具，您的回答将被视为无效并被拒绝。"
                    "\n⚠️ 您必须先调用工具获取数据，然后基于数据进行分析。"
                    "\n⚠️ 没有例外，没有借口，必须调用工具。"
                    "\n"
                    "\n您可以访问以下工具：{tool_names}。"
                    "\n{system_message}"
                    "\n供您参考，当前日期是{current_date}。我们正在查看公司{ticker}。"
                    "\n请按照上述要求执行，用中文撰写所有分析内容。",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        
        # 获取模型信息用于统一新闻工具的特殊处理
        model_info = ""
        try:
            if hasattr(llm, 'model_name'):
                model_info = f"{llm.__class__.__name__}:{llm.model_name}"
            else:
                model_info = llm.__class__.__name__
        except:
            model_info = "Unknown"
        
        logger.info(f"[新闻分析师] 准备调用LLM进行新闻分析，模型: {model_info}")
        
        # 🚨 DashScope预处理：强制获取新闻数据
        pre_fetched_news = None
        if 'DashScope' in llm.__class__.__name__:
            logger.warning(f"[新闻分析师] 🚨 检测到DashScope模型，启动预处理强制新闻获取...")
            try:
                # 强制预先获取新闻数据
                logger.info(f"[新闻分析师] 🔧 预处理：强制调用统一新闻工具...")
                pre_fetched_news = unified_news_tool(stock_code=ticker, max_news=10, model_info=model_info)
                
                if pre_fetched_news and len(pre_fetched_news.strip()) > 100:
                    logger.info(f"[新闻分析师] ✅ 预处理成功获取新闻: {len(pre_fetched_news)} 字符")
                    
                    # 直接基于预获取的新闻生成分析，跳过工具调用
                    enhanced_prompt = f"""
您是一位专业的财经新闻分析师。请基于以下已获取的最新新闻数据，对股票 {ticker} 进行详细分析：

=== 最新新闻数据 ===
{pre_fetched_news}

=== 分析要求 ===
{system_message}

请基于上述真实新闻数据撰写详细的中文分析报告。注意：新闻数据已经提供，您无需再调用任何工具。
"""
                    
                    logger.info(f"[新闻分析师] 🔄 使用预获取新闻数据直接生成分析...")
                    llm_start_time = datetime.now()
                    result = llm.invoke([{"role": "user", "content": enhanced_prompt}])
                    
                    llm_end_time = datetime.now()
                    llm_time_taken = (llm_end_time - llm_start_time).total_seconds()
                    logger.info(f"[新闻分析师] LLM调用完成（预处理模式），耗时: {llm_time_taken:.2f}秒")
                    
                    # 直接返回结果，跳过后续的工具调用检测
                    if hasattr(result, 'content') and result.content:
                        report = result.content
                        logger.info(f"[新闻分析师] ✅ 预处理模式成功，报告长度: {len(report)} 字符")
                        
                        # 跳转到最终处理
                        state["messages"].append(result)
                        end_time = datetime.now()
                        time_taken = (end_time - start_time).total_seconds()
                        logger.info(f"[新闻分析师] 新闻分析完成，总耗时: {time_taken:.2f}秒")
                        return {
                            "messages": [result],
                            "news_report": report,
                        }
                    
                else:
                    logger.warning(f"[新闻分析师] ⚠️ 预处理获取新闻失败，回退到标准模式")
                    
            except Exception as e:
                logger.error(f"[新闻分析师] ❌ 预处理失败: {e}，回退到标准模式")
        
        # 使用统一的Google工具调用处理器
        llm_start_time = datetime.now()
        chain = prompt | llm.bind_tools(tools)
        logger.info(f"[新闻分析师] 开始LLM调用，分析 {ticker} 的新闻")
        result = chain.invoke(state["messages"])
        
        llm_end_time = datetime.now()
        llm_time_taken = (llm_end_time - llm_start_time).total_seconds()
        logger.info(f"[新闻分析师] LLM调用完成，耗时: {llm_time_taken:.2f}秒")

        # 使用统一的Google工具调用处理器
        if GoogleToolCallHandler.is_google_model(llm):
            logger.info(f"📊 [新闻分析师] 检测到Google模型，使用统一工具调用处理器")
            
            # 创建分析提示词
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=company_name,
                analyst_type="新闻分析",
                specific_requirements="重点关注新闻事件对股价的影响、市场情绪变化、政策影响等。"
            )
            
            # 处理Google模型工具调用
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="新闻分析师"
            )
        else:
            # 非Google模型的处理逻辑
            logger.info(f"[新闻分析师] 非Google模型 ({llm.__class__.__name__})，使用标准处理逻辑")
            
            # 检查工具调用情况
            tool_call_count = len(result.tool_calls) if hasattr(result, 'tool_calls') else 0
            logger.info(f"[新闻分析师] LLM调用了 {tool_call_count} 个工具")
            
            if tool_call_count == 0:
                logger.warning(f"[新闻分析师] ⚠️ {llm.__class__.__name__} 没有调用任何工具，启动补救机制...")
                
                try:
                    # 强制获取新闻数据
                    logger.info(f"[新闻分析师] 🔧 强制调用统一新闻工具获取新闻数据...")
                    forced_news = unified_news_tool(stock_code=ticker, max_news=10, model_info="")
                    
                    if forced_news and len(forced_news.strip()) > 100:
                        logger.info(f"[新闻分析师] ✅ 强制获取新闻成功: {len(forced_news)} 字符")
                        
                        # 基于真实新闻数据重新生成分析
                        forced_prompt = f"""
您是一位专业的财经新闻分析师。请基于以下最新获取的新闻数据，对股票 {ticker} 进行详细的新闻分析：

=== 最新新闻数据 ===
{forced_news}

=== 分析要求 ===
{system_message}

请基于上述真实新闻数据撰写详细的中文分析报告。
"""
                        
                        logger.info(f"[新闻分析师] 🔄 基于强制获取的新闻数据重新生成完整分析...")
                        forced_result = llm.invoke([{"role": "user", "content": forced_prompt}])
                        
                        if hasattr(forced_result, 'content') and forced_result.content:
                            report = forced_result.content
                            logger.info(f"[新闻分析师] ✅ 强制补救成功，生成基于真实数据的报告，长度: {len(report)} 字符")
                        else:
                            logger.warning(f"[新闻分析师] ⚠️ 强制补救失败，使用原始结果")
                            report = result.content
                    else:
                        logger.warning(f"[新闻分析师] ⚠️ 统一新闻工具获取失败，使用原始结果")
                        report = result.content
                        
                except Exception as e:
                    logger.error(f"[新闻分析师] ❌ 强制补救过程失败: {e}")
                    report = result.content
            else:
                # 有工具调用，直接使用结果
                report = result.content
        
        total_time_taken = (datetime.now() - start_time).total_seconds()
        logger.info(f"[新闻分析师] 新闻分析完成，总耗时: {total_time_taken:.2f}秒")

        # 🔧 修复死循环问题：返回清洁的AIMessage，不包含tool_calls
        # 这确保工作流图能正确判断分析已完成，避免重复调用
        from langchain_core.messages import AIMessage
        clean_message = AIMessage(content=report)
        
        logger.info(f"[新闻分析师] ✅ 返回清洁消息，报告长度: {len(report)} 字符")

        return {
            "messages": [clean_message],
            "news_report": report,
        }

    return news_analyst_node
