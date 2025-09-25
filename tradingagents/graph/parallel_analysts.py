# tradingagents/graph/parallel_analysts.py

import asyncio
import threading
import time
import copy
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("parallel_analysts")


@dataclass
class AnalystPerformance:
    """分析师性能记录"""
    analyst_type: str
    start_time: float
    end_time: float
    success: bool
    error_msg: Optional[str] = None
    report_length: int = 0

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class ParallelAnalystsExecutor:
    """并行分析师执行器"""

    def __init__(self, max_workers: int = 4, timeout: float = 300):
        """
        初始化并行执行器

        Args:
            max_workers: 最大并行工作线程数
            timeout: 单个分析师超时时间（秒）
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.performances: List[AnalystPerformance] = []
        self.results_lock = threading.Lock()

    def execute_parallel(self, analyst_nodes: Dict[str, Callable],
                        state: Dict[str, Any]) -> Dict[str, Any]:
        """
        并行执行所有分析师

        Args:
            analyst_nodes: 分析师节点字典 {"analyst_type": analyst_function}
            state: 共享状态

        Returns:
            更新后的状态字典
        """
        logger.info(f"🚀 [并行执行器] 开始并行执行 {len(analyst_nodes)} 个分析师")
        start_time = time.time()

        # 清空之前的性能记录
        self.performances = []

        # 使用线程池并行执行
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_analyst = {}
            for analyst_type, analyst_node in analyst_nodes.items():
                # 为每个分析师创建状态副本，避免竞争条件
                state_copy = self._deep_copy_state(state)
                future = executor.submit(
                    self._execute_single_analyst,
                    analyst_type,
                    analyst_node,
                    state_copy
                )
                future_to_analyst[future] = analyst_type

            # 收集结果
            for future in as_completed(future_to_analyst.keys(), timeout=self.timeout + 30):
                analyst_type = future_to_analyst[future]
                try:
                    result = future.result(timeout=10)  # 短超时，因为任务应该已完成
                    results[analyst_type] = result
                except asyncio.TimeoutError as e:
                    logger.error(f"❌ [并行执行器] {analyst_type} 分析师执行超时: {str(e)}")
                    results[analyst_type] = None
                except RuntimeError as e:
                    logger.error(f"❌ [并行执行器] {analyst_type} 分析师运行时错误: {str(e)}")
                    results[analyst_type] = None
                except ValueError as e:
                    logger.error(f"❌ [并行执行器] {analyst_type} 分析师参数错误: {str(e)}")
                    results[analyst_type] = None
                except ImportError as e:
                    logger.error(f"❌ [并行执行器] {analyst_type} 分析师依赖模块缺失: {str(e)}")
                    results[analyst_type] = None

        # 合并结果
        merged_state = self._merge_analyst_results(state, results)

        total_time = time.time() - start_time
        success_count = len([r for r in results.values() if r is not None])

        logger.info(f"✅ [并行执行器] 并行执行完成，耗时 {total_time:.2f}秒")
        logger.info(f"📊 [并行执行器] 成功率: {success_count}/{len(analyst_nodes)} ({success_count/len(analyst_nodes)*100:.1f}%)")

        return merged_state

    def _execute_single_analyst(self, analyst_type: str, analyst_node: Callable,
                               state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """执行单个分析师"""
        start_time = time.time()

        try:
            logger.info(f"🔄 [{analyst_type.capitalize()} Analyst] 开始并行执行")

            # 设置超时执行
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(analyst_node, state)
                result = future.result(timeout=self.timeout)

            end_time = time.time()

            # 提取报告长度（支持更多报告类型）
            report_length = 0
            if result:
                for key in result.keys():
                    if key.endswith('_report') and result[key]:
                        report_length = len(str(result[key]))
                        break

            # 记录性能
            perf = AnalystPerformance(
                analyst_type=analyst_type,
                start_time=start_time,
                end_time=end_time,
                success=True,
                report_length=report_length
            )
            with self.results_lock:
                self.performances.append(perf)

            logger.info(f"✅ [{analyst_type.capitalize()} Analyst] 并行执行完成，耗时 {end_time - start_time:.2f}秒，报告长度 {report_length}")
            return result

        except asyncio.TimeoutError as e:
            end_time = time.time()
            error_msg = f"执行超时: {str(e)}"
            logger.error(f"❌ [{analyst_type.capitalize()} Analyst] 执行超时: {error_msg}")
        except RuntimeError as e:
            end_time = time.time()
            error_msg = f"运行时错误: {str(e)}"
            logger.error(f"❌ [{analyst_type.capitalize()} Analyst] 运行时错误: {error_msg}")
        except ValueError as e:
            end_time = time.time()
            error_msg = f"参数错误: {str(e)}"
            logger.error(f"❌ [{analyst_type.capitalize()} Analyst] 参数错误: {error_msg}")
        except ImportError as e:
            end_time = time.time()
            error_msg = f"依赖模块缺失: {str(e)}"

            # 记录失败性能
            perf = AnalystPerformance(
                analyst_type=analyst_type,
                start_time=start_time,
                end_time=end_time,
                success=False,
                error_msg=error_msg
            )
            with self.results_lock:
                self.performances.append(perf)

            logger.error(f"❌ [{analyst_type.capitalize()} Analyst] 执行异常: {error_msg}")
            return None

    def _deep_copy_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """深拷贝状态，避免并发修改冲突"""
        try:
            return copy.deepcopy(state)
        except (TypeError, AttributeError, RecursionError) as e:
            logger.warning(f"⚠️ [并行执行器] 深拷贝状态失败，使用浅拷贝: {e}")
            return copy.copy(state)

    def _merge_analyst_results(self, original_state: Dict[str, Any],
                              results: Dict[str, Any]) -> Dict[str, Any]:
        """合并分析师结果"""
        merged_state = original_state.copy()

        # 收集所有消息
        all_messages = list(merged_state.get("messages", []))

        # 合并各分析师的报告（通用方式）
        for analyst_type, result in results.items():
            if result is None:
                continue

            # 添加消息
            if "messages" in result:
                all_messages.extend(result["messages"])

            # 合并所有报告字段（以_report结尾的字段）
            for key, value in result.items():
                if key.endswith('_report') and value:
                    merged_state[key] = value

            # 更新其他重要字段
            for key in ["sender", "last_update", "analysis_timestamp"]:
                if key in result:
                    merged_state[key] = result[key]

        # 更新消息列表
        merged_state["messages"] = all_messages

        successful_analysts = [k for k, v in results.items() if v is not None]
        logger.info(f"🔄 [并行执行器] 结果合并完成，成功执行的分析师: {successful_analysts}")

        return merged_state

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能总结"""
        if not self.performances:
            return {"status": "no_data"}

        total_time = max(p.end_time for p in self.performances) - min(p.start_time for p in self.performances)
        success_count = sum(1 for p in self.performances if p.success)

        return {
            "total_parallel_time": round(total_time, 2),
            "success_rate": round(success_count / len(self.performances), 2),
            "successful_count": success_count,
            "total_count": len(self.performances),
            "analyst_performances": [
                {
                    "analyst": p.analyst_type,
                    "duration": round(p.duration, 2),
                    "success": p.success,
                    "error": p.error_msg,
                    "report_length": p.report_length
                }
                for p in self.performances
            ]
        }


def create_parallel_analysts_node(analyst_nodes: Dict[str, Callable],
                                 config: Dict[str, Any]) -> Callable:
    """
    创建并行分析师节点

    Args:
        analyst_nodes: 分析师节点字典
        config: 配置字典

    Returns:
        并行分析师执行函数
    """
    max_workers = config.get("max_parallel_workers", 4)
    timeout = config.get("analyst_timeout", 300)

    executor = ParallelAnalystsExecutor(max_workers=max_workers, timeout=timeout)

    def parallel_analysts_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """并行执行所有分析师的节点"""
        logger.info(f"📊 [并行分析师节点] 开始执行，配置: max_workers={max_workers}, timeout={timeout}s")

        # 执行并行分析
        result_state = executor.execute_parallel(analyst_nodes, state)

        # 添加性能数据到状态（可选）
        performance_summary = executor.get_performance_summary()
        result_state["parallel_performance"] = performance_summary

        logger.info(f"📊 [并行分析师节点] 执行完成，性能总结: {performance_summary}")

        return result_state

    return parallel_analysts_node