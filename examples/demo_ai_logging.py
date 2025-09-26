#!/usr/bin/env python3
"""
AI调用详细日志记录功能演示
展示新增的AI调用日志记录功能如何为调试工作提供帮助
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.utils.logging_init import get_logger

logger = get_logger("ai_logging_demo")


def demo_simple_analysis():
    """演示简单的股票分析，展示AI调用日志"""

    logger.info("🚀 [AI日志演示] 开始简单股票分析")

    # 检查环境变量
    if not os.getenv("DEEPSEEK_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️ [环境检查] 未找到AI API密钥，请设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY")
        return

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
        "memory_enabled": False,  # 关闭内存以简化演示
        "parallel_analysts": False
    }

    logger.info("🏗️ [TradingGraph] 创建TradingGraph实例（将自动启用AI调用日志）...")

    try:
        # 创建TradingGraph实例
        graph = TradingAgentsGraph(
            selected_analysts=["market"],  # 只使用市场分析师
            debug=True,
            config=config
        )

        logger.info("✅ [TradingGraph] 实例创建成功，AI调用日志已启用")

        # 执行一个简单的分析
        logger.info("📊 [分析开始] 分析股票 AAPL")
        logger.info("=" * 60)
        logger.info("⚠️ 注意观察下面的详细AI调用日志:")
        logger.info("- 🤖 [AI调用开始] 显示每次AI调用的开始")
        logger.info("- 📝 [AI调用输入] 显示输入参数详情")
        logger.info("- ✅ [AI调用成功] 显示调用成功和耗时")
        logger.info("- 📤 [AI调用输出] 显示返回结果详情")
        logger.info("- 💰 [Token使用] 显示token使用量和成本")
        logger.info("=" * 60)

        # 简单的状态用于测试
        test_state = {
            "messages": [],
            "company_of_interest": "AAPL",
            "debate_state": "invest",
            "current_date": "2024-01-15"
        }

        # 执行分析（这会触发AI调用和日志记录）
        result = graph.graph.invoke(test_state)

        logger.info("=" * 60)
        logger.info("✅ [分析完成] 分析结果已生成")
        logger.info(f"📋 [结果摘要] 生成了 {len(result.get('messages', []))} 条消息")

        # 显示最后一条消息的内容摘要
        if result.get('messages'):
            last_message = result['messages'][-1]
            content = getattr(last_message, 'content', str(last_message))[:200]
            logger.info(f"📄 [最后消息] {content}...")

        logger.info("🎯 [演示说明] 上面的日志显示了:")
        logger.info("  1. 每次AI调用的详细参数（输入消息、温度等）")
        logger.info("  2. AI调用的执行时间")
        logger.info("  3. 返回结果的详细信息")
        logger.info("  4. Token使用量统计")
        logger.info("  5. 调用成功/失败状态")

    except Exception as e:
        logger.error(f"❌ [演示失败] {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")


def demo_debugging_tips():
    """展示如何使用AI调用日志进行调试"""

    logger.info("🔍 [调试技巧] AI调用日志在调试中的应用")
    logger.info("=" * 60)

    tips = [
        "1. 📊 查看Token使用量 - 监控成本和效率",
        "2. ⏱️ 分析调用耗时 - 识别性能瓶颈",
        "3. 📝 检查输入参数 - 确保传递了正确的数据",
        "4. 📤 验证输出结果 - 检查AI响应是否符合预期",
        "5. 🔄 追踪调用顺序 - 了解AI调用的执行流程",
        "6. 🆔 使用调用ID - 关联相关的日志条目",
        "7. ❌ 错误诊断 - 快速定位失败的AI调用",
        "8. 📈 性能优化 - 根据统计数据优化参数"
    ]

    for tip in tips:
        logger.info(f"  {tip}")

    logger.info("=" * 60)
    logger.info("💡 [使用建议]")
    logger.info("  - 开发阶段：启用详细日志(log_input=True, log_output=True)")
    logger.info("  - 生产环境：只记录关键信息(log_tokens=True)")
    logger.info("  - 调试模式：使用 @log_ai_debug() 装饰器")
    logger.info("  - 日志级别：设置 DEBUG 级别查看所有详细信息")


if __name__ == "__main__":
    logger.info("🎬 [演示开始] AI调用详细日志记录功能演示")

    # 显示调试技巧
    demo_debugging_tips()

    logger.info("\n" + "=" * 80)
    logger.info("🧪 [实际演示] 现在运行真实的AI调用来展示日志效果")
    logger.info("=" * 80)

    # 运行实际演示
    demo_simple_analysis()

    logger.info("\n" + "=" * 80)
    logger.info("🎉 [演示完成] AI调用日志记录功能演示结束")
    logger.info("💡 查看上面的日志输出，了解AI调用的详细过程")
    logger.info("=" * 80)