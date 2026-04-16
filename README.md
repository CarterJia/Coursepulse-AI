# CoursePulse AI

Turn sleepy lecture slides into a personal TA report.
上传 PDF，自动产出结构化讲义、术语百科、相关教学视频。

**[Live Demo](https://coursepulse-ai.railway.app)** · [English](README.en.md)

---

## 做什么

CoursePulse AI 把课件 PDF 转成一份结构化的学习报告：按主题分段、抽取考点与易错点、配套公式与示意图、并从 B 站挑出相关教学视频。面向课业重、错过直播的大学生。

## 功能状态

✅ PDF 解析 + 两阶段 LLM 讲义生成
✅ 语义向量 + B 站视频推荐
🚧 错题诊断 — Vision 识别错误并回链课件
🚧 考前复习报告 — 权重地图 + Cheat Sheet

## 架构

三层：Next.js 前端、FastAPI 后端、Postgres + pgvector 数据库。核心流水线是 6 步：解析 → 切片 → 向量化 → Pass-1 规划 → Pass-2 撰写 → 视频推荐。

可视化讲解：访问 [`/architecture`](https://coursepulse-ai.railway.app/architecture) 页。

## 5 分钟本地跑通

前置：Docker Desktop、一个 DeepSeek API key。

```bash
git clone https://github.com/CarterJia/Coursepulse-AI.git
cd coursepulse-ai
cp .env.example .env   # 编辑 .env 填入 DEEPSEEK_API_KEY
docker compose up
```

打开 http://localhost:3000 即可使用。

## Bring your own key

Live Demo 默认每个 IP 每天 3 次免费上传。想跑更多：在首页右下点 "Use my own API key"，填入自己的 DeepSeek API key 即可解锁无限次。

key 只存在你浏览器的 localStorage，不会写入我们的数据库或日志。

## 技术栈

- Next.js 15 / TypeScript / Tailwind / shadcn/ui
- FastAPI / SQLAlchemy / Alembic
- Postgres 16 / pgvector
- DeepSeek Chat / BAAI/bge-small-zh-v1.5
- Docker Compose / Railway

## 设计文档

所有设计 spec 在 [`docs/superpowers/specs/`](docs/superpowers/specs/)。入门建议从 [`2026-04-13-coursepulse-full-product-design.md`](docs/superpowers/specs/2026-04-13-coursepulse-full-product-design.md) 开始。

## License

MIT
