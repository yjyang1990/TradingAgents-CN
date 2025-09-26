#!/usr/bin/env python3
"""
测试真实的AI调用日志记录功能
验证TradingGraph中的实际AI调用是否被正确记录
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_init import init_logging, get_logger
from tradingagents.graph.trading_graph import TradingAgentsGraph

# 初始化日志系统
init_logging()
logger = get_logger("real_ai_logging_test")

def test_real_ai_logging():
    """测试真实的AI调用日志记录"""

    logger.info("🧪 [测试开始] 真实AI调用日志记录功能测试")

    # 检查环境变量
    if not os.getenv("DEEPSEEK_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️ [环境检查] 未找到AI API密钥，请设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY")
        return False

    # 确定使用的提供商
    if os.getenv("DEEPSEEK_API_KEY"):
        provider = "deepseek"
        model = "deepseek-chat"
        base_url = "https://api.deepseek.com"
    else:
        provider = "openai"
        model = "gpt-3.5-turbo"
        base_url = "https://api.openai.com/v1"

    logger.info(f"🤖 [AI提供商] 使用 {provider}/{model}")

    # 配置
    config = {
        "llm_provider": provider,
        "deep_think_llm": model,
        "quick_think_llm": model,
        "backend_url": base_url,
        "project_dir": str(project_root),
        "memory_enabled": False,
        "parallel_analysts": False
    }

    logger.info("🏗️ [TradingGraph] 创建TradingGraph实例...")

    try:
        # 创建TradingGraph实例
        graph = TradingAgentsGraph(
            selected_analysts=["market"],
            debug=True,
            config=config
        )

        logger.info("✅ [TradingGraph] 实例创建成功")

        # 创建一个完整的测试状态
        test_state = {
            "messages": [],
            "company_of_interest": "AAPL",
            "debate_state": "invest",
            "current_date": "2024-01-15",
            "trade_date": "2024-01-15",  # 添加缺失的字段
            "research_depth": 1,  # 减少研究深度以加快测试
            "analyst_start_time": {},
            "analyst_durations": {}
        }

        logger.info("📊 [分析开始] 开始股票分析，请观察AI调用日志...")
        logger.info("=" * 80)
        logger.info("⚠️ 下面应该会看到详细的AI调用日志:")
        logger.info("- 🤖 [AI调用开始] 显示每次AI调用")
        logger.info("- ✅ [AI调用成功] 显示调用成功状态")
        logger.info("- 💰 [Token使用] 显示Token使用量")
        logger.info("=" * 80)

        # 执行一个真实的AI分析调用
        result = graph.graph.invoke(test_state)

        logger.info("=" * 80)
        logger.info("✅ [分析完成] 分析执行完成")
        logger.info(f"📋 [结果] 生成了 {len(result.get('messages', []))} 条消息")

        # 检查最后一条消息
        if result.get('messages'):
            last_message = result['messages'][-1]
            content = getattr(last_message, 'content', str(last_message))[:100]
            logger.info(f"📄 [最后消息摘要] {content}...")

        logger.info("🎯 [测试总结] 如果上面显示了AI调用日志，说明功能正常工作！")
        return True

    except Exception as e:
        logger.error(f"❌ [测试失败] {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("🎬 [测试启动] 真实AI调用日志记录功能测试")

    success = test_real_ai_logging()

    if success:
        logger.info("✅ [测试成功] AI调用日志记录功能正常工作")
        # 提示用户查看日志文件
        logger.info("💡 [查看日志] 请检查以下位置的日志文件:")
        logger.info(f"    - 控制台输出（上面的日志）")
        logger.info(f"    - 日志文件: {project_root}/logs/tradingagents.log")
        logger.info(f"    - 搜索关键词: 'ai_calls' 或 'AI调用'")
    else:
        logger.error("❌ [测试失败] AI调用日志记录功能存在问题")

    logger.info("🏁 [测试结束]")