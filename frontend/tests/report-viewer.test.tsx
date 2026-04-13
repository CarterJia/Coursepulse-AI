import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { ReportViewer } from "../components/report-viewer";

test("renders section heading", () => {
  render(<ReportViewer title="Week 1 Summary" body="Limits and derivatives." />);
  expect(screen.getByText("Week 1 Summary")).toBeInTheDocument();
});
