import { Precomputed } from "@/lib/data";
import { InfoPopover } from "./info-popover";
import { StatusBadge } from "./status-badge";
import { Switch } from "@/components/ui/switch";
import { Lock } from "lucide-react";

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

export function ControlPanel(p: Props) {
  const reg = p.data.calibration_register;
  return (
    <div className="space-y-7">
      <Group label="Scenario">
        <Row title="Forward analog set" inline value="25 SEAS5-conditioned windows · RT basis · 1-yr horizon" info={
          <InfoPopover title="Scenario ensemble" status={reg.scenario.status} source={reg.scenario.source} whyV1={reg.scenario.why_v1} upgrade={reg.scenario.upgrade} value="Apr→Mar windows, 1999–2026, probability-weighted" />
        } />
      </Group>

      <Group label="Plant state">
        <Row
          title="Initial state preset"
          info={<InfoPopover title="Initial plant state" status={reg.init_state.status} source={reg.init_state.source} whyV1={reg.init_state.why_v1} upgrade={reg.init_state.upgrade} value={`aged: each mode's historical end-state (EOH ≈ 42k)\nfresh: modeling default (EOH = 24k)`} />}
          badge={reg.init_state.status}
        >
          <Segmented
            options={[{ k: "aged", label: "Aged (from history)" }, { k: "fresh", label: "Fresh start (EOH 24k)" }]}
            value={p.initState}
            onChange={p.setInitState}
            testid="init"
          />
        </Row>
      </Group>

      <Group label="Market">
        <Row
          title="Gas price"
          info={<InfoPopover title="Henry Hub gas multiplier" status={reg.gas_price.status} source={reg.gas_price.source} whyV1={reg.gas_price.why_v1} upgrade={reg.gas_price.upgrade} value={`Applied as a uniform multiplier on the historical Henry Hub series; delivered cost includes RGGI ($${(0.995).toFixed(3)}/MMBtu).`} />}
          badge={reg.gas_price.status}
        >
          <Segmented
            options={p.data.gas_multipliers.map((m) => ({ k: String(m), label: m === 1.0 ? "Base" : `${m}×` }))}
            value={String(p.gasMult)}
            onChange={(v) => p.setGasMult(parseFloat(v))}
            testid="gas"
          />
        </Row>
      </Group>

      <Group label="Policy">
        <Row
          title="Dispatch policy"
          info={<InfoPopover title="A/B/C dispatch policy" status={reg.policy.status} source={reg.policy.source} whyV1={reg.policy.why_v1} upgrade={reg.policy.upgrade} value={`A = myopic merchant (flat 1.0× wear hurdle)\nB = NPV-rational (clamps at 2.5× as MI nears)\nC = risk-averse (ramps to 4.0× near threshold)`} />}
          badge={reg.policy.status}
        >
          <Segmented
            options={p.data.modes.map((m) => ({ k: m, label: m }))}
            value={p.policy}
            onChange={p.setPolicy}
            testid="policy"
            compact
          />
          <div className="mt-3 flex items-center gap-2.5">
            <Switch checked={p.comparePolicies} onCheckedChange={p.setComparePolicies} data-testid="switch-compare" id="compare" />
            <label htmlFor="compare" className="text-[11.5px] text-muted-foreground select-none cursor-pointer">
              Overlay all three policies on the distribution
            </label>
          </div>
        </Row>
      </Group>

      <Group label="Future modules" subdued>
        <p className="text-[11px] text-muted-foreground/80 mb-3 leading-relaxed">
          Disabled in v1 — visible so the roadmap is transparent. Each future control declares why it's currently inactive and what would unlock it.
        </p>
        <DisabledRow title="Capacity revenue (ICAP)" entry={reg.capacity_revenue} />
        <DisabledRow title="Steam revenue (host)" entry={reg.steam_revenue} />
        <DisabledRow title="Deeper LTSA terms" entry={reg.ltsa_deeper} />
        <DisabledRow title="Multi-year horizon" entry={reg.multi_year} />
        <DisabledRow title="Custom wear constants" entry={reg.wear_constants} />
      </Group>
    </div>
  );
}

function Group({ label, subdued, children }: { label: string; subdued?: boolean; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <span className={`eyebrow ${subdued ? "text-muted-foreground/60" : ""}`}>{label}</span>
        <div className="flex-1 h-px bg-border" />
      </div>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

function Row({ title, info, badge, inline, value, children }: { title: string; info?: React.ReactNode; badge?: string; inline?: boolean; value?: string; children?: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5">
          <p className="text-[12px] font-medium tracking-tight text-foreground">{title}</p>
          {info}
        </div>
        {badge && <StatusBadge status={badge} size="xs" />}
      </div>
      {inline && value && <p className="text-[11px] text-muted-foreground leading-relaxed">{value}</p>}
      {children}
    </div>
  );
}

function Segmented({ options, value, onChange, testid, compact }: { options: { k: string; label: string }[]; value: string; onChange: (v: string) => void; testid: string; compact?: boolean }) {
  return (
    <div role="radiogroup" className="inline-grid w-full grid-flow-col auto-cols-fr border border-border rounded-md overflow-hidden bg-secondary/40">
      {options.map((o) => {
        const active = o.k === value;
        return (
          <button
            key={o.k}
            role="radio"
            aria-checked={active}
            data-testid={`segmented-${testid}-${o.k}`}
            onClick={() => onChange(o.k)}
            className={`text-[12px] font-medium tracking-tight ${compact ? "py-1.5" : "py-2"} transition-colors ${active
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

function DisabledRow({ title, entry }: { title: string; entry: { status: string; source: string; why_v1: string; upgrade: string } }) {
  return (
    <div className="opacity-65 border-l border-dashed border-border pl-3 ml-px py-1.5">
      <div className="flex items-center justify-between gap-2 mb-0.5">
        <div className="flex items-center gap-1.5">
          <Lock className="w-2.5 h-2.5 text-muted-foreground/60" />
          <p className="text-[11.5px] font-medium tracking-tight">{title}</p>
          <InfoPopover title={title} status={entry.status} source={entry.source} whyV1={entry.why_v1} upgrade={entry.upgrade} />
        </div>
      </div>
      <p className="text-[10.5px] text-muted-foreground/80 leading-relaxed">{entry.why_v1}</p>
    </div>
  );
}
