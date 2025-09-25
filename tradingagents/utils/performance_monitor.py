"""
性能监控和优化工具

为AData市场数据集成提供性能监控、分析和优化建议功能。

Author: Claude (Opus 4.1)
Created: 2025-09-25
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标数据结构"""
    timestamp: float
    function_name: str
    execution_time: float
    memory_before: float
    memory_after: float
    memory_delta: float
    cache_hit: bool
    data_size: int
    error_occurred: bool
    error_message: Optional[str] = None


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.function_stats: Dict[str, List[PerformanceMetrics]] = defaultdict(list)
        self.cache_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"hits": 0, "misses": 0})
        self.error_stats: Dict[str, int] = defaultdict(int)
        self.lock = threading.RLock()

    def record_metric(self, metric: PerformanceMetrics):
        """记录性能指标"""
        with self.lock:
            self.metrics_history.append(metric)
            self.function_stats[metric.function_name].append(metric)

            # 限制每个函数的历史记录数量
            if len(self.function_stats[metric.function_name]) > 100:
                self.function_stats[metric.function_name] = \
                    self.function_stats[metric.function_name][-100:]

            # 更新缓存统计
            if metric.cache_hit:
                self.cache_stats[metric.function_name]["hits"] += 1
            else:
                self.cache_stats[metric.function_name]["misses"] += 1

            # 更新错误统计
            if metric.error_occurred:
                self.error_stats[metric.function_name] += 1

    def get_function_performance(self, function_name: str) -> Dict[str, Any]:
        """获取指定函数的性能统计"""
        with self.lock:
            metrics = self.function_stats.get(function_name, [])
            if not metrics:
                return {"error": f"No metrics found for function {function_name}"}

            execution_times = [m.execution_time for m in metrics if not m.error_occurred]
            memory_deltas = [m.memory_delta for m in metrics if not m.error_occurred]

            if not execution_times:
                return {"error": f"No successful executions for function {function_name}"}

            cache_stats = self.cache_stats[function_name]
            total_cache_ops = cache_stats["hits"] + cache_stats["misses"]
            cache_hit_rate = (cache_stats["hits"] / total_cache_ops * 100) if total_cache_ops > 0 else 0

            return {
                "function_name": function_name,
                "total_calls": len(metrics),
                "successful_calls": len(execution_times),
                "error_count": self.error_stats[function_name],
                "avg_execution_time": sum(execution_times) / len(execution_times),
                "min_execution_time": min(execution_times),
                "max_execution_time": max(execution_times),
                "avg_memory_delta": sum(memory_deltas) / len(memory_deltas),
                "cache_hit_rate": cache_hit_rate,
                "last_call": metrics[-1].timestamp if metrics else None
            }

    def get_overall_performance(self) -> Dict[str, Any]:
        """获取整体性能统计"""
        with self.lock:
            if not self.metrics_history:
                return {"error": "No performance data available"}

            total_calls = len(self.metrics_history)
            successful_calls = sum(1 for m in self.metrics_history if not m.error_occurred)
            total_errors = sum(1 for m in self.metrics_history if m.error_occurred)

            execution_times = [m.execution_time for m in self.metrics_history if not m.error_occurred]

            # 计算整体缓存命中率
            total_hits = sum(stats["hits"] for stats in self.cache_stats.values())
            total_cache_ops = sum(stats["hits"] + stats["misses"] for stats in self.cache_stats.values())
            overall_cache_hit_rate = (total_hits / total_cache_ops * 100) if total_cache_ops > 0 else 0

            # 找出最慢的函数
            function_avg_times = {}
            for func_name, metrics in self.function_stats.items():
                successful_metrics = [m for m in metrics if not m.error_occurred]
                if successful_metrics:
                    avg_time = sum(m.execution_time for m in successful_metrics) / len(successful_metrics)
                    function_avg_times[func_name] = avg_time

            slowest_functions = sorted(function_avg_times.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                "monitoring_period": {
                    "start_time": self.metrics_history[0].timestamp,
                    "end_time": self.metrics_history[-1].timestamp,
                    "duration_hours": (self.metrics_history[-1].timestamp - self.metrics_history[0].timestamp) / 3600
                },
                "call_statistics": {
                    "total_calls": total_calls,
                    "successful_calls": successful_calls,
                    "error_calls": total_errors,
                    "success_rate": (successful_calls / total_calls * 100) if total_calls > 0 else 0
                },
                "performance_statistics": {
                    "avg_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
                    "min_execution_time": min(execution_times) if execution_times else 0,
                    "max_execution_time": max(execution_times) if execution_times else 0
                },
                "cache_statistics": {
                    "overall_cache_hit_rate": overall_cache_hit_rate,
                    "total_cache_operations": total_cache_ops
                },
                "top_functions": {
                    "slowest_functions": slowest_functions,
                    "most_called_functions": [(func, len(metrics)) for func, metrics in
                                            sorted(self.function_stats.items(), key=lambda x: len(x[1]), reverse=True)[:5]]
                }
            }

    def get_performance_insights(self) -> List[str]:
        """获取性能优化建议"""
        insights = []
        overall_stats = self.get_overall_performance()

        if "error" in overall_stats:
            return ["无足够数据进行性能分析"]

        # 缓存命中率分析
        cache_hit_rate = overall_stats["cache_statistics"]["overall_cache_hit_rate"]
        if cache_hit_rate < 70:
            insights.append(f"⚠️ 缓存命中率较低({cache_hit_rate:.1f}%)，建议优化缓存策略")
        elif cache_hit_rate > 90:
            insights.append(f"✅ 缓存命中率优秀({cache_hit_rate:.1f}%)")

        # 错误率分析
        success_rate = overall_stats["call_statistics"]["success_rate"]
        if success_rate < 95:
            insights.append(f"⚠️ 成功率较低({success_rate:.1f}%)，建议检查错误处理机制")

        # 性能分析
        avg_time = overall_stats["performance_statistics"]["avg_execution_time"]
        if avg_time > 2.0:
            insights.append(f"⚠️ 平均执行时间较长({avg_time:.2f}秒)，建议优化数据获取逻辑")

        # 慢函数分析
        slowest_functions = overall_stats["top_functions"]["slowest_functions"]
        if slowest_functions and slowest_functions[0][1] > 5.0:
            func_name, avg_time = slowest_functions[0]
            insights.append(f"🐌 最慢函数 {func_name} 平均耗时 {avg_time:.2f}秒，建议优先优化")

        # 调用频率分析
        most_called = overall_stats["top_functions"]["most_called_functions"]
        if most_called:
            func_name, call_count = most_called[0]
            insights.append(f"🔥 最频繁调用的函数是 {func_name}({call_count}次调用)，建议重点关注其性能")

        if not insights:
            insights.append("✅ 系统性能表现良好，无明显优化点")

        return insights

    def export_report(self, filepath: str) -> bool:
        """导出性能报告"""
        try:
            report_data = {
                "export_time": datetime.now().isoformat(),
                "overall_performance": self.get_overall_performance(),
                "function_details": {
                    func_name: self.get_function_performance(func_name)
                    for func_name in self.function_stats.keys()
                },
                "performance_insights": self.get_performance_insights()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            logger.info(f"性能报告已导出到: {filepath}")
            return True
        except Exception as e:
            logger.error(f"导出性能报告失败: {e}")
            return False


class PerformanceProfiler:
    """性能分析装饰器"""

    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor

    def profile(self, function_name: Optional[str] = None):
        """性能分析装饰器"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                fname = function_name or func.__name__

                # 获取执行前内存
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB

                start_time = time.time()
                error_occurred = False
                error_message = None
                result = None
                data_size = 0
                cache_hit = False

                try:
                    result = func(*args, **kwargs)

                    # 尝试检测缓存命中（基于执行时间启发式判断）
                    execution_time = time.time() - start_time
                    if execution_time < 0.1:  # 小于100ms可能是缓存命中
                        cache_hit = True

                    # 估算数据大小
                    if isinstance(result, str):
                        data_size = len(result)
                    elif hasattr(result, '__len__'):
                        try:
                            data_size = len(str(result))
                        except:
                            data_size = 0

                except Exception as e:
                    error_occurred = True
                    error_message = str(e)
                    result = None

                # 获取执行后内存
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                execution_time = time.time() - start_time

                # 记录性能指标
                metric = PerformanceMetrics(
                    timestamp=time.time(),
                    function_name=fname,
                    execution_time=execution_time,
                    memory_before=memory_before,
                    memory_after=memory_after,
                    memory_delta=memory_after - memory_before,
                    cache_hit=cache_hit,
                    data_size=data_size,
                    error_occurred=error_occurred,
                    error_message=error_message
                )

                self.monitor.record_metric(metric)

                if error_occurred:
                    raise Exception(error_message)

                return result

            return wrapper
        return decorator


class SystemResourceMonitor:
    """系统资源监控器"""

    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.resource_history: deque = deque(maxlen=1000)

    def start_monitoring(self, interval: float = 5.0):
        """开始系统资源监控"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_resources,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("系统资源监控已启动")

    def stop_monitoring(self):
        """停止系统资源监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("系统资源监控已停止")

    def _monitor_resources(self, interval: float):
        """资源监控循环"""
        while self.monitoring:
            try:
                # 获取系统资源信息
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                resource_data = {
                    "timestamp": time.time(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                }

                self.resource_history.append(resource_data)

                # 如果资源使用率过高，记录警告
                if cpu_percent > 80:
                    logger.warning(f"CPU使用率过高: {cpu_percent}%")
                if memory.percent > 85:
                    logger.warning(f"内存使用率过高: {memory.percent}%")
                if disk.percent > 90:
                    logger.warning(f"磁盘使用率过高: {disk.percent}%")

                time.sleep(interval)

            except Exception as e:
                logger.error(f"资源监控出错: {e}")
                time.sleep(interval)

    def get_resource_summary(self) -> Dict[str, Any]:
        """获取资源使用总结"""
        if not self.resource_history:
            return {"error": "No resource monitoring data available"}

        recent_data = list(self.resource_history)[-60:]  # 最近60个数据点

        cpu_values = [data["cpu_percent"] for data in recent_data]
        memory_values = [data["memory_percent"] for data in recent_data]

        return {
            "monitoring_period": {
                "start_time": recent_data[0]["timestamp"],
                "end_time": recent_data[-1]["timestamp"],
                "data_points": len(recent_data)
            },
            "cpu_statistics": {
                "average": sum(cpu_values) / len(cpu_values),
                "maximum": max(cpu_values),
                "minimum": min(cpu_values)
            },
            "memory_statistics": {
                "average_percent": sum(memory_values) / len(memory_values),
                "maximum_percent": max(memory_values),
                "current_available_gb": recent_data[-1]["memory_available_gb"]
            },
            "disk_statistics": {
                "current_usage_percent": recent_data[-1]["disk_percent"],
                "current_free_gb": recent_data[-1]["disk_free_gb"]
            }
        }


# 全局性能监控实例
global_performance_monitor = PerformanceMonitor()
global_profiler = PerformanceProfiler(global_performance_monitor)
global_resource_monitor = SystemResourceMonitor()


def get_performance_dashboard() -> str:
    """获取性能监控仪表板"""
    try:
        overall_stats = global_performance_monitor.get_overall_performance()
        insights = global_performance_monitor.get_performance_insights()
        resource_summary = global_resource_monitor.get_resource_summary()

        dashboard = f"""
# 🎯 TradingAgents-CN 性能监控仪表板
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## 📊 整体性能统计
"""

        if "error" not in overall_stats:
            call_stats = overall_stats["call_statistics"]
            perf_stats = overall_stats["performance_statistics"]
            cache_stats = overall_stats["cache_statistics"]

            dashboard += f"""
### 调用统计
- **总调用次数**: {call_stats['total_calls']}
- **成功调用**: {call_stats['successful_calls']}
- **失败调用**: {call_stats['error_calls']}
- **成功率**: {call_stats['success_rate']:.1f}%

### 性能指标
- **平均执行时间**: {perf_stats['avg_execution_time']:.3f}秒
- **最快执行**: {perf_stats['min_execution_time']:.3f}秒
- **最慢执行**: {perf_stats['max_execution_time']:.3f}秒

### 缓存统计
- **缓存命中率**: {cache_stats['overall_cache_hit_rate']:.1f}%
- **总缓存操作**: {cache_stats['total_cache_operations']}
"""

        dashboard += "\n## 🎯 性能优化建议\n"
        for i, insight in enumerate(insights, 1):
            dashboard += f"{i}. {insight}\n"

        # 资源监控信息
        dashboard += "\n## 💻 系统资源状况\n"
        if "error" not in resource_summary:
            cpu_stats = resource_summary["cpu_statistics"]
            mem_stats = resource_summary["memory_statistics"]
            disk_stats = resource_summary["disk_statistics"]

            dashboard += f"""
### CPU使用情况
- **平均使用率**: {cpu_stats['average']:.1f}%
- **峰值使用率**: {cpu_stats['maximum']:.1f}%

### 内存使用情况
- **平均使用率**: {mem_stats['average_percent']:.1f}%
- **当前可用内存**: {mem_stats['current_available_gb']:.2f}GB

### 磁盘使用情况
- **当前使用率**: {disk_stats['current_usage_percent']:.1f}%
- **剩余空间**: {disk_stats['current_free_gb']:.2f}GB
"""
        else:
            dashboard += "系统资源监控数据不可用\n"

        dashboard += f"""
---
*监控范围*: AData市场数据集成系统
*数据来源*: 性能监控器 + 系统资源监控器
"""

        return dashboard

    except Exception as e:
        return f"⚠️ 生成性能仪表板失败: {str(e)}"


def initialize_performance_monitoring():
    """初始化性能监控系统"""
    try:
        # 启动系统资源监控
        global_resource_monitor.start_monitoring(interval=10.0)
        logger.info("✅ 性能监控系统初始化完成")
        return True
    except Exception as e:
        logger.error(f"❌ 性能监控系统初始化失败: {e}")
        return False


def cleanup_performance_monitoring():
    """清理性能监控系统"""
    try:
        global_resource_monitor.stop_monitoring()
        logger.info("✅ 性能监控系统清理完成")
    except Exception as e:
        logger.error(f"❌ 性能监控系统清理失败: {e}")


if __name__ == "__main__":
    # 测试性能监控系统
    initialize_performance_monitoring()

    print("性能监控系统测试...")
    time.sleep(2)

    # 模拟一些性能数据
    @global_profiler.profile("test_function")
    def test_function():
        time.sleep(0.1)
        return "test_result" * 100

    # 执行测试函数几次
    for _ in range(5):
        test_function()

    # 生成性能报告
    dashboard = get_performance_dashboard()
    print(dashboard)

    cleanup_performance_monitoring()