import "@/app/globals.css";

export const metadata = {
  title: "CoursePulse AI",
  description: "Transform slides into structured teaching reports",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">{children}</body>
    </html>
  );
}
