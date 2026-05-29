import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/lib/theme";

export function Header({ generatedAt, basis, nScen }: { generatedAt: string; basis: string; nScen: number }) {
  const { theme, toggle } = useTheme();
  const generated = new Date(generatedAt);
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="max-w-[1480px] mx-auto px-6 lg:px-10 h-[57px] flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Logo />
          <div className="hidden md:block leading-tight">
            <p className="text-sm font-medium tracking-tight">GT Digital Twin</p>
            <p className="text-[11px] text-muted-foreground tracking-wide">Lockport Energy Associates · Engine Showcase v1</p>
          </div>
        </div>
        <div className="flex items-center gap-5">
          <div className="hidden sm:flex items-center gap-4 text-[11px] font-mono text-muted-foreground">
            <Stat label="basis" value={basis} />
            <Stat label="scenarios" value={String(nScen)} />
            <Stat label="computed" value={generated.toLocaleDateString(undefined, { month: "short", day: "numeric" })} />
          </div>
          <button
            onClick={toggle}
            data-testid="button-theme-toggle"
            className="w-8 h-8 rounded-md border border-border flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>
    </header>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="text-muted-foreground/60 tracking-wide">{label}</span>
      <span className="text-foreground/80">{value}</span>
    </span>
  );
}

function Logo() {
  return (
    <svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-label="GT Digital Twin">
      <circle cx="16" cy="16" r="11" stroke="currentColor" strokeWidth="1.5" className="text-foreground/70" />
      <circle cx="16" cy="16" r="4.5" fill="currentColor" className="text-primary" />
      <line x1="16" y1="1" x2="16" y2="5" stroke="currentColor" strokeWidth="1.5" className="text-foreground/70" />
      <line x1="16" y1="27" x2="16" y2="31" stroke="currentColor" strokeWidth="1.5" className="text-foreground/70" />
      <line x1="1" y1="16" x2="5" y2="16" stroke="currentColor" strokeWidth="1.5" className="text-foreground/70" />
      <line x1="27" y1="16" x2="31" y2="16" stroke="currentColor" strokeWidth="1.5" className="text-foreground/70" />
    </svg>
  );
}
