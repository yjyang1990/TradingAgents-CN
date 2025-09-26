#!/usr/bin/env python3
"""
LLM适配器增强器
为现有的LLM适配器动态添加详细的AI调用日志记录功能
"""

import functools
import inspect
from typing import Any, Callable, Type, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from tradingagents.utils.ai_call_logger import log_ai_call, log_ai_debug
from tradingagents.utils.logging_init import get_logger

logger = get_logger("llm_enhancer")


def enhance_llm_with_logging(
    llm_instance: Any,
    provider: str,
    model: str = None,
    enable_detailed_logging: bool = True
) -> Any:
    """
    为LLM实例动态添加详细的AI调用日志记录

    Args:
        llm_instance: LLM实例
        provider: 提供商名称
        model: 模型名称
        enable_detailed_logging: 是否启用详细日志记录

    Returns:
        增强后的LLM实例
    """

    # 获取模型名称
    actual_model = model
    if not actual_model and hasattr(llm_instance, 'model'):
        actual_model = llm_instance.model
    elif not actual_model and hasattr(llm_instance, 'model_name'):
        actual_model = llm_instance.model_name

    logger.info(f"🔧 [LLM增强器] 为 {provider}/{actual_model} 添加详细日志记录")

    # 增强 _generate 方法
    if hasattr(llm_instance, '_generate') and callable(getattr(llm_instance, '_generate')):
        original_generate = getattr(llm_instance, '_generate')

        # 如果还没有被装饰过
        if not hasattr(original_generate, '_ai_logging_enhanced'):
            if enable_detailed_logging:
                enhanced_generate = log_ai_call(
                    provider=provider,
                    model=actual_model,
                    log_input=True,
                    log_output=True,
                    log_tokens=True
                )(original_generate)
            else:
                enhanced_generate = log_ai_call(
                    provider=provider,
                    model=actual_model,
                    log_input=False,
                    log_output=False,
                    log_tokens=True
                )(original_generate)

            enhanced_generate._ai_logging_enhanced = True
            setattr(llm_instance, '_generate', enhanced_generate)
            logger.debug(f"✅ [LLM增强器] {provider}/{actual_model} _generate方法已增强")

    # 增强 invoke 方法 - 使用更安全的方式处理Pydantic模型
    if hasattr(llm_instance, 'invoke') and callable(getattr(llm_instance, 'invoke')):
        original_invoke = getattr(llm_instance, 'invoke')

        # 如果还没有被装饰过
        if not hasattr(original_invoke, '_ai_logging_enhanced'):
            if enable_detailed_logging:
                enhanced_invoke = log_ai_call(
                    provider=provider,
                    model=actual_model,
                    log_input=True,
                    log_output=True,
                    log_tokens=True
                )(original_invoke)
            else:
                enhanced_invoke = log_ai_call(
                    provider=provider,
                    model=actual_model,
                    log_input=False,
                    log_output=False,
                    log_tokens=True
                )(original_invoke)

            enhanced_invoke._ai_logging_enhanced = True

            # 使用更安全的方式设置方法，处理Pydantic模型的限制
            try:
                # 尝试直接设置
                setattr(llm_instance, 'invoke', enhanced_invoke)
                logger.debug(f"✅ [LLM增强器] {provider}/{actual_model} invoke方法已增强")
            except (ValueError, AttributeError) as e:
                # 如果是Pydantic模型，尝试使用__dict__直接设置
                if hasattr(llm_instance, '__dict__'):
                    llm_instance.__dict__['invoke'] = enhanced_invoke
                    logger.debug(f"✅ [LLM增强器] {provider}/{actual_model} invoke方法已增强 (使用__dict__)")
                else:
                    logger.warning(f"⚠️ [LLM增强器] 无法增强 {provider}/{actual_model} invoke方法: {e}")
                    # 不阻止继续处理其他方法

    # 增强 generate 方法（如果存在）
    if hasattr(llm_instance, 'generate') and callable(getattr(llm_instance, 'generate')):
        original_generate_method = getattr(llm_instance, 'generate')

        if not hasattr(original_generate_method, '_ai_logging_enhanced'):
            if enable_detailed_logging:
                enhanced_generate_method = log_ai_call(
                    provider=provider,
                    model=actual_model,
                    log_input=True,
                    log_output=True,
                    log_tokens=True
                )(original_generate_method)
            else:
                enhanced_generate_method = log_ai_call(
                    provider=provider,
                    model=actual_model,
                    log_input=False,
                    log_output=False,
                    log_tokens=True
                )(original_generate_method)

            enhanced_generate_method._ai_logging_enhanced = True

            # 使用更安全的方式设置方法
            try:
                setattr(llm_instance, 'generate', enhanced_generate_method)
                logger.debug(f"✅ [LLM增强器] {provider}/{actual_model} generate方法已增强")
            except (ValueError, AttributeError) as e:
                if hasattr(llm_instance, '__dict__'):
                    llm_instance.__dict__['generate'] = enhanced_generate_method
                    logger.debug(f"✅ [LLM增强器] {provider}/{actual_model} generate方法已增强 (使用__dict__)")
                else:
                    logger.warning(f"⚠️ [LLM增强器] 无法增强 {provider}/{actual_model} generate方法: {e}")

    # 为实例添加增强标记 - 使用更安全的方式
    try:
        llm_instance._ai_logging_enhanced = True
        llm_instance._enhanced_provider = provider
        llm_instance._enhanced_model = actual_model
    except (ValueError, AttributeError):
        # 对于Pydantic模型，使用__dict__
        if hasattr(llm_instance, '__dict__'):
            llm_instance.__dict__['_ai_logging_enhanced'] = True
            llm_instance.__dict__['_enhanced_provider'] = provider
            llm_instance.__dict__['_enhanced_model'] = actual_model

    return llm_instance


def enhance_openai_llm(llm_instance: ChatOpenAI, enable_detailed_logging: bool = True) -> ChatOpenAI:
    """为OpenAI LLM实例添加详细日志记录"""
    return enhance_llm_with_logging(
        llm_instance=llm_instance,
        provider="openai",
        enable_detailed_logging=enable_detailed_logging
    )


def enhance_anthropic_llm(llm_instance: ChatAnthropic, enable_detailed_logging: bool = True) -> ChatAnthropic:
    """为Anthropic LLM实例添加详细日志记录"""
    return enhance_llm_with_logging(
        llm_instance=llm_instance,
        provider="anthropic",
        enable_detailed_logging=enable_detailed_logging
    )


def enhance_all_llm_methods(llm_instance: Any, provider: str) -> Any:
    """
    使用调试模式增强LLM实例的所有相关方法
    自动检测并装饰所有AI调用相关的方法
    """

    logger.info(f"🔍 [LLM全面增强] 开始为 {provider} LLM实例添加调试日志")

    # 需要增强的方法列表
    methods_to_enhance = [
        '_generate', 'invoke', 'generate', 'chat', '_chat',
        'predict', '_predict', 'call', '_call', 'stream',
        '_stream', 'agenerate', '_agenerate', 'ainvoke'
    ]

    enhanced_count = 0

    for method_name in methods_to_enhance:
        if hasattr(llm_instance, method_name):
            method = getattr(llm_instance, method_name)
            if callable(method) and not hasattr(method, '_ai_logging_enhanced'):
                # 使用调试模式装饰器
                enhanced_method = log_ai_debug()(method)
                enhanced_method._ai_logging_enhanced = True
                setattr(llm_instance, method_name, enhanced_method)
                enhanced_count += 1
                logger.debug(f"✅ [LLM全面增强] {provider} {method_name}方法已增强")

    if enhanced_count > 0:
        logger.info(f"🎯 [LLM全面增强] 已为 {provider} LLM实例增强 {enhanced_count} 个方法")
        llm_instance._ai_debug_enhanced = True
    else:
        logger.warning(f"⚠️ [LLM全面增强] 未找到可增强的方法 for {provider}")

    return llm_instance


def create_enhanced_llm_factory(
    original_llm_class: Type,
    provider: str,
    enable_auto_enhancement: bool = True
):
    """
    创建自动增强的LLM工厂类

    Args:
        original_llm_class: 原始LLM类
        provider: 提供商名称
        enable_auto_enhancement: 是否启用自动增强

    Returns:
        增强后的LLM工厂类
    """

    class EnhancedLLM(original_llm_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            if enable_auto_enhancement:
                logger.info(f"🏭 [LLM工厂] 自动增强 {provider} LLM实例")
                enhance_llm_with_logging(
                    llm_instance=self,
                    provider=provider,
                    enable_detailed_logging=True
                )

    EnhancedLLM.__name__ = f"Enhanced{original_llm_class.__name__}"
    EnhancedLLM.__qualname__ = f"Enhanced{original_llm_class.__name__}"

    return EnhancedLLM


# 便捷函数：批量增强LLM实例
def batch_enhance_llms(llm_instances: dict, enable_detailed_logging: bool = True) -> dict:
    """
    批量增强多个LLM实例

    Args:
        llm_instances: LLM实例字典，格式: {"provider_name": llm_instance}
        enable_detailed_logging: 是否启用详细日志记录

    Returns:
        增强后的LLM实例字典
    """

    enhanced_instances = {}

    for provider, llm_instance in llm_instances.items():
        logger.info(f"🔄 [批量增强] 正在增强 {provider} LLM实例")

        try:
            enhanced_instance = enhance_llm_with_logging(
                llm_instance=llm_instance,
                provider=provider,
                enable_detailed_logging=enable_detailed_logging
            )
            enhanced_instances[provider] = enhanced_instance
            logger.info(f"✅ [批量增强] {provider} LLM实例增强成功")

        except Exception as e:
            logger.error(f"❌ [批量增强] {provider} LLM实例增强失败: {e}")
            enhanced_instances[provider] = llm_instance  # 使用原始实例

    logger.info(f"🎯 [批量增强] 完成，共增强 {len(enhanced_instances)} 个LLM实例")
    return enhanced_instances


def is_llm_enhanced(llm_instance: Any) -> bool:
    """检查LLM实例是否已被增强"""
    return hasattr(llm_instance, '_ai_logging_enhanced') and llm_instance._ai_logging_enhanced


def get_llm_enhancement_info(llm_instance: Any) -> dict:
    """获取LLM实例的增强信息"""
    if not is_llm_enhanced(llm_instance):
        return {"enhanced": False}

    return {
        "enhanced": True,
        "provider": getattr(llm_instance, '_enhanced_provider', 'unknown'),
        "model": getattr(llm_instance, '_enhanced_model', 'unknown'),
        "debug_enhanced": getattr(llm_instance, '_ai_debug_enhanced', False)
    }