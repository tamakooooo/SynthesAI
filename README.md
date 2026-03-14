<div align="center">
  <img src="logo.png" alt="Video Analyzer" width="96" />
  <h1>Video Analyzer（AstrBot 插件）</h1>
  <p><b>B站 / 抖音视频总结、必剪转写兜底、飞书知识库发布</b></p>
</div>

---

## 简介

`Video Analyzer` 是一个 AstrBot 插件，支持：

- B站视频总结
- 抖音视频总结（依赖 `douyin-downloader`）
- 平台字幕获取 + 必剪转写兜底
- 总结图片渲染
- 飞书知识库发布（含思维导图、截图）

> 当前仓库已按 AstrBot 插件形态整理，不再包含 OpenClaw skill 入口代码。

---

## 安装

### 1) 部署插件

将仓库放入 AstrBot 插件目录（或在插件市场/面板上传）。

### 2) 安装系统依赖

```bash
apt install -y ffmpeg wkhtmltopdf
```

### 3) 安装 Python 依赖

```bash
python3 -m pip install -r requirements.txt
```

---

## 配置

在 AstrBot 插件配置页填写（参考 `_conf_schema.json` 与 `config.example.json`）：

### 必填（LLM）
- `llm.api_key`
- `llm.model`
- `llm.base_url`（可选，默认 OpenAI）

### 飞书（启用发布时建议填写）
- `feishu_app_id`
- `feishu_app_secret`
- `feishu_wiki_space_id`
- `feishu_parent_node_token`（可选）
- `feishu_domain`（`feishu` / `lark`）

### 抖音（分析抖音链接时需要）
- `douyin_downloader_runner_path`（例如 `/opt/douyin-downloader/run.py`）
- `douyin_downloader_python`（例如 `/usr/bin/python3`）
- 可选 Cookie：`douyin_cookie_*`

---

## 使用命令

### 基础
- `/总结帮助`
- `/总结 <视频链接或BV号>`
- `/最新视频 <UP主UID/空间链接/昵称>`

### B站登录
- `/B站登录`
- `/B站登出`

### 订阅
- `/订阅 <UP主>`
- `/取消订阅 <UP主>`
- `/订阅列表`
- `/检查更新`

### 推送目标
- `/添加推送群 <群号>`
- `/添加推送号 <QQ号>`
- `/推送列表`
- `/移除推送 <群号或QQ号>`
- `/飞书发布状态`

---

## 关键实现说明

- 音频下载：`yt-dlp + ffmpeg`
- 视频截图下载策略：`720P 优先`（降低体积、减少超时）
- 字幕策略：优先平台字幕，无字幕时走必剪转写
- 飞书发布：创建知识库文档并回填图片/思维导图

---

## 常见问题

### 1) 报错“飞书配置不完整”
补齐：`feishu_app_id / feishu_app_secret / feishu_wiki_space_id`

### 2) 下载慢或超时
- 已默认 720P 优先
- 建议检查网络与代理
- 可先关闭图片输出定位问题

### 3) 抖音失败
- 确认 `douyin_downloader_runner_path` 与 Python 路径可执行
- 先执行抖音扫码登录，或补充 Cookie

---

## 许可证

MIT
