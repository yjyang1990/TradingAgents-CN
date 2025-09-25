"""
增强错误处理和重试机制

为市场数据提供器提供统一的错误处理、重试策略和故障恢复机制
- 智能重试策略（指数退避、抖动）
- 熔断器模式
- 降级策略
- 错误监控和报告
- 异步错误处理
"""

import time
import random
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, Type
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps
from enum import Enum
import traceback
import json

try:
    from tradingagents.utils.logging_manager import get_logger
    logger = get_logger('error_handling')
except ImportError:
    logger = None


class RetryStrategy(Enum):
    """重试策略"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIBONACCI_BACKOFF = "fibonacci_backoff"


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    backoff_multiplier: float = 2.0
    retriable_exceptions: List[Type[Exception]] = field(default_factory=lambda: [
        ConnectionError, TimeoutError, ValueError
    ])


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5  # 失败阈值
    recovery_timeout: int = 60  # 恢复超时（秒）
    expected_exception: Type[Exception] = Exception
    min_requests: int = 10  # 最小请求数才开启熔断


@dataclass
class ErrorRecord:
    """错误记录"""
    timestamp: datetime
    error_type: str
    error_message: str
    function_name: str
    stack_trace: str
    retry_count: int = 0
    resolved: bool = False


class CircuitBreaker:
    """熔断器实现"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.request_count = 0
        self.last_failure_time = None
        self._lock = threading.RLock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """通过熔断器调用函数"""
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    if logger:
                        logger.info(f"熔断器半开: {func.__name__}")
                else:
                    raise Exception(f"熔断器开启，拒绝调用: {func.__name__}")

            self.request_count += 1

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except self.config.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置熔断器"""
        if self.last_failure_time is None:
            return True

        return (datetime.now() - self.last_failure_time).total_seconds() >= self.config.recovery_timeout

    def _on_success(self):
        """成功时的处理"""
        with self._lock:
            self.success_count += 1
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                if logger:
                    logger.info("熔断器已关闭，恢复正常")

    def _on_failure(self):
        """失败时的处理"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.request_count >= self.config.min_requests:
                if self.state == CircuitBreakerState.HALF_OPEN:
                    self.state = CircuitBreakerState.OPEN
                    if logger:
                        logger.warning("熔断器在半开状态下再次失败，重新开启")
                elif (self.state == CircuitBreakerState.CLOSED and
                      self.failure_count >= self.config.failure_threshold):
                    self.state = CircuitBreakerState.OPEN
                    if logger:
                        logger.warning(f"熔断器开启，失败次数: {self.failure_count}")

    def get_state(self) -> Dict[str, Any]:
        """获取熔断器状态"""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'request_count': self.request_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class ErrorMonitor:
    """错误监控器"""

    def __init__(self, max_records: int = 1000):
        self.max_records = max_records
        self.error_records: deque = deque(maxlen=max_records)
        self.error_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._lock = threading.RLock()

    def record_error(self, func_name: str, error: Exception, retry_count: int = 0):
        """记录错误"""
        with self._lock:
            error_record = ErrorRecord(
                timestamp=datetime.now(),
                error_type=type(error).__name__,
                error_message=str(error),
                function_name=func_name,
                stack_trace=traceback.format_exc(),
                retry_count=retry_count
            )

            self.error_records.append(error_record)

            # 更新统计
            self.error_stats[func_name][error_record.error_type] += 1

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误摘要"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._lock:
            recent_errors = [
                record for record in self.error_records
                if record.timestamp > cutoff_time
            ]

            # 按功能分组统计
            function_errors = defaultdict(lambda: defaultdict(int))
            for record in recent_errors:
                function_errors[record.function_name][record.error_type] += 1

            # 按时间分组统计
            hourly_errors = defaultdict(int)
            for record in recent_errors:
                hour_key = record.timestamp.strftime('%Y-%m-%d %H:00')
                hourly_errors[hour_key] += 1

            return {
                'total_errors': len(recent_errors),
                'unique_functions': len(function_errors),
                'function_errors': dict(function_errors),
                'hourly_distribution': dict(hourly_errors),
                'most_common_errors': self._get_most_common_errors(recent_errors),
                'report_period_hours': hours,
                'report_time': datetime.now().isoformat()
            }

    def _get_most_common_errors(self, error_records: List[ErrorRecord], limit: int = 5) -> List[Dict[str, Any]]:
        """获取最常见的错误"""
        error_counts = defaultdict(int)
        for record in error_records:
            key = f"{record.function_name}:{record.error_type}"
            error_counts[key] += 1

        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

        return [
            {'error_key': key, 'count': count}
            for key, count in sorted_errors
        ]


class EnhancedRetryHandler:
    """增强重试处理器"""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_monitor = ErrorMonitor()
        self._lock = threading.RLock()

    def _get_circuit_breaker(self, func_name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """获取或创建熔断器"""
        if func_name not in self.circuit_breakers:
            with self._lock:
                if func_name not in self.circuit_breakers:
                    self.circuit_breakers[func_name] = CircuitBreaker(config)
        return self.circuit_breakers[func_name]

    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """计算重试延迟"""
        if config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay

        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** (attempt - 1))

        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * attempt

        elif config.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            fib_sequence = self._fibonacci_sequence(attempt + 1)
            delay = config.base_delay * fib_sequence[attempt]

        else:
            delay = config.base_delay

        # 应用最大延迟限制
        delay = min(delay, config.max_delay)

        # 添加抖动
        if config.jitter:
            delay = delay * (0.5 + random.random() * 0.5)

        return delay

    def _fibonacci_sequence(self, n: int) -> List[int]:
        """生成斐波那契数列"""
        if n <= 0:
            return []
        elif n == 1:
            return [1]
        elif n == 2:
            return [1, 1]

        sequence = [1, 1]
        for i in range(2, n):
            sequence.append(sequence[i-1] + sequence[i-2])

        return sequence

    def _is_retriable_exception(self, exception: Exception, config: RetryConfig) -> bool:
        """检查异常是否可重试"""
        return any(isinstance(exception, exc_type) for exc_type in config.retriable_exceptions)

    def retry_with_circuit_breaker(self,
                                 retry_config: RetryConfig = None,
                                 circuit_config: CircuitBreakerConfig = None,
                                 fallback_func: Callable = None):
        """
        带熔断器的重试装饰器

        Args:
            retry_config: 重试配置
            circuit_config: 熔断器配置
            fallback_func: 降级函数
        """
        def decorator(func: Callable) -> Callable:
            func_name = f"{func.__module__}.{func.__name__}"

            # 使用默认配置
            r_config = retry_config or RetryConfig()
            c_config = circuit_config or CircuitBreakerConfig()

            # 获取熔断器
            circuit_breaker = self._get_circuit_breaker(func_name, c_config)

            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(1, r_config.max_attempts + 1):
                    try:
                        # 通过熔断器调用函数
                        result = circuit_breaker.call(func, *args, **kwargs)

                        if attempt > 1 and logger:
                            logger.info(f"{func_name} 第{attempt}次尝试成功")

                        return result

                    except Exception as e:
                        last_exception = e

                        # 记录错误
                        self.error_monitor.record_error(func_name, e, attempt)

                        # 检查是否为熔断器异常
                        if "熔断器开启" in str(e):
                            if fallback_func:
                                if logger:
                                    logger.warning(f"{func_name} 熔断器开启，使用降级函数")
                                return fallback_func(*args, **kwargs)
                            else:
                                raise e

                        # 检查是否可重试
                        if not self._is_retriable_exception(e, r_config):
                            if logger:
                                logger.error(f"{func_name} 不可重试异常: {e}")
                            break

                        # 如果是最后一次尝试，不再等待
                        if attempt >= r_config.max_attempts:
                            break

                        # 计算延迟并等待
                        delay = self._calculate_delay(attempt, r_config)
                        if logger:
                            logger.warning(f"{func_name} 第{attempt}次尝试失败，{delay:.2f}秒后重试: {e}")
                        time.sleep(delay)

                # 所有重试都失败了
                if fallback_func:
                    if logger:
                        logger.error(f"{func_name} 所有重试失败，使用降级函数")
                    return fallback_func(*args, **kwargs)
                else:
                    if logger:
                        logger.error(f"{func_name} 所有重试失败: {last_exception}")
                    raise last_exception

            return wrapper
        return decorator

    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        # 获取所有熔断器状态
        circuit_breaker_states = {
            name: cb.get_state()
            for name, cb in self.circuit_breakers.items()
        }

        # 获取错误摘要
        error_summary = self.error_monitor.get_error_summary()

        # 计算健康评分
        health_score = self._calculate_health_score(circuit_breaker_states, error_summary)

        return {
            'health_score': health_score,
            'circuit_breakers': circuit_breaker_states,
            'error_summary': error_summary,
            'total_circuit_breakers': len(self.circuit_breakers),
            'open_circuit_breakers': len([
                cb for cb in self.circuit_breakers.values()
                if cb.state == CircuitBreakerState.OPEN
            ]),
            'timestamp': datetime.now().isoformat()
        }

    def _calculate_health_score(self, cb_states: Dict, error_summary: Dict) -> float:
        """计算系统健康评分（0-100）"""
        if not cb_states and error_summary.get('total_errors', 0) == 0:
            return 100.0

        # 熔断器健康评分
        cb_score = 100.0
        if cb_states:
            open_breakers = len([
                state for state in cb_states.values()
                if state['state'] == 'open'
            ])
            cb_score = max(0, 100 - (open_breakers / len(cb_states) * 50))

        # 错误率评分
        error_score = 100.0
        total_errors = error_summary.get('total_errors', 0)
        if total_errors > 0:
            # 简单的错误评分算法：每100个错误扣10分
            error_penalty = min(total_errors / 10, 50)
            error_score = max(0, 100 - error_penalty)

        # 综合评分
        final_score = (cb_score * 0.6 + error_score * 0.4)
        return round(final_score, 1)


# 预定义的重试配置
RETRY_CONFIGS = {
    'fast': RetryConfig(max_attempts=2, base_delay=0.5, max_delay=5.0),
    'standard': RetryConfig(max_attempts=3, base_delay=1.0, max_delay=30.0),
    'patient': RetryConfig(max_attempts=5, base_delay=2.0, max_delay=60.0),
    'network_heavy': RetryConfig(
        max_attempts=4,
        base_delay=1.0,
        max_delay=45.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        retriable_exceptions=[ConnectionError, TimeoutError, ValueError]
    )
}

CIRCUIT_BREAKER_CONFIGS = {
    'sensitive': CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30),
    'standard': CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60),
    'tolerant': CircuitBreakerConfig(failure_threshold=10, recovery_timeout=120)
}


# 全局重试处理器实例
_global_retry_handler = None

def get_retry_handler() -> EnhancedRetryHandler:
    """获取全局重试处理器实例"""
    global _global_retry_handler
    if _global_retry_handler is None:
        _global_retry_handler = EnhancedRetryHandler()
    return _global_retry_handler


# 便捷装饰器函数
def robust_data_fetcher(retry_type: str = 'standard',
                       circuit_type: str = 'standard',
                       fallback_func: Callable = None):
    """
    稳健数据获取装饰器

    Args:
        retry_type: 重试类型 ('fast', 'standard', 'patient', 'network_heavy')
        circuit_type: 熔断器类型 ('sensitive', 'standard', 'tolerant')
        fallback_func: 降级函数
    """
    retry_config = RETRY_CONFIGS.get(retry_type, RETRY_CONFIGS['standard'])
    circuit_config = CIRCUIT_BREAKER_CONFIGS.get(circuit_type, CIRCUIT_BREAKER_CONFIGS['standard'])

    return get_retry_handler().retry_with_circuit_breaker(
        retry_config=retry_config,
        circuit_config=circuit_config,
        fallback_func=fallback_func
    )


def async_error_safe(fallback_value: Any = None):
    """
    异步安全装饰器，确保异步函数不会因异常而中断

    Args:
        fallback_value: 异常时返回的默认值
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                func_name = f"{func.__module__}.{func.__name__}"
                get_retry_handler().error_monitor.record_error(func_name, e)

                if logger:
                    logger.error(f"异步函数 {func_name} 异常: {e}")

                return fallback_value
        return wrapper
    return decorator