import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { UploadForm } from "../components/upload-form";

test("renders upload dropzone with button", () => {
  render(<UploadForm />);
  expect(screen.getByText(/drop your pdf here/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /upload/i })).toBeInTheDocument();
});
