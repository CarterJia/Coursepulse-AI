"use client";

import { useState } from "react";
import { UploadForm } from "@/components/upload-form";
import { JobStatus } from "@/components/job-status";
import { DocumentList } from "@/components/document-list";

type Feature = {
  id: string;
  status: "shipped" | "wip";
  title: string;
  blurb: string;
};

const FEATURES: Feature[] = [
  { id: "parsing", status: "shipped", title: "PDF 解析 + 两阶段 LLM 讲义生成", blurb: "上传课件，自动生成主题分明的教学报告。" },
  { id: "videos", status: "shipped", title: "语义向量 + B 站视频推荐", blurb: "bge-small-zh 相似度打分，只留真正相关的视频。" },
  { id: "diagnosis", status: "wip", title: "错题诊断", blurb: "Vision 识别作业错误并回链到课件知识点。" },
  { id: "sprint", status: "wip", title: "考前复习报告", blurb: "权重地图 + Cheat Sheet 生成。" },
];

export default function HomePage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [docId, setDocId] = useState<string | null>(null);

  return (
    <main className="max-w-5xl mx-auto py-16 px-4 space-y-16">
      <section>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">CoursePulse AI</h1>
        <p className="mt-4 text-lg text-gray-600 max-w-2xl">
          Turn sleepy lecture slides into a personal TA report.
          上传 PDF，自动产出结构化讲义、术语百科、相关教学视频。
        </p>
        <div className="mt-6 flex gap-3">
          <a
            href="#upload"
            className="inline-flex items-center rounded-md bg-indigo-600 text-white px-4 py-2 text-sm font-medium hover:bg-indigo-500 transition-colors"
          >
            Upload your slides
          </a>
        </div>
      </section>

      <section aria-labelledby="features-heading" className="space-y-4">
        <h2 id="features-heading" className="text-2xl font-semibold tracking-tight">What's inside</h2>
        <div className="grid md:grid-cols-2 gap-4">
          {FEATURES.map((f) => (
            <div
              key={f.id}
              className={`rounded-lg border p-4 ${
                f.status === "shipped" ? "border-gray-200 bg-white" : "border-dashed border-gray-300 bg-gray-50"
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold">
                  {f.status === "shipped" ? (
                    <span className="text-emerald-600">
                      <span aria-hidden="true">✅ </span>已上线
                    </span>
                  ) : (
                    <span className="text-gray-500">
                      <span aria-hidden="true">🚧 </span>研发中
                    </span>
                  )}
                </span>
              </div>
              <h3 className="mt-2 font-semibold text-gray-900">{f.title}</h3>
              <p className="mt-1 text-sm text-gray-600">{f.blurb}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="upload" className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Upload</h2>
          <p className="mt-1 text-sm text-gray-600">PDF only.</p>
        </div>

        <UploadForm
          onUploaded={(data) => {
            setDocId(data.document_id);
            setJobId(data.job_id);
          }}
        />

        {jobId && (
          <JobStatus
            jobId={jobId}
            onComplete={() => {
              if (docId) window.location.href = `/documents/${docId}`;
            }}
          />
        )}
      </section>

      <section aria-label="Recent documents">
        <h2 className="text-2xl font-semibold tracking-tight mb-4">Recent documents</h2>
        <DocumentList />
      </section>
    </main>
  );
}
