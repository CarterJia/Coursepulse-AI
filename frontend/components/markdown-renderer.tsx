"use client";

import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import mermaid from "mermaid";

interface MarkdownRendererProps {
  content: string;
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

  useEffect(() => {
    ensureMermaidInitialized();
    if (ref.current) {
      const id = `mermaid-${Math.random().toString(36).slice(2)}`;
      mermaid
        .render(id, code)
        .then(({ svg }) => {
          if (ref.current) ref.current.innerHTML = svg;
        })
        .catch((err) => {
          if (ref.current) ref.current.innerHTML = `<pre>Mermaid error: ${String(err)}</pre>`;
        });
    }
  }, [code]);

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
            return (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={src} alt={alt ?? ""} className="rounded border my-4 max-w-full" />
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
