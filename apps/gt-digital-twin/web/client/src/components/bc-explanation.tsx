import { Precomputed, keyFor, fmtMoneyM } from "@/lib/data";
import { AlertCircle } from "lucide-react";

// Explains B≈C when policy comparison is visible: on a 1-yr horizon, B and C
// may be nearly indistinguishable because C's distinctive headroom<1,000 regime is not reached.
export function BcExplanation({ data, gasMult }: { data: Precomputed; gasMult: number }) {
  const a = data.grid[keyFor("A", gasMult, "aged")]?.quantiles.net_pl_usd.P50;
  const b = data.grid[keyFor("B", gasMult, "aged")]?.quantiles.net_pl_usd.P50;
  const c = data.grid[keyFor("C", gasMult, "aged")]?.quantiles.net_pl_usd.P50;
  if (a === undefined || b === undefined || c === undefined) return null;
  const bcGap = Math.abs(b - c);

  return (
    <aside className="rounded-md border border-card-border bg-secondary/30 p-4 lg:p-5">
      <div className="flex items-start gap-3">
        <div className="w-6 h-6 rounded-full bg-[hsl(var(--status-assumed)/0.15)] flex items-center justify-center shrink-0 mt-0.5">
          <AlertCircle className="w-3.5 h-3.5 text-[hsl(var(--status-assumed))]" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-[12.5px] font-medium tracking-tight mb-1">Why B ≈ C on a 1-year horizon</h3>
          <p className="text-[11.5px] text-muted-foreground leading-[1.6]">
            Policies B and C only differ where EOH headroom drops below ~1,000 — B clamps the wear-penalty multiplier at 2.5×, C keeps climbing to 4.0×. On a 1-year forward from aged EOH ≈ 42k, headroom stays in the 5,600 → 1,600 band the whole run. The plant never operates in C's distinctive regime, so the policy difference can't express itself. Most of A's visible edge is inherited state, not in-forward dispatch (A took its MI in history; B/C carry the deferred MI). A multi-year forward is what would actually let the in-forward policy bite — see <span className="font-mono">dispatch_mechanics.md §3.7</span> and ADR-009.
          </p>
          <div className="mt-3 grid grid-cols-3 gap-3 max-w-md">
            <Stat label="A" value={fmtMoneyM(a, 2)} primary />
            <Stat label="B" value={fmtMoneyM(b, 2)} />
            <Stat label="C" value={fmtMoneyM(c, 2)} />
          </div>
          <p className="mt-2.5 text-[10.5px] text-muted-foreground/80 font-mono">
            B vs C P50 differ by ~{fmtMoneyM(bcGap, 2)} — below display precision. A vs B/C gap is mostly inherited historical state.
          </p>
        </div>
      </div>
    </aside>
  );
}

function Stat({ label, value, primary }: { label: string; value: string; primary?: boolean }) {
  return (
    <div className="border-l border-border pl-3">
      <p className="eyebrow text-[9.5px] mb-0.5">Policy {label}</p>
      <p className={`tabular text-sm ${primary ? "text-primary" : "text-foreground"}`}>{value}</p>
    </div>
  );
}
