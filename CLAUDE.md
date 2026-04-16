# CoursePulse AI

将沉闷的 Slides 转化为逻辑严密的"私人助教报告"，连接知识断层，通过错题驱动精准复习。

## 产品设计文档

**权威设计 spec：** [`docs/superpowers/specs/2026-04-13-coursepulse-full-product-design.md`](docs/superpowers/specs/2026-04-13-coursepulse-full-product-design.md)

包含：架构、5 个垂直切片的完整设计、API 端点、数据库表、前端页面规划。

## 技术栈

- **前端：** Next.js + Tailwind CSS + shadcn/ui
- **后端：** FastAPI (Python)
- **数据库：** Postgres 16 + pgvector
- **AI：** OpenAI GPT-4o (LLM + Vision) + text-embedding-3-small (Embedding)
- **编排：** Docker Compose
- **视频推荐：** YouTube Data API v3（可选）

## 核心功能

1. **课件解析与扩写** — 上传 PDF，生成结构化教学讲义 + 术语百科
2. **视频推荐** — 按章节推荐 YouTube 短视频
3. **错题诊断** — 上传作业截图，GPT-4o Vision 识别错误，回链课件知识点
4. **考前复习** — 综合权重打分，生成复习优先级地图 + Cheat Sheet

## 项目结构

```
frontend/          Next.js 前端
backend/           FastAPI 后端
  app/
    api/routes/    API 路由
    models/        SQLAlchemy 数据模型
    services/      业务逻辑（解析、检索、报告、诊断、视频）
    schemas/       Pydantic 请求/响应模型
    tasks/         异步任务（Job 状态机）
    db/            数据库连接与 Base
  alembic/         数据库迁移
  tests/           后端测试
storage/           本地文件存储（slides/, assignments/, derived/）
docs/              设计文档与归档
```

## 开发约定

- 异步重任务用 FastAPI BackgroundTasks，不引入 Celery
- GPT-4o prompt 模板集中在 `services/prompts.py`
- 文件存磁盘，不存数据库
- YouTube API 可选，缺 key 时优雅降级
- 单用户本地应用，不做认证系统

## 历史文档

- [`docs/archive/2026-03-10-coursepulse-mvp-implementation-plan.md`](docs/archive/2026-03-10-coursepulse-mvp-implementation-plan.md) — 骨架阶段实施计划（已完成）
