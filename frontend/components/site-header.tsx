import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-gray-200">
      <div className="max-w-6xl mx-auto h-14 px-4 flex items-center justify-between">
        <Link href="/" className="font-semibold text-gray-900 tracking-tight">
          CoursePulse AI
        </Link>
        <nav aria-label="Main navigation" className="flex items-center gap-6 text-sm text-gray-600">
          <Link href="/architecture" className="hover:text-gray-900 transition-colors">
            Architecture
          </Link>
          <a
            href="https://github.com/CarterJia/Coursepulse-AI"
            className="hover:text-gray-900 transition-colors"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
        </nav>
      </div>
    </header>
  );
}
