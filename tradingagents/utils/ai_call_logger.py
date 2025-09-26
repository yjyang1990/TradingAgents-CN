#!/usr/bin/env python3
"""
AI调用详细日志记录器
专门用于记录AI模型调用的详细参数、返回结果等调试信息
"""

import json
import time
import functools
import hashlib
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
import traceback

from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.logging_manager import get_logger_manager

# AI调用专用日志器
ai_logger = get_logger("ai_calls")
logger_manager = get_logger_manager()


def truncate_text(text: str, max_length: int = 500) -> str:
    """安全地截断文本，避免日志过长"""
    if not text:
        return ""

    text_str = str(text)
    if len(text_str) <= max_length:
        return text_str

    return text_str[:max_length] + f"... (截断，总长度: {len(text_str)})"


def safe_json_dumps(obj: Any) -> str:
    """安全地序列化对象为JSON，处理不可序列化的对象"""
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    except Exception:
        return str(obj)


def extract_message_info(messages: List) -> Dict:
    """提取消息信息用于日志记录"""
    if not messages:
        return {"count": 0, "types": [], "total_chars": 0}

    msg_info = {
        "count": len(messages),
        "types": [],
        "total_chars": 0,
        "messages_preview": []
    }

    for i, msg in enumerate(messages):
        if hasattr(msg, '__class__'):
            msg_type = msg.__class__.__name__
        else:
            msg_type = type(msg).__name__

        msg_info["types"].append(msg_type)

        # 提取消息内容
        content = ""
        if hasattr(msg, 'content'):
            content = str(msg.content)
        elif isinstance(msg, dict) and 'content' in msg:
            content = str(msg['content'])
        elif isinstance(msg, str):
            content = msg

        msg_info["total_chars"] += len(content)

        # 添加前几条消息的预览（截断版本）
        if i < 3:
            msg_info["messages_preview"].append({
                "type": msg_type,
                "content": truncate_text(content, 200),
                "length": len(content)
            })

    return msg_info


def log_ai_call(
    provider: str,
    model: str = None,
    log_input: bool = True,
    log_output: bool = True,
    log_tokens: bool = True,
    debug_level: str = "INFO"
):
    """
    AI调用详细日志装饰器

    Args:
        provider: AI提供商名称（如：openai、deepseek、anthropic等）
        model: 模型名称，如果不提供则尝试从实例中获取
        log_input: 是否记录输入参数详情
        log_output: 是否记录输出结果详情
        log_tokens: 是否记录token使用情况
        debug_level: 日志级别（DEBUG、INFO、WARNING、ERROR）
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成调用ID用于追踪
            call_id = hashlib.md5(f"{time.time()}{func.__name__}".encode()).hexdigest()[:8]

            # 获取模型名称
            actual_model = model
            if not actual_model and args and hasattr(args[0], 'model_name'):
                actual_model = getattr(args[0], 'model_name', 'unknown')
            elif not actual_model and args and hasattr(args[0], 'model'):
                actual_model = getattr(args[0], 'model', 'unknown')

            start_time = time.time()

            # 记录调用开始
            call_info = {
                "call_id": call_id,
                "provider": provider,
                "model": actual_model or "unknown",
                "function": func.__name__,
                "start_time": datetime.now().isoformat(),
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }

            ai_logger.info(
                f"🤖 [AI调用开始] {provider}/{actual_model} - {func.__name__} [ID: {call_id}]",
                extra=call_info
            )

            # 记录详细输入参数（如果启用）
            if log_input:
                input_details = {}

                # 处理位置参数
                if args:
                    for i, arg in enumerate(args):
                        if i == 0:  # 通常是self实例，跳过
                            continue
                        elif hasattr(arg, '__iter__') and not isinstance(arg, str):
                            # 处理消息列表
                            try:
                                if hasattr(arg, '__len__') and len(arg) > 0:
                                    first_item = arg[0] if len(arg) > 0 else None
                                    if hasattr(first_item, 'content') or isinstance(first_item, dict):
                                        # 这看起来像消息列表
                                        input_details[f"messages"] = extract_message_info(arg)
                                    else:
                                        input_details[f"arg_{i}"] = {
                                            "type": type(arg).__name__,
                                            "length": len(arg),
                                            "preview": truncate_text(str(arg), 100)
                                        }
                                else:
                                    input_details[f"arg_{i}"] = truncate_text(str(arg), 100)
                            except Exception:
                                input_details[f"arg_{i}"] = f"<{type(arg).__name__}>"
                        else:
                            input_details[f"arg_{i}"] = truncate_text(str(arg), 100)

                # 处理关键字参数
                for key, value in kwargs.items():
                    if key in ['session_id', 'analysis_type', 'temperature', 'max_tokens']:
                        input_details[key] = value
                    else:
                        input_details[key] = truncate_text(str(value), 100)

                if input_details:
                    ai_logger.debug(
                        f"📝 [AI调用输入] [ID: {call_id}] 详细参数",
                        extra={
                            "call_id": call_id,
                            "event_type": "ai_input_details",
                            "input_details": input_details
                        }
                    )

            try:
                # 执行AI调用
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # 记录调用成功
                success_info = {
                    "call_id": call_id,
                    "provider": provider,
                    "model": actual_model or "unknown",
                    "function": func.__name__,
                    "duration": round(duration, 3),
                    "success": True,
                    "end_time": datetime.now().isoformat()
                }

                ai_logger.info(
                    f"✅ [AI调用成功] {provider}/{actual_model} - {func.__name__} [ID: {call_id}] (耗时: {duration:.2f}s)",
                    extra=success_info
                )

                # 记录详细输出结果（如果启用）
                if log_output and result is not None:
                    output_details = {}

                    # 分析返回结果的类型和内容
                    result_type = type(result).__name__
                    output_details["result_type"] = result_type

                    if hasattr(result, 'content'):
                        # LangChain AIMessage 类型
                        content = str(result.content)
                        output_details["content"] = truncate_text(content, 1000)
                        output_details["content_length"] = len(content)

                        # 记录附加信息
                        if hasattr(result, 'additional_kwargs'):
                            additional = result.additional_kwargs
                            if additional:
                                output_details["additional_kwargs"] = {
                                    key: truncate_text(str(value), 200)
                                    for key, value in additional.items()
                                }

                    elif hasattr(result, 'generations'):
                        # ChatResult 类型
                        output_details["generations_count"] = len(result.generations)
                        if result.generations:
                            first_gen = result.generations[0]
                            if hasattr(first_gen, 'message') and hasattr(first_gen.message, 'content'):
                                content = str(first_gen.message.content)
                                output_details["first_generation_content"] = truncate_text(content, 1000)
                                output_details["first_generation_length"] = len(content)

                        # 记录LLM输出信息（包含token使用）
                        if hasattr(result, 'llm_output') and result.llm_output:
                            llm_output = result.llm_output
                            output_details["llm_output"] = {}

                            # Token使用信息
                            if 'token_usage' in llm_output:
                                token_usage = llm_output['token_usage']
                                output_details["token_usage"] = {
                                    "prompt_tokens": token_usage.get('prompt_tokens', 0),
                                    "completion_tokens": token_usage.get('completion_tokens', 0),
                                    "total_tokens": token_usage.get('total_tokens', 0)
                                }

                            # 其他元信息
                            for key, value in llm_output.items():
                                if key != 'token_usage':
                                    output_details["llm_output"][key] = truncate_text(str(value), 200)

                    else:
                        # 其他类型的结果
                        result_str = str(result)
                        output_details["content"] = truncate_text(result_str, 1000)
                        output_details["content_length"] = len(result_str)

                    if output_details:
                        ai_logger.debug(
                            f"📤 [AI调用输出] [ID: {call_id}] 详细结果",
                            extra={
                                "call_id": call_id,
                                "event_type": "ai_output_details",
                                "output_details": output_details
                            }
                        )

                # 记录Token使用情况（如果启用且可用）
                if log_tokens:
                    token_info = extract_token_usage(result, args, kwargs)
                    if token_info:
                        ai_logger.info(
                            f"💰 [Token使用] [ID: {call_id}] 输入: {token_info.get('input_tokens', 0)}, "
                            f"输出: {token_info.get('output_tokens', 0)}, "
                            f"总计: {token_info.get('total_tokens', 0)}, "
                            f"成本: ¥{token_info.get('cost', 0.0):.6f}",
                            extra={
                                "call_id": call_id,
                                "event_type": "ai_token_usage",
                                **token_info
                            }
                        )

                return result

            except Exception as e:
                duration = time.time() - start_time

                # 记录调用失败
                error_info = {
                    "call_id": call_id,
                    "provider": provider,
                    "model": actual_model or "unknown",
                    "function": func.__name__,
                    "duration": round(duration, 3),
                    "success": False,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "end_time": datetime.now().isoformat()
                }

                ai_logger.error(
                    f"❌ [AI调用失败] {provider}/{actual_model} - {func.__name__} [ID: {call_id}] "
                    f"(耗时: {duration:.2f}s): {str(e)}",
                    extra=error_info,
                    exc_info=True
                )

                # 记录详细错误堆栈
                error_details = {
                    "call_id": call_id,
                    "event_type": "ai_error_details",
                    "traceback": traceback.format_exc(),
                    "error_args": [str(arg) for arg in e.args] if hasattr(e, 'args') else []
                }

                ai_logger.debug(
                    f"🔍 [AI调用错误详情] [ID: {call_id}]",
                    extra=error_details
                )

                # 重新抛出异常
                raise

        return wrapper
    return decorator


def extract_token_usage(result: Any, args: tuple, kwargs: dict) -> Optional[Dict]:
    """从结果中提取token使用信息"""
    token_info = {}

    # 从ChatResult中提取token使用
    if hasattr(result, 'llm_output') and result.llm_output:
        token_usage = result.llm_output.get('token_usage', {})
        if token_usage:
            token_info.update({
                "input_tokens": token_usage.get('prompt_tokens', 0),
                "output_tokens": token_usage.get('completion_tokens', 0),
                "total_tokens": token_usage.get('total_tokens', 0)
            })

    # 从kwargs中提取会话和分析类型信息
    token_info.update({
        "session_id": kwargs.get('session_id', 'unknown'),
        "analysis_type": kwargs.get('analysis_type', 'unknown')
    })

    # 如果有token tracker，尝试计算成本
    try:
        from tradingagents.config.config_manager import token_tracker
        if token_info.get('total_tokens', 0) > 0:
            # 这里可以根据provider和model计算成本
            # 暂时设为0，实际成本由token_tracker计算
            token_info["cost"] = 0.0
    except ImportError:
        pass

    return token_info if token_info else None


def log_model_invoke(provider: str, model: str = None):
    """专门用于model.invoke()调用的装饰器"""
    return log_ai_call(
        provider=provider,
        model=model,
        log_input=True,
        log_output=True,
        log_tokens=True,
        debug_level="INFO"
    )


def log_chat_completion(provider: str, model: str = None):
    """专门用于聊天完成调用的装饰器"""
    return log_ai_call(
        provider=provider,
        model=model,
        log_input=True,
        log_output=True,
        log_tokens=True,
        debug_level="INFO"
    )


def log_ai_debug():
    """调试模式的AI调用日志装饰器，记录所有详细信息"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 自动检测provider和model
            provider = "unknown"
            model = "unknown"

            if args and hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__
                if 'DeepSeek' in class_name:
                    provider = "deepseek"
                elif 'OpenAI' in class_name:
                    provider = "openai"
                elif 'Anthropic' in class_name:
                    provider = "anthropic"
                elif 'DashScope' in class_name:
                    provider = "dashscope"
                elif 'Google' in class_name:
                    provider = "google"

                if hasattr(args[0], 'model'):
                    model = args[0].model
                elif hasattr(args[0], 'model_name'):
                    model = args[0].model_name

            # 应用详细日志记录
            return log_ai_call(
                provider=provider,
                model=model,
                log_input=True,
                log_output=True,
                log_tokens=True,
                debug_level="DEBUG"
            )(func)(*args, **kwargs)

        return wrapper
    return decorator


# 便捷函数：记录AI调用摘要
def log_ai_call_summary(
    call_id: str,
    provider: str,
    model: str,
    function_name: str,
    success: bool,
    duration: float,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost: float = 0.0,
    **extra_info
):
    """记录AI调用摘要信息"""
    summary = {
        "call_id": call_id,
        "provider": provider,
        "model": model,
        "function": function_name,
        "success": success,
        "duration": duration,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cost": cost,
        "timestamp": datetime.now().isoformat(),
        **extra_info
    }

    status = "成功" if success else "失败"
    ai_logger.info(
        f"📊 [AI调用摘要] {provider}/{model} - {status} [ID: {call_id}]",
        extra=summary
    )