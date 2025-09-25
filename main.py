from tradingagents.graph.trading_graph import TradingAgentsGraph

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('default')

# 导入配置加载器
from tradingagents.utils.config_loader import load_main_config

# 从配置文件和环境变量加载配置
config = load_main_config()

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate("NVDA", "2024-05-10")
logger.info(f"📊 分析决策结果: {decision}")

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
