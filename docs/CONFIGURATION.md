# SynthesAI Configuration Guide

> 推荐方案：**日常只维护 `config/settings.local.yaml`**

**SynthesAI v0.3.1** | **更新日期**: 2026-04-24

---

## 配置文件概览

SynthesAI 现在推荐使用一个本地统一配置文件来管理几乎所有自定义设置：

```text
优先级（从高到低）
1. 环境变量
2. config/settings.local.yaml
3. config/settings.yaml / modules.yaml / adapters.yaml / server.yaml
```

### 推荐理解方式

- `settings.local.yaml`
  - 你的本地私有配置主文件
  - 推荐把 API Key、本地模型、模块开关、飞书配置、服务端覆盖都写在这里
- `settings.yaml`
  - 默认全局配置模板
- `modules.yaml`
  - 默认模块配置模板
- `adapters.yaml`
  - 默认适配器配置模板
- `server.yaml`
  - 默认服务端配置模板

也就是说：

**默认值仍然分散在多个模板文件里，但你自己的实际配置，推荐集中写到 `settings.local.yaml`。**

---

## 快速开始

### 1. 创建本地统一配置

```bash
cp config/settings.local.yaml.example config/settings.local.yaml
```

### 2. 编辑 `config/settings.local.yaml`

你可以在这一个文件里完成：

- LLM API Key 与模型配置
- 模块启用开关和优先级
- 飞书知识库配置
- 服务端 host / port / 鉴权 / 队列参数

### 3. 示例

```yaml
llm:
  default_provider: "openai"
  providers:
    openai:
      api_key_env: "OPENAI_API_KEY"
      base_url: "https://api.tamako.online/v1"
      default_model: "kimi-k2.5"

modules:
  video_summary:
    enabled: true
    priority: 1

adapters:
  feishu:
    enabled: true
    config:
      app_id_env: "FEISHU_APP_ID"
      app_secret_env: "FEISHU_APP_SECRET"
      space_id: "wikcnxxxxxxxx"
      root_node_token: "wikntxxxxxxxx"
      publish_modules:
        - "video_summary"

server:
  host: "0.0.0.0"
  port: 8000
  auth:
    enabled: true
    api_key_env: "SYNTHESAI_API_KEY"
```

---

## 一体化配置范围

下面这些内容现在都推荐放进 `config/settings.local.yaml`：

### 1. 全局与 LLM

- `app`
- `llm`
- `cache`
- `history`
- `task`
- `output`
- `plugin`
- `performance`
- `security`

### 2. 模块覆盖

- `modules.video_summary`
- `modules.link_learning`
- `modules.vocabulary`

### 3. 适配器覆盖

- `adapters.feishu`
- `event_bus.subscriptions`

### 4. 服务端覆盖

- `server.host`
- `server.port`
- `server.auth`
- `server.task_queue`
- `server.timeouts`

---

## 配置文件职责

### `config/settings.local.yaml`

推荐作为你的唯一日常编辑入口。

适合放：

- 私有 API Key
- 本地 provider/base_url/model
- 模块启停
- 飞书知识库参数
- 服务端本地运行参数

### `config/settings.yaml`

公共默认配置模板。

不要放真实密钥。

### `config/modules.yaml`

模块默认模板。

通常不需要直接编辑，除非你想修改仓库默认值。

### `config/adapters.yaml`

适配器默认模板。

通常不需要直接编辑，除非你想修改仓库默认值。

### `config/server.yaml`

服务端默认模板。

通常不需要直接编辑，除非你想修改仓库默认值。

---

## 推荐工作流

### 本地开发

- 优先编辑 `config/settings.local.yaml`
- 敏感信息优先用环境变量
- 服务端配置变更后重启服务

### 团队协作

- 不提交 `settings.local.yaml`
- 提交 `settings.local.yaml.example`
- 共享默认行为时修改默认模板文件

### 生产环境

- 优先使用环境变量承载密钥
- `settings.local.yaml` 只放非敏感覆盖项或部署期生成

---

## 安全建议

- 不要把真实 API Key 提交到 git
- 不要把 `settings.local.yaml` 分享给他人
- 不要把 cookie 文件提交到 git
- 飞书 `app_secret` 只通过环境变量注入

---

## 当前限制

- `settings.local.yaml` 现在已经可以统一覆盖模块、适配器和服务端配置
- 但服务端 `server.*` 配置修改后需要**重启服务**才会生效
- 默认模板文件仍然保留，作为系统默认值来源

---

## 推荐入口

如果你只记一个文件，请记住：

```text
config/settings.local.yaml
```

如果你只记一个模板，请记住：

```text
config/settings.local.yaml.example
```
