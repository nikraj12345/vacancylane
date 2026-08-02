"use client";

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import { Briefcase, Check, ChevronDown, X } from "lucide-react";
import {
  EXPERIENCE_OPTIONS,
  type ExperienceBandId,
} from "@/lib/experience";
import { cn } from "@/lib/utils";

interface ExperienceMultiSelectProps {
  value: ExperienceBandId[];
  onChange: (value: ExperienceBandId[]) => void;
  className?: string;
}

type PanelPosition = {
  top: number;
  left: number;
  width: number;
  maxHeight: number;
  placement: "below" | "above";
};

const PANEL_GAP = 6;

export function ExperienceMultiSelect({
  value,
  onChange,
  className,
}: ExperienceMultiSelectProps) {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [position, setPosition] = useState<PanelPosition | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => setMounted(true), []);

  const updatePosition = useCallback(() => {
    const trigger = triggerRef.current;
    if (!trigger) return;
    const rect = trigger.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom - PANEL_GAP - 8;
    const spaceAbove = rect.top - PANEL_GAP - 8;
    const openAbove = spaceBelow < 180 && spaceAbove > spaceBelow;
    const available = Math.max(160, openAbove ? spaceAbove : spaceBelow);
    setPosition({
      top: openAbove ? rect.top - PANEL_GAP : rect.bottom + PANEL_GAP,
      left: rect.left,
      width: Math.max(rect.width, 220),
      maxHeight: Math.min(280, available),
      placement: openAbove ? "above" : "below",
    });
  }, []);

  useLayoutEffect(() => {
    if (!open) return;
    updatePosition();
    const onScroll = () => updatePosition();
    window.addEventListener("scroll", onScroll, true);
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("resize", onScroll);
    };
  }, [open, updatePosition]);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: MouseEvent) {
      const target = event.target as Node;
      if (
        triggerRef.current?.contains(target) ||
        panelRef.current?.contains(target)
      ) {
        return;
      }
      setOpen(false);
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  function toggle(id: ExperienceBandId) {
    onChange(
      value.includes(id) ? value.filter((item) => item !== id) : [...value, id]
    );
  }

  const selected = EXPERIENCE_OPTIONS.filter((option) =>
    value.includes(option.id)
  );

  const panel = open && position && (
    <div
      ref={panelRef}
      style={{
        top: position.placement === "below" ? position.top : undefined,
        bottom:
          position.placement === "above"
            ? window.innerHeight - position.top
            : undefined,
        left: position.left,
        width: position.width,
        maxHeight: position.maxHeight,
      }}
      className="fixed z-[9999] overflow-hidden rounded-xl border border-white/12 bg-[#101411] shadow-2xl shadow-black/60"
    >
      <div className="border-b border-white/8 px-3 py-2">
        <p className="text-[10px] font-semibold uppercase tracking-[.14em] text-slate-500">
          Years of experience
        </p>
        <p className="mt-1 text-[11px] text-slate-500">
          Strict match — jobs must state overlapping years
        </p>
      </div>
      <div className="py-1">
        {EXPERIENCE_OPTIONS.map((option) => {
          const active = value.includes(option.id);
          return (
            <button
              key={option.id}
              type="button"
              onClick={() => toggle(option.id)}
              className={cn(
                "flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm transition hover:bg-white/5",
                active ? "text-emerald-200" : "text-slate-300"
              )}
            >
              <span
                className={cn(
                  "flex h-4 w-4 shrink-0 items-center justify-center rounded border",
                  active
                    ? "border-emerald-400 bg-emerald-400 text-[#07100c]"
                    : "border-white/15"
                )}
              >
                {active && <Check className="h-3 w-3" />}
              </span>
              {option.label}
            </button>
          );
        })}
      </div>
      {value.length > 0 && (
        <div className="flex items-center justify-between border-t border-white/8 px-3 py-2">
          <span className="text-[11px] text-slate-500">
            {value.length} selected
          </span>
          <button
            type="button"
            onClick={() => onChange([])}
            className="text-[11px] text-slate-400 hover:text-white"
          >
            Clear
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div className={cn("relative", className)}>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="inline-flex h-9 min-w-[170px] max-w-[280px] items-center gap-1.5 rounded-lg border border-white/8 bg-[#101411] px-3 text-xs text-slate-300 outline-none hover:border-white/15 focus-visible:border-emerald-400/50"
      >
        <Briefcase className="h-3.5 w-3.5 shrink-0 text-emerald-400" />
        {selected.length === 0 ? (
          <span className="truncate text-slate-500">Any experience</span>
        ) : (
          <span className="flex min-w-0 flex-1 flex-wrap gap-1">
            {selected.map((option) => (
              <span
                key={option.id}
                className="inline-flex items-center gap-1 rounded-md border border-emerald-400/20 bg-emerald-400/10 px-1.5 py-0.5 text-[10px] text-emerald-200"
              >
                {option.label}
                <span
                  role="button"
                  tabIndex={-1}
                  onClick={(event) => {
                    event.stopPropagation();
                    toggle(option.id);
                  }}
                  className="rounded hover:text-white"
                >
                  <X className="h-3 w-3" />
                </span>
              </span>
            ))}
          </span>
        )}
        <ChevronDown
          className={cn(
            "ml-auto h-3.5 w-3.5 shrink-0 text-slate-500 transition-transform",
            open && "rotate-180"
          )}
        />
      </button>
      {mounted && panel ? createPortal(panel, document.body) : null}
    </div>
  );
}
