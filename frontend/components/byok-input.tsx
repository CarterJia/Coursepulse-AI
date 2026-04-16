"use client";

import { useEffect, useState } from "react";
import { clearStoredKey, getStoredKey, setStoredKey } from "@/lib/byok";

export function BYOKInput() {
  const [expanded, setExpanded] = useState(false);
  const [value, setValue] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const existing = getStoredKey();
    if (existing) {
      setSaved(true);
    }
  }, []);

  return (
    <div className="text-sm">
      {!expanded ? (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="text-indigo-600 hover:underline"
        >
          {saved ? "Using your API key — change" : "Use my own API key (unlock unlimited)"}
        </button>
      ) : (
        <div className="flex gap-2 items-center">
          <input
            type="password"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="sk-..."
            className="flex-1 rounded border border-gray-300 px-3 py-1.5 text-sm"
          />
          <button
            type="button"
            onClick={() => {
              if (value.trim()) {
                setStoredKey(value.trim());
                setSaved(true);
              } else {
                clearStoredKey();
                setSaved(false);
              }
              setExpanded(false);
              setValue("");
            }}
            className="rounded bg-gray-900 text-white px-3 py-1.5 text-sm hover:bg-gray-700"
          >
            Save
          </button>
          <button
            type="button"
            onClick={() => {
              clearStoredKey();
              setSaved(false);
              setExpanded(false);
              setValue("");
            }}
            className="text-gray-500 hover:text-gray-900 text-xs"
          >
            Clear
          </button>
        </div>
      )}
      <p className="mt-1 text-xs text-gray-500">
        Stored only in your browser's localStorage. Never sent to our server's logs.
      </p>
    </div>
  );
}
