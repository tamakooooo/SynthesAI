# 项目命名规范

> **版本**: v0.2.0
> **更新日期**: 2026-03-31

本文档定义 Learning Assistant 项目的命名规范，确保整个项目命名一致。

---

## 📋 命名标准

### 1. 项目命名

| 类型 | 命名 | 格式 | 用途 |
|------|------|------|------|
| **项目名称** | Learning Assistant | Title Case | 官方名称 |
| **包名 (PyPI)** | `learning-assistant` | kebab-case | pip install |
| **导入名** | `learning_assistant` | snake_case | Python import |
| **CLI 命令** | `la` | lowercase | 命令行 |
| **GitHub 仓库** | `learning-assistant` | kebab-case | Git clone |

---

### 2. 目录命名

#### 项目根目录

```
learning-assistant/              # ✅ kebab-case
├── src/
│   └── learning_assistant/     # ✅ snake_case (Python 标准)
├── skills/                     # ✅ lowercase
├── tests/                      # ✅ lowercase
├── docs/                       # ✅ lowercase
├── config/                     # ✅ lowercase
└── data/                       # ✅ lowercase
```

#### Skills 目录

```
skills/
├── video-summary/              # ✅ kebab-case
│   ├── SKILL.md               # ✅ 大写
│   └── references/            # ✅ lowercase
├── list-skills/               # ✅ kebab-case
└── learning-history/          # ✅ kebab-case
```

---

### 3. Python 代码命名

#### 模块和包

```python
# ✅ 正确
learning_assistant/            # snake_case
├── core/                      # snake_case
├── modules/                   # snake_case
└── video_summary/             # snake_case
```

#### 类名

```python
# ✅ 正确：PascalCase
class VideoSummaryModule:
    pass

class AgentAPI:
    pass

class PluginManager:
    pass
```

#### 函数和变量

```python
# ✅ 正确：snake_case
def summarize_video(url: str) -> dict:
    pass

async def get_history(limit: int) -> list:
    pass

video_count = 10
output_dir = "./outputs"
```

#### 常量

```python
# ✅ 正确：UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
API_VERSION = "v1"
```

---

### 4. 配置文件命名

| 文件 | 命名 | 格式 |
|------|------|------|
| Python 项目配置 | `pyproject.toml` | ✅ lowercase |
| Markdown 文档 | `README.md`, `CHANGELOG.md` | ✅ UPPERCASE |
| YAML 配置 | `settings.yaml`, `modules.yaml` | ✅ lowercase |
| Git 忽略 | `.gitignore` | ✅ lowercase |
| 环境变量 | `.env` | ✅ lowercase |

---

### 5. CLI 命令命名

#### 主命令

```bash
# ✅ 正确：简短、易记
la                    # Learning Assistant
```

#### 子命令

```bash
# ✅ 正确：snake_case 或 kebab-case
la setup
la version
la list-plugins       # kebab-case
la video
la history
```

---

### 6. 文档命名

#### Markdown 文件

```bash
# ✅ 正确：kebab-case
user-guide.md
api-documentation.md
plugin-development.md
agent-integration.md
```

#### 文档标题

```markdown
# ✅ 正确：Title Case
# User Guide
# API Documentation
# Plugin Development Tutorial
```

---

## 🔍 命名检查清单

### 项目级别

- [x] 项目名称：Learning Assistant
- [x] PyPI 包名：`learning-assistant`
- [x] GitHub 仓库：`learning-assistant`
- [ ] 项目根目录：`learning-assistant`（待重命名）

### 代码级别

- [x] Python 包：`learning_assistant` (snake_case)
- [x] 类名：PascalCase
- [x] 函数：snake_case
- [x] 变量：snake_case
- [x] 常量：UPPER_SNAKE_CASE

### Skills 级别

- [x] Skills 目录：kebab-case (`video-summary`)
- [x] SKILL.md 文件：大写
- [x] YAML `name` 字段：kebab-case

### 文档级别

- [x] Markdown 文件：kebab-case
- [x] 文档标题：Title Case
- [x] 配置文件：lowercase

---

## 🚨 常见错误

### ❌ 错误示例

```bash
# 错误：目录名不一致
Video_analyzer/                # snake_case 与项目名不一致
├── src/
│   └── Learning_Assistant/    # PascalCase（应为 snake_case）

# 错误：文件名不一致
skills/
├── video-summary.md           # 应为 SKILL.md
├── VideoSummary/              # PascalCase（应为 kebab-case）
```

### ✅ 正确示例

```bash
# 正确：统一命名
learning-assistant/            # kebab-case（项目根目录）
├── src/
│   └── learning_assistant/    # snake_case（Python 标准）
│       ├── modules/
│       │   └── video_summary/ # snake_case（Python 模块）
├── skills/
│   ├── video-summary/         # kebab-case（Skill 目录）
│   │   └── SKILL.md           # UPPERCASE（标准文件名）
│   ├── list-skills/           # kebab-case
│   └── learning-history/      # kebab-case
```

---

## 📚 命名参考资源

### Python 官方规范

- [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Packaging User Guide](https://packaging.python.org/en/latest/)

### Claude Code Skills 规范

- Skill 文件名必须是 `SKILL.md`（大写）
- Skill `name` 字段必须是 kebab-case
- Skill 目录名必须是 kebab-case

### 社区最佳实践

- **项目名**: kebab-case（GitHub, PyPI）
- **Python 包**: snake_case
- **类名**: PascalCase
- **函数/变量**: snake_case
- **常量**: UPPER_SNAKE_CASE
- **CLI 命令**: lowercase 或 kebab-case

---

## 🔄 重命名操作指南

如需重命名，请参考 [RENAME_GUIDE.md](RENAME_GUIDE.md)。

---

## ✅ 验证命名一致性

运行以下命令检查命名一致性：

```bash
# 检查 Python 包名
grep "name = " pyproject.toml

# 检查目录命名
ls -la src/learning_assistant/
ls -la skills/

# 检查 Skills name 字段
grep -r "^name:" skills/*/SKILL.md

# 检查文档命名
find . -name "*.md" -type f | grep -v node_modules
```

---

**最后更新**: 2026-03-31
**维护者**: Learning Assistant Team