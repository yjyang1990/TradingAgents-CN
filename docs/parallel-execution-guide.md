# TradingAgents 并行执行指南

## 📋 概述

TradingAgents 现已支持**并行分析师执行**，可以同时运行多个分析师，显著提升系统性能。这个功能允许市场分析师、基本面分析师、新闻分析师和社交媒体分析师同时工作，而不是按顺序执行。

## 🚀 性能提升

**预期性能提升:**
- **执行时间**: 从 4-6分钟 缩短到 1-2分钟
- **资源利用**: CPU使用率提升 3-4倍
- **稳定性**: 单个分析师失败不影响其他分析师
- **扩展性**: 轻松添加新分析师而不影响性能

## ⚙️ 配置选项

### 环境变量配置

```bash
# 启用并行分析师执行
PARALLEL_ANALYSTS_ENABLED=true

# 最大并行工作线程数（建议：CPU核心数）
MAX_PARALLEL_WORKERS=4

# 单个分析师超时时间（秒）
ANALYST_TIMEOUT=300

# 并行执行失败重试次数
PARALLEL_RETRY_COUNT=2
```

### 代码配置

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 创建配置
config = DEFAULT_CONFIG.copy()

# 启用并行执行
config["parallel_analysts"] = True
config["max_parallel_workers"] = 4      # 4个并行线程
config["analyst_timeout"] = 300         # 5分钟超时
config["parallel_retry_count"] = 2      # 重试次数

# 创建TradingAgents实例
ta = TradingAgentsGraph(debug=True, config=config)

# 执行分析（自动使用并行模式）
_, decision = ta.propagate("NVDA", "2024-05-10")
```

## 🔧 支持的分析师

并行执行支持以下分析师类型：

- ✅ **market** - 市场分析师
- ✅ **social** - 社交媒体分析师
- ✅ **news** - 新闻分析师
- ✅ **fundamentals** - 基本面分析师
- ✅ **china_market** - 中国市场分析师

## 📊 性能监控

系统会自动记录并行执行的性能数据：

```python
# 获取性能数据
if hasattr(ta, 'curr_state') and ta.curr_state:
    perf_data = ta.curr_state.get("parallel_performance", {})

    print(f"总并行时间: {perf_data.get('total_parallel_time')}秒")
    print(f"成功率: {perf_data.get('success_rate')}")
    print(f"成功/总数: {perf_data.get('successful_count')}/{perf_data.get('total_count')}")

    # 各分析师详细性能
    for perf in perf_data.get("analyst_performances", []):
        status = "✅" if perf["success"] else "❌"
        print(f"{status} {perf['analyst']}: {perf['duration']:.2f}s")
```

## 🧪 性能测试

使用提供的测试脚本对比串行与并行性能：

```bash
# 运行性能测试
python test_parallel_execution.py
```

测试脚本会：
1. 执行串行模式测试
2. 执行并行模式测试
3. 对比性能差异
4. 测试不同配置的效果

## 🛠️ 最佳配置建议

### CPU核心数配置
```python
import os

# 根据CPU核心数设置工作线程
cpu_count = os.cpu_count()
config["max_parallel_workers"] = min(cpu_count, 6)  # 不超过6个线程
```

### 超时时间配置
```python
# 根据模型类型调整超时
if config["llm_provider"] == "openai":
    config["analyst_timeout"] = 180      # 3分钟
elif config["llm_provider"] == "deepseek":
    config["analyst_timeout"] = 300      # 5分钟
else:
    config["analyst_timeout"] = 240      # 4分钟
```

### LLM提供商优化
```python
# 针对不同LLM提供商的并行优化
if config["llm_provider"] == "openai":
    config["max_parallel_workers"] = 4   # OpenAI支持高并发
elif config["llm_provider"] == "deepseek":
    config["max_parallel_workers"] = 2   # DeepSeek限制并发
```

## 🔍 故障排除

### 常见问题

**Q: 并行执行失败怎么办？**
A: 系统会自动回退到串行模式，确保分析能够完成。

**Q: 某个分析师超时了？**
A: 增加 `analyst_timeout` 设置，或减少 `max_parallel_workers`。

**Q: 内存使用过高？**
A: 减少 `max_parallel_workers`，避免同时运行过多分析师。

### 调试模式

```python
# 启用详细日志
import logging
logging.getLogger("parallel_analysts").setLevel(logging.DEBUG)

# 创建实例时启用调试
ta = TradingAgentsGraph(debug=True, config=config)
```

## 📈 使用示例

### 基本用法

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
import time

# 配置并行执行
config = DEFAULT_CONFIG.copy()
config["parallel_analysts"] = True
config["max_parallel_workers"] = 4

# 创建实例
ta = TradingAgentsGraph(config=config)

# 测量执行时间
start_time = time.time()
_, decision = ta.propagate("AAPL", "2024-05-10")
execution_time = time.time() - start_time

print(f"执行时间: {execution_time:.2f}秒")
print(f"决策结果: {decision}")
```

### 批量分析

```python
# 并行分析多只股票
stocks = ["AAPL", "TSLA", "NVDA", "MSFT"]
results = {}

for stock in stocks:
    print(f"🔍 分析 {stock}...")
    start_time = time.time()

    _, decision = ta.propagate(stock, "2024-05-10")
    execution_time = time.time() - start_time

    results[stock] = {
        "decision": decision,
        "time": execution_time
    }

    print(f"✅ {stock} 分析完成，耗时 {execution_time:.2f}秒")

# 输出总结
total_time = sum(r["time"] for r in results.values())
print(f"\n📊 总执行时间: {total_time:.2f}秒")
```

## 🔄 从串行模式迁移

如果你目前使用串行模式，迁移到并行模式非常简单：

### 旧代码（串行）
```python
config = DEFAULT_CONFIG.copy()
# 默认为串行执行
ta = TradingAgentsGraph(config=config)
```

### 新代码（并行）
```python
config = DEFAULT_CONFIG.copy()
config["parallel_analysts"] = True    # 只需添加这一行！
ta = TradingAgentsGraph(config=config)
```

## 🚀 高级功能

### 自定义分析师组合

```python
# 选择特定分析师进行并行执行
selected_analysts = ["market", "fundamentals", "news"]

ta = TradingAgentsGraph(
    selected_analysts=selected_analysts,
    config=config
)
```

### 条件并行执行

```python
# 根据条件启用并行
import os

config["parallel_analysts"] = (
    os.getenv("ENVIRONMENT") == "production" and
    os.cpu_count() >= 4
)
```

## 📚 技术架构

并行执行基于以下核心组件：

1. **ParallelAnalystsExecutor** - 并行执行管理器
2. **ThreadPoolExecutor** - 线程池实现
3. **Performance Monitor** - 性能监控
4. **State Merger** - 结果合并器

详细技术文档请参考源码：
- `tradingagents/graph/parallel_analysts.py`
- `tradingagents/graph/setup.py`

---

🎉 **恭喜！** 您现在可以使用TradingAgents的并行分析师功能，享受更快的分析速度和更好的系统性能！