import { useContext, ReactNode } from "react";
import { Precomputed, Reference } from "@/lib/data";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Lock, SlidersHorizontal } from "lucide-react";
import { InfoPopover, ReferencesContext, renderCitations } from "./info-popover";
import { StatusBadge } from "./status-badge";
import { TERMS } from "./term-info";

// A·B·C personality vocabulary (ADR-009). Surfaced as a sublabel under each
// policy button so the user sees the personality at the moment of choosing,
// no hover needed. Kept short to fit under single-letter buttons.
const POLICY_PERSONALITY = {
  A: "Myopic",
  B: "NPV-rational",
  C: "Risk-averse",
} as const;

interface Props {
  policy: string;
  setPolicy: (v: string) => void;
  gasMult: number;
  setGasMult: (v: number) => void;
  initState: string;
  setInitState: (v: string) => void;
  data: Precomputed;
}

// Horizontal sticky control bar — replaces the sidebar from v1.
// Lives just below the hero so users can change the scenario anchor while reading.
export function ControlBar(p: Props) {
  const reg = p.data.calibration_register;
  return (
    <div className="sticky top-[57px] z-20 -mx-6 lg:-mx-10 px-6 lg:px-10 py-3 border-y border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/82">
      <div className="flex flex-wrap items-end gap-x-8 gap-y-4">
        {/* SCENARIO ANCHOR label: vertically centered against the row (not bottom-pinned). */}
        <span className="eyebrow text-[10px] text-primary tracking-[0.2em] self-center">Scenario anchor</span>

        {/* The three control groups live in their own flex-1 container with
            justify-between, so the gaps between Policy / Gas price / Initial state
            auto-grow to fill the row width — no right-side dead space. */}
        <div className="flex-1 flex flex-wrap items-end justify-between gap-x-8 gap-y-4">
          <Group label="Policy" termKey="policy_abc" badge={reg.policy.status} info={
            <InfoPopover title="Operating policy" status={reg.policy.status} source={reg.policy.source} whyV1={reg.policy.why_v1} upgrade={reg.policy.upgrade}
              value={`v1 surface = A/B/C dispatch postures:\nA = myopic merchant (1.0× wear hurdle)\nB = NPV-rational (clamps at 2.5×)\nC = risk-averse (ramps to 4.0×)\n\n"Policy" here is the broader operating-strategy lever — dispatch is the v1 slice; LTSA terms, contract structure, and other operating choices will join the same surface (see the "Custom" workbench affordance next to A/B/C).`} />
          }>
            <div className="inline-flex items-stretch gap-1.5">
              <Segmented
                options={p.data.modes.map((m) => ({
                  k: m,
                  label: m,
                  sub: POLICY_PERSONALITY[m as keyof typeof POLICY_PERSONALITY],
                }))}
                value={p.policy}
                onChange={p.setPolicy}
                testid="policy"
              />
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
        className="w-[460px] text-xs leading-relaxed p-0 border border-popover-border max-h-[80vh] overflow-y-auto"
      >
        {/* Header — title + roadmap badge + one-line intro */}
        <div className="p-4 border-b border-card-border">
          <div className="flex items-start justify-between gap-3 mb-1.5">
            <p className="text-sm font-medium tracking-tight">Policy strategy workbench</p>
            <span className="text-[9px] uppercase tracking-[0.18em] font-semibold text-muted-foreground border border-card-border bg-card/70 px-1.5 py-[1px] rounded shrink-0">
              roadmap
            </span>
          </div>
          <p className="text-[11.5px] text-foreground/80 leading-[1.55]">
            Design and compare candidate dispatch / wear policies against the same
            probability-weighted forward engine that drives A·B·C today. Preview of intent —
            not active in v1.
          </p>
        </div>

        {/* Three sections of preview knobs */}
        <div className="px-4 py-3 space-y-4">
          <WorkbenchSection title="Wear hurdle curve">
            <WorkbenchKnob
              label="Cap multiplier"
              body="Maximum hurdle multiplier when EOH headroom is exhausted. Current presets: A 1.0× · B 2.5× · C 4.0×."
            />
            <WorkbenchKnob
              label="Activation headroom"
              body="EOH below the next-inspection threshold at which the hurdle starts ramping. Currently 4,000 EOH for both B and C."
            />
            <WorkbenchKnob
              label="Curve shape"
              body="How the multiplier interpolates between 1.0× and the cap. Currently linear ramp; step / quadratic / custom on the roadmap."
            />
          </WorkbenchSection>

          <WorkbenchSection title="Start economics">
            <WorkbenchKnob
              label="Wear fraction of start C&M"
              body="Share of [Kumar2012] start C&M charged to a marginal start decision. Currently 0.42 (the GT-side fraction of Kumar's total)."
            />
            <WorkbenchKnob
              label="Per-start-type weights"
              body="Relative aggression on cold / warm / hot starts. Currently $79 / $55 / $35 per MW [Kumar2012] (2011 USD, Gas-CC Table 1-1)."
            />
          </WorkbenchSection>

          <WorkbenchSection title="Comparison & sweep">
            <WorkbenchKnob
              label="Side-by-side"
              body="Overlay a custom policy against A · B · C on the distribution + P&L decomposition. Currently A·B·C overlay only."
            />
            <WorkbenchKnob
              label="Parameter sweep"
              body="Vary one knob across [low · mid · high] over all 25 scenarios — quantify which knob moves the headline most. Currently not exposed."
            />
            <WorkbenchKnob
              label="Save as preset"
              body="Name and persist a custom policy (e.g. 'Lockport-tuned NPV-rational') for reuse across runs. Currently not exposed."
            />
          </WorkbenchSection>
        </div>

        {/* Scope footnote — the ADR-009 anchor that prevents over-promising */}
        <div className="px-4 py-3 border-t border-card-border bg-secondary/30">
          <p className="text-[11px] text-muted-foreground leading-[1.55] italic">
            v1 ships only the three fixed postures; the premium magnitudes (2.5×/4.0×) are
            deferred per ADR-009 pending a complete revenue stack. This workbench is where
            the re-derivation will land.
          </p>
        </div>
      </PopoverContent>
    </Popover>
  );
}

// Section eyebrow + spaced row container used inside the PolicyWorkbenchAffordance
// popover. Eyebrow style matches the rest of the dashboard.
function WorkbenchSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <p className="eyebrow text-[9.5px] mb-1.5">{title}</p>
      <div>{children}</div>
    </div>
  );
}

// Single preview knob row inside the workbench popover.
// Label (medium weight) + body (muted) on two lines, hairline separator.
// `body` may contain `[KEY]` citation markers which are rendered as clickable
// anchors via the same ReferencesContext used by InfoPopover.
function WorkbenchKnob({ label, body }: { label: string; body: string }) {
  const refs = useContext(ReferencesContext) as Record<string, Reference>;
  return (
    <div className="py-1.5 border-b border-card-border/60 last:border-b-0">
      <p className="text-[11px] font-medium text-foreground/90 leading-tight">{label}</p>
      <p className="text-[10.5px] text-muted-foreground mt-0.5 leading-[1.5]">
        {renderCitations(body, refs)}
      </p>
    </div>
  );
}

// Group label has ONE info icon — the InfoPopover (i) — which already carries
// the term explanation in its `value` block plus the calibration-register
// provenance (status / source / why-v1 / upgrade). We deliberately do NOT also
// render a TermInfo (?) here, to avoid duplicate icons on the same label.
// The `termKey` prop is kept on the signature so call-sites still type-check,
// but is intentionally unused.
//
// Layout: label-above-buttons (stacked vertically). Each Group is one column
// in the scenario-anchor row. Stacking gives each Group a fixed compact width
// matching its widest child, so the row stays in one line even when the policy
// buttons carry personality sublabels (A/B/C with Myopic/NPV-rational/Risk-averse).
function Group({ label, badge, info, termKey: _termKey, children }: { label: string; badge?: string; info?: React.ReactNode; termKey?: keyof typeof TERMS; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-1.5">
        <span className="eyebrow text-[10px]">{label}</span>
        {info}
        {badge && <StatusBadge status={badge} size="xs" />}
      </div>
      {children}
    </div>
  );
}

function Segmented({ options, value, onChange, testid }: { options: { k: string; label: string; sub?: string }[]; value: string; onChange: (v: string) => void; testid: string }) {
  // Some segmented controls carry a `sub` per option (e.g. policy personality:
  // A → Myopic, B → NPV-rational, C → Risk-averse). When present, render it as
  // a small muted line under the main label so the vocabulary is visible at all
  // times — no hover needed.
  const hasSub = options.some((o) => o.sub);
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
            className={`px-3 ${hasSub ? "py-1.5" : "py-1.5"} text-[11.5px] font-medium tracking-tight transition-colors leading-tight ${active
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"}`}
          >
            <div className="flex flex-col items-center gap-0.5">
              <span>{o.label}</span>
              {o.sub && (
                <span className={`font-mono text-[9px] tracking-tight ${active ? "text-foreground/70" : "text-muted-foreground/75"}`}>
                  {o.sub}
                </span>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}
