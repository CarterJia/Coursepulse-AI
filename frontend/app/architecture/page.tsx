export const metadata = {
  title: "Architecture — CoursePulse AI",
  description: "How the pipeline works and why it was designed this way",
};

type PipelineStep = {
  id: string;
  phase: string;
  tech: string;
  blurb: string;
  tone: "gray" | "blue" | "yellow" | "green";
};

const STEPS: PipelineStep[] = [
  { id: "1", phase: "解析", tech: "PyMuPDF", blurb: "PDF → 每页文本 + 图像", tone: "gray" },
  { id: "2", phase: "切片", tech: "按章节分块", blurb: "104 页 → 104 knowledge chunks", tone: "gray" },
  { id: "3", phase: "向量化", tech: "bge-small-zh", blurb: "pgvector 存储，支持语义检索", tone: "blue" },
  { id: "4", phase: "Pass-1 LLM", tech: "DeepSeek 规划", blurb: "定主题 + 考点 + 关键词", tone: "yellow" },
  { id: "5", phase: "Pass-2 LLM", tech: "逐主题撰写", blurb: "Markdown 讲义 + 公式", tone: "yellow" },
  { id: "6", phase: "视频推荐", tech: "B 站检索 + 余弦相似度", blurb: "阈值 0.62 过滤噪声", tone: "green" },
];

const TONE_STYLES: Record<PipelineStep["tone"], string> = {
  gray: "bg-gray-50 border-gray-200",
  blue: "bg-indigo-50 border-indigo-200",
  yellow: "bg-amber-50 border-amber-200",
  green: "bg-emerald-50 border-emerald-200",
};

export default function ArchitecturePage() {
  return (
    <main className="max-w-6xl mx-auto px-4 py-16 space-y-16">
      <header>
        <p className="text-xs uppercase tracking-widest text-gray-500 font-semibold">How it works</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight">从 PDF 到结构化讲义的 6 步流水线</h1>
        <p className="mt-3 text-gray-600 max-w-2xl">
          上传一份课件需要协同 5 个 AI 调用、2 种模型、1 个向量库。下面是每一步在做什么。
        </p>
      </header>

      <section aria-label="Pipeline">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          {STEPS.map((step) => (
            <div key={step.id} className={`rounded-lg border p-3 ${TONE_STYLES[step.tone]}`}>
              <div className="text-[10px] font-bold text-indigo-600">① {step.phase}</div>
              <div className="mt-1 text-sm font-semibold text-gray-900">{step.tech}</div>
              <div className="mt-1 text-xs text-gray-600">{step.blurb}</div>
            </div>
          ))}
        </div>
      </section>

      <section aria-label="Design decisions">
        <p className="text-xs uppercase tracking-widest text-gray-500 font-semibold">Design decisions</p>
        <div className="mt-4 grid md:grid-cols-3 gap-6">
          <article className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-900">为什么分两个 LLM Pass？</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              Pass-1 只输出结构化 JSON 规划（主题、考点、关键词），便宜快。Pass-2 按主题并发撰写详细 Markdown。
              比单次大提示 token 省约 40%，且失败可局部重试。
            </p>
          </article>
          <article className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-900">为什么相似度阈值是 0.62？</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              实测 <code className="font-mono text-xs bg-gray-100 px-1 py-0.5 rounded">bge-small-zh</code> 对无关
              中文文本基线分数在 0.3–0.5，噪声带 0.5–0.6，真正相关 ≥0.65。选 0.62 是召回率和噪声的折中。
              曾经因为阈值 0.55 出现过 "Excel IF 函数" 被推给 Q-learning 主题的假阳性案例。
            </p>
          </article>
          <article className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-900">为什么给 Bilibili 加 session warmup？</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              直接 <code className="font-mono text-xs bg-gray-100 px-1 py-0.5 rounded">requests.get</code> 会被
              反爬：10 次请求 9 次空响应。解决方案：复用 Session、首次 GET <code className="font-mono text-xs bg-gray-100 px-1 py-0.5 rounded">bilibili.com</code>
              拿 <code className="font-mono text-xs bg-gray-100 px-1 py-0.5 rounded">buvid3</code> cookie、带浏览器 header、请求间 0.8s 间隔。
            </p>
          </article>
        </div>
      </section>

      <section aria-label="Stack" className="bg-gray-900 text-white rounded-lg p-6">
        <p className="text-xs uppercase tracking-widest text-gray-400 font-semibold">Stack</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {[
            "Next.js 15",
            "FastAPI",
            "Postgres + pgvector",
            "DeepSeek",
            "sentence-transformers",
            "Docker Compose",
            "Railway",
          ].map((s) => (
            <span key={s} className="bg-gray-800 px-3 py-1 rounded text-xs">
              {s}
            </span>
          ))}
        </div>
      </section>
    </main>
  );
}
