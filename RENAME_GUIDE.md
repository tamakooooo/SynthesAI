# 项目重命名指南

> **目标**: 统一项目命名为 `learning-assistant` (kebab-case)
> **日期**: 2026-03-31

---

## 📊 重命名清单

### 1. ✅ 已正确命名

| 项目 | 当前名称 | 状态 |
|------|---------|------|
| Python 包名 | `learning-assistant` | ✅ 正确 |
| 包目录 | `learning_assistant` | ✅ 正确（Python 标准） |
| CLI 命令 | `la` | ✅ 正确 |
| Skills 文件夹 | `skills/` | ✅ 正确 |
| Skill 子目录 | `video-summary/`, `list-skills/`, `learning-history/` | ✅ 正确 |

---

### 2. ❌ 需要重命名

| 项目 | 当前名称 | 目标名称 | 优先级 |
|------|---------|---------|--------|
| **项目根目录** | `Video_analyzer` | `learning-assistant` | 🔴 高 |

---

## 🔧 重命名步骤

### Step 1: 重命名项目根目录

**方法 1: VSCode 中重命名**

```bash
# 1. 关闭 VSCode
# 2. 在文件管理器中重命名
Video_analyzer → learning-assistant

# 3. 重新打开项目
code c:/Users/10405/Desktop/ai/learning-assistant
```

**方法 2: 命令行重命名**

```bash
# 注意：需要在项目外执行
cd /c/Users/10405/Desktop/ai
mv Video_analyzer learning-assistant
cd learning-assistant
```

---

### Step 2: 更新 Git 远程仓库（如果需要）

```bash
# 如果你的 GitHub 仓库名不是 learning-assistant
# 1. 在 GitHub 上重命名仓库
# 2. 更新本地配置

cd learning-assistant
git remote set-url origin https://github.com/yourname/learning-assistant.git
```

---

### Step 3: 验证重命名

```bash
# 验证目录名
pwd
# 应该输出：/c/Users/10405/Desktop/ai/learning-assistant

# 验证包名
grep "name = " pyproject.toml
# 应该输出：name = "learning-assistant"

# 验证 CLI
la version
# 应该正常工作

# 验证包导入
python -c "import learning_assistant; print(learning_assistant.__version__)"
# 应该输出：0.2.0
```

---

## 📝 重命名后检查清单

- [ ] 项目根目录已重命名为 `learning-assistant`
- [ ] Git 远程仓库 URL 已更新（如果需要）
- [ ] `la version` 命令正常工作
- [ ] `pytest` 测试通过
- [ ] Skills 在 Claude Code 中可用
- [ ] README.md 中的路径引用正确

---

## 🚨 注意事项

### 1. VSCode 工作区

如果你有 VSCode 工作区文件（`.code-workspace`），需要更新路径。

### 2. 虚拟环境

如果使用了虚拟环境，可能需要重新创建：

```bash
# 删除旧的虚拟环境
rm -rf venv

# 创建新的虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 重新安装依赖
pip install -e ".[dev]"
```

### 3. IDE 缓存

清除 IDE 缓存：

```bash
# VSCode
rm -rf .vscode

# PyCharm
rm -rf .idea

# 重新打开项目让 IDE 重新索引
```

---

## 🎯 预期结果

重命名后的项目结构：

```
learning-assistant/              # ✅ 项目根目录
├── pyproject.toml              # name = "learning-assistant"
├── src/
│   └── learning_assistant/     # ✅ Python 包目录
│       ├── __init__.py
│       ├── api/                # ✅ Agent API
│       ├── core/
│       ├── modules/
│       └── cli.py
├── skills/                     # ✅ Skills 目录
│   ├── video-summary/
│   ├── list-skills/
│   └── learning-history/
├── tests/
├── docs/
└── README.md
```

---

## 📦 已验证的命名一致性

### Python 包命名规则

| 类型 | 命名风格 | 示例 | 用途 |
|------|---------|------|------|
| **PyPI 包名** | kebab-case | `learning-assistant` | pip install |
| **导入名** | snake_case | `learning_assistant` | Python import |
| **项目目录** | kebab-case | `learning-assistant` | Git clone |

### CLI 命令

```bash
# 安装后
pip install learning-assistant

# CLI 命令
la video https://...
la version
la list-plugins
```

### Skills 命名

```bash
skills/
├── video-summary/      # ✅ kebab-case
├── list-skills/        # ✅ kebab-case
└── learning-history/   # ✅ kebab-case
```

---

## ✅ 完成重命名后

1. **测试功能**
```bash
pytest
la version
```

2. **更新文档引用**
- README.md 中的路径
- 文档中的示例代码
- GitHub 仓库链接

3. **提交变更**
```bash
git add .
git commit -m "refactor: rename project to learning-assistant"
git push
```

---

**最后更新**: 2026-03-31