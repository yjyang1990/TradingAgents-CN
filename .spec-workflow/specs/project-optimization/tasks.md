# 项目优化任务文档

- [x] 1. 清理requirements.txt文件
  - 文件: requirements.txt (删除)
  - 备份现有文件到.backup/目录
  - 验证pyproject.toml包含所有必需依赖
  - 目的: 统一依赖管理，避免冲突
  - _Leverage: pyproject.toml现有依赖列表_
  - _Requirements: 需求1_
  - _Prompt: 实现spec project-optimization的任务，首先运行spec-workflow-guide获取工作流指导然后实现任务：Role: DevOps工程师，专门负责依赖管理和项目配置 | Task: 安全删除requirements.txt文件，确保pyproject.toml包含所有必需的依赖项，按需求1进行依赖管理标准化 | Restrictions: 必须先备份文件，不能删除pyproject.toml中缺失的依赖，确保安装流程不受影响 | Success: requirements.txt已删除，pyproject.toml完整，pip安装正常工作 | 在tasks.md中将此任务标记为进行中[-]，完成后标记为已完成[x]_

- [x] 2. 修复导入语句和顺序
  - 文件: tradingagents/**/*.py (多个文件)
  - 移除所有 import * 语句，替换为具体导入
  - 修复导入顺序，遵循PEP8规范
  - 修复examples/my_stock_analysis.py:121的导入位置问题
  - 目的: 提高代码质量和可读性
  - _Leverage: 现有导入模式，AST解析_
  - _Requirements: 需求2_
  - _Prompt: 实现spec project-optimization的任务，首先运行spec-workflow-guide获取工作流指导然后实现任务：Role: Python代码质量专家，专长于代码重构和PEP8标准 | Task: 修复所有Python文件中的导入问题，移除import *语句，修正导入顺序，特别处理examples/my_stock_analysis.py的导入问题，按需求2改进代码质量 | Restrictions: 必须保持功能完全不变，不能破坏现有模块引用，确保所有导入都能正常工作 | Success: 无import *语句，导入顺序符合PEP8，所有文件正常导入 | 在tasks.md中将此任务标记为进行中[-]，完成后标记为已完成[x]_

- [x] 3. 统一日志系统，替换print语句
  - 文件: 262个包含print语句的Python文件
  - 将所有print()替换为统一的logger调用
  - 保持相同的输出内容和格式
  - 确保日志级别适当(info/debug/warning/error)
  - 目的: 统一日志管理，提升调试能力
  - _Leverage: tradingagents.utils.logging_manager现有日志系统_
  - _Requirements: 需求2_
  - _Prompt: 实现spec project-optimization的任务，首先运行spec-workflow-guide获取工作流指导然后实现任务：Role: 系统工程师，专长于日志系统集成和代码重构 | Task: 将所有print语句转换为统一的日志调用，使用现有logging_manager系统，保持输出内容不变，按需求2统一日志系统 | Restrictions: 必须保持输出格式和内容完全一致，不能影响用户体验，确保日志级别合理 | Success: 无print语句，统一使用logger，输出效果相同 | 在tasks.md中将此任务标记为进行中[-]，完成后标记为已完成[x]_

- [x] 4. 清理TDX弃用代码
  - 文件: tradingagents/dataflows/tdx_utils.py, data_source_manager.py等
  - 移除所有TDX数据源相关代码和引用
  - 清理弃用警告和相关测试文件
  - 更新文档，移除TDX相关说明
  - 目的: 减少维护负担，清理冗余代码
  - _Leverage: grep搜索TDX引用，现有数据源架构_
  - _Requirements: 需求3_
  - _Prompt: 实现spec project-optimization的任务，首先运行spec-workflow-guide获取工作流指导然后实现任务：Role: 代码维护工程师，专门负责遗留代码清理和架构优化 | Task: 完全移除TDX相关的弃用代码，包括tdx_utils.py和所有引用，清理相关测试和文档，按需求3进行弃用代码清理 | Restrictions: 必须确保不影响其他数据源功能，保持Tushare等数据源正常工作，不能删除仍在使用的代码 | Success: 无TDX相关代码，其他数据源正常，系统功能完整 | 在tasks.md中将此任务标记为进行中[-]，完成后标记为已完成[x]_

- [x] 5. 移除其他弃用函数
  - 文件: web/utils/analysis_runner.py等包含弃用标记的文件
  - 移除generate_demo_results_deprecated等弃用函数
  - 清理所有标记为"已弃用"、"deprecated"的代码块
  - 更新调用这些函数的代码
  - 目的: 简化代码库，移除无用代码
  - _Leverage: grep搜索弃用标记，现有功能架构_
  - _Requirements: 需求3_
  - _Prompt: 实现spec project-optimization的任务，首先运行spec-workflow-guide获取工作流指导然后实现任务：Role: 代码重构专家，专门负责清理弃用代码和维护代码健康 | Task: 移除所有明确标记为弃用的函数和代码块，如generate_demo_results_deprecated，更新相关调用，按需求3清理弃用代码 | Restrictions: 只删除明确标记为弃用的代码，不能删除仍在使用的功能，确保调用者有替代方案 | Success: 无弃用标记的代码，相关调用已更新或移除 | 在tasks.md中将此任务标记为进行中[-]，完成后标记为已完成[x]_

- [x] 6. 配置外部化 - 提取main.py硬编码配置
  - 文件: main.py, 新建config/optimization.json
  - 将main.py中的硬编码配置移至配置文件
  - 创建配置模板和环境变量支持
  - 保持DEFAULT_CONFIG作为fallback机制
  - 目的: 提高配置灵活性，支持不同环境
  - _Leverage: 现有DEFAULT_CONFIG系统，环境变量处理_
  - _Requirements: 需求4_
  - _Prompt: 实现spec project-optimization的任务，首先运行spec-workflow-guide获取工作流指导然后实现任务：Role: 配置管理专家，专长于配置外部化和环境管理 | Task: 将main.py中硬编码的API端点、模型配置等移至外部配置文件，支持环境变量覆盖，保持DEFAULT_CONFIG作为fallback，按需求4实现配置外部化 | Restrictions: 必须保持向后兼容，DEFAULT_CONFIG仍可用，不能破坏现有用户配置 | Success: main.py无硬编码配置，支持配置文件和环境变量 | 在tasks.md中将此任务标记为进行中[-]，完成后标记为已完成[x]_

- [x] 7. 配置外部化 - 处理其他硬编码配置
  - 文件: examples/my_stock_analysis.py等包含硬编码的文件
  - 提取API密钥检查、模型配置等硬编码部分
  - 统一使用环境变量和配置文件
  - 提供配置示例和文档
  - 目的: 完善配置管理，提升用户体验
  - _Leverage: 现有环境变量处理，配置管理模式_
  - _Requirements: 需求4_
  - _Prompt: 实现spec project-optimization的任务，首先运行spec-workflow-guide获取工作流指导然后实现任务：Role: 系统配置工程师，专门处理配置标准化和用户体验优化 | Task: 处理examples等文件中的硬编码配置，统一配置管理方式，提供配置模板和文档，按需求4完成配置外部化 | Restrictions: 必须保持示例代码的可用性，配置方式要简单易懂，不能增加用户配置复杂度 | Success: 配置统一管理，用户配置简单，示例正常工作 | 在tasks.md中将此任务标记为进行中[-]，完成后标记为已完成[x]_

- [x] 8. 改进异常处理
  - 文件: 包含通用Exception处理的Python文件
  - 将通用except Exception替换为具体异常类型
  - 添加更详细的错误信息和处理逻辑
  - 确保错误处理不影响功能正常运行
  - 目的: 提高错误处理的精确性和调试能力
  - _Leverage: Python内置异常类型，现有错误处理模式_
  - _Requirements: 需求2_
  - _Prompt: 实现spec project-optimization的任务，首先运行spec-workflow-guide获取工作流指导然后实现任务：Role: Python异常处理专家，专长于错误处理优化和调试支持 | Task: 改进异常处理，将通用Exception替换为具体异常类型，添加详细错误信息，保持功能稳定性，按需求2优化代码质量 | Restrictions: 必须保持现有错误处理行为，不能让程序更容易崩溃，确保用户体验不受影响 | Success: 异常处理更精确，错误信息更详细，功能稳定性不变 | 在tasks.md中将此任务标记为进行中[-]，完成后标记为已完成[x]_

- [x] 9. 优化模块导入性能
  - 文件: __init__.py文件和高频导入的模块
  - 减少不必要的模块导入
  - 使用延迟导入优化启动时间
  - 优化导入路径和模块依赖
  - 目的: 提升应用启动速度和运行效率
  - _Leverage: 现有模块结构，Python导入机制_
  - _Requirements: 需求5_
  - _Prompt: 实现spec project-optimization的任务，首先运行spec-workflow-guide获取工作流指导然后实现任务：Role: Python性能优化专家，专长于模块加载和导入优化 | Task: 优化模块导入，减少不必要导入，使用延迟加载，优化启动性能，按需求5提升性能 | Restrictions: 必须保持所有功能正常，不能破坏模块间依赖关系，确保兼容性 | Success: 启动时间减少，模块导入高效，功能完全正常 | 在tasks.md中将此任务标记为进行中[-]，完成后标记为已完成[x]_

- [x] 10. 统一缓存管理机制
  - 文件: tradingagents/dataflows/cache_manager.py, adaptive_cache.py等
  - 整合分散的缓存实现
  - 统一缓存配置和生命周期管理
  - 优化缓存性能和内存使用
  - 目的: 提升数据获取效率，统一缓存策略
  - _Leverage: 现有缓存管理器，Redis配置_
  - _Requirements: 需求5_
  - _Prompt: 实现spec project-optimization的任务，首先运行spec-workflow-guide获取工作流指导然后实现任务：Role: 缓存系统架构师，专长于缓存优化和数据管理 | Task: 统一分散的缓存实现，优化缓存策略和配置管理，提升缓存效率，按需求5进行性能优化 | Restrictions: 必须保持现有缓存功能，不能影响数据获取的正确性，确保缓存一致性 | Success: 缓存机制统一，性能提升，数据一致性保证 | 在tasks.md中将此任务标记为进行中[-]，完成后标记为已完成[x]_

- [x] 11. 验证并行分析功能
  - 文件: tradingagents/graph/parallel_analysts.py, main.py配置
  - 验证并行分析配置的有效性
  - 优化并行工作线程数和超时设置
  - 确保并行分析稳定可靠
  - 目的: 确保并行分析功能正常，优化性能配置
  - _Leverage: 现有并行分析实现，配置管理_
  - _Requirements: 需求5_
  - _Prompt: 实现spec project-optimization的任务，首先运行spec-workflow-guide获取工作流指导然后实现任务：Role: 并发系统工程师，专长于多线程和并行处理优化 | Task: 验证和优化并行分析功能，调整线程数和超时配置，确保并行处理稳定可靠，按需求5提升性能 | Restrictions: 必须确保并行分析结果正确，不能引入并发安全问题，保持系统稳定 | Success: 并行分析功能正常，性能优化，无并发问题 | 在tasks.md中将此任务标记为进行中[-]，完成后标记为已完成[x]_

- [x] 12. 综合测试和验证
  - 文件: 整个项目
  - 运行完整的功能测试
  - 验证所有优化不影响现有功能
  - 检查性能改进效果
  - 创建优化报告和文档
  - 目的: 确保优化成功，功能完整，性能提升
  - _Leverage: 现有测试用例，性能监控_
  - _Requirements: 所有需求_
  - _Prompt: 实现spec project-optimization的任务，首先运行spec-workflow-guide获取工作流指导然后实现任务：Role: QA工程师和系统验证专家，专长于综合测试和质量保证 | Task: 执行全面的功能和性能测试，验证所有优化效果，确保功能完整性，生成优化报告，涵盖所有需求 | Restrictions: 必须确保所有功能正常工作，性能确实有改进，不能遗漏任何重要功能测试 | Success: 所有功能正常，性能有提升，优化报告完整 | 在tasks.md中将此任务标记为进行中[-]，完成后标记为已完成[x]_