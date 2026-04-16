import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { Accordion } from "../components/ui/accordion";
import { TopicCard } from "../components/topic-card";

test("renders topic title and markdown body", () => {
  render(
    <Accordion type="multiple" defaultValue={["t"]}>
      <TopicCard id="t" title="矩阵乘法" body="> **💡 一句话：** 线性变换" />
    </Accordion>
  );
  expect(screen.getByText("矩阵乘法")).toBeInTheDocument();
  // blockquote content appears
  expect(screen.getByText(/一句话/)).toBeInTheDocument();
});
