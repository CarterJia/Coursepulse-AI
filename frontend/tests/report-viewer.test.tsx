import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { ReportViewer } from "../components/report-viewer";

const REPORTS = [
  { id: "o", section_type: "overview" as const, title: "课件概览", body: "概览内容" },
  { id: "t", section_type: "tldr" as const, title: "要点", body: "- 要点一\n- 要点二" },
  { id: "t1", section_type: "topic" as const, title: "矩阵乘法", body: "展开" },
  { id: "t2", section_type: "topic" as const, title: "可逆矩阵", body: "展开" },
  { id: "e", section_type: "exam_summary" as const, title: "考点汇总", body: "考点" },
  { id: "q", section_type: "quick_review" as const, title: "30 分钟", body: "急救" },
];

test("renders overview and tldr in top zone", () => {
  render(<ReportViewer reports={REPORTS} />);
  expect(screen.getByText("课件概览")).toBeInTheDocument();
  expect(screen.getByText("要点")).toBeInTheDocument();
});

test("renders all topic titles", () => {
  render(<ReportViewer reports={REPORTS} />);
  expect(screen.getByText("矩阵乘法")).toBeInTheDocument();
  expect(screen.getByText("可逆矩阵")).toBeInTheDocument();
});

test("renders exam_summary and quick_review in bottom zone", () => {
  render(<ReportViewer reports={REPORTS} />);
  expect(screen.getByText("考点汇总")).toBeInTheDocument();
  expect(screen.getByText("30 分钟")).toBeInTheDocument();
});

test("shows empty state when no reports", () => {
  render(<ReportViewer reports={[]} />);
  expect(screen.getByText(/No reports/i)).toBeInTheDocument();
});
