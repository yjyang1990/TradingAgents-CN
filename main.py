from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('default')


# Create a custom config
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"  # Use a different model
config["backend_url"] = "https://hk-api.gptbest.vip/v1"  # Use a different backend
config["deep_think_llm"] = "gpt-4.1"  # Use a different model
config["quick_think_llm"] = "gpt-4.1"  # Use a different model
config["max_debate_rounds"] = 1  # Increase debate rounds
config["online_tools"] = True  # Enable online tools

# 启用并行分析师执行 - 新功能!
config["parallel_analysts"] = True        # 启用并行执行
config["max_parallel_workers"] = 4        # 4个并行工作线程
config["analyst_timeout"] = 300           # 5分钟超时

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate("NVDA", "2024-05-10")
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
