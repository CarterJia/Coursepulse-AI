"""Prompt templates for the two-pass report pipeline.

Pass 1 (REPORT_PLAN_PROMPT) builds the global plan in JSON.
Pass 2 (TOPIC_WRITE_PROMPT) writes one topic's Markdown card.
build_retry_prompt wraps Pass 1 retries with error feedback.
"""

REPORT_PLAN_PROMPT = """你是一位资深助教, 正在为学生生成一份考试导向的学习报告。

## 原始课件内容 (逐页列出)

{pages_block}

## 每页图片清单

{image_manifest_block}

## 你的任务

阅读全部内容, 输出**一个 JSON 对象**, 严格遵守下面的 schema:

{{
  "overview": "2-3 段中文, 说明本课件讲什么、主线是什么",
  "tldr": ["要点 1", "要点 2", "..."],
  "topics": [
    {{
      "title": "主题名 (语义化, 不要写成 'Pages 1-4')",
      "source_pages": [3, 4, 5],
      "uses_images_from_pages": [4],
      "key_points": ["该主题的核心要点"],
      "exam_tips": ["考点提示"],
      "common_mistakes": ["易错点"],
      "search_keywords": ["术语原文", "常见别名", "英文缩写", "通俗说法"]
    }}
  ],
  "exam_summary": {{
    "must_know": ["整份课件的必考清单"],
    "common_pitfalls": ["整份课件的整体易错点"]
  }},
  "quick_review": ["30 分钟急救包, 3-5 条"]
}}

## 判断考点和易错点的启发式

- 出现"重点"/"考试"/"Example"/"注意"等标记的内容
- 所有公式、定义、证明
- 反复出现的术语
- Slide 标题层级高的条目
- 作业题原题出现过的内容

## 其他要求

- 主题数量应当按语义自然划分, 通常 3-8 个
- source_pages 必须是 1-indexed 整数列表, 且出现的页码必须在上面的原始课件中存在
- uses_images_from_pages 可为空数组 []
- search_keywords: 每个主题 3-4 个关键词, 用于在 B站 / YouTube 搜索相关教学视频。
  * 关键目标: **增加召回**, 覆盖同一概念的不同说法
  * 要混合: (1) 课件中的专业术语 (2) 该概念的常见别名 / 中英文写法 / 通俗说法 (up 主实际会用的标题词)
  * 例子: 主题"Q函数估计与回传" → ["Q函数", "Q-learning", "值函数估计", "强化学习 价值函数"]
  * 例子: 主题"UCT算法" → ["UCT", "UCB", "置信上界", "蒙特卡洛树搜索 选择策略"]
  * 例子: 主题"MCTS四步骤" → ["MCTS 流程", "蒙特卡洛树搜索 算法步骤", "selection expansion simulation"]
  * 不要太泛 (如"数学") 也不要太窄 (如完整的公式)
- tldr 条目 5-10 条
- 用与课件相同的语言写作 (中文课件用中文)
- **只输出 JSON, 不要输出任何 Markdown 包裹或解释性文字**
"""


TOPIC_WRITE_PROMPT = """你正在为一份学习报告撰写**一个主题**的 Markdown 卡片。

## 主题元信息

- 标题: {topic_title}
- 涵盖页面: {source_pages}
- 可用图片: {image_paths_block}
- 已确定的核心要点: {key_points}
- 已确定的考点提示: {exam_tips}
- 已确定的易错点: {common_mistakes}

## 该主题相关的原始课件内容

{pages_block}

## 输出格式 (严格遵守)

四个分区之间**必须空两行**(即两个连续空行)。**不要**输出 "### 主题: xxx" 或 "主题: xxx" 之类的标题行, 也不要重复主题名 — 前端已经在折叠卡片顶栏显示标题。直接从"💡 一句话"开始输出。

```
> **💡 一句话：** <一句话抓住本质>


**✍️ 展开：**

<2-5 段完整讲解, 把抽象变直觉>

(如需: **📐 关键公式：** — 三行独立块的 $$ 公式)
(如需: Markdown 表格对比)
(如需示意图: ```mermaid 代码块 — 用 graph LR / graph TD 描述概念流程或结构)


> **⚠️ 考点提示：** <根据已确定的 exam_tips 扩写>


> **🧠 易错点：** <根据已确定的 common_mistakes 扩写>
```

## 格式规则

- **数学公式 (最重要规则, 必须严格遵守)**:
  - 行内小片段 (例如变量 $s$, $a$, 单个符号) 用 $...$
  - 所有关键公式 / 重要公式 / 考点公式 / 定义式 / 核心定理 (如 UCT、PUCT、Bellman、Q-learning 更新式) **必须**用下面的三行块级形式, `$$` 开/闭都独占一行:
    ```
    $$
    UCT(s,a) = Q(s,a) + c\\sqrt{{\\frac{{\\ln N(s)}}{{N(s,a)}}}}
    $$
    ```
  - 禁止写成同一行的 `$$公式$$`(这种格式会被当成行内,失去视觉突出)
  - 禁止用 `$公式$` 包裹整条关键公式(会被当成行内)
  - 公式前后必须各空一行
- 重点术语用 **加粗**
- 提示、警告用 > blockquote
- 四个小节标题 (💡 一句话、✍️ 展开、⚠️ 考点提示、🧠 易错点) 之间**必须空两行**
- 不要输出任何 "### 主题:" 或 "主题:" 开头的标题行
- 尽量用直观类比帮助理解
- 使用与原课件相同的语言

## Mermaid 图示规则 (严格)

- 如要画图, 只使用 `graph LR` 或 `graph TD`。
- 节点标签**只允许**: ASCII 字母、数字、空格、汉字。
- 节点标签**不允许**出现: ( ) [ ] {{ }} , ; : " ' / \\
- 如果标签需要符号或公式, 必须把整个标签用双引号包起来, 例如 `A["Q(s,a) 回传"] --> B["UCB1 选择"]`。
- 不确定能否画对时, 跳过 Mermaid, 改用上面提供的图片。

## 图片引用规则 (严格)

- **不要嵌入原课件图片**。课件原图常常包含 logo、二维码、低质量截图, 观感差。
- 如果需要图示, 一律用 `mermaid` 代码块自己画流程图 / 结构图。
- 公式直接用 KaTeX ($$ ... $$), 不要把公式截图嵌入。
- 不要输出任何 `![](...)` 语法。

## 列表格式规则

- 枚举≥2 个条目时, **必须**用 Markdown 列表 (每条独占一行, 行首有 `- ` 或 `1. `)。
- **⚠️ 考点提示 和 🧠 易错点 的 blockquote 里如果有多条**, 必须这样写:
  ```
  > **⚠️ 考点提示：**
  >
  > - 第一条...
  > - 第二条...
  > - 第三条...
  ```
  不要把多条写成一段长话或用冒号分隔的平铺文字。
- 有顺序/步骤用 `1. 2. 3.` (例如算法步骤)。
- 并列/无顺序用 `- ` (例如考点清单)。
- 不要在同一段里写成 "1. xx 2. yy 3. zz" — 必须拆成单独的行。
- 不要使用 (1)、①、1) 这类内联编号。

**只输出上面格式定义的 Markdown, 不要加开场白或结语。**
"""


def build_retry_prompt(original_prompt: str, previous_response: str, error: str) -> str:
    """Wrap a failed Pass-1 attempt with the error feedback so the LLM can correct itself."""
    return (
        f"{original_prompt}\n\n"
        f"## 上次尝试失败\n\n"
        f"你上次的输出是:\n\n```\n{previous_response}\n```\n\n"
        f"解析失败原因: {error}\n\n"
        f"请修正这个错误并重新输出一个合法的 JSON 对象。不要输出任何其他文本。"
    )


# ---------------------------------------------------------------------------
# Legacy prompts — kept because reporting.py still imports CHAPTER_REPORT_PROMPT
# ---------------------------------------------------------------------------

CHAPTER_REPORT_PROMPT = """\
You are an expert teaching assistant. Given the following raw slide content \
from a course chapter titled "{chapter_title}", produce a clear, logically \
structured lecture note that:

1. Expands abbreviated bullet points into full explanations
2. Fills in implicit logical steps between concepts
3. Adds intuitive examples where helpful
4. Preserves all formulas and technical terms exactly

## Slide Content

{context}

## Instructions

Write the expanded lecture note in Markdown. Use ## for section headings. \
Be thorough but concise — aim for 2-3x the length of the original content. \
Write in the same language as the slide content.

Respond with ONLY the lecture note content, no preamble."""

GLOSSARY_EXTRACT_PROMPT = """\
You are a teaching assistant. From the following course material, extract \
all technical terms and jargon that a student might not know.

## Course Material

{text}

## Instructions

For each term, provide:
- term: the exact term as it appears
- definition: a clear 1-2 sentence definition
- analogy: a simple real-world analogy (optional, omit if not helpful)

Respond as a JSON array:
[{{"term": "...", "definition": "...", "analogy": "..."}}]

Only include genuinely technical terms, not common words. Respond with ONLY \
the JSON array, no preamble."""
