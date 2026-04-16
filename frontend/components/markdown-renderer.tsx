"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import mermaid from "mermaid";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const SECTION_LABEL_RE = /^(💡|✍️|⚠️|🧠|📐)/;

interface MarkdownRendererProps {
  content: string;
}

function resolveSrc(src: string | undefined): string | undefined {
  if (!src) return undefined;
  if (src.startsWith("/api/")) return `${API_BASE}${src}`;
  return src;
}

function SafeImage({ src, alt }: { src: string | undefined; alt: string }) {
  const [failed, setFailed] = useState(false);
  const resolved = resolveSrc(src);
  if (!resolved || failed) return null;
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={resolved}
      alt={alt}
      className="rounded border my-4 max-w-full"
      onError={() => setFailed(true)}
    />
  );
}

let mermaidInitialized = false;
function ensureMermaidInitialized() {
  if (!mermaidInitialized && typeof window !== "undefined") {
    mermaid.initialize({ startOnLoad: false, theme: "default" });
    mermaidInitialized = true;
  }
}

function MermaidBlock({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    ensureMermaidInitialized();
    if (ref.current) {
      const id = `mermaid-${Math.random().toString(36).slice(2)}`;
      mermaid
        .render(id, code)
        .then(({ svg }) => {
          if (ref.current) ref.current.innerHTML = svg;
        })
        .catch(() => setHidden(true));
    }
  }, [code]);

  if (hidden) return null;
  return <div ref={ref} className="mermaid-block my-4" />;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          code({ className, children, ...rest }) {
            const match = /language-(\w+)/.exec(className || "");
            if (match && match[1] === "mermaid") {
              return <MermaidBlock code={String(children).trim()} />;
            }
            return (
              <code className={className} {...rest}>
                {children}
              </code>
            );
          },
          img({ src, alt }) {
            return <SafeImage src={typeof src === "string" ? src : undefined} alt={alt ?? ""} />;
          },
          strong({ children, ...rest }) {
            const text = Array.isArray(children)
              ? children.map((c) => (typeof c === "string" ? c : "")).join("")
              : typeof children === "string"
              ? children
              : "";
            if (SECTION_LABEL_RE.test(text.trim())) {
              return (
                <strong className="section-label" {...rest}>
                  {children}
                </strong>
              );
            }
            return <strong {...rest}>{children}</strong>;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
