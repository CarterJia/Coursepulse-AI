import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { MarkdownRenderer } from "../components/markdown-renderer";


test("renders plain markdown bold", () => {
  render(<MarkdownRenderer content="**hello**" />);
  expect(screen.getByText("hello").tagName).toBe("STRONG");
});

test("renders inline LaTeX as KaTeX span", () => {
  const { container } = render(<MarkdownRenderer content="When $x^2 = 4$ then..." />);
  // KaTeX emits a .katex class
  expect(container.querySelector(".katex")).not.toBeNull();
});

test("renders Mermaid code block as a div with mermaid class", () => {
  const md = "```mermaid\ngraph LR\nA-->B\n```";
  const { container } = render(<MarkdownRenderer content={md} />);
  expect(container.querySelector(".mermaid-block")).not.toBeNull();
});

test("renders image tags for markdown images", () => {
  render(<MarkdownRenderer content="![alt](/api/files/abc/page_1_img_0.png)" />);
  const img = screen.getByAltText("alt") as HTMLImageElement;
  expect(img.src).toContain("/api/files/abc/page_1_img_0.png");
});

test("renders GFM tables", () => {
  const md = "| A | B |\n|---|---|\n| 1 | 2 |";
  render(<MarkdownRenderer content={md} />);
  expect(screen.getByRole("table")).toBeInTheDocument();
});
