import { Precomputed } from "@/lib/data";
import { Switch } from "@/components/ui/switch";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Lock, SlidersHorizontal } from "lucide-react";
import { InfoPopover } from "./info-popover";
import { StatusBadge } from "./status-badge";
import { TERMS } from "./term-info";

interface Props {
  policy: string;
  setPolicy: (v: string) => void;
  gasMult: number;
  setGasMult: (v: number) => void;
  initState: string;
  setInitState: (v: string) => void;
  comparePolicies: boolean;
  setComparePolicies: (v: boolean) => void;
  data: Precomputed;
}

// Horizontal sticky control bar — replaces the sidebar from v1.
// Lives just below the hero so users can change the scenario anchor while reading.
export function ControlBar(p: Props) {
  const reg = p.data.calibration_register;
  return (
    <div className="sticky top-[57px] z-20 -mx-6 lg:-mx-10 px-6 lg:px-10 py-3 border-y border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/82">
      <div className="flex flex-wrap items-center gap-x-7 gap-y-3">
        <span className="eyebrow text-[10px] text-primary tracking-[0.2em]">Scenario anchor</span>

        <Group label="Policy" termKey="policy_abc" badge={reg.policy.status} info={
          <InfoPopover title="A/B/C dispatch policy" status={reg.policy.status} source={reg.policy.source} whyV1={reg.policy.why_v1} upgrade={reg.policy.upgrade}
            value={`A = myopic merchant (1.0× wear hurdle)\nB = NPV-rational (clamps at 2.5×)\nC = risk-averse (ramps to 4.0×)`} />
        }>
          <div className="inline-flex items-stretch gap-1.5">
            <Segmented options={p.data.modes.map((m) => ({ k: m, label: m }))} value={p.policy} onChange={p.setPolicy} testid="policy" />
            <PolicyWorkbenchAffordance />
          </div>
        </Group>

        <Group label="Gas price" termKey="henry_hub" badge={reg.gas_price.status} info={
          <InfoPopover title="Henry Hub multiplier" status={reg.gas_price.status} source={reg.gas_price.source} whyV1={reg.gas_price.why_v1} upgrade={reg.gas_price.upgrade}
            value="Uniform multiplier on Henry Hub series" />
        }>
          <Segmented
            options={p.data.gas_multipliers.map((m) => ({ k: String(m), label: m === 1.0 ? "Base" : `${m}×` }))}
            value={String(p.gasMult)}
            onChange={(v) => p.setGasMult(parseFloat(v))}
            testid="gas"
          />
        </Group>

        <Group label="Initial state" termKey="initial_state" badge={reg.init_state.status} info={
          <InfoPopover title="Initial plant state" status={reg.init_state.status} source={reg.init_state.source} whyV1={reg.init_state.why_v1} upgrade={reg.init_state.upgrade}
            value={`aged: each mode's historical end-state\nfresh: EOH 24k modeling default`} />
        }>
          <Segmented
            options={[{ k: "aged", label: "Aged" }, { k: "fresh", label: "Fresh" }]}
            value={p.initState}
            onChange={p.setInitState}
            testid="init"
          />
        </Group>

        <div className="flex items-center gap-2.5 ml-auto">
          <Switch checked={p.comparePolicies} onCheckedChange={p.setComparePolicies} data-testid="switch-compare" id="compare" />
          <label htmlFor="compare" className="text-[11px] text-muted-foreground select-none cursor-pointer leading-tight">
            Overlay A·B·C on distribution
          </label>
        </div>
      </div>
    </div>
  );
}

// Disabled "Custom" affordance next to the A/B/C selector — communicates that
// A/B/C are three fixed postures inside a broader policy-design surface that
// is on the roadmap, not the engine's full ceiling. Visual language: lock
// icon + dashed/striped (.control-disabled) consistent with the rest of the
// roadmap signals across the dashboard.
function PolicyWorkbenchAffordance() {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-disabled="true"
          data-testid="button-policy-workbench"
          title="Policy strategy workbench — roadmap"
          className="control-disabled inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium tracking-tight text-muted-foreground hover:text-foreground transition-colors cursor-help"
        >
          <SlidersHorizontal className="w-3 h-3 text-muted-foreground/80" aria-hidden="true" />
          <span className="hidden md:inline">Custom</span>
          <Lock className="w-2.5 h-2.5 text-muted-foreground/70" aria-hidden="true" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        side="bottom"
        align="start"
        className="w-[340px] text-xs leading-relaxed p-4 border border-popover-border"
      >
        <div className="flex items-start justify-between gap-3 mb-2">
          <p className="text-sm font-medium tracking-tight">Policy strategy workbench</p>
          <span className="text-[9px] uppercase tracking-[0.18em] font-semibold text-muted-foreground border border-card-border bg-card/70 px-1.5 py-[1px] rounded shrink-0">
            roadmap
          </span>
        </div>
        <p className="text-[11.5px] text-foreground/85 leading-[1.55]">
          Future module: design and compare candidate dispatch / wear policies — custom
          wear hurdles, headroom rules, start-cost weights — against the same
          probability-weighted forward engine that drives A·B·C today.
        </p>
        <p className="text-[11px] text-muted-foreground leading-[1.55] mt-2 italic">
          v1 ships only the three fixed postures (A myopic · B NPV-rational · C risk-averse);
          the premium magnitudes (2.5×/4.0×) are deferred per ADR-009 pending a complete
          revenue stack. This workbench is where that re-derivation will land.
        </p>
      </PopoverContent>
    </Popover>
  );
}

// Group label has ONE info icon — the InfoPopover (i) — which already carries
// the term explanation in its `value` block plus the calibration-register
// provenance (status / source / why-v1 / upgrade). We deliberately do NOT also
// render a TermInfo (?) here, to avoid duplicate icons on the same label.
// The `termKey` prop is kept on the signature so call-sites still type-check,
// but is intentionally unused.
function Group({ label, badge, info, termKey: _termKey, children }: { label: string; badge?: string; info?: React.ReactNode; termKey?: keyof typeof TERMS; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1.5">
        <span className="eyebrow text-[10px]">{label}</span>
        {info}
        {badge && <StatusBadge status={badge} size="xs" />}
      </div>
      {children}
    </div>
  );
}

function Segmented({ options, value, onChange, testid }: { options: { k: string; label: string }[]; value: string; onChange: (v: string) => void; testid: string }) {
  return (
    <div role="radiogroup" className="inline-grid grid-flow-col auto-cols-fr border border-border rounded-md overflow-hidden bg-secondary/30">
      {options.map((o) => {
        const active = o.k === value;
        return (
          <button
            key={o.k}
            role="radio"
            aria-checked={active}
            data-testid={`segmented-${testid}-${o.k}`}
            onClick={() => onChange(o.k)}
            className={`px-3 py-1.5 text-[11.5px] font-medium tracking-tight transition-colors ${active
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"}`}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
