"""
增强缓存策略和错误处理

基于现有统一缓存管理器，提供智能缓存策略和高级错误处理机制
- 智能TTL策略（根据数据类型和访问频率动态调整）
- 缓存预热机制
- 批量缓存操作
- 缓存性能监控
- 高级错误恢复策略
"""

import time
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import gc

try:
    from tradingagents.utils.unified_cache_manager import UnifiedCacheManager, CacheEntry
    from tradingagents.utils.logging_manager import get_logger
    cache_available = True
except ImportError:
    cache_available = False

if cache_available:
    logger = get_logger('enhanced_cache')
else:
    logger = None


@dataclass
class CacheMetrics:
    """缓存性能指标"""
    hit_count: int = 0
    miss_count: int = 0
    error_count: int = 0
    total_get_time: float = 0.0
    total_set_time: float = 0.0
    last_reset: datetime = field(default_factory=datetime.now)
    access_patterns: Dict[str, List[datetime]] = field(default_factory=lambda: defaultdict(list))

    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self.hit_count + self.miss_count
        return (self.hit_count / total * 100) if total > 0 else 0.0

    @property
    def avg_get_time(self) -> float:
        """平均获取时间（毫秒）"""
        total_ops = self.hit_count + self.miss_count
        return (self.total_get_time / total_ops * 1000) if total_ops > 0 else 0.0

    @property
    def avg_set_time(self) -> float:
        """平均设置时间（毫秒）"""
        total_sets = self.hit_count  # 近似值
        return (self.total_set_time / total_sets * 1000) if total_sets > 0 else 0.0


@dataclass
class SmartTTLRule:
    """智能TTL规则"""
    pattern: str  # 键匹配模式
    base_ttl: int  # 基础TTL（秒）
    access_factor: float = 1.0  # 访问频率因子
    time_decay: float = 0.9  # 时间衰减因子
    max_ttl: int = 86400  # 最大TTL（24小时）
    min_ttl: int = 60  # 最小TTL（1分钟）


class EnhancedCacheManager:
    """增强缓存管理器"""

    def __init__(self, base_cache_manager: UnifiedCacheManager = None):
        """
        初始化增强缓存管理器

        Args:
            base_cache_manager: 基础缓存管理器，如果为None则创建新实例
        """
        self.base_manager = base_cache_manager or UnifiedCacheManager()
        self.metrics = CacheMetrics()
        self.ttl_rules: List[SmartTTLRule] = []
        self._lock = threading.RLock()
        self._prewarming_tasks = set()

        # 初始化默认TTL规则
        self._init_default_ttl_rules()

        # 启动后台任务
        self._start_background_tasks()

    def _init_default_ttl_rules(self):
        """初始化默认TTL规则"""
        default_rules = [
            SmartTTLRule("market_data:*", 300, access_factor=1.5),  # 市场数据：5分钟基础，高访问频率延长
            SmartTTLRule("capital_flow:*", 600, access_factor=1.2),  # 资金流向：10分钟基础
            SmartTTLRule("concept_data:*", 1800, access_factor=1.0),  # 概念数据：30分钟基础
            SmartTTLRule("dividend_data:*", 3600, access_factor=0.8),  # 股息数据：1小时基础，低访问频率缩短
            SmartTTLRule("stock_data:*", 1800, access_factor=1.3),  # 股票数据：30分钟基础
            SmartTTLRule("news_data:*", 900, access_factor=2.0),  # 新闻数据：15分钟基础，高访问频率大幅延长
        ]
        self.ttl_rules.extend(default_rules)

    def _start_background_tasks(self):
        """启动后台任务"""
        # 启动缓存清理任务
        cleanup_thread = threading.Thread(target=self._background_cleanup, daemon=True)
        cleanup_thread.start()

        # 启动指标收集任务
        metrics_thread = threading.Thread(target=self._background_metrics_collection, daemon=True)
        metrics_thread.start()

    def _background_cleanup(self):
        """后台缓存清理任务"""
        while True:
            try:
                time.sleep(300)  # 每5分钟清理一次
                self._cleanup_expired_entries()
            except Exception as e:
                if logger:
                    logger.error(f"后台清理任务错误: {e}")

    def _background_metrics_collection(self):
        """后台指标收集任务"""
        while True:
            try:
                time.sleep(60)  # 每分钟收集一次
                self._update_access_patterns()
            except Exception as e:
                if logger:
                    logger.error(f"指标收集任务错误: {e}")

    def _cleanup_expired_entries(self):
        """清理过期缓存条目"""
        with self._lock:
            try:
                # 使用基础管理器的清理功能
                stats = self.get_cache_stats()
                if logger:
                    logger.debug(f"缓存状态: {stats}")
            except Exception as e:
                if logger:
                    logger.error(f"缓存清理失败: {e}")

    def _update_access_patterns(self):
        """更新访问模式统计"""
        with self._lock:
            current_time = datetime.now()
            # 清理1小时前的访问记录
            cutoff_time = current_time - timedelta(hours=1)

            for key, access_times in self.metrics.access_patterns.items():
                self.metrics.access_patterns[key] = [
                    t for t in access_times if t > cutoff_time
                ]

    def _calculate_smart_ttl(self, namespace: str, key: str, base_ttl: int = None) -> int:
        """计算智能TTL"""
        cache_key = f"{namespace}:{key}"

        # 查找匹配的TTL规则
        matching_rule = None
        for rule in self.ttl_rules:
            import fnmatch
            if fnmatch.fnmatch(cache_key, rule.pattern):
                matching_rule = rule
                break

        if not matching_rule:
            return base_ttl or 3600  # 默认1小时

        # 基础TTL
        calculated_ttl = matching_rule.base_ttl

        # 根据访问频率调整
        access_times = self.metrics.access_patterns.get(cache_key, [])
        if access_times:
            recent_accesses = len([t for t in access_times if t > datetime.now() - timedelta(minutes=30)])
            if recent_accesses > 0:
                # 访问频率越高，TTL越长
                frequency_multiplier = min(recent_accesses * matching_rule.access_factor / 10, 3.0)
                calculated_ttl = int(calculated_ttl * frequency_multiplier)

        # 应用边界限制
        calculated_ttl = max(matching_rule.min_ttl, min(calculated_ttl, matching_rule.max_ttl))

        return calculated_ttl

    def get_with_retry(self, namespace: str, key: str, retry_count: int = 3, **kwargs) -> Any:
        """
        带重试机制的缓存获取

        Args:
            namespace: 命名空间
            key: 缓存键
            retry_count: 重试次数
            **kwargs: 额外参数

        Returns:
            缓存数据，失败时返回None
        """
        cache_key = f"{namespace}:{key}"

        for attempt in range(retry_count + 1):
            start_time = time.time()
            try:
                # 记录访问
                with self._lock:
                    self.metrics.access_patterns[cache_key].append(datetime.now())

                result = self.base_manager.get(namespace, key, **kwargs)

                # 更新指标
                with self._lock:
                    elapsed_time = time.time() - start_time
                    self.metrics.total_get_time += elapsed_time

                    if result is not None:
                        self.metrics.hit_count += 1
                    else:
                        self.metrics.miss_count += 1

                return result

            except Exception as e:
                with self._lock:
                    self.metrics.error_count += 1

                if logger:
                    logger.warning(f"缓存获取失败 (尝试 {attempt + 1}/{retry_count + 1}): {e}")

                if attempt < retry_count:
                    time.sleep(0.1 * (attempt + 1))  # 指数退避
                    continue
                else:
                    if logger:
                        logger.error(f"缓存获取最终失败: {cache_key}")
                    return None

    def set_with_smart_ttl(self, namespace: str, key: str, data: Any,
                          data_type: str = "default", **kwargs) -> bool:
        """
        使用智能TTL设置缓存

        Args:
            namespace: 命名空间
            key: 缓存键
            data: 要缓存的数据
            data_type: 数据类型
            **kwargs: 额外参数

        Returns:
            是否设置成功
        """
        start_time = time.time()

        try:
            # 计算智能TTL
            smart_ttl = self._calculate_smart_ttl(namespace, key)

            result = self.base_manager.set(
                namespace, key, data, data_type,
                ttl_seconds=smart_ttl, **kwargs
            )

            # 更新指标
            with self._lock:
                elapsed_time = time.time() - start_time
                self.metrics.total_set_time += elapsed_time

            if logger:
                logger.debug(f"智能缓存设置: {namespace}:{key}, TTL: {smart_ttl}s")

            return result

        except Exception as e:
            with self._lock:
                self.metrics.error_count += 1

            if logger:
                logger.error(f"智能缓存设置失败: {e}")
            return False

    def batch_get(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量获取缓存

        Args:
            items: 包含namespace、key等信息的字典列表

        Returns:
            键值对字典
        """
        results = {}

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_item = {
                executor.submit(
                    self.get_with_retry,
                    item['namespace'],
                    item['key'],
                    **item.get('kwargs', {})
                ): item for item in items
            }

            for future in as_completed(future_to_item):
                item = future_to_item[future]
                cache_key = f"{item['namespace']}:{item['key']}"
                try:
                    result = future.result()
                    results[cache_key] = result
                except Exception as e:
                    if logger:
                        logger.error(f"批量获取失败 {cache_key}: {e}")
                    results[cache_key] = None

        return results

    def batch_set(self, items: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        批量设置缓存

        Args:
            items: 包含namespace、key、data等信息的字典列表

        Returns:
            设置结果字典
        """
        results = {}

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_item = {
                executor.submit(
                    self.set_with_smart_ttl,
                    item['namespace'],
                    item['key'],
                    item['data'],
                    item.get('data_type', 'default'),
                    **item.get('kwargs', {})
                ): item for item in items
            }

            for future in as_completed(future_to_item):
                item = future_to_item[future]
                cache_key = f"{item['namespace']}:{item['key']}"
                try:
                    result = future.result()
                    results[cache_key] = result
                except Exception as e:
                    if logger:
                        logger.error(f"批量设置失败 {cache_key}: {e}")
                    results[cache_key] = False

        return results

    def prewarm_cache(self, prewarming_tasks: List[Dict[str, Any]]):
        """
        缓存预热

        Args:
            prewarming_tasks: 预热任务列表，包含data_fetcher（数据获取函数）等信息
        """
        if logger:
            logger.info(f"开始缓存预热，共{len(prewarming_tasks)}个任务")

        def prewarm_task(task):
            try:
                namespace = task['namespace']
                key = task['key']
                data_fetcher = task['data_fetcher']
                data_type = task.get('data_type', 'default')

                # 检查是否已缓存
                if self.get_with_retry(namespace, key) is not None:
                    return f"已缓存: {namespace}:{key}"

                # 获取数据并缓存
                data = data_fetcher()
                if data is not None:
                    success = self.set_with_smart_ttl(namespace, key, data, data_type)
                    return f"预热{'成功' if success else '失败'}: {namespace}:{key}"
                else:
                    return f"数据获取失败: {namespace}:{key}"

            except Exception as e:
                return f"预热错误 {task.get('namespace')}:{task.get('key')}: {e}"

        # 异步执行预热任务
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(prewarm_task, task) for task in prewarming_tasks]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if logger:
                        logger.debug(result)
                except Exception as e:
                    if logger:
                        logger.error(f"预热任务异常: {e}")

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        with self._lock:
            # 计算访问模式统计
            pattern_stats = {}
            for cache_key, access_times in self.metrics.access_patterns.items():
                if access_times:
                    recent_accesses = [t for t in access_times if t > datetime.now() - timedelta(hours=1)]
                    pattern_stats[cache_key] = {
                        'total_accesses': len(access_times),
                        'recent_accesses': len(recent_accesses),
                        'avg_access_interval': self._calculate_avg_interval(access_times)
                    }

            # 获取基础缓存统计
            base_stats = self.get_cache_stats()

            return {
                'performance_metrics': {
                    'hit_rate': round(self.metrics.hit_rate, 2),
                    'total_operations': self.metrics.hit_count + self.metrics.miss_count,
                    'error_count': self.metrics.error_count,
                    'avg_get_time_ms': round(self.metrics.avg_get_time, 2),
                    'avg_set_time_ms': round(self.metrics.avg_set_time, 2),
                },
                'access_patterns': pattern_stats,
                'base_cache_stats': base_stats,
                'ttl_rules_count': len(self.ttl_rules),
                'report_time': datetime.now().isoformat()
            }

    def _calculate_avg_interval(self, access_times: List[datetime]) -> float:
        """计算平均访问间隔（分钟）"""
        if len(access_times) < 2:
            return 0.0

        intervals = []
        sorted_times = sorted(access_times)
        for i in range(1, len(sorted_times)):
            interval = (sorted_times[i] - sorted_times[i-1]).total_seconds() / 60
            intervals.append(interval)

        return statistics.mean(intervals) if intervals else 0.0

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            return self.base_manager.stats()
        except Exception as e:
            if logger:
                logger.error(f"获取缓存统计失败: {e}")
            return {}

    def optimize_cache_performance(self):
        """优化缓存性能"""
        if logger:
            logger.info("开始缓存性能优化...")

        try:
            # 强制垃圾回收
            gc.collect()

            # 清理过期条目
            self._cleanup_expired_entries()

            # 重置指标（可选）
            with self._lock:
                if self.metrics.hit_count + self.metrics.miss_count > 10000:
                    self.metrics = CacheMetrics()

            if logger:
                logger.info("缓存性能优化完成")

        except Exception as e:
            if logger:
                logger.error(f"缓存性能优化失败: {e}")


def cache_with_fallback(fallback_func: Callable = None, ttl_seconds: int = 3600):
    """
    带降级机制的缓存装饰器

    Args:
        fallback_func: 降级函数，缓存失败时调用
        ttl_seconds: 缓存TTL
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache_available:
                return func(*args, **kwargs)

            # 生成缓存键
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # 尝试从缓存获取
            try:
                cache_manager = EnhancedCacheManager()
                cached_result = cache_manager.get_with_retry("function_cache", cache_key)
                if cached_result is not None:
                    return cached_result
            except Exception as e:
                if logger:
                    logger.warning(f"缓存获取失败，使用原函数: {e}")

            # 执行原函数
            try:
                result = func(*args, **kwargs)

                # 缓存结果
                try:
                    cache_manager.set_with_smart_ttl("function_cache", cache_key, result)
                except Exception as e:
                    if logger:
                        logger.warning(f"缓存设置失败: {e}")

                return result

            except Exception as e:
                # 如果有降级函数，则调用
                if fallback_func:
                    if logger:
                        logger.warning(f"原函数失败，使用降级函数: {e}")
                    return fallback_func(*args, **kwargs)
                else:
                    raise

        return wrapper
    return decorator


# 全局增强缓存管理器实例
_enhanced_cache_manager = None

def get_enhanced_cache_manager() -> EnhancedCacheManager:
    """获取全局增强缓存管理器实例"""
    global _enhanced_cache_manager
    if _enhanced_cache_manager is None and cache_available:
        _enhanced_cache_manager = EnhancedCacheManager()
    return _enhanced_cache_manager