# Frame Extraction Feature - Usage Examples

## Quick Start

### 基础使用

```bash
# 1. 运行视频总结（自动提取帧）
la video https://www.bilibili.com/video/BV1G49MBLE4D

# 2. 查看输出位置
# Markdown: data/outputs/{title}_summary.md
# Frames:   data/frames/{title}/chapter_01.jpg, chapter_02.jpg, ...
```

### 验证输出

```bash
# 查看生成的 Markdown
cat data/outputs/*_summary.md | grep "!\["

# 查看提取的帧文件
ls data/frames/*/

# 检查帧文件数量
ls data/frames/{title}/chapter_*.jpg | wc -l
```

## Detailed Workflow

### Step 1: 下载并处理视频

```bash
# 示例：处理一个B站视频
la video https://www.bilibili.com/video/BV1G49MBLE4D

# 系统会自动执行：
# 1. Download video
# 2. Extract audio
# 3. Transcribe audio
# 4. Generate summary (with chapters)
# 5. Extract frames for each chapter
# 6. Export Markdown with screenshots
```

### Step 2: 查看输出结构

```
data/
├── outputs/
│   └── 吃一个花甲_等于吃上万根玻璃纤维_summary.md
│       # Markdown文件（包含章节截图引用）
│
└── frames/
    └── 吃一个花甲_等于吃上万根玻璃纤维/
        ├── chapter_01.jpg  # 第1章截图（00:00）
        ├── chapter_02.jpg  # 第2章截图（05:30）
        ├── chapter_03.jpg  # 第3章截图（10:15）
        └── ...
```

### Step 3: Markdown 内容示例

```markdown
## 📖 章节

### 谣言溯源：营销号的误读与夸大

> ⏱️ 00:00

![谣言溯源：营销号的误读与夸大](../frames/吃一个花甲_等于吃上万根玻璃纤维/chapter_01.jpg)

本章分析了网络谣言的起源，指出营销号为吸引流量而进行的不实报道...

### 研究剖析：实验设计与核心发现

> ⏱️ 05:30

![研究剖析：实验设计与核心发现](../frames/吃一个花甲_等于吃上万根玻璃纤维/chapter_02.jpg)

详细解读科研文献的实验设计方法...

### 风险评估：玻璃纤维的人体危害分析

> ⏱️ 10:15

![风险评估：玻璃纤维的人体危害分析](../frames/吃一个花甲_等于吃上万根玻璃纤维/chapter_03.jpg)

科学评估玻璃纤维经消化道摄入的实际风险...
```

### Step 4: 预览 Markdown

**VS Code Preview**:
```bash
# 在 VS Code 中打开
code data/outputs/*_summary.md

# 按 Ctrl+Shift+V 预览
# 截图应该正确显示
```

**Typora Preview**:
```bash
# 在 Typora 中打开
typora data/outputs/*_summary.md

# 截图实时渲染
```

**Browser Preview**:
```bash
# 转换为 HTML（如需要）
pandoc data/outputs/*_summary.md -o preview.html

# 在浏览器中打开
open preview.html  # Mac
start preview.html  # Windows
xdg-open preview.html  # Linux
```

## Configuration Examples

### 启用帧提取（默认）

```yaml
# config/modules.yaml
video_summary:
  config:
    frame_extraction:
      enabled: true      # 启用
      output_dir: "data/frames"
      format: "jpg"
      quality: 85
```

### 禁用帧提取

```yaml
# config/modules.yaml
video_summary:
  config:
    frame_extraction:
      enabled: false     # 禁用
```

**效果**:
- Markdown 无截图引用
- 跳过所有帧提取处理
- 输出速度更快

### 高质量截图

```yaml
# config/modules.yaml
video_summary:
  config:
    frame_extraction:
      enabled: true
      format: "jpg"
      quality: 95        # 更高质量（文件更大）
```

**对比**:
- Quality 85: ~100-200KB per frame
- Quality 95: ~300-500KB per frame
- Quality 100: ~500KB+ per frame

### PNG无损格式

```yaml
# config/modules.yaml
video_summary:
  config:
    frame_extraction:
      enabled: true
      format: "png"      # PNG无损
      quality: 85        # PNG不使用quality参数
```

**PNG特点**:
- 无损压缩
- 文件更大（~500KB-1MB）
- 质量最佳
- 适合印刷或进一步编辑

### 自定义输出目录

```yaml
# config/modules.yaml
video_summary:
  config:
    frame_extraction:
      enabled: true
      output_dir: "custom/screenshots"  # 自定义目录
```

**注意**:
- Markdown相对路径会自动调整
- 目录会自动创建
- 确保路径在项目内（便于管理）

## Advanced Usage

### 批量处理多个视频

```bash
# 创建批处理脚本
cat > batch_process.sh << 'EOF'
#!/bin/bash
videos=(
  "https://www.bilibili.com/video/BV1G49MBLE4D"
  "https://www.bilibili.com/video/BV1234567890"
  "https://www.bilibili.com/video/BV9876543210"
)

for url in "${videos[@]}"; do
  echo "Processing: $url"
  la video "$url"
  echo "Completed: $url"
  echo "---"
done
EOF

# 运行批处理
chmod +x batch_process.sh
./batch_process.sh
```

### 检查处理结果

```bash
# 查看所有输出的 Markdown
ls -lh data/outputs/*_summary.md

# 查看所有提取的帧目录
ls -lh data/frames/

# 统计每个视频的帧数量
for dir in data/frames/*/; do
  echo "$(basename "$dir"): $(ls "$dir"chapter_*.jpg | wc -l) frames"
done
```

### 清理旧数据

```bash
# 清理所有帧截图
rm -rf data/frames/

# 清理所有视频总结
rm -rf data/outputs/video/

# 清理特定视频的数据
rm -rf data/frames/{title}/
rm data/outputs/{title}_summary.md
```

## Edge Cases Examples

### 音频视频（无视频流）

```bash
# 处理纯音频+封面的视频
la video https://www.bilibili.com/audio/au123456

# 系统自动检测无视频流
# 使用封面图片作为所有章节截图
# 输出：所有章节使用同一封面图片
```

**输出示例**:
```markdown
### 第一章节

> ⏱️ 00:00

![第一章节](../frames/audio_title/cover.jpg)

内容摘要...

### 第二章节

> ⏱️ 05:30

![第二章节](../frames/audio_title/cover.jpg)

内容摘要...
```

### 长视频（多章节）

```bash
# 处理2小时长视频（预计10-15章节）
la video https://www.bilibili.com/video/BV1234567890

# 帧提取时间：< 20秒
# 帧文件总大小：~2-5MB
# Markdown输出：正确显示所有章节截图
```

### 特殊字符标题

```bash
# 处理标题含特殊字符的视频
la video https://www.bilibili.com/video/BV...

# 标题："Video: Special @#$ Characters!"
# 系统自动净化为："Video_ Special ___ Characters!"
# 输出目录：data/frames/Video_ Special ___ Characters!/
```

## Troubleshooting Examples

### FFmpeg Not Found

```bash
# 错误信息
RuntimeError: FFmpeg not found. Please install FFmpeg.

# 解决方案
# Windows:
1. 下载 FFmpeg: https://ffmpeg.org/download.html
2. 解压到 C:\ffmpeg
3. 添加到 PATH: setx PATH "%PATH%;C:\ffmpeg\bin"

# Linux:
sudo apt-get update
sudo apt-get install ffmpeg

# Mac:
brew install ffmpeg

# 验证安装
ffmpeg -version
```

### 截图未显示

```bash
# 问题：Markdown中截图未显示

# 检查步骤：
# 1. 确认配置启用
grep "enabled: true" config/modules.yaml

# 2. 确认帧文件存在
ls data/frames/{title}/chapter_*.jpg

# 3. 检查相对路径
grep "!\[" data/outputs/{title}_summary.md

# 4. 验证路径正确性
# 应显示：../frames/{title}/chapter_01.jpg

# 5. 在 VS Code 中预览
code data/outputs/{title}_summary.md
# 按 Ctrl+Shift+V 预览
```

### 帧提取失败

```bash
# 问题：部分章节无截图

# 查看日志
# 最后的错误信息会记录在日志中

# 可能原因：
# 1. 视频文件损坏 → 重新下载
# 2. 时间戳超出范围 → 系统会使用 0.0
# 3. FFmpeg超时 → 检查视频大小和格式

# 检查输出
ls -l data/frames/{title}/
# 查看是否有 chapter_XX.jpg 文件

# 检查 Markdown
grep "screenshot_path" data/outputs/{title}_summary.md
# 查看是否有 null 值
```

### 跨平台路径问题

```bash
# 问题：Windows路径显示错误

# 系统自动处理
# 输入：data\frames\title\chapter_01.jpg
# 输出：../frames/title/chapter_01.jpg

# 验证
# 在 Markdown 中应看到正斜杠 /
grep "../frames/" data/outputs/*_summary.md
```

## Testing Commands

### 单元测试

```bash
# 运行 FrameExtractor 单元测试
pytest tests/modules/test_frame_extractor.py -v

# 预期结果
# 23 passed, 1 warning
```

### 集成测试

```bash
# 测试完整视频总结流程（需要 API Key）
# 设置 API Key
export OPENAI_API_KEY="your-api-key"

# 运行测试
pytest tests/modules/test_video_summary_module.py -k "integration" -v
```

### 手动验证

```bash
# 1. 准备测试视频
TEST_URL="https://www.bilibili.com/video/BV1G49MBLE4D"

# 2. 运行视频总结
la video "$TEST_URL"

# 3. 检查输出目录
OUTPUT_DIR="data/outputs/video"
FRAMES_DIR="data/frames"

# 4. 查看生成的文件
ls -lh "$OUTPUT_DIR"
ls -lh "$FRAMES_DIR"

# 5. 验证 Markdown 内容
cat "$OUTPUT_DIR"/*_summary.md | grep "!\["

# 6. 统计帧数量
FRAMES_COUNT=$(ls "$FRAMES_DIR"/*/chapter_*.jpg | wc -l)
echo "Total frames extracted: $FRAMES_COUNT"

# 7. 预览 Markdown
code "$OUTPUT_DIR"/*_summary.md
```

## Performance Benchmarks

### 典型视频处理时间

```
# 10分钟视频（5章节）
Download:        60-120s
Audio Extract:   10-20s
Transcribe:      120-300s
Summary:         30-60s
Frame Extract:   5-10s    ← 新增部分
Total:           225-510s

# 帧提取占比：< 2-3% 总时间
```

### 存储空间

```
# 10分钟视频（5章节）
Markdown:        ~50KB
Frames (5):      ~500KB-1MB (JPEG 85)
Frames (5 PNG):  ~2-5MB (PNG无损)
Total:           ~550KB-1.1MB

# 每帧大小：
JPEG 85:         ~100-200KB
JPEG 95:         ~300-500KB
PNG:             ~500KB-1MB
```

## Best Practices

### 配置建议

**推荐配置（平衡质量与大小）**:
```yaml
frame_extraction:
  enabled: true
  format: "jpg"
  quality: 85        # 推荐：最佳平衡
```

**高质量配置（印刷/编辑）**:
```yaml
frame_extraction:
  enabled: true
  format: "png"      # 无损
```

**快速配置（节省空间）**:
```yaml
frame_extraction:
  enabled: true
  format: "jpg"
  quality: 70        # 较小文件
```

### 目录管理

```bash
# 定期清理旧数据
# 保留最近30天的数据
find data/frames -mtime +30 -type d -exec rm -rf {} +
find data/outputs/video -mtime +30 -type f -exec rm {} +

# 查看存储占用
du -sh data/frames
du -sh data/outputs/video

# 备份重要数据
tar -czf backup_$(date +%Y%m%d).tar.gz data/frames data/outputs/video
```

### 批量处理优化

```bash
# 并行处理（注意 API Rate Limit）
# 不推荐：可能导致 API 超限
for url in "${urls[@]}"; do
  la video "$url" &
done
wait

# 推荐：顺序处理
for url in "${urls[@]}"; do
  la video "$url"
  sleep 60  # 等待60秒，避免API限速
done
```

## Integration Examples

### 与其他工具集成

**Pandoc转换**:
```bash
# Markdown → PDF（带截图）
pandoc data/outputs/*_summary.md -o output.pdf --pdf-engine=xelatex

# Markdown → HTML
pandoc data/outputs/*_summary.md -o output.html --standalone

# Markdown → Word
pandoc data/outputs/*_summary.md -o output.docx
```

**Obsidian笔记**:
```bash
# 复制到 Obsidian vault
cp data/outputs/*_summary.md ~/obsidian/notes/
cp -r data/frames ~/obsidian/notes/

# 在 Obsidian 中打开
# 截图正确显示（相对路径兼容）
```

**Notion导入**:
```bash
# 转换为 HTML
pandoc data/outputs/*_summary.md -o output.html --embed-images

# 上传到 Notion
# 或使用 Notion API 导入
```

---

**更新日期**: 2026-04-11
**状态**: ✅ 可用于生产环境
**测试**: ✅ 全部通过
**文档**: ✅ 完善