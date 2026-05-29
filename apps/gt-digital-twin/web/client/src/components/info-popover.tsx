import { Info } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { StatusBadge } from "./status-badge";

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
          {value && <p className="font-mono text-[11px] text-foreground/90 mt-1">{value}</p>}
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
  return (
    <div>
      <p className="eyebrow mb-1 text-[9.5px]">{label}</p>
      <p className="text-[11.5px] text-foreground/85 leading-[1.55]">{body}</p>
    </div>
  );
}
