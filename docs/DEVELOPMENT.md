# SynthesAI 开发进度

> 最后更新: 2026-04-24

## 项目概述

SynthesAI 是一个 AI 驱动的学习助手，支持：
- 视频内容总结（B站/YouTube/抖音）
- 网页知识卡片生成
- 词汇提取与学习

---

## 已完成工作

### Phase 1: Server 端 API（已完成 ✅）

**时间**: 2026-04-23

#### Bug 修复
- [x] `schemas.py`: `LearningStatistics` 字段位置错误 → 已修复
- [x] `exceptions.py`: 添加 `to_http_status()` 方法
- [x] `convenience.py`: 添加 `get_shared_api()` 共享实例

#### 新增 server 模块
- [x] `server/config.py` - 服务器配置加载
- [x] `server/context.py` - ServerContext 共享实例管理
- [x] `server/middleware.py` - API Key 认证中间件
- [x] `server/task_manager.py` - 内存任务队列
- [x] `server/main.py` - FastAPI 应用入口
- [x] `server/routes/system.py` - /health, /ready 端点
- [x] `server/routes/query.py` - /skills, /history, /statistics
- [x] `server/routes/link.py` - POST /api/v1/link
- [x] `server/routes/vocabulary.py` - POST /api/v1/vocabulary
- [x] `server/routes/video.py` - 异步任务端点

#### 部署配置
- [x] `config/server.yaml` - 服务器配置文件
- [x] `docker/Dockerfile` - API Docker 构建
- [x] `docker/docker-compose.yaml` - Docker Compose
- [x] `pyproject.toml` - 添加 `[server]` 依赖组

#### API 端点
| 端点 | 类型 | 功能 |
|------|------|------|
| `GET /health` | 系统 | 健康检查 |
| `POST /api/v1/link` | 同步 | 页知识卡片 |
| `POST /api/v1/vocabulary` | 同步 | 词汇提取 |
| `POST /api/v1/video/submit` | 异步 | 提交视频任务 |
| `GET /api/v1/video/{id}/status` | 异步 | 查询进度 |
| `GET /api/v1/video/{id}/result` | 异步 | 获取结果 |
| `GET /api/v1/skills` | 查询 | 技能列表 |
| `GET /api/v1/history` | 查询 | 学习历史 |
| `GET /api/v1/statistics` | 查询 | 学习统计 |

---

### Phase 2: WebUI（已完成 ✅）

**时间**: 2026-04-23

#### 项目配置
- [x] `webui/DESIGN.md` - Notion 风格设计系统
- [x] `webui/package.json` - React + Vite + Tailwind
- [x] `webui/vite.config.ts` - Vite 配置 + API 代理
- [x] `webui/tsconfig.json` - TypeScript 配置
- [x] `webui/tailwind.config.js` - Tailwind 配置
- [x] `webui/postcss.config.js` - PostCSS
- [x] `webui/index.html` - HTML 入口

#### React 代码
- [x] `src/main.tsx` - React 入口
- [x] `src/App.tsx` - 路由配置
- [x] `src/styles/globals.css` - Tailwind + 组件样式
- [x] `src/services/api.ts` - API 客户端（全部端点）
- [x] `src/hooks/useLocalStorage.ts` - localStorage hook
- [x] `src/hooks/useTaskPolling.ts` - 视频任务轮询
- [x] `src/components/layout/Sidebar.tsx` - 侧边栏
- [x] `src/components/layout/MainLayout.tsx` - 主布局
- [x] `src/pages/LinkPage.tsx` - 知识卡片页
- [x] `src/pages/VocabularyPage.tsx` - 词汇学习页
- [x] `src/pages/VideoPage.tsx` - 视频总结页
- [x] `src/pages/HistoryPage.tsx` - 学习历史页
- [x] `src/pages/StatisticsPage.tsx` - 学习统计页
- [x] `src/pages/SettingsPage.tsx` - 设置页

#### 部署配置
- [x] `webui/Dockerfile.webui` - WebUI Docker 构建
- [x] `webui/nginx.conf` - Nginx 反向代理
- [x] `docker/docker-compose.yaml` - 添加 WebUI 服务

---

### Phase 3: P0 功能完善（已完成 ✅）

**时间**: 2026-04-24

#### 导出工具模块
- [x] `src/utils/export.ts` - 统一导出工具模块
  - Markdown 格式转换（支持三种结果类型）
  - 文件下载功能（Blob + URL.createObjectURL）
  - PDF 导出（浏览器打印功能）
  - 文件名清理和时间戳生成

#### 页面功能集成
- [x] `LinkPage.tsx` - 导出 Markdown/PDF 按钮
- [x] `VocabularyPage.tsx` - 导出 Markdown/PDF 按钮
- [x] `VideoPage.tsx` - 导出 Markdown/PDF + 下载字幕按钮

#### TypeScript 修复
- [x] `src/vite-env.d.ts` - Vite 环境类型声明
- [x] 未使用导入清理（Sidebar、useLocalStorage、StatisticsPage）
- [x] VideoPage metadata 类型断言修复

---

## 待完成工作

### 优先级 P1 - 测试与验证

- [ ] **单元测试**: Server API 单元测试
- [ ] **集成测试**: WebUI + API 成成测试
- [ ] **E2E 测试**: 完整流程测试

### 优先级 P2 - 优化

- [ ] **响应式设计**: 移动端优化
- [ ] **加载状态**: 更丰富的 loading 状态
- [ ] **骨架屏**: 数据加载骨架屏
- [ ] **主题切换**: 支持暗色模式

### 优先级 P3 - 扩展功能

- [ ] **历史详情**: 点击历史记录查看详情
- [ ] **批量处理**: 批量提交多个任务
- [ ] **收藏功能**: 收藏喜欢的知识卡片
- [ ] **分享功能**: 分享知识卡片链接

---

## 快速启动

### Server API
```bash
cd /mnt/SynthesAI
pip install -e ".[server]"
uvicorn learning_assistant.server.main:app --reload
# API: http://localhost:8000
```

### WebUI 开发
```bash
cd /mnt/SynthesAI/webui
npm install
npm run dev
# WebUI: http://localhost:5173
```

### Docker 部署
```bash
cd /mnt/SynthesAI/docker
docker-compose up -d
# API: http://localhost:8000
# WebUI: http://localhost:3000
```

---

## 文件结构

```
/mnt/SynthesAI/
├── src/learning_assistant/
│   ├── api/                    # Python API 层
│   │   ├── schemas.py          # ✅ 已修复
│   │   ├── exceptions.py       # ✅ 已添加 HTTP 状态码
│   │   ├── convenience.py      # ✅ 已添加共享实例
│   │   └── agent_api.py        # 核心 API 类
│   │
│   ├── server/                 # ✅ FastAPI 服务端
│   │   ├── main.py             # 应用入口
│   │   ├── config.py           # 配置加载
│   │   ├── context.py          # 共享实例
│   │   ├── middleware.py       # 认证中间件
│   │   ├── task_manager.py     # 任务队列
│   │   └ routes/               # 路由模块
│   │
│   └ modules/                  # 核心功能模块
│   │   ├── video_summary/
│   │   ├── link_learning/
│   │   └ vocabulary/
│   │
│   └ core/                     # 核心组件
│   │   ├── config_manager.py
│   │   ├── plugin_manager.py
│   │   └── event_bus.py
│
├── webui/                      # ✅ React WebUI
│   ├── DESIGN.md               # 设计系统
│   ├── src/
│   │   ├── pages/              # 6 个页面
│   │   ├── components/         # 布局组件
│   │   ├── services/           # API 客户端
│   │   └ hooks/                # 自定义 hooks
│   │   └ styles/               # Tailwind 样式
│   │
│   ├── Dockerfile.webui        # Docker 构建
│   └ nginx.conf               # Nginx 配置
│
├── docker/
│   ├── Dockerfile              # API Docker
│   └ docker-compose.yaml      # 完整部署
│
├── config/
│   ├── server.yaml             # 服务器配置
│   ├── settings.yaml           # 全局设置
│   ├── modules.yaml            # 模块配置
│
└── docs/
    └── DEVELOPMENT.md          # 本文档
```

---

## 注意事项

1. **API Key**: WebUI 需要在设置页配置 API Key（环境变量 `SYNTHESAI_API_KEY`）
2. **异步任务**: 视频任务轮询间隔 5 秒，最长等待约 10 分钟
3. **依赖安装**: 需要 Node.js 20+ 和 Python 3.11+
4. **端口**: API 8000, WebUI 3000 (Docker) 或 5173 (开发)

---

## 下次开发

明天继续时：
1. 先 `npm install` 安装 WebUI 依赖
2. 启动后端 API 测试连接
3. 实现导出/下载功能（P0）
4. 添加单元测试（P1）

祝开发顺利喵～ ฅ'ω'ฅ