"use client";

import { useEffect, useState } from "react";
import { getStoredKey } from "@/lib/byok";

interface Props {
  remaining: number | null;
}

export function QuotaIndicator({ remaining }: Props) {
  const [hasKey, setHasKey] = useState(false);

  useEffect(() => {
    setHasKey(!!getStoredKey());
  }, [remaining]);

  if (hasKey) {
    return <span className="text-xs text-gray-500">Using your API key · unlimited</span>;
  }
  if (remaining === null) {
    return <span className="text-xs text-gray-500">Daily quota: 3 uploads</span>;
  }
  return <span className="text-xs text-gray-500">Today: {remaining}/3 remaining</span>;
}
