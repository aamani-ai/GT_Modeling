/**
 * TwinLayers — compact narrative flow visual.
 *
 * Sits high in the page (between the hero + control bar and the §01/§02
 * forecast) to set up the rest of the dashboard: this is not a single
 * model, it is a chain of five composable modules. Each module's
 * outputs flow into the next; the §-numbered sections downstream
 * expose each layer in detail.
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

  const layers: { id: string; eyebrow: string; title: string; sub: string; kind: "input" | "core" | "output" }[] = [
    { id: "env", eyebrow: "01 · Inputs",   title: "Weather & market",      sub: "SEAS5 · NYISO LBMP · Henry Hub",       kind: "input" },
    { id: "st",  eyebrow: "02 · State",     title: "Engineering state",     sub: "EOH · rotor · fouling · counters",        kind: "core" },
    { id: "dp",  eyebrow: "03 · Decision",  title: "Dispatch policy",       sub: "Spark margin · 3/2/1×CC · A/B/C hurdle",  kind: "core" },
    { id: "wr",  eyebrow: "04 · Ledger",    title: "Wear & LTSA accrual",   sub: "Fatigue · CI/MI events · contract",      kind: "core" },
    { id: "out", eyebrow: "05 · Outputs",   title: "Distribution & P&L",    sub: "Energy margin · owner cost · spread",   kind: "output" },
  ];

  // Column geometry: 5 columns inside 1400 wide. 60px left/right gutter.
  const VBW = 1400;
  const VBH = 230;
  const gutter = 50;
  const colWidth = (VBW - gutter * 2) / 5;
  const blockW = colWidth - 22; // 22px gap between blocks
  const blockH = 110;
  const blockY = 60;

  return (
    <section className="space-y-5" data-testid="twin-layers">
      <header className="max-w-2xl">
        <p className="eyebrow mb-2">How the twin composes</p>
        <h2 className="display-sm text-[20px] md:text-[22px] tracking-[-0.01em] leading-[1.15]">
          Five modules, one composed forecast.
        </h2>
        <p className="mt-2 text-[12.5px] text-foreground/70 leading-[1.55]">
          The engine is a chain — environment conditioning enters on the left, each module updates state, and the
          dispatch / wear / contract layers compose into the right-hand distribution. The sections below open up
          each module; the configuration deep-dive at the bottom of the page exposes every knob.
        </p>
      </header>

      <div className="panel p-5 lg:p-6 grid-bg">
        <svg
          viewBox={`0 0 ${VBW} ${VBH}`}
          className="w-full h-auto"
          role="img"
          aria-labelledby="twin-layers-title twin-layers-desc"
        >
          <title id="twin-layers-title">Five-stage digital twin flow diagram</title>
          <desc id="twin-layers-desc">
            Weather and market inputs feed engineering state, which feeds dispatch policy, which feeds wear and
            LTSA accrual, which produces the output distribution and profit-and-loss decomposition.
          </desc>

          {/* Top eyebrow row label */}
          <text x={gutter} y={28} className="num-pro" fontSize="11"
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

          {/* Connector arrows between blocks */}
          {layers.slice(0, -1).map((_, i) => {
            const x1 = gutter + i * colWidth + blockW;
            const x2 = gutter + (i + 1) * colWidth;
            const y = blockY + blockH / 2;
            const isLive = i >= 1 && i <= 3; // core chain
            return (
              <g key={`arrow-${i}`}>
                <line
                  x1={x1}
                  y1={y}
                  x2={x2 - 6}
                  y2={y}
                  stroke={isLive ? "hsl(var(--signal))" : "hsl(var(--primary))"}
                  strokeWidth="1.4"
                  opacity={isLive ? 0.85 : 0.5}
                />
                <polygon
                  points={`${x2 - 6},${y - 4} ${x2},${y} ${x2 - 6},${y + 4}`}
                  fill={isLive ? "hsl(var(--signal))" : "hsl(var(--primary))"}
                  opacity={isLive ? 0.85 : 0.55}
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

            // All five cards share the same clean card fill so every label
            // stays legible. The kind (input / core / output) is differentiated
            // by border color only — institutional, not brochure-styled.
            const borderColor = isCore
              ? "hsl(var(--signal))"
              : isOutput
                ? "hsl(var(--primary))"
                : "hsl(var(--border-strong))";

            const fill = "hsl(var(--card))";

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

          {/* Module-to-section index along the bottom */}
          {layers.map((l, i) => {
            const x = gutter + i * colWidth;
            // Refs match the post-swap section order: §01 P&L, §02 Forecast.
            const ref = ["§02 fuel/LBMP envelope", "§07 engine state", "§01 P&L · §05 analogs", "§03 assumptions · §07 LTSA", "§01 P&L · §02 forecast"][i];
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
            <span className="w-2.5 h-2.5 rounded-sm border border-[hsl(var(--border-strong))] bg-card" />
            Boundary input
          </span>
          <span className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-sm border-2 border-[hsl(var(--signal))] bg-card" />
            Live engine module
          </span>
          <span className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-sm border-2 border-[hsl(var(--primary))] bg-card" />
            Composed output
          </span>
          <span className="ml-auto font-mono text-[10px]">5 modules · 1 probability-weighted distribution</span>
        </div>
      </div>
    </section>
  );
}
