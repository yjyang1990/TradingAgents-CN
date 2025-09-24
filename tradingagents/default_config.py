import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./data"),
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "o4-mini",
    "quick_think_llm": "gpt-4o-mini",
    "backend_url": "https://hk-api.gptbest.vip/v1",
    "custom_openai_base_url": "https://hk-api.gptbest.vip/v1",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Tool settings - 从环境变量读取，提供默认值
    "online_tools": os.getenv("ONLINE_TOOLS_ENABLED", "false").lower() == "true",
    "online_news": os.getenv("ONLINE_NEWS_ENABLED", "true").lower() == "true",
    "realtime_data": os.getenv("REALTIME_DATA_ENABLED", "false").lower() == "true",

    # Parallel execution settings - 并行执行配置
    "parallel_analysts": os.getenv("PARALLEL_ANALYSTS_ENABLED", "false").lower() == "true",
    "max_parallel_workers": int(os.getenv("MAX_PARALLEL_WORKERS", "4")),
    "analyst_timeout": int(os.getenv("ANALYST_TIMEOUT", "300")),  # 单个分析师超时时间（秒）
    "parallel_retry_count": int(os.getenv("PARALLEL_RETRY_COUNT", "2")),  # 并行执行失败重试次数

    # Note: Database and cache configuration is now managed by .env file and config.database_manager
    # No database/cache settings in default config to avoid configuration conflicts
}
