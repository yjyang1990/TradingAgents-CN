#!/usr/bin/env python3
"""
统一缓存管理器
整合项目中分散的缓存实现，提供统一的缓存接口和生命周期管理
"""

import os
import json
import pickle
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from enum import Enum

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('cache')

# 导入配置管理
from tradingagents.utils.config_loader import load_main_config


class CacheBackend(Enum):
    """缓存后端类型"""
    MEMORY = "memory"
    FILE = "file"
    REDIS = "redis"
    MONGODB = "mongodb"


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    data: Any
    created_at: datetime
    ttl_seconds: int
    metadata: Dict[str, Any] = None

    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        if self.ttl_seconds <= 0:  # 永不过期
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """从字典创建"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class CacheBackendInterface(ABC):
    """缓存后端接口"""

    @abstractmethod
    def get(self, key: str) -> Optional[CacheEntry]:
        """获取缓存项"""
        pass

    @abstractmethod
    def set(self, key: str, entry: CacheEntry) -> bool:
        """设置缓存项"""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """清空缓存"""
        pass

    @abstractmethod
    def keys(self, pattern: str = "*") -> List[str]:
        """获取所有匹配的键"""
        pass

    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        pass


class MemoryCacheBackend(CacheBackendInterface):
    """内存缓存后端"""

    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self._access_order: List[str] = []  # LRU跟踪

    def _cleanup_expired(self):
        """清理过期缓存"""
        current_time = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            self.delete(key)

    def _enforce_size_limit(self):
        """强制执行大小限制（LRU策略）"""
        while len(self.cache) > self.max_size:
            if self._access_order:
                oldest_key = self._access_order.pop(0)
                self.delete(oldest_key)
            else:
                break

    def _update_access_order(self, key: str):
        """更新访问顺序"""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def get(self, key: str) -> Optional[CacheEntry]:
        self._cleanup_expired()
        entry = self.cache.get(key)
        if entry and not entry.is_expired():
            self._update_access_order(key)
            return entry
        elif entry and entry.is_expired():
            self.delete(key)
        return None

    def set(self, key: str, entry: CacheEntry) -> bool:
        try:
            self.cache[key] = entry
            self._update_access_order(key)
            self._enforce_size_limit()
            return True
        except Exception as e:
            logger.error(f"内存缓存设置失败 {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        if key in self.cache:
            del self.cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False

    def clear(self) -> bool:
        self.cache.clear()
        self._access_order.clear()
        return True

    def keys(self, pattern: str = "*") -> List[str]:
        # 简单的模式匹配
        import fnmatch
        return [key for key in self.cache.keys() if fnmatch.fnmatch(key, pattern)]

    def stats(self) -> Dict[str, Any]:
        self._cleanup_expired()
        return {
            "backend": "memory",
            "total_entries": len(self.cache),
            "max_size": self.max_size,
            "memory_usage_mb": sum(len(pickle.dumps(entry)) for entry in self.cache.values()) / (1024 * 1024)
        }


class FileCacheBackend(CacheBackendInterface):
    """文件缓存后端"""

    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "cache_index.json"
        self._load_index()

    def _load_index(self):
        """加载缓存索引"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
            else:
                self.index = {}
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"加载缓存索引失败，创建新索引: {e}")
            self.index = {}

    def _save_index(self):
        """保存缓存索引"""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f)
        except OSError as e:
            logger.error(f"保存缓存索引失败: {e}")

    def _get_file_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"

    def get(self, key: str) -> Optional[CacheEntry]:
        try:
            if key not in self.index:
                return None

            file_path = self._get_file_path(key)
            if not file_path.exists():
                # 清理损坏的索引项
                del self.index[key]
                self._save_index()
                return None

            with open(file_path, 'rb') as f:
                entry_data = pickle.load(f)
                entry = CacheEntry.from_dict(entry_data) if isinstance(entry_data, dict) else entry_data

            if entry.is_expired():
                self.delete(key)
                return None

            return entry
        except (OSError, pickle.PickleError, KeyError, TypeError) as e:
            logger.error(f"文件缓存获取失败 {key}: {e}")
            return None

    def set(self, key: str, entry: CacheEntry) -> bool:
        try:
            file_path = self._get_file_path(key)

            with open(file_path, 'wb') as f:
                entry_data = entry.to_dict()
                pickle.dump(entry_data, f)

            self.index[key] = {
                "file": str(file_path),
                "created_at": entry.created_at.isoformat(),
                "ttl_seconds": entry.ttl_seconds
            }
            self._save_index()
            return True
        except (OSError, pickle.PickleError) as e:
            logger.error(f"文件缓存设置失败 {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        try:
            if key in self.index:
                file_path = self._get_file_path(key)
                if file_path.exists():
                    file_path.unlink()
                del self.index[key]
                self._save_index()
                return True
        except OSError as e:
            logger.error(f"文件缓存删除失败 {key}: {e}")
        return False

    def clear(self) -> bool:
        try:
            for key in list(self.index.keys()):
                self.delete(key)
            return True
        except Exception as e:
            logger.error(f"文件缓存清空失败: {e}")
            return False

    def keys(self, pattern: str = "*") -> List[str]:
        import fnmatch
        return [key for key in self.index.keys() if fnmatch.fnmatch(key, pattern)]

    def stats(self) -> Dict[str, Any]:
        total_size = 0
        valid_entries = 0
        for key in self.index:
            file_path = self._get_file_path(key)
            if file_path.exists():
                total_size += file_path.stat().st_size
                valid_entries += 1

        return {
            "backend": "file",
            "total_entries": valid_entries,
            "index_entries": len(self.index),
            "total_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir)
        }


class UnifiedCacheManager:
    """统一缓存管理器"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化统一缓存管理器

        Args:
            config: 缓存配置，如果为None则从主配置加载
        """
        self.config = config or self._load_cache_config()
        self.backends: Dict[str, CacheBackendInterface] = {}
        self.primary_backend = self.config.get("primary_backend", "file")
        self.fallback_backends = self.config.get("fallback_backends", [])

        # 初始化后端
        self._init_backends()

        logger.info(f"✅ 统一缓存管理器初始化完成，主要后端: {self.primary_backend}")

    def _load_cache_config(self) -> Dict[str, Any]:
        """加载缓存配置"""
        main_config = load_main_config()

        # 默认缓存配置
        default_cache_config = {
            "primary_backend": "file",
            "fallback_backends": ["memory"],
            "backends": {
                "memory": {
                    "max_size": 1000
                },
                "file": {
                    "cache_dir": os.getenv("TRADINGAGENTS_CACHE_DIR", "./cache")
                },
                "redis": {
                    "enabled": os.getenv("REDIS_ENABLED", "false").lower() == "true",
                    "host": os.getenv("REDIS_HOST", "localhost"),
                    "port": int(os.getenv("REDIS_PORT", "6379")),
                    "password": os.getenv("REDIS_PASSWORD"),
                    "db": int(os.getenv("REDIS_DB", "0"))
                }
            },
            "default_ttl": {
                "stock_data": 3600,        # 1小时
                "news_data": 1800,         # 30分钟
                "fundamentals": 86400,     # 24小时
                "market_data": 300,        # 5分钟
            }
        }

        return main_config.get("cache", default_cache_config)

    def _init_backends(self):
        """初始化缓存后端"""
        backend_configs = self.config.get("backends", {})

        # 初始化内存后端
        memory_config = backend_configs.get("memory", {})
        self.backends["memory"] = MemoryCacheBackend(
            max_size=memory_config.get("max_size", 1000)
        )

        # 初始化文件后端
        file_config = backend_configs.get("file", {})
        self.backends["file"] = FileCacheBackend(
            cache_dir=file_config.get("cache_dir", "./cache")
        )

        # 可选：初始化Redis后端
        redis_config = backend_configs.get("redis", {})
        if redis_config.get("enabled", False):
            try:
                self._init_redis_backend(redis_config)
                logger.info("✅ Redis缓存后端已启用")
            except ImportError:
                logger.warning("⚠️ Redis不可用，跳过Redis后端初始化")
            except Exception as e:
                logger.error(f"❌ Redis后端初始化失败: {e}")

    def _init_redis_backend(self, config: Dict[str, Any]):
        """初始化Redis后端（如果可用）"""
        # Redis后端实现留待后续扩展
        logger.info("Redis后端暂未实现，使用其他后端")

    def _get_cache_key(self, namespace: str, key: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [namespace, key]
        if kwargs:
            # 将kwargs按键排序确保一致性
            sorted_params = sorted(kwargs.items())
            params_str = "&".join(f"{k}={v}" for k, v in sorted_params)
            key_parts.append(params_str)

        return ":".join(key_parts)

    def _get_ttl(self, data_type: str = "default") -> int:
        """获取TTL秒数"""
        default_ttls = self.config.get("default_ttl", {})
        return default_ttls.get(data_type, 3600)  # 默认1小时

    def get(self, namespace: str, key: str, **kwargs) -> Any:
        """
        获取缓存数据

        Args:
            namespace: 命名空间
            key: 缓存键
            **kwargs: 额外参数（会影响缓存键）

        Returns:
            缓存的数据，如果不存在则返回None
        """
        cache_key = self._get_cache_key(namespace, key, **kwargs)

        # 尝试主要后端
        if self.primary_backend in self.backends:
            entry = self.backends[self.primary_backend].get(cache_key)
            if entry:
                logger.debug(f"缓存命中 ({self.primary_backend}): {cache_key}")
                return entry.data

        # 尝试备用后端
        for backend_name in self.fallback_backends:
            if backend_name in self.backends:
                entry = self.backends[backend_name].get(cache_key)
                if entry:
                    logger.debug(f"缓存命中 ({backend_name}): {cache_key}")
                    # 将数据写回主要后端
                    self.set(namespace, key, entry.data, ttl_seconds=entry.ttl_seconds, **kwargs)
                    return entry.data

        logger.debug(f"缓存未命中: {cache_key}")
        return None

    def set(self, namespace: str, key: str, data: Any, data_type: str = "default",
            ttl_seconds: int = None, **kwargs) -> bool:
        """
        设置缓存数据

        Args:
            namespace: 命名空间
            key: 缓存键
            data: 要缓存的数据
            data_type: 数据类型（影响默认TTL）
            ttl_seconds: TTL秒数，如果为None则使用默认值
            **kwargs: 额外参数（会影响缓存键）

        Returns:
            是否设置成功
        """
        cache_key = self._get_cache_key(namespace, key, **kwargs)

        if ttl_seconds is None:
            ttl_seconds = self._get_ttl(data_type)

        entry = CacheEntry(
            key=cache_key,
            data=data,
            created_at=datetime.now(),
            ttl_seconds=ttl_seconds,
            metadata={"data_type": data_type, "namespace": namespace}
        )

        # 写入主要后端
        success = False
        if self.primary_backend in self.backends:
            success = self.backends[self.primary_backend].set(cache_key, entry)
            if success:
                logger.debug(f"缓存设置成功 ({self.primary_backend}): {cache_key}")

        return success

    def delete(self, namespace: str, key: str, **kwargs) -> bool:
        """删除缓存项"""
        cache_key = self._get_cache_key(namespace, key, **kwargs)

        success = True
        for backend_name, backend in self.backends.items():
            if not backend.delete(cache_key):
                success = False
            else:
                logger.debug(f"缓存删除成功 ({backend_name}): {cache_key}")

        return success

    def clear_namespace(self, namespace: str) -> bool:
        """清空指定命名空间的所有缓存"""
        pattern = f"{namespace}:*"

        success = True
        for backend_name, backend in self.backends.items():
            try:
                keys = backend.keys(pattern)
                for key in keys:
                    if not backend.delete(key):
                        success = False
                logger.info(f"命名空间 {namespace} 缓存清空成功 ({backend_name})")
            except Exception as e:
                logger.error(f"清空命名空间 {namespace} 失败 ({backend_name}): {e}")
                success = False

        return success

    def clear_all(self) -> bool:
        """清空所有缓存"""
        success = True
        for backend_name, backend in self.backends.items():
            try:
                if not backend.clear():
                    success = False
                else:
                    logger.info(f"缓存清空成功 ({backend_name})")
            except Exception as e:
                logger.error(f"缓存清空失败 ({backend_name}): {e}")
                success = False

        return success

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有后端的统计信息"""
        stats = {}
        for backend_name, backend in self.backends.items():
            try:
                stats[backend_name] = backend.stats()
            except Exception as e:
                logger.error(f"获取后端统计失败 ({backend_name}): {e}")
                stats[backend_name] = {"error": str(e)}

        return stats

    def cleanup_expired(self) -> Dict[str, int]:
        """清理所有过期缓存项"""
        cleanup_stats = {}

        for backend_name, backend in self.backends.items():
            try:
                if isinstance(backend, MemoryCacheBackend):
                    backend._cleanup_expired()
                    cleanup_stats[backend_name] = "cleaned"
                elif isinstance(backend, FileCacheBackend):
                    # 对文件后端，需要遍历清理
                    keys = backend.keys()
                    cleaned = 0
                    for key in keys:
                        entry = backend.get(key)
                        if entry is None:  # get方法会自动清理过期项
                            cleaned += 1
                    cleanup_stats[backend_name] = cleaned
                else:
                    cleanup_stats[backend_name] = "not_supported"
            except Exception as e:
                logger.error(f"清理过期缓存失败 ({backend_name}): {e}")
                cleanup_stats[backend_name] = f"error: {e}"

        return cleanup_stats


# 全局缓存管理器实例
_global_cache_manager = None


def get_unified_cache_manager() -> UnifiedCacheManager:
    """获取全局统一缓存管理器实例"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = UnifiedCacheManager()
    return _global_cache_manager


def cache_decorator(namespace: str, data_type: str = "default", ttl_seconds: int = None):
    """
    缓存装饰器

    Args:
        namespace: 命名空间
        data_type: 数据类型
        ttl_seconds: TTL秒数

    Usage:
        @cache_decorator("stock_data", "market_data", ttl_seconds=300)
        def get_stock_price(symbol: str, date: str) -> float:
            # 实际获取数据的代码
            return fetch_stock_price(symbol, date)
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            cache_manager = get_unified_cache_manager()

            # 生成缓存键（基于函数名和参数）
            func_name = func.__name__
            cache_key = f"{func_name}_{hash(str(args) + str(sorted(kwargs.items())))}"

            # 尝试从缓存获取
            cached_result = cache_manager.get(namespace, cache_key)
            if cached_result is not None:
                logger.debug(f"缓存装饰器命中: {func_name}")
                return cached_result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(namespace, cache_key, result, data_type, ttl_seconds)
            logger.debug(f"缓存装饰器设置: {func_name}")

            return result

        return wrapper
    return decorator