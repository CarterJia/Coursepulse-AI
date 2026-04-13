import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { UploadForm } from "../components/upload-form";

test("renders upload button", () => {
  render(<UploadForm />);
  expect(screen.getByRole("button", { name: /upload/i })).toBeInTheDocument();
});
