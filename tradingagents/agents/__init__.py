# 使用延迟导入优化模块加载性能
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .utils.agent_utils import Toolkit, create_msg_delete
    from .utils.agent_states import AgentState, InvestDebateState, RiskDebateState
    from .utils.memory import FinancialSituationMemory

# 延迟导入装饰器
def _lazy_import(name, module_path):
    """延迟导入函数"""
    def __getattr__(attr_name):
        if attr_name == name:
            module = __import__(module_path, fromlist=[name])
            return getattr(module, name)
        raise AttributeError(f"module '{__name__}' has no attribute '{attr_name}'")
    return __getattr__

# 只在模块级别保留最基础的导入
try:
    from tradingagents.utils.logging_init import get_logger
    logger = get_logger("default")
except ImportError:
    logger = None

# 动态导入实现
def __getattr__(name):
    """动态导入函数，只在首次访问时导入对应模块"""
    import_map = {
        # 工具类
        'Toolkit': ('tradingagents.agents.utils.agent_utils', 'Toolkit'),
        'create_msg_delete': ('tradingagents.agents.utils.agent_utils', 'create_msg_delete'),

        # 状态类
        'AgentState': ('tradingagents.agents.utils.agent_states', 'AgentState'),
        'InvestDebateState': ('tradingagents.agents.utils.agent_states', 'InvestDebateState'),
        'RiskDebateState': ('tradingagents.agents.utils.agent_states', 'RiskDebateState'),

        # 内存类
        'FinancialSituationMemory': ('tradingagents.agents.utils.memory', 'FinancialSituationMemory'),

        # 分析师
        'create_fundamentals_analyst': ('tradingagents.agents.analysts.fundamentals_analyst', 'create_fundamentals_analyst'),
        'create_market_analyst': ('tradingagents.agents.analysts.market_analyst', 'create_market_analyst'),
        'create_news_analyst': ('tradingagents.agents.analysts.news_analyst', 'create_news_analyst'),
        'create_social_media_analyst': ('tradingagents.agents.analysts.social_media_analyst', 'create_social_media_analyst'),

        # 研究员
        'create_bear_researcher': ('tradingagents.agents.researchers.bear_researcher', 'create_bear_researcher'),
        'create_bull_researcher': ('tradingagents.agents.researchers.bull_researcher', 'create_bull_researcher'),

        # 风险管理
        'create_risky_debator': ('tradingagents.agents.risk_mgmt.aggresive_debator', 'create_risky_debator'),
        'create_safe_debator': ('tradingagents.agents.risk_mgmt.conservative_debator', 'create_safe_debator'),
        'create_neutral_debator': ('tradingagents.agents.risk_mgmt.neutral_debator', 'create_neutral_debator'),

        # 管理者
        'create_research_manager': ('tradingagents.agents.managers.research_manager', 'create_research_manager'),
        'create_risk_manager': ('tradingagents.agents.managers.risk_manager', 'create_risk_manager'),

        # 交易者
        'create_trader': ('tradingagents.agents.trader.trader', 'create_trader'),
    }

    if name in import_map:
        module_path, attr_name = import_map[name]
        try:
            module = __import__(module_path, fromlist=[attr_name])
            return getattr(module, attr_name)
        except ImportError as e:
            if logger:
                logger.warning(f"延迟导入失败 {name}: {e}")
            raise ImportError(f"无法导入 {name}: {e}")

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "FinancialSituationMemory",
    "Toolkit",
    "AgentState",
    "create_msg_delete",
    "InvestDebateState",
    "RiskDebateState",
    "create_bear_researcher",
    "create_bull_researcher",
    "create_research_manager",
    "create_fundamentals_analyst",
    "create_market_analyst",
    "create_neutral_debator",
    "create_news_analyst",
    "create_risky_debator",
    "create_risk_manager",
    "create_safe_debator",
    "create_social_media_analyst",
    "create_trader",
]
