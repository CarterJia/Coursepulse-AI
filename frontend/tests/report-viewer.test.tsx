import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { ReportViewer } from "../components/report-viewer";

test("renders chapter titles in accordion", () => {
  const reports = [
    { id: "1", title: "Chapter: Pages 1-4", body: "Expanded lecture content." },
  ];
  render(<ReportViewer reports={reports} />);
  expect(screen.getByText("Chapter: Pages 1-4")).toBeInTheDocument();
});
