# SynthesAI Configuration Guide

> **完整的配置指南** - 从基础到高级，涵盖所有配置选项

**SynthesAI v0.2.0** | **更新日期**: 2026-04-11

---

## 📋 目录

- [配置文件概览](#配置文件概览)
- [快速开始](#快速开始)
- [API Key 管理](#api-key-管理)
- [模块配置](#模块配置)
- [性能调优](#性能调优)
- [环境变量](#环境变量)
- [多环境管理](#多环境管理)
- [常见问题](#常见问题)

---

## 配置文件概览

SynthesAI 使用分层配置系统，支持多种配置来源：

```
优先级 (从高到低):
1. 环境变量           → 最高优先级，适合生产环境
2. settings.local.yaml    → 本地私有配置，包含 API Keys
3. settings.yaml          → 全局默认配置，已提交到 git
```

### 配置文件结构

```
config/
├── settings.yaml              # 全局默认配置 (已提交)
├── settings.local.yaml        # 本地私有配置 (未提交，包含 API Keys)
├── settings.local.yaml.example # 配置模板
├── modules.yaml               # 模块配置
├── adapters.yaml              # 适配器配置
└── cookies/                   # 视频平台认证 Cookie
    ├── bilibili_cookies.txt
    └── .gitkeep
```

---

## 快速开始

### 步骤 1: 创建本地配置

```bash
cd config
cp settings.local.yaml.example settings.local.yaml
```

### 步骤 2: 配置 API Key

编辑 `config/settings.local.yaml`:

```yaml
llm:
  default_provider: "openai"

  providers:
    openai:
      api_key: "sk-your-real-api-key-here"
      default_model: "gpt-4o"
```

### 步骤 3: 验证配置

```bash
# 运行首次配置命令
la setup

# 测试配置是否生效
la video https://www.bilibili.com/video/BV1G49MBLE4D
```

**完成！** 现在可以正常使用所有功能。

---

### 1. `config/settings.yaml` (Public Configuration)

This file contains:
- Default settings (log level, cache, etc.)
- LLM provider configurations (models, base URLs, timeouts)
- Environment variable names for API keys

**This file is committed to git** - do NOT put real API keys here.

### 2. `config/settings.local.yaml` (Private Configuration)

This file contains:
- Real API keys
- Local overrides (custom models, base URLs, etc.)

**This file is NOT committed to git** - it's ignored via `.gitignore`.

---

## API Key 管理

### 配置方式对比

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **settings.local.yaml** | 持久保存，无需重复设置 | 需手动创建文件 | 本地开发，个人使用 |
| **环境变量** | 安全，适合 CI/CD | 每次重启需重新设置 | 生产环境，自动化 |
| **命令行参数** | 临时使用，灵活 | 不持久，容易遗忘 | 临时测试，调试 |

### 推荐配置流程

**本地开发**: 使用 `settings.local.yaml`
**生产环境**: 使用环境变量
**临时测试**: 使用命令行参数

### 详细配置示例

#### OpenAI / 自定义端点

```yaml
llm:
  providers:
    openai:
      api_key: "sk-xxxxx"
      base_url: "https://api.openai.com/v1"  # 官方端点
      # OR 自定义端点 (如 Kimi, DeepSeek 等):
      # base_url: "https://api.tamako.online/v1"
      default_model: "gpt-4o"
      timeout: 30
      max_retries: 3
```

#### Anthropic Claude

```yaml
llm:
  providers:
    anthropic:
      api_key: "sk-ant-xxxxx"
      default_model: "claude-3-5-sonnet-20241022"
      timeout: 30
      max_retries: 3
```

#### DeepSeek

```yaml
llm:
  providers:
    deepseek:
      api_key: "sk-xxxxx"
      base_url: "https://api.deepseek.com/v1"
      default_model: "deepseek-chat"
      timeout: 30
      max_retries: 3
```

### 成本控制

```yaml
llm:
  cost_tracking:
    enabled: true
    daily_limit: 10.0      # 每日限额 (USD)
    monthly_limit: 100.0   # 每月限额 (USD)
    warning_threshold: 0.8 # 达到 80% 时警告
```

---

## 模块配置

模块配置位于 `config/modules.yaml`，控制每个功能模块的行为。

### 视频总结模块 (video_summary)

#### 基础配置

```yaml
modules:
  video_summary:
    enabled: true
    priority: 1

    config:
      llm:
        provider: "openai"
        model: "gpt-4o"
        temperature: 0.3      # 低温度 = 更确定性输出
        max_tokens: 2000

      download:
        quality: "medium"     # best/medium/worst
        max_duration: 60      # 最大视频时长 (分钟)
        platforms:
          - bilibili
          - youtube
          - douyin

      audio:
        format: "wav"
        sample_rate: 16000    # ASR 推荐采样率

      transcription:
        model: "base"         # Whisper 模型大小
        language: "auto"      # 自动检测语言
        vad: true             # 启用语音活动检测
```

#### 视频平台认证

B站二维码登录:

```yaml
auth:
  providers:
    bilibili:
      enabled: true
      timeout: 180          # 二维码超时 (秒)
      poll_interval: 2      # 轮询间隔 (秒)
```

使用命令:

```bash
la auth login --platform bilibili
la auth status --platform bilibili
la auth logout --platform bilibili
```

#### 章节截图提取

```yaml
frame_extraction:
  enabled: true
  output_dir: "data/frames"
  format: "jpg"            # jpg/png
  quality: 85              # JPEG 质量 (1-100)
```

- 为每个章节提取关键帧
- 截图嵌入 Markdown 输出
- 相对路径引用，便于分享

### 链接学习模块 (link_learning)

#### 网页抓取配置

```yaml
modules:
  link_learning:
    config:
      fetcher:
        timeout: 30
        max_retries: 3
        retry_delay: 2
        use_playwright: false  # 不使用浏览器引擎
        proxy: null            # 设置代理: "http://127.0.0.1:7890"

      parser:
        engine: "trafilatura"
        include_comments: false
        include_tables: true
        min_content_length: 100  # 最小正文长度
```

#### 功能开关

```yaml
features:
  generate_qa: true           # 生成问答对
  generate_quiz: true         # 生成测验题
  extract_tags: true          # 提取标签
  estimate_difficulty: true   # 估估难度
```

### 单词学习模块 (vocabulary)

#### 单词提取

```yaml
modules:
  vocabulary:
    config:
      extraction:
        word_count: 10
        difficulty_distribution:
          beginner: 30%
          intermediate: 50%
          advanced: 20%
        min_word_length: 3
        exclude_stopwords: true
```

#### 音标查询 (三层查询)

```yaml
phonetic:
  lookup_order:           # 查询顺序
    - local               # 1. 本地词典 (最快)
    - api                 # 2. Free Dictionary API
    - llm                 # 3. LLM 生成 (兜底)
  local_dictionary: "data/dictionaries/english.json"
  api_url: "https://api.dictionaryapi.dev/api/v2/entries/en/"
```

#### 上下文故事

```yaml
story:
  enabled: true
  default_word_count: 300      # 故事词数
  default_difficulty: "intermediate"
```

---

## 性能调优

### 并行处理

```yaml
performance:
  multiprocessing: true     # 启用多进程
  worker_count: 4           # 并行 Worker 数量
  memory_limit_mb: 500      # 内存限制
```

**建议**:
- CPU 核数 ≤ 4: `worker_count = 2`
- CPU 核数 > 4: `worker_count = CPU 核数`
- 视频处理: 推荐 `worker_count = 4`

### 缓存配置

```yaml
cache:
  enabled: true
  directory: "data/cache"
  expiry_days: 7            # 缓存有效期
  max_size_mb: 500          # 最大缓存大小
```

**清理缓存**:

```bash
# 手动清理
rm -rf data/cache/*

# 或使用命令
la cache clear
```

### 输出配置

```yaml
output:
  default_format: "markdown"  # markdown/json/pdf
  directory: "data/outputs"
  auto_subdirs: true          # 模块自动创建子目录
```

---

## 环境变量

### 基础环境变量

```bash
# LLM API Keys (必需)
export OPENAI_API_KEY="sk-your-key"
export ANTHROPIC_API_KEY="sk-ant-your-key"
export DEEPSEEK_API_KEY="sk-your-key"

# 可选配置
export LEARNING_ASSISTANT_LOG_LEVEL="INFO"
export LLM_PROVIDER="openai"              # 默认提供商
export LLM_MODEL="gpt-4"                  # 默认模型
```

### 配置文件中的环境变量引用

使用 `${VAR:default}` 语法:

```yaml
llm:
  provider: "${LLM_PROVIDER:openai}"
  model: "${LLM_MODEL:gpt-4}"
```

- 如果 `LLM_PROVIDER` 环境变量存在，使用它的值
- 否则使用默认值 `openai`

### .env 文件支持

创建 `.env` 文件 (项目根目录):

```bash
OPENAI_API_KEY=sk-your-key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LOG_LEVEL=INFO
```

加载 `.env`:

```bash
# 使用 python-dotenv 自动加载
pip install python-dotenv

# 或手动加载
source .env
```

**注意**: `.env` 文件不要提交到 git (已在 `.gitignore` 中)。

---

## 多环境管理

### 开发环境

```bash
# 使用 settings.local.yaml
config/settings.local.yaml

# 内容:
llm:
  default_provider: "openai"
  providers:
    openai:
      api_key: "sk-dev-key"
      default_model: "gpt-4o"
```

### 生产环境

```bash
# 使用环境变量
export OPENAI_API_KEY="sk-prod-key"
export LLM_MODEL="gpt-4-turbo"
export LOG_LEVEL="WARNING"

# 或在 CI/CD 中设置
```

### 测试环境

```yaml
# config/settings.test.yaml (可选)
llm:
  providers:
    openai:
      api_key: "sk-test-key"
      base_url: "https://api.example.com/v1"
```

---

## 安全最佳实践

### 1. 文件权限

```bash
# 限制配置文件权限
chmod 600 config/settings.local.yaml
chmod 600 config/cookies/bilibili_cookies.txt
```

### 2. API Key 安全

- ❌ **永远不要**将 API Key 硬编码在代码中
- ❌ **永远不要**提交 `settings.local.yaml` 到 git
- ✅ **推荐**使用环境变量 (生产环境)
- ✅ **推荐**定期轮换 API Key

### 3. .gitignore 保护

已自动忽略:

```gitignore
config/settings.local.yaml
config/cookies/
.env
*.log
data/cache/
data/history/
```

### 4. 检查配置泄露

```bash
# 搜索可能泄露的 API Key
git log --all --full-history -- "*.yaml" | grep -i "api_key"

# 如果发现泄露，立即:
# 1. 轮换 API Key
# 2. 从 git 历史中删除敏感文件
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch config/settings.local.yaml' \
  --prune-empty --tag-name-filter cat -- --all
```

---

## 常见问题

### API Key 未找到

**错误**: `Error: API key not found`

**解决方案**:

1. 检查 `config/settings.local.yaml` 是否存在:
   ```bash
   ls -la config/settings.local.yaml
   ```

2. 检查 API Key 是否配置:
   ```bash
   grep "api_key" config/settings.local.yaml
   ```

3. 或使用环境变量:
   ```bash
   export OPENAI_API_KEY="sk-your-key"
   ```

### 配置不生效

**原因**: 环境变量优先级高于配置文件

**检查**:

```bash
# 查看环境变量
echo $OPENAI_API_KEY

# 如果存在，会覆盖 settings.local.yaml
```

**解决方案**:

- 移除环境变量: `unset OPENAI_API_KEY`
- 或直接在配置文件中使用环境变量引用

### 视频下载失败

**B站视频需要登录**:

```bash
# 登录 B站
la auth login --platform bilibili

# 检查登录状态
la auth status --platform bilibili
```

**Cookie 过期**:

```bash
# 重新登录
la auth logout --platform bilibili
la auth login --platform bilibili
```

### LLM 调用超时

**调整超时设置**:

```yaml
llm:
  providers:
    openai:
      timeout: 60          # 增加到 60 秒
      max_retries: 5       # 增加重试次数
```

### 缓存占用过大

**清理缓存**:

```bash
# 查看缓存大小
du -sh data/cache

# 清理缓存
rm -rf data/cache/*
```

**调整缓存配置**:

```yaml
cache:
  max_size_mb: 200         # 降低缓存上限
  expiry_days: 3           # 缩短有效期
```

### 模块加载失败

**检查模块配置**:

```bash
# 查看模块配置
la list-plugins

# 检查 modules.yaml
grep "enabled" config/modules.yaml
```

**启用/禁用模块**:

```yaml
modules:
  video_summary:
    enabled: true   # 启用
  link_learning:
    enabled: false  # 禁用
```

---

## 配置验证

### 验证配置文件

```bash
# 首次配置
la setup

# 验证 LLM 配置
python -c "from learning_assistant.core.llm.service import LLMService; \
  import os; \
  api_key = os.environ.get('OPENAI_API_KEY'); \
  service = LLMService('openai', api_key, 'gpt-4o'); \
  print('✅ LLM 配置正确')"
```

### 测试视频总结

```bash
# 使用测试视频
la video https://www.bilibili.com/video/BV1G49MBLE4D
```

---

## 高级配置

### 自定义 Prompt 模板

修改 `templates/prompts/video_summary.yaml`:

```yaml
system_prompt: |
  你是一个专业的视频内容分析师...

user_prompt_template: |
  请分析以下视频内容...

output_schema:
  type: object
  properties:
    title:
      type: string
    chapters:
      type: array
      items:
        properties:
          title:
            type: string
          start_time:
            type: string
          summary:
            type: string
```

### 自定义输出模板

修改 `templates/outputs/video_summary.md`:

```markdown
# {{title}}

> **视频时长**: {{metadata.duration}}
> **观看平台**: {{metadata.platform}}

## 📋 目录

{% for chapter in chapters %}
- [{{chapter.title}}]({{chapter.start_time}})
{% endfor %}

## 🎬 章节内容

{% for chapter in chapters %}
### {{chapter.title}}

{% if chapter.screenshot_path %}
![{{chapter.title}}](../frames/{{chapter.screenshot_path}})
{% endif %}

{{chapter.summary}}
{% endfor %}
```

---

## 相关文档

- [API 使用示例](./API_EXAMPLES.md)
- [用户指南](./user-guide.md)
- [常见问题](./faq.md)
- [架构文档](../ARCHITECTURE.md)

---

**版本**: v0.2.0
**更新日期**: 2026-04-10
**维护者**: Learning Assistant Team