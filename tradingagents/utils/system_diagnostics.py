"""
系统诊断和健康检查工具

为AData市场数据集成提供系统健康检查、诊断和维护功能。

Author: Claude (Opus 4.1)
Created: 2025-09-25
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import importlib
import traceback

logger = logging.getLogger(__name__)


class SystemDiagnostics:
    """系统诊断器"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.diagnostic_results = {}

    def run_full_diagnostic(self) -> Dict[str, Any]:
        """运行完整系统诊断"""
        logger.info("🔍 开始系统诊断检查...")

        results = {
            "diagnostic_time": datetime.now().isoformat(),
            "system_info": self._check_system_info(),
            "dependencies": self._check_dependencies(),
            "data_sources": self._check_data_sources(),
            "cache_system": self._check_cache_system(),
            "configuration": self._check_configuration(),
            "file_integrity": self._check_file_integrity(),
            "network_connectivity": self._check_network_connectivity(),
            "health_score": 0,
            "recommendations": []
        }

        # 计算健康评分
        results["health_score"] = self._calculate_health_score(results)

        # 生成建议
        results["recommendations"] = self._generate_recommendations(results)

        self.diagnostic_results = results
        logger.info(f"🎯 系统诊断完成，健康评分: {results['health_score']}/100")

        return results

    def _check_system_info(self) -> Dict[str, Any]:
        """检查系统基础信息"""
        try:
            import platform
            import psutil

            return {
                "status": "healthy",
                "python_version": sys.version,
                "platform": platform.platform(),
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_free_gb": psutil.disk_usage(str(self.project_root)).free / (1024**3),
                "project_root": str(self.project_root)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _check_dependencies(self) -> Dict[str, Any]:
        """检查依赖包状态"""
        required_packages = [
            "pandas", "numpy", "requests", "akshare", "baostock",
            "langchain_core", "redis", "psutil"
        ]

        results = {
            "status": "checking",
            "required_packages": {},
            "missing_packages": [],
            "version_conflicts": []
        }

        for package in required_packages:
            try:
                module = importlib.import_module(package)
                version = getattr(module, "__version__", "unknown")
                results["required_packages"][package] = {
                    "installed": True,
                    "version": version
                }
            except ImportError:
                results["missing_packages"].append(package)
                results["required_packages"][package] = {
                    "installed": False,
                    "version": None
                }

        if results["missing_packages"]:
            results["status"] = "warning"
        else:
            results["status"] = "healthy"

        return results

    def _check_data_sources(self) -> Dict[str, Any]:
        """检查数据源连接状态"""
        data_sources_status = {
            "status": "checking",
            "sources": {}
        }

        # 检查AKShare
        try:
            import akshare as ak
            # 尝试获取一个简单的数据
            df = ak.stock_zh_a_hist(symbol="002115", start_date="20240101", end_date="20240102", adjust="")
            data_sources_status["sources"]["akshare"] = {
                "available": True,
                "error": None,
                "test_result": f"获取到 {len(df)} 行数据" if df is not None else "连接成功"
            }
        except Exception as e:
            data_sources_status["sources"]["akshare"] = {
                "available": False,
                "error": str(e),
                "test_result": None
            }

        # 检查BaoStock
        try:
            import baostock as bs
            lg = bs.login()
            if lg.error_code == '0':
                bs.logout()
                data_sources_status["sources"]["baostock"] = {
                    "available": True,
                    "error": None,
                    "test_result": "登录成功"
                }
            else:
                data_sources_status["sources"]["baostock"] = {
                    "available": False,
                    "error": lg.error_msg,
                    "test_result": None
                }
        except Exception as e:
            data_sources_status["sources"]["baostock"] = {
                "available": False,
                "error": str(e),
                "test_result": None
            }

        # 检查Tushare（如果配置了token）
        tushare_token = os.getenv('TUSHARE_TOKEN')
        if tushare_token:
            try:
                import tushare as ts
                ts.set_token(tushare_token)
                pro = ts.pro_api()
                df = pro.stock_basic(list_status='L', limit=1)
                data_sources_status["sources"]["tushare"] = {
                    "available": True,
                    "error": None,
                    "test_result": f"获取到 {len(df)} 行数据"
                }
            except Exception as e:
                data_sources_status["sources"]["tushare"] = {
                    "available": False,
                    "error": str(e),
                    "test_result": None
                }
        else:
            data_sources_status["sources"]["tushare"] = {
                "available": False,
                "error": "未设置TUSHARE_TOKEN环境变量",
                "test_result": None
            }

        # 计算整体状态
        available_sources = sum(1 for source in data_sources_status["sources"].values() if source["available"])
        total_sources = len(data_sources_status["sources"])

        if available_sources == 0:
            data_sources_status["status"] = "critical"
        elif available_sources < total_sources:
            data_sources_status["status"] = "warning"
        else:
            data_sources_status["status"] = "healthy"

        data_sources_status["summary"] = f"{available_sources}/{total_sources} 数据源可用"

        return data_sources_status

    def _check_cache_system(self) -> Dict[str, Any]:
        """检查缓存系统状态"""
        cache_status = {
            "status": "checking",
            "cache_backends": {},
            "cache_directories": {}
        }

        try:
            # 检查Redis连接（如果配置了）
            try:
                import redis
                r = redis.Redis(host='localhost', port=6379, decode_responses=True)
                r.ping()
                cache_status["cache_backends"]["redis"] = {
                    "available": True,
                    "error": None
                }
            except Exception as e:
                cache_status["cache_backends"]["redis"] = {
                    "available": False,
                    "error": str(e)
                }

            # 检查文件缓存目录
            cache_dirs = [
                ".cache",
                "cache",
                ".trading_cache",
                os.path.expanduser("~/.trading_cache")
            ]

            for cache_dir in cache_dirs:
                cache_path = Path(cache_dir)
                if cache_path.exists():
                    cache_status["cache_directories"][str(cache_path)] = {
                        "exists": True,
                        "writable": os.access(cache_path, os.W_OK),
                        "size_mb": sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file()) / (1024*1024)
                    }
                else:
                    cache_status["cache_directories"][str(cache_path)] = {
                        "exists": False,
                        "writable": False,
                        "size_mb": 0
                    }

            # 测试缓存写入
            try:
                from ..utils.unified_cache_manager import UnifiedCacheManager
                cache_manager = UnifiedCacheManager()
                test_key = f"diagnostic_test_{int(time.time())}"
                cache_manager.set("test", test_key, "diagnostic_data")
                retrieved_data = cache_manager.get("test", test_key)

                cache_status["cache_write_test"] = {
                    "success": retrieved_data == "diagnostic_data",
                    "error": None
                }

                # 清理测试数据
                try:
                    cache_manager.delete("test", test_key)
                except:
                    pass

            except Exception as e:
                cache_status["cache_write_test"] = {
                    "success": False,
                    "error": str(e)
                }

            cache_status["status"] = "healthy"

        except Exception as e:
            cache_status["status"] = "error"
            cache_status["error"] = str(e)

        return cache_status

    def _check_configuration(self) -> Dict[str, Any]:
        """检查配置文件状态"""
        config_status = {
            "status": "checking",
            "config_files": {},
            "environment_variables": {},
            "validation_errors": []
        }

        # 检查配置文件
        config_files = [
            "config/main_config.json",
            ".env",
            ".env.example",
            "pyproject.toml",
            "requirements.txt"
        ]

        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    config_status["config_files"][config_file] = {
                        "exists": True,
                        "readable": os.access(config_path, os.R_OK),
                        "size_bytes": config_path.stat().st_size,
                        "modified": datetime.fromtimestamp(config_path.stat().st_mtime).isoformat()
                    }

                    # 对JSON文件进行语法检查
                    if config_file.endswith('.json'):
                        try:
                            with open(config_path, 'r', encoding='utf-8') as f:
                                json.load(f)
                            config_status["config_files"][config_file]["json_valid"] = True
                        except json.JSONDecodeError as e:
                            config_status["config_files"][config_file]["json_valid"] = False
                            config_status["validation_errors"].append(f"{config_file}: {str(e)}")

                except Exception as e:
                    config_status["config_files"][config_file] = {
                        "exists": True,
                        "error": str(e)
                    }
            else:
                config_status["config_files"][config_file] = {
                    "exists": False
                }

        # 检查重要环境变量
        important_env_vars = [
            "TUSHARE_TOKEN",
            "REDIS_URL",
            "LOG_LEVEL",
            "PYTHONPATH"
        ]

        for env_var in important_env_vars:
            value = os.getenv(env_var)
            config_status["environment_variables"][env_var] = {
                "set": value is not None,
                "value_length": len(value) if value else 0
            }

        # 确定整体状态
        critical_missing = []
        if not config_status["config_files"].get("config/main_config.json", {}).get("exists", False):
            critical_missing.append("主配置文件缺失")

        if critical_missing:
            config_status["status"] = "critical"
            config_status["critical_issues"] = critical_missing
        elif config_status["validation_errors"]:
            config_status["status"] = "warning"
        else:
            config_status["status"] = "healthy"

        return config_status

    def _check_file_integrity(self) -> Dict[str, Any]:
        """检查重要文件完整性"""
        integrity_status = {
            "status": "checking",
            "core_modules": {},
            "missing_files": [],
            "import_errors": []
        }

        # 检查核心模块文件
        core_modules = [
            "tradingagents/dataflows/interface.py",
            "tradingagents/dataflows/data_source_manager.py",
            "tradingagents/dataflows/market_data_capital_flow_utils.py",
            "tradingagents/dataflows/market_data_concept_utils.py",
            "tradingagents/dataflows/market_data_dividend_utils.py",
            "tradingagents/utils/unified_cache_manager.py",
            "tradingagents/utils/enhanced_cache_policies.py",
            "tradingagents/utils/enhanced_error_handling.py",
            "tradingagents/agents/utils/agent_utils.py"
        ]

        for module_path in core_modules:
            full_path = self.project_root / module_path
            if full_path.exists():
                try:
                    integrity_status["core_modules"][module_path] = {
                        "exists": True,
                        "size_bytes": full_path.stat().st_size,
                        "modified": datetime.fromtimestamp(full_path.stat().st_mtime).isoformat(),
                        "readable": os.access(full_path, os.R_OK)
                    }

                    # 尝试语法检查（简单的编译测试）
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        compile(content, str(full_path), 'exec')
                        integrity_status["core_modules"][module_path]["syntax_valid"] = True
                    except SyntaxError as e:
                        integrity_status["core_modules"][module_path]["syntax_valid"] = False
                        integrity_status["import_errors"].append(f"{module_path}: {str(e)}")

                except Exception as e:
                    integrity_status["core_modules"][module_path] = {
                        "exists": True,
                        "error": str(e)
                    }
            else:
                integrity_status["missing_files"].append(module_path)
                integrity_status["core_modules"][module_path] = {
                    "exists": False
                }

        # 确定整体状态
        if integrity_status["missing_files"]:
            integrity_status["status"] = "critical"
        elif integrity_status["import_errors"]:
            integrity_status["status"] = "warning"
        else:
            integrity_status["status"] = "healthy"

        return integrity_status

    def _check_network_connectivity(self) -> Dict[str, Any]:
        """检查网络连通性"""
        connectivity_status = {
            "status": "checking",
            "endpoints": {}
        }

        # 测试重要的网络端点
        test_endpoints = [
            ("百度", "https://www.baidu.com"),
            ("新浪财经", "https://finance.sina.com.cn"),
            ("东方财富", "https://www.eastmoney.com"),
            ("PyPI", "https://pypi.org")
        ]

        for name, url in test_endpoints:
            try:
                import requests
                start_time = time.time()
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'TradingAgents-CN/1.0'
                })
                response_time = time.time() - start_time

                connectivity_status["endpoints"][name] = {
                    "accessible": response.status_code == 200,
                    "response_time_ms": int(response_time * 1000),
                    "status_code": response.status_code,
                    "error": None
                }
            except Exception as e:
                connectivity_status["endpoints"][name] = {
                    "accessible": False,
                    "response_time_ms": -1,
                    "status_code": None,
                    "error": str(e)
                }

        # 计算网络状态
        accessible_count = sum(1 for ep in connectivity_status["endpoints"].values() if ep["accessible"])
        total_count = len(connectivity_status["endpoints"])

        if accessible_count == 0:
            connectivity_status["status"] = "critical"
        elif accessible_count < total_count:
            connectivity_status["status"] = "warning"
        else:
            connectivity_status["status"] = "healthy"

        connectivity_status["summary"] = f"{accessible_count}/{total_count} 端点可访问"

        return connectivity_status

    def _calculate_health_score(self, results: Dict[str, Any]) -> int:
        """计算系统健康评分 (0-100)"""
        scores = {
            "system_info": 15,
            "dependencies": 20,
            "data_sources": 25,
            "cache_system": 15,
            "configuration": 15,
            "file_integrity": 10
        }

        total_score = 0

        for component, max_score in scores.items():
            if component not in results:
                continue

            component_status = results[component].get("status", "error")

            if component_status == "healthy":
                total_score += max_score
            elif component_status == "warning":
                total_score += max_score * 0.7
            elif component_status == "critical":
                total_score += max_score * 0.3
            # error状态得0分

        return min(100, max(0, int(total_score)))

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """根据诊断结果生成建议"""
        recommendations = []

        # 依赖包建议
        deps = results.get("dependencies", {})
        if deps.get("missing_packages"):
            recommendations.append(f"🔧 安装缺失的依赖包: {', '.join(deps['missing_packages'])}")

        # 数据源建议
        data_sources = results.get("data_sources", {})
        if data_sources.get("status") in ["warning", "critical"]:
            for source_name, source_info in data_sources.get("sources", {}).items():
                if not source_info.get("available", False):
                    if source_name == "tushare" and "TUSHARE_TOKEN" in str(source_info.get("error", "")):
                        recommendations.append("🔑 设置TUSHARE_TOKEN环境变量以启用Tushare数据源")
                    else:
                        recommendations.append(f"🔌 修复{source_name}数据源连接问题")

        # 配置文件建议
        config = results.get("configuration", {})
        if config.get("status") == "critical":
            recommendations.append("⚙️ 创建并配置主配置文件 config/main_config.json")
        if config.get("validation_errors"):
            recommendations.append("📝 修复配置文件中的语法错误")

        # 文件完整性建议
        file_integrity = results.get("file_integrity", {})
        if file_integrity.get("missing_files"):
            recommendations.append("📁 恢复缺失的核心模块文件")
        if file_integrity.get("import_errors"):
            recommendations.append("🐛 修复模块文件中的语法错误")

        # 网络连通性建议
        network = results.get("network_connectivity", {})
        if network.get("status") in ["warning", "critical"]:
            recommendations.append("🌐 检查网络连接和防火墙设置")

        # 缓存系统建议
        cache = results.get("cache_system", {})
        if cache.get("cache_write_test", {}).get("success") is False:
            recommendations.append("💾 修复缓存系统写入权限问题")

        # 通用建议
        health_score = results.get("health_score", 0)
        if health_score < 60:
            recommendations.append("⚠️ 系统健康状况需要紧急关注和修复")
        elif health_score < 80:
            recommendations.append("🔧 建议进行系统维护和优化")
        else:
            recommendations.append("✅ 系统运行状况良好")

        return recommendations

    def export_diagnostic_report(self, filepath: str) -> bool:
        """导出诊断报告"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.diagnostic_results, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"诊断报告已导出到: {filepath}")
            return True
        except Exception as e:
            logger.error(f"导出诊断报告失败: {e}")
            return False

    def get_summary_report(self) -> str:
        """获取诊断摘要报告"""
        if not self.diagnostic_results:
            return "⚠️ 请先运行系统诊断"

        results = self.diagnostic_results
        health_score = results.get("health_score", 0)

        # 健康状态emoji
        if health_score >= 90:
            health_emoji = "🟢"
            health_desc = "优秀"
        elif health_score >= 80:
            health_emoji = "🟡"
            health_desc = "良好"
        elif health_score >= 60:
            health_emoji = "🟠"
            health_desc = "一般"
        else:
            health_emoji = "🔴"
            health_desc = "需要关注"

        report = f"""
# 🏥 TradingAgents-CN 系统健康检查报告
*诊断时间: {results['diagnostic_time']}*

## {health_emoji} 总体健康评分: {health_score}/100 ({health_desc})

## 📊 各组件状态检查

### 🖥️ 系统环境
"""

        # 各组件状态
        components = [
            ("系统信息", "system_info", "🖥️"),
            ("依赖包", "dependencies", "📦"),
            ("数据源", "data_sources", "📡"),
            ("缓存系统", "cache_system", "💾"),
            ("配置文件", "configuration", "⚙️"),
            ("文件完整性", "file_integrity", "📁"),
            ("网络连通性", "network_connectivity", "🌐")
        ]

        for name, key, emoji in components:
            if key in results:
                status = results[key].get("status", "unknown")
                status_emoji = {
                    "healthy": "✅",
                    "warning": "⚠️",
                    "critical": "❌",
                    "error": "🚫"
                }.get(status, "❓")

                report += f"- {emoji} {name}: {status_emoji} {status}\n"

        # 关键发现
        report += "\n## 🔍 关键发现\n"

        # 数据源状态
        if "data_sources" in results:
            ds_summary = results["data_sources"].get("summary", "")
            report += f"- 📡 数据源状态: {ds_summary}\n"

        # 缺失依赖
        if "dependencies" in results:
            missing = results["dependencies"].get("missing_packages", [])
            if missing:
                report += f"- 📦 缺失依赖包: {', '.join(missing)}\n"

        # 配置问题
        if "configuration" in results:
            config_errors = results["configuration"].get("validation_errors", [])
            if config_errors:
                report += f"- ⚙️ 配置问题: {len(config_errors)}个错误\n"

        # 建议措施
        report += "\n## 💡 优化建议\n"
        recommendations = results.get("recommendations", [])
        for i, rec in enumerate(recommendations[:5], 1):  # 只显示前5个建议
            report += f"{i}. {rec}\n"

        if len(recommendations) > 5:
            report += f"... 还有 {len(recommendations) - 5} 条建议\n"

        report += f"""
---
*运行环境*: {results.get('system_info', {}).get('platform', 'Unknown')}
*项目路径*: {results.get('system_info', {}).get('project_root', 'Unknown')}
*报告生成*: TradingAgents-CN 系统诊断工具
"""

        return report


def run_quick_health_check() -> str:
    """快速健康检查"""
    diagnostics = SystemDiagnostics()
    try:
        results = diagnostics.run_full_diagnostic()
        return diagnostics.get_summary_report()
    except Exception as e:
        return f"⚠️ 系统诊断失败: {str(e)}\n\n请检查系统环境和权限设置。"


if __name__ == "__main__":
    # 运行系统诊断
    print("🔍 开始TradingAgents-CN系统诊断...")
    report = run_quick_health_check()
    print(report)