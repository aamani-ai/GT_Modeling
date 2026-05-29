import { createContext, useContext, Fragment, ReactNode } from "react";
import { Info } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { StatusBadge } from "./status-badge";
import { Reference } from "@/lib/data";

/**
 * Context for the §9 references map (citation key → {title, url}).
 *
 * Set once at the Showcase root with the references block from
 * precomputed.json; consumed here by `Block` so that `[KEY]` patterns in any
 * popover's source / why-v1 / upgrade text resolve to clickable links to the
 * underlying paper, spec, or dataset. Default `{}` keeps the popover working
 * even when no references are provided (e.g. older precomputed.json files).
 */
export const ReferencesContext = createContext<Record<string, Reference>>({});

/**
 * Render a text body, replacing `[KEY]` citation markers with clickable
 * anchors when the key resolves in the ReferencesContext. Unknown keys
 * render as plain text (no broken links).
 */
export function renderCitations(body: string, refs: Record<string, Reference>): ReactNode {
  const parts: ReactNode[] = [];
  const pattern = /\[([A-Za-z0-9_-]+)\]/g;
  let lastIdx = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = pattern.exec(body)) !== null) {
    if (m.index > lastIdx) parts.push(body.slice(lastIdx, m.index));
    const key = m[1];
    const ref = refs[key];
    if (ref) {
      parts.push(
        <a
          key={`ref-${i++}`}
          href={ref.url}
          target="_blank"
          rel="noopener noreferrer"
          title={ref.title}
          className="text-primary underline decoration-primary/40 underline-offset-2 hover:decoration-primary transition-colors"
        >
          [{key}]
        </a>
      );
    } else {
      parts.push(m[0]); // keep plain [KEY] when unknown
    }
    lastIdx = m.index + m[0].length;
  }
  if (lastIdx < body.length) parts.push(body.slice(lastIdx));
  return parts.length === 1 ? parts[0] : <Fragment>{parts}</Fragment>;
}

export function InfoPopover({
  title,
  status,
  source,
  whyV1,
  upgrade,
  value,
}: {
  title: string;
  status: string;
  source: string;
  whyV1: string;
  upgrade: string;
  value?: string;
}) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          aria-label={`Details for ${title}`}
          className="inline-flex items-center justify-center w-4 h-4 rounded-full text-muted-foreground/60 hover:text-primary hover:bg-accent transition-colors"
          data-testid={`info-${title.toLowerCase().replace(/\s+/g, "-")}`}
        >
          <Info className="w-3 h-3" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        side="right"
        align="start"
        className="w-[340px] text-xs leading-relaxed p-0 border border-popover-border"
      >
        <div className="p-4 border-b border-card-border">
          <div className="flex items-start justify-between gap-3 mb-2">
            <p className="text-sm font-medium tracking-tight">{title}</p>
            <StatusBadge status={status} size="xs" />
          </div>
          {value && <p className="font-mono text-[11px] text-foreground/90 mt-1 whitespace-pre-line">{value}</p>}
        </div>
        <div className="p-4 space-y-3">
          <Block label="Source" body={source} />
          <Block label="Why acceptable for v1" body={whyV1} />
          <Block label="What would upgrade it" body={upgrade} />
        </div>
      </PopoverContent>
    </Popover>
  );
}

function Block({ label, body }: { label: string; body: string }) {
  const refs = useContext(ReferencesContext);
  return (
    <div>
      <p className="eyebrow mb-1 text-[9.5px]">{label}</p>
      <p className="text-[11.5px] text-foreground/85 leading-[1.55]">{renderCitations(body, refs)}</p>
    </div>
  );
}
