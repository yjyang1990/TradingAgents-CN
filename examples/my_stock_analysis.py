#!/usr/bin/env python3
"""
个人股票分析脚本
根据您的需求自定义分析参数
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('default')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from tradingagents.llm_adapters import ChatDashScope
from langchain_core.messages import HumanMessage, SystemMessage

# 加载环境变量
load_dotenv()

def analyze_my_stock():
    """分析您感兴趣的股票"""

    # 从环境变量或配置文件获取股票分析配置
    STOCK_SYMBOL = os.getenv("STOCK_SYMBOL", "NVDA")  # 可通过环境变量设置
    ANALYSIS_FOCUS = os.getenv("ANALYSIS_FOCUS", "AI芯片和数据中心业务前景")

    # 模型配置，支持环境变量覆盖
    model_name = os.getenv("ANALYSIS_MODEL", "qwen-plus-latest")
    temperature = float(os.getenv("ANALYSIS_TEMPERATURE", "0.1"))
    max_tokens = int(os.getenv("ANALYSIS_MAX_TOKENS", "4000"))

    logger.info(f"🚀 开始分析股票: {STOCK_SYMBOL}")
    logger.info(f"🎯 分析重点: {ANALYSIS_FOCUS}")
    logger.info(f"🤖 使用模型: {model_name}")
    logger.info("=" * 60)

    # 检查API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error("❌ 请设置 DASHSCOPE_API_KEY 环境变量")
        logger.info("💡 提示: export DASHSCOPE_API_KEY=your_api_key")
        return

    try:
        # 初始化模型（支持配置）
        llm = ChatDashScope(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 构建分析提示
        system_prompt = """
你是一位专业的股票分析师，具有丰富的投资经验。
请提供客观、详细、实用的股票分析报告。
分析应该包含具体数据、清晰逻辑和可操作建议。
"""
        
        analysis_prompt = f"""
请对股票 {STOCK_SYMBOL} 进行全面的投资分析，特别关注{ANALYSIS_FOCUS}。

请从以下角度进行分析：

1. **公司基本面分析**
   - 最新财务数据（营收、利润、现金流）
   - 核心业务表现和增长趋势
   - 竞争优势和护城河

2. **技术面分析**
   - 当前股价走势和趋势判断
   - 关键技术指标（MA、RSI、MACD等）
   - 重要支撑位和阻力位

3. **行业和市场分析**
   - 行业发展趋势和市场机会
   - 主要竞争对手比较
   - 市场地位和份额变化

4. **风险评估**
   - 主要风险因素识别
   - 宏观经济影响
   - 行业特定风险

5. **投资建议**
   - 投资评级（买入/持有/卖出）
   - 目标价位和时间框架
   - 适合的投资者类型
   - 仓位管理建议

请用中文撰写，提供具体的数据和分析依据。
"""
        
        # 生成分析
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=analysis_prompt)
        ]
        
        logger.info(f"⏳ 正在生成分析报告...")
        response = llm.invoke(messages)
        
        logger.info(f"\n📊 {STOCK_SYMBOL} 投资分析报告:")
        logger.info(f"=" * 60)
        logger.info(f"\n{response.content}")
        logger.info(f"=" * 60)
        
        # 保存报告
        filename = f"{STOCK_SYMBOL}_analysis_report.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"股票代码: {STOCK_SYMBOL}\n")
            f.write(f"分析重点: {ANALYSIS_FOCUS}\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n")
            f.write(response.content)
        
        logger.info(f"✅ 分析报告已保存到: {filename}")
        
    except ImportError as e:
        logger.error(f"❌ 模块导入失败: {e}")
        logger.info("💡 请检查是否正确安装了所需依赖")
    except ConnectionError as e:
        logger.error(f"❌ 网络连接失败: {e}")
        logger.info("💡 请检查网络连接和API端点配置")
    except KeyError as e:
        logger.error(f"❌ API响应格式异常: {e}")
        logger.info("💡 请检查API密钥和模型名称是否正确")
    except ValueError as e:
        logger.error(f"❌ 参数错误: {e}")
        logger.info("💡 请检查模型参数配置")
    except OSError as e:
        logger.error(f"❌ 文件操作失败: {e}")
        logger.info("💡 请检查文件权限和磁盘空间")

if __name__ == "__main__":
    analyze_my_stock()
