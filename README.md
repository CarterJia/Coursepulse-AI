# CoursePulse AI

一个面向海外留学生的 AI 学习工具——上传课件 PDF，自动生成结构化中文讲义、术语百科和相关教学视频推荐。

**[Live Demo](https://coursepulse-ai.railway.app)** · [English](README.en.md)

---

## 解决什么问题

海外理工科留学生面临一个共同痛点：英文课件信息密度高、课堂节奏快，课后缺乏中文辅导资源。CoursePulse AI 让你把一份课件 PDF 变成一份完整的中文学习报告：

1. **上传课件** — 拖入一份 PDF，系统自动解析每一页的文字、公式和图表
2. **AI 生成讲义** — 按主题分章节，逐章扩写为易懂的中文讲义，标注考点、易错点和关键公式
3. **术语百科** — 自动提取专业术语，给出中文定义和通俗类比
4. **视频推荐** — 根据每章主题从 B 站匹配高相关度的短视频，辅助理解抽象概念
5. **错题诊断**（开发中）— 上传批改后的作业截图，AI 识别错误并回链到对应课件知识点
6. **考前复习**（开发中）— 综合课件权重和错题频率，生成复习优先级地图和 Cheat Sheet

## 功能状态

- ✅ PDF 解析 + 两阶段 LLM 讲义生成
- ✅ 语义向量 + B 站视频推荐
- 🚧 错题诊断 — Vision 识别错误并回链课件
- 🚧 考前复习报告 — 权重地图 + Cheat Sheet

## 架构

```
Browser
  │
  ▼
┌──────────────────┐
│  Next.js Frontend │  shadcn/ui + Tailwind
│  (port 3000)      │
└────────┬─────────┘
         │ REST API
         ▼
┌──────────────────┐
│  FastAPI Backend  │
│  (port 8000)      │
│                   │
│  Sync routes:     │  uploads, queries, glossary, video search
│  BackgroundTasks: │  PDF parsing, report gen, diagnosis
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌──────────┐
│Postgres │  │ DeepSeek │
│pgvector │  │ Chat API │
│ (5432)  │  │ + BAAI   │
└────────┘  │ Embedding│
            └──────────┘
```

### 核心流水线

用户上传一份 PDF 后，后端按以下 6 步生成完整报告：

```mermaid
flowchart LR
    A["① 解析\nPyMuPDF 提取\n逐页文本+图片"] --> B["② 切片\n按语义段落\n切分知识块"]
    B --> C["③ 向量化\nBAI/bge-small-zh\n写入 pgvector"]
    C --> D["④ Pass-1 规划\nDeepSeek 生成\n章节大纲"]
    D --> E["⑤ Pass-2 撰写\n逐章节扩写\n考点+易错点+公式"]
    E --> F["⑥ 视频推荐\nB站搜索+向量\n相似度排序"]
```

### 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| LLM | DeepSeek Chat | 中文理科内容质量高，成本低于 GPT-4o |
| Embedding | BAAI/bge-small-zh-v1.5 | 中文语义匹配优于 OpenAI 英文模型 |
| 报告生成 | 两阶段（规划→撰写）| 单次生成容易遗漏章节或结构混乱 |
| 视频推荐 | B 站爬虫 + 向量相似度 | 无官方 API；余弦相似度过滤噪声 |
| 向量存储 | pgvector | 不引入额外基础设施，复用 Postgres |
| 异步任务 | FastAPI BackgroundTasks | 单用户场景，避免 Celery/Redis 复杂度 |
| 配额控制 | 内存计数 + BYOK 旁路 | 无需 Redis；BYOK 用户自带 key 不受限 |

### 数据库核心表

```mermaid
erDiagram
    courses ||--o{ documents : contains
    documents ||--o{ document_pages : has
    documents ||--o{ reports : generates
    documents ||--o{ glossary_entries : extracts
    documents ||--o{ video_recommendations : matches
    document_pages ||--o{ knowledge_chunks : splits
    knowledge_chunks ||--o{ embeddings : embeds
    courses ||--o{ assignments : receives
    assignments ||--o{ mistake_diagnoses : analyzes
```

可视化讲解：访问 [`/architecture`](https://coursepulse-ai.railway.app/architecture) 页。

## 5 分钟本地跑通

前置：Docker Desktop、一个 DeepSeek API key。

```bash
git clone https://github.com/CarterJia/Coursepulse-AI.git
cd Coursepulse-AI
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

## License

MIT
