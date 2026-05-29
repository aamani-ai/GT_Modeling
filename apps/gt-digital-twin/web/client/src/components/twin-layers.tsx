/**
 * TwinLayers — compact narrative flow visual.
 *
 * Sits high in the page (collapsible §00 between the hero + control bar
 * and §01 P&L) to set up the rest of the dashboard: this is not a single
 * model, it is one static asset anchor + a chain of five composable
 * runtime modules. Each module's outputs flow into the next; the
 * §-numbered sections downstream expose each layer in detail.
 *
 * Implementation: pure SVG flow diagram. Five labelled blocks +
 * connecting lines. The "live" cells use the signal cyan; the
 * downstream outputs use the primary teal. No animation by default —
 * this is an instrument panel, not a marketing banner.
 */
export function TwinLayers() {
  // Five modules across, evenly distributed, in a single horizontal row.
  // Widths chosen for 1440 viewport where the showcase main is 1480 max.
  // SVG viewBox: 1400 × 220 — scales fluidly inside the panel.

  const layers: { id: string; eyebrow: string; title: string; sub: string; kind: "asset" | "input" | "core" | "output" }[] = [
    // 00 · Asset is the static structural anchor (§02 Plant Profile). It does NOT
    // update per tick — it bounds what the engine is allowed to model in the first
    // place. Rendered with a distinct "static config" treatment so the reader
    // doesn't confuse it with the live engine modules to its right.
    { id: "as",  eyebrow: "00 · Asset",    title: "Plant profile",         sub: "Identity · Capability · Realization",   kind: "asset" },
    { id: "env", eyebrow: "01 · Inputs",   title: "Weather & market",      sub: "SEAS5 · NYISO LBMP · Henry Hub",       kind: "input" },
    { id: "st",  eyebrow: "02 · State",     title: "Engineering state",     sub: "EOH · rotor · fouling · counters",        kind: "core" },
    { id: "dp",  eyebrow: "03 · Decision",  title: "Dispatch policy",       sub: "Spark margin · 3/2/1×CC · A/B/C hurdle",  kind: "core" },
    { id: "wr",  eyebrow: "04 · Ledger",    title: "Wear & LTSA accrual",   sub: "Fatigue · CI/MI events · contract",      kind: "core" },
    { id: "out", eyebrow: "05 · Outputs",   title: "Distribution & P&L",    sub: "Energy margin · owner cost · spread",   kind: "output" },
  ];

  // Column geometry: 6 columns inside 1400 wide. 50px left/right gutter.
  const VBW = 1400;
  const VBH = 230;
  const gutter = 50;
  const colWidth = (VBW - gutter * 2) / 6;
  const blockW = colWidth - 18; // 18px gap between blocks
  const blockH = 110;
  const blockY = 60;

  return (
    <section className="space-y-5" data-testid="twin-layers">
      <header className="max-w-2xl">
        <p className="eyebrow mb-2">How the twin composes</p>
        <h2 className="display-sm text-[20px] md:text-[22px] tracking-[-0.01em] leading-[1.15]">
          One static anchor, five modules, one composed forecast.
        </h2>
        <p className="mt-2 text-[12.5px] text-foreground/70 leading-[1.55]">
          Box <span className="font-mono">00 · Asset</span> is the static structural anchor (set once per asset; detailed in §02). The
          remaining boxes are the runtime engine — environment conditioning enters on the left, each module
          updates state, and dispatch / wear / contract layers compose into the right-hand distribution. The
          asset → inputs arrow is dashed because it is a <em>bounding</em> relationship, not a per-tick data flow.
        </p>
      </header>

      <div className="panel p-5 lg:p-6 grid-bg">
        <svg
          viewBox={`0 0 ${VBW} ${VBH}`}
          className="w-full h-auto"
          role="img"
          aria-labelledby="twin-layers-title twin-layers-desc"
        >
          <title id="twin-layers-title">Asset anchor plus five-stage digital twin flow diagram</title>
          <desc id="twin-layers-desc">
            The plant profile (asset anchor) bounds what the engine can model. Weather and market inputs feed
            engineering state, which feeds dispatch policy, which feeds wear and LTSA accrual, which produces
            the output distribution and profit-and-loss decomposition.
          </desc>

          {/* Top eyebrow row label — Asset (static anchor) sits left of Inputs */}
          <text x={gutter} y={28} className="num-pro" fontSize="11"
                fill="hsl(var(--muted-foreground))"
                style={{ letterSpacing: "0.16em", textTransform: "uppercase", fontWeight: 600 }}>
            STATIC ANCHOR
          </text>
          <text x={gutter + colWidth} y={28} className="num-pro" fontSize="11"
                fill="hsl(var(--muted-foreground))"
                style={{ letterSpacing: "0.16em", textTransform: "uppercase", fontWeight: 600 }}>
            INPUTS
          </text>
          <text x={VBW - gutter} y={28} textAnchor="end" className="num-pro" fontSize="11"
                fill="hsl(var(--muted-foreground))"
                style={{ letterSpacing: "0.16em", textTransform: "uppercase", fontWeight: 600 }}>
            OUTPUTS
          </text>

          {/* Horizontal axis baseline */}
          <line x1={gutter} y1={blockY + blockH + 28} x2={VBW - gutter} y2={blockY + blockH + 28}
                stroke="hsl(var(--border-strong))" strokeWidth="1" strokeDasharray="2 3" />

          {/* Connector arrows between blocks. The asset→inputs link is dashed and
              dim — it's a *bounding* relationship (asset config sets what's legal),
              not a per-tick data flow. The runtime chain (inputs→state→…→outputs)
              uses solid colored arrows. */}
          {layers.slice(0, -1).map((_, i) => {
            const x1 = gutter + i * colWidth + blockW;
            const x2 = gutter + (i + 1) * colWidth;
            const y = blockY + blockH / 2;
            const isAssetBound = i === 0;          // asset → inputs (bounding)
            const isLive = i >= 2 && i <= 4;       // 02 STATE ← 01 INPUTS through 04 LEDGER
            const stroke = isAssetBound
              ? "hsl(var(--border-strong))"
              : isLive
              ? "hsl(var(--signal))"
              : "hsl(var(--primary))";
            return (
              <g key={`arrow-${i}`}>
                <line
                  x1={x1}
                  y1={y}
                  x2={x2 - 9}
                  y2={y}
                  stroke={stroke}
                  strokeWidth={isAssetBound ? 1.2 : 1.6}
                  strokeDasharray={isAssetBound ? "4 4" : undefined}
                  opacity={isAssetBound ? 0.55 : 0.9}
                />
                <polygon
                  points={`${x2 - 9},${y - 6} ${x2},${y} ${x2 - 9},${y + 6}`}
                  fill={stroke}
                  opacity={isAssetBound ? 0.55 : 0.9}
                />
              </g>
            );
          })}

          {/* Module blocks */}
          {layers.map((l, i) => {
            const x = gutter + i * colWidth;
            const isInput = l.kind === "input";
            const isOutput = l.kind === "output";
            const isCore = l.kind === "core";
            const isAsset = l.kind === "asset";

            // Differentiate kind via BOTH fill tint AND border color (text stays
            // foreground/black for legibility because all tints are very light).
            //   00 asset / static anchor → muted card fill, dashed muted border
            //     (rendered separately below since SVG <rect> can't take a
            //     stroke-dasharray prop in the normal flow)
            //   01 boundary input → card fill, neutral border
            //   02–04 core / live engine module → signal-soft fill (light blue),
            //     signal border, with a live-tick dot in the top-right
            //   05 composed output → accent fill (light teal), primary border
            const borderColor = isAsset
              ? "hsl(var(--border-strong))"
              : isCore
                ? "hsl(var(--signal))"
                : isOutput
                  ? "hsl(var(--primary))"
                  : "hsl(var(--border-strong))";

            const fill = isAsset
              ? "hsl(var(--muted) / 0.45)"
              : isCore
                ? "hsl(var(--signal-soft))"
                : isOutput
                  ? "hsl(var(--accent))"
                  : "hsl(var(--card))";

            return (
              <g key={l.id}>
                <rect
                  x={x}
                  y={blockY}
                  width={blockW}
                  height={blockH}
                  rx={6}
                  fill={fill}
                  stroke={borderColor}
                  strokeWidth={isCore ? 1.4 : 1}
                  strokeDasharray={isAsset ? "4 4" : undefined}
                />
                <text
                  x={x + 14}
                  y={blockY + 22}
                  fontSize="10.5"
                  fill="hsl(var(--muted-foreground))"
                  style={{ letterSpacing: "0.14em", textTransform: "uppercase", fontWeight: 600 }}
                >
                  {l.eyebrow}
                </text>
                <text
                  x={x + 14}
                  y={blockY + 50}
                  fontSize="15"
                  fill="hsl(var(--foreground))"
                  style={{ fontWeight: 600, letterSpacing: "-0.01em" }}
                >
                  {l.title}
                </text>
                <text
                  x={x + 14}
                  y={blockY + 76}
                  fontSize="11"
                  fill="hsl(var(--foreground) / 0.75)"
                  style={{ letterSpacing: "0" }}
                >
                  {l.sub}
                </text>
                {/* Live tick — only on core modules */}
                {isCore && (
                  <g>
                    <circle
                      cx={x + blockW - 14}
                      cy={blockY + 16}
                      r={3.5}
                      fill="hsl(var(--signal))"
                    />
                    <circle
                      cx={x + blockW - 14}
                      cy={blockY + 16}
                      r={6.5}
                      fill="none"
                      stroke="hsl(var(--signal))"
                      strokeWidth={1}
                      opacity={0.4}
                    />
                  </g>
                )}
              </g>
            );
          })}

          {/* Module-to-section index along the bottom.
              Section order after the §02 Plant Profile insertion (2026-05-29):
                §01 P&L  ·  §02 Plant Profile  ·  §03 Forecast  ·  §04 Assumptions
                §05 Conditioning  ·  §06 Analogs  ·  §07 Backtest  ·  §08 Engine
                §09 What matters  ·  §10 Twin configuration. */}
          {layers.map((l, i) => {
            const x = gutter + i * colWidth;
            const ref = [
              "§02 plant profile",
              "§03 fuel/LBMP envelope",
              "§08 engine state",
              "§01 P&L · §06 analogs",
              "§04 assumptions · §08 LTSA",
              "§01 P&L · §03 forecast",
            ][i];
            return (
              <text
                key={`ref-${i}`}
                x={x + 14}
                y={blockY + blockH + 22}
                fontSize="10"
                fill="hsl(var(--muted-foreground))"
                fontFamily="var(--font-mono)"
                style={{ letterSpacing: "0" }}
              >
                {ref}
              </text>
            );
          })}
        </svg>

        <div className="hairline mt-5 pt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-[10.5px] text-muted-foreground">
          <span className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-sm bg-[hsl(var(--muted)/0.45)] outline outline-1 outline-dashed outline-[hsl(var(--border-strong))]" />
            Static anchor (per asset)
          </span>
          <span className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-sm border border-[hsl(var(--border-strong))] bg-card" />
            Boundary input
          </span>
          <span className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-sm border border-[hsl(var(--signal))] bg-[hsl(var(--signal-soft))]" />
            Live engine module
          </span>
          <span className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-sm border border-[hsl(var(--primary))] bg-[hsl(var(--accent))]" />
            Composed output
          </span>
          <span className="ml-auto font-mono text-[10px]">1 anchor · 5 modules · 1 distribution</span>
        </div>
      </div>
    </section>
  );
}
