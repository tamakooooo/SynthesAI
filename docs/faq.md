# 常见问题 (FAQ)

> 版本: v0.3.2 | 更新日期: 2026-04-28

## 安装相关

### Q: 如何安装 FFmpeg？

**A**: 
- Windows: `choco install ffmpeg`
- macOS: `brew install ffmpeg`
- Linux: `sudo apt-get install ffmpeg`

### Q: 支持哪些 Python 版本？

**A**: Python 3.11 或更高版本。

### Q: 如何安装 VideoCaptioner (免费ASR)？

**A**:
```bash
pip install videocaptioner
videocaptioner --version  # 验证安装
```

VideoCaptioner 提供免费的 ASR 后端：
- `bijian`: B站必剪 (免费)
- `jianying`: 剪映 (免费)
- `faster-whisper`: 本地模型 (免费)

---

## 配置相关

### Q: API Key 配置在哪里？

**A**: 通过环境变量配置：
```bash
# LLM API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export DEEPSEEK_API_KEY="sk-..."

# ASR API Key (可选，付费高质量)
export SILICONCLOUD_API_KEY="sk-..."
```

### Q: 支持哪些 LLM 提供商？

**A**: OpenAI、Anthropic、DeepSeek。

### Q: 如何配置 SiliconCloud ASR？

**A**:
1. 获取 API Key: https://cloud.siliconflow.cn/account/ak
2. 设置环境变量: `export SILICONCLOUD_API_KEY="sk-..."`
3. 配置文件:
```yaml
modules:
  video_summary:
    transcriber: "siliconcloud"
```

---

## 使用相关

### Q: 支持哪些视频平台？

**A**: B站、YouTube、抖音等主流平台。

### Q: 视频转录是免费的吗？

**A**: 是的，有多种免费选项：

| 方式 | 说明 | 成本 |
|------|------|------|
| **VideoCaptioner (bijian)** | B站必剪 ASR | 免费 |
| **VideoCaptioner (jianying)** | 剪映 ASR | 免费 |
| **VideoCaptioner (faster-whisper)** | 本地模型 | 免费 |
| **SiliconCloud** | 高质量 API | 付费 |

默认使用 VideoCaptioner + bijian，完全免费。

### Q: 为什么视频下载失败？

**A**: 可能原因：
1. 视频需要登录 - 配置 Cookie
2. 网络问题 - 检查网络连接
3. 地区限制 - 使用代理
4. B站视频 - 确保已安装 yutto

### Q: 为什么 B站视频需要 yutto？

**A**: B站视频需要 WBI 签名认证，yutto 自动处理：
```bash
pip install yutto>=2.2.0
```

### Q: 转录失败怎么办？

**A**: 可能解决方案：
1. 等待几分钟后重试 (频率限制)
2. 切换 ASR 后端:
   - `bijian` → `jianying`
   - 或使用 `siliconcloud` (付费)

---

## 开发相关

### Q: 如何开发自定义模块？

**A**: 参考 [插件开发教程](plugin-development.md)。

### Q: 如何运行测试？

**A**: `pytest tests/ -v`

### Q: 如何切换 ASR 引擎？

**A**: 
```python
from learning_assistant.modules.video_summary.transcriber import AudioTranscriber

# 免费: VideoCaptioner + bijian
transcriber = AudioTranscriber(
    engine="videocaptioner",
    asr_engine="bijian"
)

# 付费: SiliconCloud (高质量)
transcriber = AudioTranscriber(
    engine="siliconcloud",
    api_key="sk-..."
)
```

---

## ASR 引擎对比

| 引擎 | 类型 | 成本 | 质量 | 推荐场景 |
|------|------|------|------|----------|
| **videocaptioner** | CLI | 免费 | 高 | 默认，中文视频 |
| **siliconcloud** | API | 付费 | 极高 | 高质量需求 |
| **faster_whisper** | 本地 | 免费 | 中 | 离线场景 |

---

更多问题请提交 GitHub Issues。