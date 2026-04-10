# SynthesAI - AI Agent 文档索引

> **快速导航指南** - 帮助 AI Agent 找到所需文档

**SynthesAI - Synthesize Knowledge with AI Intelligence**

## 🤖 Agent 必读文档（优先级排序）

### 🔴 **立即阅读**（核心架构）

1. **[ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)** ⭐⭐⭐
   - 项目四层架构详解
   - 核心组件说明
   - 设计理念和决策
   - Agent 开发模式
   - **Agent 必读，理解全局架构**

2. **[AGENT_DEVELOPMENT_GUIDE.md](AGENT_DEVELOPMENT_GUIDE.md)** ⭐⭐⭐
   - Agent 开发标准流程
   - 组件使用示例
   - 最佳实践和注意事项
   - 常见任务清单
   - **Agent 开发实操手册**

3. **[knowledge_card_prompt_update.md](knowledge_card_prompt_update.md)** ⭐⭐
   - 知识卡片系统指南
   - 格式规范（关键！）
   - VisualCardGenerator 使用
   - **链接总结模块必读**

---

## 📚 模块文档

### Link Learning（链接总结）

- **[link_learning_design.md](link_learning_design.md)** - 模块设计文档
- **[link_learning_implementation_summary.md](link_learning_implementation_summary.md)** - 实现总结
- **[link_learning_cli_guide.md](link_learning_cli_guide.md)** - CLI 使用指南
- **[link_learning_user_guide.md](link_learning_user_guide.md)** - 用户指南
- **[link_learning_completion_summary.md](link_learning_completion_summary.md)** - 完成总结

### Video Summary（视频总结）

- **[plugin-development.md](plugin-development.md)** - 插件开发（包含视频模块）

### Vocabulary（词汇学习）

- **[vocabulary_learning_design.md](vocabulary_learning_design.md)** - 设计文档
- **[vocabulary_user_guide.md](vocabulary_user_guide.md)** - 用户指南

---

## 🔧 配置和设置

### 必读配置文档

- **[CONFIGURATION.md](CONFIGURATION.md)** - 完整配置指南
- **[API_KEY_SETUP.md](API_KEY_SETUP.md)** - API Key 配置（Agent 必需）
- **[COOKIE_AUTHENTICATION.md](COOKIE_AUTHENTICATION.md)** - Cookie 认证（视频模块）
- **[QUICK_START.md](QUICK_START.md)** - 快速开始（5分钟上手）

### Agent 配置文件

- `config/settings.yaml` - 全局设置
- `config/settings.local.yaml` - 本地配置（API Keys）
- `config/modules.yaml` - 模块配置

---

## 🧪 测试和质量

- **[test_strategy.md](test_strategy.md)** - 测试策略
- **[test_results_summary_20260410.md](test_results_summary_20260410.md)** - 测试结果
- **[BEST_PRACTICES.md](BEST_PRACTICES.md)** - 最佳实践

---

## 📖 API 和集成

- **[API_EXAMPLES.md](API_EXAMPLES.md)** - API 使用示例
- **[api.md](api.md)** - API 文档
- **[agent_integration.md](agent_integration.md)** - Agent 集成指南

---

## 🎯 用户指南

- **[user-guide.md](user-guide.md)** - 用户总指南
- **[demo_examples.md](demo_examples.md)** - 示例演示
- **[faq.md](faq.md)** - 常见问题

---

## 📊 项目状态

- **[project_status_current.md](project_status_current.md)** - 当前状态
- **[project_summary_20260410.md](project_summary_20260410.md)** - 项目总结
- **[github_release_v0.1.0.md](github_release_v0.1.0.md)** - Release 文档

---

## 🚀 开发规划

- **[development_options_v0.3.md](development_options_v0.3.md)** - v0.3 开发选项
- **[next_step_planning.md](next_step_planning.md)** - 下一步规划
- **[batch_processing_progress.md](batch_processing_progress.md)** - 批处理进度

---

## 📝 其他文档

- **[format_comparison_example.html](format_comparison_example.html)** - 格式对比示例（HTML，浏览器打开）
- **[day1_completion_summary.md](day1_completion_summary.md)** - Day 1 总结

---

## 🗂️ 文件结构导航

### 核心代码位置

```
src/learning_assistant/
├── cli.py                    # CLI 入口（Layer 1）
├── core/                     # 核心组件（Layer 4）
│   ├── llm/                  # LLM 服务
│   ├── exporters/            # 导出器
│   │   ├── visual_card.py    # 知识卡片生成器 ⭐
│   │   └── markdown.py       # Markdown 导出器
│   ├── plugin_manager.py     # 插件管理器
│   ├── event_bus.py          # 事件总线
│   ├── config_manager.py     # 配置管理
│   └── history_manager.py    # 历史管理
│   └ prompt_manager.py       # 提示词管理
│
├── modules/                  # 学习模块（Layer 3）
│   ├── link_learning/        # 链接总结 ⭐
│   ├── video_summary/        # 视频总结
│   └ vocabulary/             # 词汇学习
│
└── auth/                     # 认证（Layer 4）
    ├── providers/            # 认证提供者
```

### 配置位置

```
config/
├── settings.yaml             # 全局设置
├── settings.local.yaml       # 本地配置（API Keys）
├── modules.yaml              # 模块配置
└── adapters.yaml             # 适配器配置
```

### 模板位置

```
templates/
├── prompts/                  # LLM 提示词模板
│   └── link_summary.yaml     # 链接总结 v2.0 ⭐
│
└── outputs/                  # 输出模板
    ├── link_summary.md       # Markdown 模板
    └── vocabulary_card.md    # 词汇卡片模板
```

### 输出位置

```
data/
├── outputs/
│   ├── link/                 # 链接总结输出
│   │   ├── *.md              # Markdown 文件
│   │   ├── *.html            # HTML 知识卡片
│   │   └── *.png             # PNG 图片
│   │
│   ├── video/                # 视频总结输出
│   └── vocabulary/           # 词汇学习输出
│
└── history/
    ├── link/                 # 链接历史
    ├── video/                # 视频历史
    └── vocabulary/           # 词汇历史
```

### 测试位置

```
tests/
├── modules/                  # 模块测试
│   ├── test_link_learning.py
│   ├── test_video_summary.py
│   └── test_vocabulary.py
│
├── core/                     # 核心组件测试
│   ├── test_llm_service.py
│   ├── test_prompt_manager.py
│   └── test_exporters.py
│
└── api/                      # API 测试
    └── test_api.py
```

---

## 🎯 Agent 任务导航表

| Agent 任务 | 需阅读文档 | 关键文件 |
|-----------|-----------|---------|
| **理解项目架构** | ARCHITECTURE_OVERVIEW.md | src/learning_assistant/core/ |
| **开发新模块** | AGENT_DEVELOPMENT_GUIDE.md | templates/prompts/, modules/ |
| **生成知识卡片** | knowledge_card_prompt_update.md | visual_card.py, link_summary.yaml |
| **配置 API Key** | API_KEY_SETUP.md | config/settings.local.yaml |
| **添加新 Provider** | ARCHITECTURE_OVERVIEW.md (Layer 4) | core/llm/providers/ |
| **优化提示词** | knowledge_card_prompt_update.md | templates/prompts/*.yaml |
| **扩展导出器** | AGENT_DEVELOPMENT_GUIDE.md (Exporters) | core/exporters/ |
| **编写测试** | test_strategy.md | tests/ |

---

## 🔍 快速查找关键词

| 需找内容 | 文档位置 | 关键字 |
|---------|---------|--------|
| "LLM Service 如何使用" | AGENT_DEVELOPMENT_GUIDE.md → LLM Service | `llm_service.call()` |
| "Prompt Template 创建" | AGENT_DEVELOPMENT_GUIDE.md → Prompt Manager | `template.yaml` |
| "知识卡片格式" | knowledge_card_prompt_update.md → 格式规范 | `关键词：详细描述` |
| "配置管理" | CONFIGURATION.md + AGENT_DEVELOPMENT_GUIDE.md | `ConfigManager` |
| "插件加载" | ARCHITECTURE_OVERVIEW.md → Plugin Management | `PluginManager` |
| "异步处理" | AGENT_DEVELOPMENT_GUIDE.md → 注意事项 | `async def`, `await` |
| "错误处理" | AGENT_DEVELOPMENT_GUIDE.md → 最佳实践 | `try-except`, `logger` |

---

## 💡 Agent 学习路径建议

### 初级 Agent（入门）

**第 1 天**：
1. 阅读 ARCHITECTURE_OVERVIEW.md（理解架构）
2. 阅读 QUICK_START.md（快速上手）
3. 配置 API Key（API_KEY_SETUP.md）
4. 运行第一个链接总结（`la link <url>`）

**第 2 天**：
1. 阅读 AGENT_DEVELOPMENT_GUIDE.md（开发指南）
2. 理解 Prompt Template 结构
3. 理解 VisualCardGenerator 使用
4. 查看现有模块代码（link_learning）

**第 3 天**：
1. 小改动练习（修改输出模板）
2. 测试验证（编写单元测试）
3. 提交代码

### 中级 Agent（开发）

**第 1 周**：
- 理解所有核心组件
- 开发小功能（如优化提示词）
- 理解异步架构

**第 2 周**：
- 创建新导出器（如 PDF）
- 扩展模块功能
- 完整测试

**第 3 周**：
- 创建新模块（简单模块）
- 优化性能
- 完整文档

### 高级 Agent（架构）

**第 1 月**：
- 理解设计决策
- 提出架构改进
- 重构核心组件

**第 2 月**：
- 创建新 Provider
- Agent 集成优化
- 批量处理设计

---

## 📌 Agent 重要提醒

### ⚠️ 必须遵守

- ✅ 所有异步函数使用 `async def` + `await`
- ✅ 类型注解使用 `dict[str, Any]`（不是 `Dict`）
- ✅ API Key 从配置读取（不硬编码）
- ✅ 知识卡片格式：`关键词：详细描述`
- ✅ 添加详细日志和错误处理

### ⚠️ 避免错误

- ❌ 不要修改核心架构（除非必要）
- ❌ 不要在 async 函数中使用 `asyncio.run()`
- ❌ 不要硬编码配置或密钥
- ❌ 不要跳过测试
- ❌ 不要使用字符串路径（用 `Path` 对象）

---

## 🆘 Agent 问题诊断

| 问题 | 检查文档 | 解决方案 |
|------|---------|---------|
| LLM 调用失败 | API_KEY_SETUP.md | 检查 API Key 配置 |
| 异步错误 | AGENT_DEVELOPMENT_GUIDE.md | 使用 await，不用 asyncio.run() |
| 格式验证失败 | knowledge_card_prompt_update.md | 确保关键词：描述格式 |
| PNG 渲染失败 | AGENT_DEVELOPMENT_GUIDE.md | 安装 Playwright + Chromium |
| 配置错误 | CONFIGURATION.md | 验证 YAML Schema |

---

## 📞 Agent 获取帮助

### 文档帮助

- 查阅相关文档（见上方索引）
- 查看现有模块代码（参考实现）
- 阅读 AGENT_DEVELOPMENT_GUIDE.md 最佳实践

### 代码参考

- `link_learning` 模块：完整实现示例
- `VisualCardGenerator`：知识卡片生成示例
- `PromptManager`：提示词管理示例

### 测试验证

- 查看 `tests/` 目录的测试代码
- 运行测试验证功能
- 使用真实数据测试

---

**Agent 开发愉快！从 ARCHITECTURE_OVERVIEW.md 开始，逐步深入。**