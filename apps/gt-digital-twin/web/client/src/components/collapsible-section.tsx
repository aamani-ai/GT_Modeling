// v1.2 — Collapsible section wrapper. Lets technical content (conditioning, analog
// table, engine layers) sit below the headline story while staying one click away.
//
// Default behavior is `defaultOpen=false`, i.e. minimized. The trigger is a slim
// horizontal bar so the page rhythm doesn't shout — closer to a documentation
// table-of-contents than a flashy accordion.

import { useState, ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";

interface Props {
  /** Section number shown in the eyebrow, e.g. "02". */
  index: string;
  /** Short section heading. */
  title: string;
  /** One-line description shown next to the title even when collapsed. */
  hint?: string;
  /** Right-side metadata (e.g. "real · backtest"). */
  meta?: string;
  defaultOpen?: boolean;
  children: ReactNode;
  testId?: string;
}

export function CollapsibleSection({
  index,
  title,
  hint,
  meta,
  defaultOpen = false,
  children,
  testId,
}: Props) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <Collapsible open={open} onOpenChange={setOpen} data-testid={testId ?? `collapsible-${index}`}>
      <CollapsibleTrigger
        className="w-full group flex items-center justify-between gap-4 py-3.5 px-4 border-y border-border bg-secondary/20 hover:bg-secondary/40 transition-colors text-left"
        data-testid={`${testId ?? `collapsible-${index}`}-trigger`}
      >
        <div className="flex items-center gap-4 min-w-0">
          <span className="font-mono text-[10.5px] tracking-[0.16em] uppercase text-muted-foreground shrink-0">§{index}</span>
          <span className="text-[14px] font-medium text-foreground shrink-0">{title}</span>
          {hint && <span className="hidden md:inline text-[12.5px] text-muted-foreground truncate">{hint}</span>}
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {meta && <span className="hidden md:inline font-mono text-[10px] text-muted-foreground">{meta}</span>}
          <span className="text-[10.5px] font-mono uppercase tracking-[0.1em] text-muted-foreground">{open ? "Hide" : "Show"}</span>
          <ChevronDown
            className={`h-4 w-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`}
            aria-hidden
          />
        </div>
      </CollapsibleTrigger>
      <CollapsibleContent className="overflow-hidden">
        <div className="pt-12 pb-2">{children}</div>
      </CollapsibleContent>
    </Collapsible>
  );
}
