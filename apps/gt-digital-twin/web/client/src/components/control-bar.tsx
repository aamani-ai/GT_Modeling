import { Precomputed } from "@/lib/data";
import { Switch } from "@/components/ui/switch";
import { InfoPopover } from "./info-popover";
import { StatusBadge } from "./status-badge";

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

        <Group label="Policy" badge={reg.policy.status} info={
          <InfoPopover title="A/B/C dispatch policy" status={reg.policy.status} source={reg.policy.source} whyV1={reg.policy.why_v1} upgrade={reg.policy.upgrade}
            value={`A = myopic merchant (1.0× wear hurdle)\nB = NPV-rational (clamps at 2.5×)\nC = risk-averse (ramps to 4.0×)`} />
        }>
          <Segmented options={p.data.modes.map((m) => ({ k: m, label: m }))} value={p.policy} onChange={p.setPolicy} testid="policy" />
        </Group>

        <Group label="Gas price" badge={reg.gas_price.status} info={
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

        <Group label="Initial state" badge={reg.init_state.status} info={
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

function Group({ label, badge, info, children }: { label: string; badge?: string; info?: React.ReactNode; children: React.ReactNode }) {
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
