#!/usr/bin/env python3
"""
配置加载工具
支持从JSON文件和环境变量加载配置，并与DEFAULT_CONFIG合并
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Union

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('config')


def load_config_from_file(config_path: Union[str, Path]) -> Dict[str, Any]:
    """从JSON文件加载配置"""
    try:
        config_path = Path(config_path)
        if not config_path.exists():
            logger.info(f"配置文件不存在: {config_path}")
            return {}

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 移除注释字段
        config = {k: v for k, v in config.items() if not k.startswith('_')}

        logger.info(f"✅ 从文件加载配置: {config_path}")
        return config

    except json.JSONDecodeError as e:
        logger.error(f"❌ 配置文件JSON格式错误: {e}")
        return {}
    except FileNotFoundError as e:
        logger.error(f"❌ 配置文件未找到: {e}")
        return {}
    except PermissionError as e:
        logger.error(f"❌ 配置文件权限不足: {e}")
        return {}
    except OSError as e:
        logger.error(f"❌ 配置文件系统错误: {e}")
        return {}
    except UnicodeDecodeError as e:
        logger.error(f"❌ 配置文件编码错误: {e}")
        return {}


def load_config_from_env() -> Dict[str, Any]:
    """从环境变量加载配置"""
    env_config = {}

    # 定义环境变量映射
    env_mappings = {
        'LLM_PROVIDER': 'llm_provider',
        'BACKEND_URL': 'backend_url',
        'DEEP_THINK_LLM': 'deep_think_llm',
        'QUICK_THINK_LLM': 'quick_think_llm',
        'MAX_DEBATE_ROUNDS': 'max_debate_rounds',
        'ONLINE_TOOLS': 'online_tools',
        'PARALLEL_ANALYSTS': 'parallel_analysts',
        'MAX_PARALLEL_WORKERS': 'max_parallel_workers',
        'ANALYST_TIMEOUT': 'analyst_timeout'
    }

    for env_var, config_key in env_mappings.items():
        value = os.getenv(env_var)
        if value is not None:
            # 处理不同数据类型
            if config_key in ['max_debate_rounds', 'max_parallel_workers', 'analyst_timeout']:
                try:
                    env_config[config_key] = int(value)
                except ValueError:
                    logger.warning(f"⚠️ 环境变量 {env_var} 值无效，忽略: {value}")
                    continue
            elif config_key in ['online_tools', 'parallel_analysts']:
                env_config[config_key] = value.lower() in ['true', '1', 'yes', 'on']
            else:
                env_config[config_key] = value

            logger.info(f"🔧 从环境变量加载: {config_key} = {env_config[config_key]}")

    return env_config


def merge_configs(base_config: Dict[str, Any], *configs: Dict[str, Any]) -> Dict[str, Any]:
    """合并多个配置，后面的配置会覆盖前面的配置"""
    merged = base_config.copy()

    for config in configs:
        merged.update(config)

    return merged


def load_main_config(config_file: str = None) -> Dict[str, Any]:
    """加载主配置文件

    优先级：环境变量 > 配置文件 > DEFAULT_CONFIG
    """
    from tradingagents.default_config import DEFAULT_CONFIG

    # 1. 基础配置
    config = DEFAULT_CONFIG.copy()

    # 2. 配置文件
    if config_file is None:
        # 查找默认配置文件位置
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / "config" / "main_config.json"

    file_config = load_config_from_file(config_file)

    # 3. 环境变量配置
    env_config = load_config_from_env()

    # 4. 合并配置（环境变量优先级最高）
    final_config = merge_configs(config, file_config, env_config)

    logger.info(f"📋 最终配置加载完成，共 {len(final_config)} 个配置项")
    if file_config:
        logger.info(f"📄 配置文件覆盖项: {list(file_config.keys())}")
    if env_config:
        logger.info(f"🔧 环境变量覆盖项: {list(env_config.keys())}")

    return final_config