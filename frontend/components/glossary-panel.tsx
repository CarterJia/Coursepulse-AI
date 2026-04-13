"use client";

import { useState } from "react";

interface GlossaryEntry {
  term: string;
  definition: string;
  analogy?: string;
}

interface GlossaryPanelProps {
  entries: GlossaryEntry[];
}

export function GlossaryPanel({ entries }: GlossaryPanelProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (entries.length === 0) return null;

  return (
    <aside className="border-l pl-4 ml-4">
      <h3 className="font-semibold mb-2">Glossary</h3>
      <ul className="space-y-2">
        {entries.map((entry) => (
          <li key={entry.term}>
            <button
              className="text-blue-600 underline text-sm"
              onClick={() => setExpanded(expanded === entry.term ? null : entry.term)}
            >
              {entry.term}
            </button>
            {expanded === entry.term && (
              <div className="mt-1 text-sm text-gray-600">
                <p>{entry.definition}</p>
                {entry.analogy && <p className="italic mt-1">{entry.analogy}</p>}
              </div>
            )}
          </li>
        ))}
      </ul>
    </aside>
  );
}
