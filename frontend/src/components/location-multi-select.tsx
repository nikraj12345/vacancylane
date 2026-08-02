"use client";

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import { Check, ChevronDown, LoaderCircle, MapPin, X } from "lucide-react";
import {
  getPopularLocations,
  getSpecialLocations,
  searchLocations,
  searchLocationsAsync,
  type LocationOption,
} from "@/lib/locations";
import { cn } from "@/lib/utils";

interface LocationMultiSelectProps {
  value: LocationOption[];
  onChange: (value: LocationOption[]) => void;
  placeholder?: string;
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
const PANEL_MAX_HEIGHT = 360;

export function LocationMultiSelect({
  value,
  onChange,
  placeholder = "Search city or country...",
  className,
}: LocationMultiSelectProps) {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [query, setQuery] = useState("");
  const [options, setOptions] = useState<LocationOption[]>(() =>
    searchLocations("")
  );
  const [loading, setLoading] = useState(false);
  const [position, setPosition] = useState<PanelPosition | null>(null);

  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => setMounted(true), []);

  // The panel is portaled to <body>, so it is never clipped by ancestors
  // that use overflow-hidden. Position is derived from the trigger rect.
  const updatePosition = useCallback(() => {
    const trigger = triggerRef.current;
    if (!trigger) return;

    const rect = trigger.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom - PANEL_GAP - 8;
    const spaceAbove = rect.top - PANEL_GAP - 8;
    const openAbove = spaceBelow < 240 && spaceAbove > spaceBelow;
    const available = Math.max(180, openAbove ? spaceAbove : spaceBelow);

    setPosition({
      top: openAbove ? rect.top - PANEL_GAP : rect.bottom + PANEL_GAP,
      left: rect.left,
      width: rect.width,
      maxHeight: Math.min(PANEL_MAX_HEIGHT, available),
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

  useEffect(() => {
    let cancelled = false;
    const q = query.trim();

    setOptions(searchLocations(q));

    if (!q) {
      setLoading(false);
      return;
    }

    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const found = await searchLocationsAsync(q, 50);
        if (!cancelled) setOptions(found);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 180);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query]);

  const quickPicks = useMemo(
    () => [...getSpecialLocations(), ...getPopularLocations().slice(0, 10)],
    []
  );

  function toggle(option: LocationOption) {
    const exists = value.some((item) => item.id === option.id);
    onChange(
      exists ? value.filter((item) => item.id !== option.id) : [...value, option]
    );
  }

  function remove(id: string) {
    onChange(value.filter((item) => item.id !== id));
  }

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
      className="fixed z-[9999] flex min-w-64 flex-col overflow-hidden rounded-xl border border-white/12 bg-[#101411] shadow-2xl shadow-black/60"
    >
      <div className="shrink-0 border-b border-white/8 p-2">
        <div className="relative">
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Type a city or country..."
            className="h-9 w-full rounded-lg border border-white/8 bg-black/25 px-3 pr-8 text-sm text-white outline-none placeholder:text-slate-600 focus:border-emerald-400/40"
          />
          {loading && (
            <LoaderCircle className="absolute right-2.5 top-2.5 h-4 w-4 animate-spin text-slate-500" />
          )}
        </div>
      </div>

      {!query && (
        <div className="shrink-0 border-b border-white/8 px-2 py-2">
          <p className="mb-1.5 px-1 text-[10px] font-semibold uppercase tracking-[.14em] text-slate-500">
            Popular
          </p>
          <div className="flex flex-wrap gap-1.5">
            {quickPicks.map((option) => {
              const active = value.some((item) => item.id === option.id);
              return (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => toggle(option)}
                  className={cn(
                    "rounded-md border px-2 py-1 text-[11px] transition",
                    active
                      ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-200"
                      : "border-white/8 text-slate-400 hover:border-white/20 hover:text-slate-200"
                  )}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div className="min-h-0 flex-1 overflow-y-auto py-1">
        {options.length === 0 && (
          <p className="px-3 py-6 text-center text-xs text-slate-500">
            No locations found
          </p>
        )}
        {options.map((option) => {
          const active = value.some((item) => item.id === option.id);
          return (
            <button
              key={option.id}
              type="button"
              onClick={() => toggle(option)}
              className={cn(
                "flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition hover:bg-white/5",
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
              <span className="min-w-0 flex-1 truncate">{option.label}</span>
              <span className="shrink-0 text-[10px] uppercase tracking-wide text-slate-600">
                {option.type}
              </span>
            </button>
          );
        })}
      </div>

      {value.length > 0 && (
        <div className="flex shrink-0 items-center justify-between border-t border-white/8 px-3 py-2">
          <span className="text-[11px] text-slate-500">
            {value.length} selected
          </span>
          <button
            type="button"
            onClick={() => onChange([])}
            className="text-[11px] text-slate-400 hover:text-white"
          >
            Clear all
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div className={cn("relative w-full", className)}>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => {
          setOpen((current) => !current);
          setTimeout(() => inputRef.current?.focus(), 0);
        }}
        className="flex max-h-[76px] min-h-10 w-full flex-wrap items-center gap-1.5 overflow-y-auto rounded-lg border border-white/10 bg-black/20 px-2.5 py-1.5 text-left text-sm text-white outline-none focus-visible:border-emerald-400/50"
      >
        <MapPin className="h-3.5 w-3.5 shrink-0 text-emerald-400" />
        {value.length === 0 && (
          <span className="truncate text-slate-600">{placeholder}</span>
        )}
        {value.map((item) => (
          <span
            key={item.id}
            className="inline-flex max-w-[160px] items-center gap-1 rounded-md border border-emerald-400/20 bg-emerald-400/10 px-1.5 py-0.5 text-[11px] text-emerald-200"
          >
            <span className="truncate">{item.label}</span>
            <span
              role="button"
              tabIndex={-1}
              onClick={(event) => {
                event.stopPropagation();
                remove(item.id);
              }}
              className="shrink-0 rounded hover:text-white"
            >
              <X className="h-3 w-3" />
            </span>
          </span>
        ))}
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
