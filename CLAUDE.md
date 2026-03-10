# CoursePulse AI - 产品架构与开发指南 (v1.0)

## 1. 产品定位 (Product Vision)

**核心宣言：** 将沉闷的 Slides 转化为逻辑严密的“私人助教报告”，连接知识断层，通过错题驱动精准复习。

**目标用户：**
- 课业繁重的大学生
- 错过直播课的学生
- 理科、工科等逻辑紧密专业的学生

## 2. 核心功能模块 (Core Modules)

### 📂 模块一：智能解析与逻辑补全 (The Brain)

**多格式输入：**
- 支持用户手动上传 PPTX、PDF 及图片

**语境注入 (Context Infusion)：**
- 识别 Slides 上的精简文字与大纲
- 利用大语言模型检索相关领域的通用知识，将“关键词”扩写还原为“逻辑严密、易于理解的讲义”

**视觉与公式解析：**
- 自动识别图片中的图表趋势和数学公式，转化为标准文本

### 🎥 模块二：多维可视化增强 (Visual Bridge)

**视频锚点：**
- 提取章节核心概念，自动匹配 YouTube / Bilibili 优质教育视频，例如 Khan Academy、3Blue1Brown

**精准降落：**
- 筛选时长小于 10 分钟的高评分科普视频，辅助理解抽象概念

**术语百科：**
- 遇到 PPT 里的专业名词，自动在侧边栏给出定义和简单类比

### ✍️ 模块三：作业错因诊断 (Recovery Room)

**错题对齐：**
- 用户上传批改后的作业或 Quiz 照片

**知识闭环：**
- 识别：这是哪个知识点错了？
- 定位：这个知识点在 Slides 的第几页？
- 补救：推荐一段针对该错误点的讲解或变体练习题

**错因画像：**
- 明确区分用户是“计算失误”、“逻辑谬误”还是“基础概念缺失”

### 🗓️ 模块四：考前复习报告 (Sprint Report)

**权重地图：**
- 根据 Slides 篇幅占比和作业错误频率，自动生成“掌握程度地图”，标注复习优先级（必考 / 高频 / 了解即可）

**Cheat Sheet：**
- 一键将整学期的核心公式和关键结论压缩，生成一张符合考试要求的 A4 纸复习精要

## 3. 数据流转示意 (Data Flow)

1. **输入阶段：** Slides 文件 / 作业截图 -> 文本提取与视觉元素分析 -> 提取为“知识元”
2. **处理阶段：** 知识元 -> LLM 逻辑补全 + 外部视频检索 API -> 结构化教学报告
3. **诊断阶段：** 错题视觉识别 -> 知识库检索匹配 -> 错因分析与针对性补漏建议
4. **输出阶段：** 汇总全量数据 -> 权重排序 -> 生成最终的考前复习优先级清单与小抄

## 4. 潜在技术栈建议 (Tech Stack)

**前端 (Frontend)：**
- Next.js + Tailwind CSS，用于打造响应式、阅读体验感强的报告界面

**后端 (Backend)：**
- Python（FastAPI 或 Flask），方便调用各种 AI 库

**AI 核心引擎：**
- **LLM：** Claude 3.5 Sonnet 或 GPT-4o，适合逻辑推理、长文本处理和代码 / 公式理解
- **Embedding：** OpenAI `text-embedding-3-small`，用于构建本地知识库
- **Vector DB：** Pinecone 或 Milvus，存储课件内容以便快速、精准检索

**工具库与 API：**
- `Marker` 或 `PyMuPDF`，用于高精度解析 PDF 和 PPTX
- YouTube Data API v3，用于自动搜索视频链接与元数据

## 5. 产品路线图 (Roadmap)

### Phase 1 (MVP 最小可行性产品)
- 跑通 Slides 手动上传
- 自动生成文字版扩写总结
- 自动推荐并嵌入相关视频链接

### Phase 2 (诊断系统)
- 开发作业截图上传与分析模块
- 实现“错题 -> 课件对应页码”的双向跳转与溯源

### Phase 3 (体验优化)
- 加入课堂录音（Speech-to-Text）支持
- 将教授的口述重点与 Slides 融合，提升报告的“教授语气还原度”

### Phase 4 (社交与共享)
- 上线学习小组模式
- 同一门课的学生可匿名共享作业错题库
- AI 综合生成“全班易错点汇总”

## 6. 当前批准的 MVP 技术架构 (Approved MVP Architecture)

### 产品形态

- 单用户、自用工具
- 本地优先运行
- 通过浏览器访问的本地 Web 应用

### 核心架构

- 前端：`Next.js` + `Tailwind CSS`
- 后端：`FastAPI`
- 数据层：`Postgres 16` + `pgvector`
- 本地编排：`Docker Compose`

架构基线采用 `模块化单体`：

- `frontend`：负责上传、阅读报告、跳转知识点、显示复习结果
- `api`：唯一业务入口，负责解析、检索、生成、诊断、视频推荐
- `db`：统一存储业务数据、生成结果和向量检索数据

### 后端模块划分

- `ingestion`：文件接收、PDF / PPT / 图片解析、OCR、公式与图表文本化
- `retrieval`：知识切片、embedding、向量召回、上下文拼装
- `reporting`：讲义扩写、章节总结、术语解释、cheat sheet 草稿
- `diagnosis`：错题识别、知识点回链、错因分类、补救建议
- `video_search`：概念抽取和短视频推荐

### AI 执行策略

采用 `混合模式`：

- 本地负责：文档解析、OCR、切片、缓存、embedding 持久化
- 云端负责：逻辑补全、讲义扩写、错因分析、解释生成

同步 / 异步边界：

- 轻任务同步：术语解释、单页总结、局部问答、视频推荐
- 重任务异步：整份课件解析、整章报告生成、错题诊断

### 数据与存储

文件本体保存在本地磁盘，不直接存数据库。建议目录：

- `storage/slides/`
- `storage/assignments/`
- `storage/derived/`

数据库核心表建议：

- `courses`
- `documents`
- `document_pages`
- `knowledge_chunks`
- `embeddings`
- `reports`
- `glossary_entries`
- `assignments`
- `mistake_diagnoses`
- `review_priorities`
- `jobs`

### MVP 范围

第一阶段聚焦：

- 上传单份课件
- 解析并切片课件内容
- 生成章节扩写总结
- 提供术语解释
- 推荐相关短视频
- 上传错题图片并回链到相关 slide
- 生成简单复习优先级

第一阶段暂不做：

- 多用户系统
- 学习小组与共享错题库
- 课堂录音融合
- 深度 Bilibili 接入
- 复杂权限系统
- 高质量可打印 cheat sheet 排版引擎
