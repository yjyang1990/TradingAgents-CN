#!/usr/bin/env python3
"""
AI调用日志记录功能测试脚本
测试新增的AI调用详细日志记录功能是否正常工作
"""

import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.ai_call_logger import log_ai_call, log_ai_debug
from tradingagents.utils.llm_enhancer import enhance_llm_with_logging
from tradingagents.utils.logging_init import get_logger

# 设置日志
logger = get_logger("ai_logging_test")

def test_ai_call_decorator():
    """测试AI调用装饰器"""

    logger.info("🧪 [测试开始] AI调用装饰器基础功能测试")

    @log_ai_call(provider="test", model="test-model", log_input=True, log_output=True)
    def mock_ai_call(messages, temperature=0.1, **kwargs):
        """模拟AI调用"""
        logger.info(f"📝 [模拟AI调用] 收到 {len(messages)} 条消息，温度：{temperature}")

        # 模拟处理时间
        import time
        time.sleep(0.1)

        # 模拟返回结果
        class MockResponse:
            def __init__(self, content):
                self.content = content
                self.additional_kwargs = {}

        return MockResponse("这是一个测试AI响应")

    # 测试调用
    test_messages = [
        {"content": "你好，这是一个测试消息"},
        {"content": "请分析一下股票AAPL"}
    ]

    try:
        result = mock_ai_call(
            messages=test_messages,
            temperature=0.2,
            session_id="test_session_001",
            analysis_type="test_analysis"
        )

        logger.info(f"✅ [测试成功] AI调用装饰器测试通过，返回结果：{result.content[:50]}...")
        return True

    except Exception as e:
        logger.error(f"❌ [测试失败] AI调用装饰器测试失败：{e}")
        return False


def test_mock_llm_enhancement():
    """测试LLM增强器功能（使用模拟LLM）"""

    logger.info("🧪 [测试开始] LLM增强器功能测试")

    class MockLLM:
        def __init__(self, model="mock-model"):
            self.model = model
            self.model_name = model

        def _generate(self, messages, **kwargs):
            """模拟_generate方法"""
            logger.info(f"📝 [模拟LLM] _generate被调用，消息数量：{len(messages)}")

            class MockChatResult:
                def __init__(self):
                    self.generations = [self.MockGeneration()]
                    self.llm_output = {
                        'token_usage': {
                            'prompt_tokens': 50,
                            'completion_tokens': 30,
                            'total_tokens': 80
                        }
                    }

                class MockGeneration:
                    def __init__(self):
                        self.message = self.MockMessage()

                    class MockMessage:
                        def __init__(self):
                            self.content = "这是模拟的AI响应内容，用于测试日志记录功能。"

            return MockChatResult()

        def invoke(self, input_data, **kwargs):
            """模拟invoke方法"""
            logger.info(f"📝 [模拟LLM] invoke被调用，输入类型：{type(input_data)}")

            class MockAIMessage:
                def __init__(self, content):
                    self.content = content
                    self.additional_kwargs = {}

            return MockAIMessage("模拟的invoke响应")

    try:
        # 创建模拟LLM实例
        mock_llm = MockLLM("test-mock-model")

        # 使用增强器增强模拟LLM
        enhanced_llm = enhance_llm_with_logging(
            llm_instance=mock_llm,
            provider="mock",
            model="test-mock-model",
            enable_detailed_logging=True
        )

        # 测试_generate方法
        test_messages = [
            {"content": "测试消息1"},
            {"content": "测试消息2"}
        ]

        result1 = enhanced_llm._generate(
            messages=test_messages,
            session_id="test_session_002",
            analysis_type="mock_test"
        )

        logger.info(f"✅ [测试成功] _generate方法增强测试通过")

        # 测试invoke方法
        result2 = enhanced_llm.invoke(
            input_data="测试invoke调用",
            session_id="test_session_003",
            analysis_type="mock_invoke_test"
        )

        logger.info(f"✅ [测试成功] invoke方法增强测试通过，结果：{result2.content[:30]}...")

        return True

    except Exception as e:
        logger.error(f"❌ [测试失败] LLM增强器测试失败：{e}")
        import traceback
        logger.error(f"详细错误：{traceback.format_exc()}")
        return False


def test_debug_decorator():
    """测试调试模式装饰器"""

    logger.info("🧪 [测试开始] 调试模式装饰器测试")

    @log_ai_debug()
    def mock_complex_ai_call(*args, **kwargs):
        """模拟复杂的AI调用"""
        logger.info(f"📝 [模拟复杂AI调用] 参数：{len(args)} 个位置参数，{len(kwargs)} 个关键字参数")

        # 模拟处理
        import time
        time.sleep(0.05)

        return {
            "status": "success",
            "data": "这是复杂AI调用的返回结果",
            "metadata": {
                "processing_time": "0.05s",
                "tokens_used": 75
            }
        }

    try:
        result = mock_complex_ai_call(
            "参数1", "参数2",
            temperature=0.3,
            max_tokens=100,
            session_id="debug_test_001"
        )

        logger.info(f"✅ [测试成功] 调试装饰器测试通过，状态：{result['status']}")
        return True

    except Exception as e:
        logger.error(f"❌ [测试失败] 调试装饰器测试失败：{e}")
        return False


def test_real_trading_graph():
    """测试真实的TradingGraph AI日志记录（如果环境允许）"""

    logger.info("🧪 [测试开始] 真实TradingGraph AI日志记录测试")

    try:
        # 检查是否有必要的环境变量
        required_env_vars = ["DEEPSEEK_API_KEY", "OPENAI_API_KEY"]
        available_providers = []

        for env_var in required_env_vars:
            if os.getenv(env_var):
                if env_var == "DEEPSEEK_API_KEY":
                    available_providers.append("deepseek")
                elif env_var == "OPENAI_API_KEY":
                    available_providers.append("openai")

        if not available_providers:
            logger.warning("⚠️ [测试跳过] 没有可用的AI提供商API密钥，跳过真实TradingGraph测试")
            return True

        logger.info(f"🔑 [环境检查] 可用的AI提供商：{available_providers}")

        # 使用第一个可用的提供商进行测试
        provider = available_providers[0]

        # 导入TradingGraph
        from tradingagents.graph.trading_graph import TradingAgentsGraph

        # 配置
        test_config = {
            "llm_provider": provider,
            "deep_think_llm": "deepseek-chat" if provider == "deepseek" else "gpt-3.5-turbo",
            "quick_think_llm": "deepseek-chat" if provider == "deepseek" else "gpt-3.5-turbo",
            "backend_url": "https://api.deepseek.com" if provider == "deepseek" else "https://api.openai.com/v1",
            "project_dir": str(project_root),
            "memory_enabled": False,  # 关闭内存以简化测试
            "parallel_analysts": False
        }

        logger.info(f"🏗️ [TradingGraph] 创建 {provider} TradingGraph实例...")

        # 创建TradingGraph实例
        graph = TradingAgentsGraph(
            selected_analysts=["market"],  # 只使用一个分析师简化测试
            debug=True,
            config=test_config
        )

        logger.info(f"✅ [测试成功] TradingGraph实例创建成功，AI日志增强已应用")

        # 可以在这里添加简单的AI调用测试
        # 但为了避免产生实际的API费用，我们只测试实例化

        return True

    except Exception as e:
        logger.error(f"❌ [测试失败] 真实TradingGraph测试失败：{e}")
        import traceback
        logger.error(f"详细错误：{traceback.format_exc()}")
        return False


def run_all_tests():
    """运行所有测试"""

    logger.info("🚀 [测试套件开始] AI调用日志记录功能完整测试")
    logger.info("=" * 60)

    tests = [
        ("AI调用装饰器基础功能", test_ai_call_decorator),
        ("LLM增强器功能", test_mock_llm_enhancement),
        ("调试模式装饰器", test_debug_decorator),
        ("真实TradingGraph集成", test_real_trading_graph)
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n📋 [执行测试] {test_name}")
        logger.info("-" * 40)

        try:
            if test_func():
                logger.info(f"✅ [测试通过] {test_name}")
                passed_tests += 1
            else:
                logger.error(f"❌ [测试失败] {test_name}")
        except Exception as e:
            logger.error(f"❌ [测试异常] {test_name}：{e}")

    logger.info("=" * 60)
    logger.info(f"🏁 [测试结果] 通过 {passed_tests}/{total_tests} 个测试")

    if passed_tests == total_tests:
        logger.info("🎉 [所有测试通过] AI调用日志记录功能测试完成！")
        return True
    else:
        logger.warning(f"⚠️ [部分测试失败] 有 {total_tests - passed_tests} 个测试失败")
        return False


if __name__ == "__main__":
    logger.info("🧪 [测试启动] AI调用日志记录功能测试脚本")
    logger.info(f"⏰ [测试时间] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📁 [项目路径] {project_root}")

    success = run_all_tests()

    if success:
        logger.info("✅ [测试完成] 所有测试成功完成")
        sys.exit(0)
    else:
        logger.error("❌ [测试失败] 部分或全部测试失败")
        sys.exit(1)