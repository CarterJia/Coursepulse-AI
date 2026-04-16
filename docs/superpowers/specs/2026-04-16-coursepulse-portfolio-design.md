# CoursePulse AI — Portfolio Packaging Design

> 把 CoursePulse AI 打磨成可放在 GitHub 主页的作品集：前端视觉升级、新增 `/architecture` 讲解页、上线 Railway Live Demo、通过配额与 BYOK 控制成本、双语 README。

## 目标与受众

**首要受众：** 国内外招聘方 / 面试官（产品岗、AI 工程岗、全栈岗）。他们不会读代码，只会花 1–3 分钟浏览首屏、截图、Demo、README。

**需要传达的两个信号：**

1. **产品 sense** — 能识别真实场景痛点，界面呈现克制、成熟
2. **AI 工程深度** — 两阶段 LLM 流水线、向量检索、爬虫反反爬这类工程取舍讲得清楚

**明确非目标：** 做成可商业化的 SaaS、支持多用户、数据持久化长时留存、做全球推广。

## 范围

### In-scope

- 新增 `/architecture` 可视化讲解页
- 现有页面（首页上传区 + 报告阅读页）视觉升级到"极简学术风"
- 配额系统（每 IP 每天 3 次）+ BYOK 解锁
- 样板 PDF（MCIT / MCTS 课件）预置入口，不占配额
- 双语 README（中文主 / `README.en.md` 副）
- Railway 部署脚本与环境配置
- "研发中"功能的 Roadmap 展示

### Out-of-scope（在页面上以 "🚧 In development" 标签呈现）

- 错题诊断（Vision）
- 考前复习报告 / Cheat Sheet
- 多用户系统、认证、学习小组
- 自定义域名接入
- CI/CD、监控、分析埋点

## 视觉体系

### 基调

极简学术风。参考 Linear / Vercel docs。

- **配色：** 黑 `#0a0a0a`、白 `#ffffff`、灰 `#6b7280` / `#f3f4f6`；单一强调色靛蓝 `#4F46E5`
- **字体：** 英文 Inter（Google Font），中文 `"PingFang SC"` / 系统默认；标题字重 700，正文 400
- **留白：** 页面最大宽度 1200px 居中；section 之间至少 64px 垂直间距
- **圆角：** 统一 8px（卡片）/ 4px（标签）
- **阴影：** 默认不用阴影；只在 hover 或重要 CTA 上用很淡的 `shadow-sm`

### 不做的事

- 不用深色主题、不用渐变背景、不用大量 emoji、不用花哨动画
- 不堆徽章墙、不用 shadcn 默认橘色边框

## 新页面：`/architecture`

### 目的

让招聘方 1 分钟内理解这个项目的技术深度，不需要读代码。

### 路由与实现

- 路由：`frontend/app/architecture/page.tsx`
- 纯静态 React 组件，不调后端 API
- 页面分三个 section，顺序从上到下

### Section 1 — 流水线 6 步卡片

横向 Flex 排列的 6 张小卡片，按颜色分组：

| # | 步骤 | 技术 | 一句话说明 | 卡片色 |
|---|------|------|-----------|--------|
| 1 | 解析 | PyMuPDF | PDF → 每页文本 + 图像 | 灰 `#f9fafb` |
| 2 | 切片 | 按章节分块 | 104 页 → 104 knowledge chunks | 灰 `#f9fafb` |
| 3 | 向量化 | bge-small-zh | pgvector 存储，支持语义检索 | 蓝 `#eef2ff` |
| 4 | Pass-1 LLM | DeepSeek 规划 | 定主题 + 考点 + 关键词 | 黄 `#fef3c7` |
| 5 | Pass-2 LLM | 逐主题撰写 | Markdown 讲义 + 公式 | 黄 `#fef3c7` |
| 6 | 视频推荐 | B 站检索 + 余弦相似度 | 阈值 0.62 过滤噪声 | 绿 `#dcfce7` |

无 hover 交互，纯静态。小屏（<768px）下 Flex 改成 2 列网格。

### Section 2 — Design Decisions（3 条）

两列网格（小屏单列），每条一个标题 + 2-3 句解释。

**1. 为什么分两个 LLM Pass？**

Pass-1 只输出结构化 JSON 规划（主题、考点、关键词），便宜快。Pass-2 按主题并发撰写详细 Markdown。比单次大提示 token 省约 40%，且失败可局部重试。

**2. 为什么相似度阈值是 0.62？**

实测 `bge-small-zh` 对无关中文文本基线分数在 0.3–0.5，噪声带 0.5–0.6，真正相关 ≥0.65。选 0.62 是召回率和噪声的折中。曾经因为阈值 0.55 出现过"Excel IF 函数"被推给 Q-learning 主题的假阳性案例。

**3. 为什么给 Bilibili 搜索加了 session warmup？**

直接 `requests.get` 会被反爬：10 次请求里有 9 次空响应。解决方案：

- 使用 `requests.Session` 复用连接
- 首次先 GET `bilibili.com` 获取 `buvid3` cookie
- 带完整浏览器 header + `Referer: https://www.bilibili.com/`
- 请求之间 `time.sleep(0.8)`

这是一个真实的生产踩坑，体现工程权衡。

### Section 3 — Stack

黑色底卡片（`bg-gray-900 text-white`），内部是扁平徽章：

```
Next.js 15 · FastAPI · Postgres + pgvector · DeepSeek
sentence-transformers · Docker Compose · Railway
```

### 入口

- 首页 Header 导航栏加 "Architecture" 链接
- README 架构章节指向这页

## 首页（上传入口）改造

### 当前状态

shadcn 默认外观，上传区是一个简单的拖拽框，无 value prop 说明。

### 改造后

- **Hero 区**（上半屏）：
  - H1 标题：`CoursePulse AI`
  - 副标题：一句话 value prop，如 "Turn sleepy lecture slides into a personal TA report"
  - 两个按钮：主按钮 "Upload your slides"（滚动到上传区），次按钮 "Try the sample"（直接用预置 MCTS PDF）
- **功能带**（Hero 下方）：四列横向展示四个核心能力。前两个 ✅，后两个 🚧 带浅色底
- **上传区**：保留拖拽 + BYOK 输入框 + 剩余配额显示
- **Footer**：GitHub 链接、License、/architecture 链接

## 报告阅读页 polish

现有报告页功能完整但视觉层级不够清晰。

- 章节卡片的 title 加大字号（text-2xl → text-3xl），增加字重
- 章节之间加 `<hr class="border-gray-200">` 分隔
- 💡 / ✍️ / ⚠️ / 🧠 四个子区块的左缩进对齐重做，标签改成小写小色块而非 emoji 前缀（emoji 保留但用小号）
- 视频推荐卡（`VideoCard`）统一圆角 8px，封面图加 `border border-gray-200`
- 代码块（Markdown 内联）统一背景色 `#f3f4f6`

## 配额与 BYOK 系统

### 设计目标

- 默认匿名访客每天能免费跑 3 次完整流水线
- 样板 PDF（预置的 MCTS 课件）不占配额，无限次预览
- 想跑更多：用户填入自己的 DeepSeek API key（BYOK）

### 后端实现

**新建 middleware：** `backend/app/middleware/quota.py`

- 拦截 `POST /api/documents`（上传触发点）
- 读请求头 `X-User-API-Key`
  - **有 key：** 跳过配额，把 key 注入到 `request.state.openai_api_key`，后端 `get_openai_client()` 优先使用该 key
  - **无 key：** 走默认配额检查
- 配额用 in-memory dict `{ip: (count, reset_timestamp)}`，每个 IP 每天 UTC 00:00 重置
- 超额时返回 `429` + `{detail: "Daily quota exhausted", use_byok: true}`

**样板 PDF 特殊路径：** `POST /api/documents/sample` — 返回预置 document_id，不走上传流水线，不占配额

**样板 PDF 预置机制：**

- PDF 文件本身：`storage/samples/mcts.pdf`，提交进 git LFS 或镜像构建时 COPY（用哪种看文件大小，>10MB 走 LFS）
- DB 记录预置：新建 Alembic 数据迁移 `alembic/versions/xxxx_seed_sample_document.py`，在 `documents` 和相关 `reports` / `topics` 表里预先插入已生成好的样板报告数据（本地先跑一遍完整流水线，把结果 `pg_dump` 出来作为 seed 数据源）
- `SAMPLE_DOCUMENT_ID` 环境变量指向 seed 出来的那条记录
- 这样用户点 "Try the sample" 不会触发任何 LLM 调用，只是跳到 `/reports/{SAMPLE_DOCUMENT_ID}` 读库

**配额计数器的运行时语义：**

- 使用 Python dict + threading.Lock，进程内存储
- Railway 容器重启（部署新版本时）会清零 —— 这对 demo 可接受
- 不引入 Redis；配额本身就是噪声过滤层，不是严格的计费门槛

**环境变量：**

- `DEEPSEEK_API_KEY` — 服务器默认 key
- `UPLOAD_QUOTA_PER_IP` — 默认 3
- `SAMPLE_DOCUMENT_ID` — 预置样板 document 的 UUID

**OpenAI client 扩展：** `services/openai_client.py` 的 `get_openai_client()` 接受可选 `api_key` 参数，优先于环境变量。所有调用方（reporting、glossary、report_planner）需传递 request 里的 key。

### 前端实现

- **上传区新增 BYOK 输入框**：点一个"Use my own API key"链接展开一个 password input + 保存按钮，存到 `localStorage.deepseek_api_key`
- **所有上传 fetch 调用加请求头**：如果 localStorage 有 key，加 `X-User-API-Key`
- **显示剩余配额**：上传按钮下方 "Today: 2/3 remaining"（从响应头读）；BYOK 模式下显示 "Using your API key"
- **样板 PDF 入口**：首页主按钮旁边的 "Try the sample" 直接打开预置 document 的报告页，不经上传

### 安全考虑

- BYOK key 只存 localStorage，不上数据库、不记日志
- 后端拿到 key 后只在当次请求中使用，不缓存

## README（双语）

### 主文档：`README.md`（中文）

```
CoursePulse AI

一句话 pitch：把课件变成私人助教报告。

[Live Demo] · [English](README.en.md)

──────────────────────────────

## 做什么

一段话：解决什么问题、对谁有价值。

## 功能状态

✅ PDF 解析 + 两阶段 LLM 讲义生成
✅ 语义向量 + B 站视频推荐
🚧 错题诊断 — Vision 识别错误并回链课件
🚧 考前复习报告 — 权重地图 + Cheat Sheet

## 架构

一段话说明三层：frontend / backend / storage。
→ 可视化讲解：/architecture

## 5 分钟本地跑通

docker compose up
打开 http://localhost:3000

## Bring your own key

默认每个 IP 每天 3 次免费。
想跑更多：在首页填入你的 DeepSeek API key（只存在你浏览器 localStorage，不经过我们服务器缓存）。

## 技术栈

- Next.js 15 / TypeScript / Tailwind
- FastAPI / SQLAlchemy / Alembic
- Postgres 16 / pgvector
- DeepSeek Chat / bge-small-zh-v1.5
- Docker Compose / Railway

## 设计文档

docs/superpowers/specs/*.md

## License

MIT
```

### 副文档：`README.en.md`

中文版的英文对照翻译，结构完全一致。

### 样式规则

- 不使用 emoji per heading
- 只在 Status 段落保留 ✅/🚧 表达状态
- section 之间用一个空行分隔；不要用 `---` 水平线堆叠
- 代码块只放会直接运行的命令，不放伪代码

## Railway 部署

### Service 拆分

三个独立 Railway services：

| Service | 构建方式 | 公网 |
|---------|---------|------|
| `frontend` | Docker，从 `frontend/Dockerfile` 构建 | 是 |
| `backend` | Docker，从 `backend/Dockerfile` 构建 | 是 |
| `postgres` | Railway Postgres 插件 | 否（仅 backend 连） |

### 环境变量（Railway 控制台配置）

**backend service：**

- `DEEPSEEK_API_KEY` — 本人的 key
- `UPLOAD_QUOTA_PER_IP=3`
- `DATABASE_URL` — Railway 自动注入
- `EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5`
- `SAMPLE_DOCUMENT_ID` — 预置 document 的 UUID

**frontend service：**

- `NEXT_PUBLIC_API_URL` — 指向 backend service 的公网域名

### 数据持久化策略

- **数据库：** Railway Postgres 插件自带持久化，报告记录永久保留
- **storage/（上传的原始 PDF 和生成的图片）：** 不挂持久卷；每次容器启动时执行清理脚本 `scripts/cleanup_storage.sh` 删除 7 天前的文件
- **样板 PDF：** 镜像构建时 COPY 进 `storage/samples/`，和代码一起走 Docker 镜像，不依赖持久卷

### 冷启动取舍

Railway $5/月 Hobby 计划常驻不休眠，首次访问 <2 秒响应。不使用免费层（冷启动 10-30 秒会劝退招聘方）。

### 域名

使用 Railway 免费子域名 `*.railway.app`。自定义域名不在本期范围内。

### 部署文档

新建 `docs/deployment.md`：步骤化地写清楚 Railway 上手、env 配置、预置样板 PDF 的上传流程。

## 文件结构变更

```
frontend/
  app/
    architecture/
      page.tsx                 # 新增
    page.tsx                   # 改造 Hero 区
  components/
    byok-input.tsx             # 新增
    quota-indicator.tsx        # 新增
  lib/
    api-client.ts              # 加 X-User-API-Key header 注入

backend/
  app/
    middleware/
      quota.py                 # 新增
    api/routes/
      documents.py             # 加 /sample 路由
    services/
      openai_client.py         # get_openai_client() 接受 api_key 参数

scripts/
  cleanup_storage.sh           # 新增，容器启动时执行

docs/
  deployment.md                # 新增

README.md                      # 重写
README.en.md                   # 新增
```

## 测试策略

- **quota middleware：** unit test 覆盖（无 key / 有 key / 超额三种路径 + IP 重置）
- **BYOK 端到端：** 手动在本地用一个假 key 跑一次，确认请求头被读取、LLM 调用用的是该 key
- **`/architecture` 页：** 只做视觉 smoke test，确保桌面/平板/手机三种断点下布局不崩
- **Railway 部署：** 部署一次后跑 smoke test — 上传样板 PDF → 查看报告 → 打开 `/architecture` 页，三步都能通

## 实施顺序建议

1. `/architecture` 页（纯静态，无依赖，可以先单独合入）
2. 首页 Hero + 报告页 polish（纯前端）
3. 配额 + BYOK middleware（后端 + 前端）
4. 样板 PDF 预置入口
5. README 重写（中英双语）
6. Railway 部署与 smoke test

## 成本估算

- Railway Hobby：$5/月
- DeepSeek API（服务器默认 key）：按每次上传 $0.02–0.05 估，配额 3/天/IP × 假设 20 IP/天 = 约 $30/月上限；大多数月份 <$5
- 月运营上限：约 $35。非招聘高峰可降到 $10 以下。

## 交付成果

- 一个可以公开访问的 Live Demo URL
- 一份 GitHub README（中 + 英）能让招聘方 3 秒理解项目
- 一个 `/architecture` 页让技术岗招聘方 1 分钟看懂工程深度
- 一条 BYOK 路径让好奇的开发者自己动手试
