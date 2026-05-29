import { TermInfo } from "./term-info";

// Persistent framing strip — top, immediately below header. Premium credibility tone.
export function Banner() {
  return (
    <div className="border-b border-border bg-secondary/30">
      <div className="max-w-[1480px] mx-auto px-6 lg:px-10 py-2.5 flex items-center gap-4">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-[hsl(var(--status-assumed))] shrink-0 animate-pulse" aria-hidden />
        <p className="text-[11px] leading-tight inline-flex items-center gap-1 flex-wrap">
          <span className="font-medium tracking-[0.16em] uppercase text-[hsl(var(--status-assumed))]">Energy-only showcase</span>
          <TermInfo termKey="energy_only" size="xs" side="bottom" />
          <span className="mx-1.5 text-muted-foreground/40">·</span>
          <span className="font-medium tracking-[0.16em] uppercase text-foreground/85">Not a valuation</span>
          <span className="mx-1.5 text-muted-foreground/40">·</span>
          <span className="text-muted-foreground inline-flex items-center gap-1">
            <span>Capacity</span>
            <TermInfo termKey="capacity_revenue" size="xs" side="bottom" />
            <span>and steam</span>
            <TermInfo termKey="steam_revenue" size="xs" side="bottom" />
            <span>revenue are excluded. Figures communicate engine mechanics and scenario spread, not asset economics.</span>
          </span>
        </p>
      </div>
    </div>
  );
}
