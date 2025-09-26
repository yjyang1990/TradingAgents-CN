# AI调用详细日志记录功能

## 概述

为了帮助开发者进行调试工作，我们为TradingAgents-CN项目添加了全面的AI调用详细日志记录功能。该功能可以记录所有AI模型调用的详细参数、返回结果、执行时间、Token使用量等信息，大大提升了调试效率。

## 主要组件

### 1. AI调用日志记录器 (`tradingagents/utils/ai_call_logger.py`)

核心组件，提供了多个装饰器和工具函数：

#### 主要装饰器：
- `@log_ai_call(provider, model, log_input=True, log_output=True, log_tokens=True)` - 通用AI调用日志装饰器
- `@log_ai_debug()` - 调试模式装饰器，自动检测提供商和模型
- `@log_model_invoke(provider, model)` - 专用于model.invoke()调用
- `@log_chat_completion(provider, model)` - 专用于聊天完成调用

#### 记录内容：
- **输入参数**：消息内容、温度、token限制等
- **输出结果**：AI响应内容、附加信息等
- **执行信息**：调用时间、执行耗时、成功/失败状态
- **Token统计**：输入token、输出token、总计、成本估算
- **调用追踪**：唯一调用ID，便于关联相关日志

### 2. LLM增强器 (`tradingagents/utils/llm_enhancer.py`)

动态增强现有LLM实例，为其添加详细日志记录功能：

#### 主要功能：
- `enhance_llm_with_logging()` - 为LLM实例添加日志记录
- `batch_enhance_llms()` - 批量增强多个LLM实例
- `enhance_all_llm_methods()` - 全面增强LLM的所有方法
- 支持Pydantic模型的安全方法覆写

#### 兼容性：
- ✅ OpenAI ChatGPT
- ✅ DeepSeek
- ✅ Anthropic Claude
- ✅ 阿里百炼 DashScope
- ✅ Google AI
- ✅ 自定义OpenAI兼容端点

### 3. DeepSeek适配器增强 (`tradingagents/llm_adapters/deepseek_adapter.py`)

为DeepSeek适配器添加了内置的详细日志记录：

- 在`_generate()`和`invoke()`方法上添加了`@log_ai_call`装饰器
- 记录Token使用量统计
- 提供成本计算和追踪

## 自动集成

### TradingGraph自动增强

在`tradingagents/graph/trading_graph.py`中，所有LLM实例在初始化后会自动增强：

```python
# 增强LLM实例，添加详细的AI调用日志记录
self.deep_thinking_llm = enhance_llm_with_logging(
    llm_instance=self.deep_thinking_llm,
    provider=self.config["llm_provider"],
    model=self.config["deep_think_llm"],
    enable_detailed_logging=True
)

self.quick_thinking_llm = enhance_llm_with_logging(
    llm_instance=self.quick_thinking_llm,
    provider=self.config["llm_provider"],
    model=self.config["quick_think_llm"],
    enable_detailed_logging=True
)
```

## 日志输出示例

### AI调用开始
```
🤖 [AI调用开始] deepseek/deepseek-chat - _generate [ID: 41966dba]
```

### 输入参数详情 (DEBUG级别)
```
📝 [AI调用输入] [ID: 41966dba] 详细参数
  - messages: 2条消息，总字符数: 156
  - temperature: 0.1
  - max_tokens: 3200
  - session_id: analysis_session_001
```

### 调用成功
```
✅ [AI调用成功] deepseek/deepseek-chat - _generate [ID: 41966dba] (耗时: 2.34s)
```

### 输出结果详情 (DEBUG级别)
```
📤 [AI调用输出] [ID: 41966dba] 详细结果
  - result_type: ChatResult
  - content: "根据市场分析，AAPL股票当前表现..."
  - content_length: 892
```

### Token使用统计
```
💰 [Token使用] [ID: 41966dba] 输入: 156, 输出: 234, 总计: 390, 成本: ¥0.002340
```

## 使用方式

### 1. 自动启用（推荐）

使用TradingGraph时会自动启用AI调用日志记录：

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph

graph = TradingAgentsGraph(
    selected_analysts=["market", "fundamentals"],
    debug=True,  # 启用调试模式
    config=your_config
)
# AI调用日志会自动记录
```

### 2. 手动装饰器使用

```python
from tradingagents.utils.ai_call_logger import log_ai_call

@log_ai_call(provider="openai", model="gpt-4", log_input=True, log_output=True)
def my_ai_function(messages, **kwargs):
    # 你的AI调用代码
    return llm.invoke(messages, **kwargs)
```

### 3. 动态增强现有LLM

```python
from tradingagents.utils.llm_enhancer import enhance_llm_with_logging

# 增强现有LLM实例
enhanced_llm = enhance_llm_with_logging(
    llm_instance=your_llm,
    provider="deepseek",
    model="deepseek-chat",
    enable_detailed_logging=True
)
```

## 配置选项

### 日志级别控制

- **INFO级别**：显示调用开始、成功/失败、Token统计
- **DEBUG级别**：额外显示详细的输入参数和输出结果

### 记录内容控制

```python
@log_ai_call(
    provider="openai",
    model="gpt-4",
    log_input=True,     # 是否记录输入参数详情
    log_output=True,    # 是否记录输出结果详情
    log_tokens=True,    # 是否记录Token使用情况
    debug_level="INFO"  # 日志级别
)
```

### 生产环境建议

```python
# 生产环境：只记录关键信息，减少日志量
@log_ai_call(
    provider="deepseek",
    log_input=False,    # 关闭输入详情
    log_output=False,   # 关闭输出详情
    log_tokens=True     # 保留Token统计用于成本监控
)
```

## 调试场景应用

### 1. 性能分析
- 监控AI调用耗时，识别性能瓶颈
- 分析Token使用效率

### 2. 成本控制
- 实时监控Token消费
- 成本预算和优化

### 3. 问题诊断
- 快速定位失败的AI调用
- 检查输入参数是否正确
- 验证输出结果格式

### 4. 功能验证
- 确保AI调用按预期执行
- 追踪复杂工作流中的AI调用顺序

## 测试验证

运行测试脚本验证功能：

```bash
python scripts/test_ai_logging.py
```

运行演示示例：

```bash
python examples/demo_ai_logging.py
```

## 技术特性

### 安全性
- 自动截断过长的日志内容，避免敏感信息泄露
- 支持配置哪些内容需要记录

### 兼容性
- 支持所有主流LLM提供商
- 自动处理Pydantic模型的方法覆写限制
- 向后兼容现有代码

### 性能
- 日志记录对AI调用性能影响极小
- 支持异步和同步调用
- 内存友好的日志管理

### 可扩展性
- 易于为新的LLM提供商添加支持
- 装饰器模式便于自定义日志格式
- 支持插件式扩展

## 总结

通过这套完整的AI调用日志记录系统，开发者可以：

1. **快速调试** - 详细的调用信息帮助快速定位问题
2. **性能监控** - 实时了解AI调用的性能表现
3. **成本控制** - 精确统计Token使用和成本
4. **质量保证** - 验证AI调用的输入输出正确性
5. **系统优化** - 基于数据进行系统调优

该功能已完全集成到TradingAgents-CN中，无需额外配置即可开始使用。