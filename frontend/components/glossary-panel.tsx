"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface GlossaryEntry {
  id: string;
  term: string;
  definition: string;
  analogy?: string | null;
}

interface GlossaryPanelProps {
  entries: GlossaryEntry[];
}

export function GlossaryPanel({ entries }: GlossaryPanelProps) {
  if (entries.length === 0) return null;

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm">
          Glossary ({entries.length})
        </Button>
      </SheetTrigger>
      <SheetContent className="overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Glossary</SheetTitle>
        </SheetHeader>
        <div className="mt-4 space-y-4">
          {entries.map((entry) => (
            <div key={entry.id}>
              <Badge variant="secondary" className="mb-1">{entry.term}</Badge>
              <p className="text-sm text-muted-foreground">{entry.definition}</p>
              {entry.analogy && (
                <p className="text-sm italic text-muted-foreground/70 mt-1">{entry.analogy}</p>
              )}
              <Separator className="mt-3" />
            </div>
          ))}
        </div>
      </SheetContent>
    </Sheet>
  );
}
