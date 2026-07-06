"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { CalendarDays, ChevronLeft, ChevronRight, X } from "lucide-react";
import { cn } from "../../lib/utils";

// ─── Constants ──────────────────────────────────────────────────────────────
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];
const DAYS_SHORT = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

// ─── Helpers ─────────────────────────────────────────────────────────────────
function formatDisplay(date: Date | null): string {
  if (!date) return "";
  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

/** Build calendar grid: returns ordered Date cells for the month view */
function buildCalendarGrid(year: number, month: number): (Date | null)[] {
  const firstDay = new Date(year, month, 1).getDay(); // 0=Sun
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const grid: (Date | null)[] = [];
  for (let i = 0; i < firstDay; i++) grid.push(null);
  for (let d = 1; d <= daysInMonth; d++) grid.push(new Date(year, month, d));
  return grid;
}

function isSameDay(a: Date, b: Date) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

// ─── Props ───────────────────────────────────────────────────────────────────
export interface DatePickerInputProps {
  /** Internal ISO value e.g. "2026-06-30T00:00" or "2026-06-30T23:59" */
  value: string;
  /** Called with the new internal ISO value when user picks a date */
  onChange: (value: string) => void;
  /** "start" appends T00:00, "end" appends T23:59 */
  mode?: "start" | "end";
  label?: string;
  placeholder?: string;
  className?: string;
  id?: string;
}

// ─── Component ───────────────────────────────────────────────────────────────
export function DatePickerInput({
  value,
  onChange,
  mode = "start",
  placeholder = "Pick a date",
  className,
  id,
}: DatePickerInputProps) {
  // Parse the raw ISO string back to a Date for display
  const parsedDate: Date | null = value
    ? (() => {
        const d = new Date(value.endsWith("Z") ? value : `${value}Z`);
        return isNaN(d.getTime()) ? null : d;
      })()
    : null;

  // Popover state
  const [open, setOpen] = useState(false);

  // Calendar navigation state (which month/year are we viewing?)
  const [viewYear, setViewYear] = useState(() => parsedDate?.getFullYear() ?? new Date().getFullYear());
  const [viewMonth, setViewMonth] = useState(() => parsedDate?.getMonth() ?? new Date().getMonth());

  // Sync view when value changes externally
  useEffect(() => {
    if (parsedDate) {
      setViewYear(parsedDate.getFullYear());
      setViewMonth(parsedDate.getMonth());
    }
  }, [value]);

  const containerRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open]);

  const handleDayClick = useCallback(
    (day: Date) => {
      const yyyy = day.getFullYear();
      const mm = String(day.getMonth() + 1).padStart(2, "0");
      const dd = String(day.getDate()).padStart(2, "0");
      const time = mode === "end" ? "23:59" : "00:00";
      onChange(`${yyyy}-${mm}-${dd}T${time}`);
      setOpen(false);
    },
    [mode, onChange]
  );

  const handleClear = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onChange("");
    },
    [onChange]
  );

  const prevMonth = () => {
    if (viewMonth === 0) { setViewYear(y => y - 1); setViewMonth(11); }
    else setViewMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (viewMonth === 11) { setViewYear(y => y + 1); setViewMonth(0); }
    else setViewMonth(m => m + 1);
  };
  const prevYear = () => setViewYear(y => y - 1);
  const nextYear = () => setViewYear(y => y + 1);

  const grid = buildCalendarGrid(viewYear, viewMonth);
  const today = new Date();

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Trigger field */}
      <button
        id={id}
        type="button"
        onClick={() => setOpen(o => !o)}
        className={cn(
          "w-full flex items-center gap-2 h-9 px-3 rounded-lg text-xs",
          "bg-[#0b0f19] border border-[#1e294b] text-left",
          "focus:outline-none focus:border-cyan-400",
          "hover:border-cyan-400/50 transition-colors",
          parsedDate ? "text-white" : "text-slate-500"
        )}
      >
        <CalendarDays className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
        <span className="flex-1 truncate">
          {parsedDate ? formatDisplay(parsedDate) : placeholder}
        </span>
        {parsedDate && (
          <span
            role="button"
            aria-label="Clear date"
            onClick={handleClear}
            className="shrink-0 text-slate-500 hover:text-slate-300 cursor-pointer"
          >
            <X className="h-3 w-3" />
          </span>
        )}
      </button>

      {/* Calendar popover */}
      {open && (
        <div
          className={cn(
            "absolute z-50 mt-1 w-[264px] rounded-xl shadow-2xl",
            "bg-[#0d1425] border border-[#1e294b]",
            "animate-in fade-in-0 zoom-in-95 duration-100",
          )}
          style={{ top: "100%", left: 0 }}
        >
          {/* Month / Year nav */}
          <div className="flex items-center justify-between px-3 pt-3 pb-1 gap-1">
            {/* Year nav */}
            <button
              type="button"
              onClick={prevYear}
              className="p-1 rounded text-slate-400 hover:text-cyan-400 hover:bg-white/5 transition-colors"
              aria-label="Previous year"
            >
              <ChevronLeft className="h-3 w-3" />
            </button>

            {/* Month nav */}
            <button
              type="button"
              onClick={prevMonth}
              className="p-1 rounded text-slate-400 hover:text-cyan-400 hover:bg-white/5 transition-colors"
              aria-label="Previous month"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </button>

            <span className="flex-1 text-center text-xs font-semibold text-white select-none">
              {MONTHS[viewMonth]} {viewYear}
            </span>

            <button
              type="button"
              onClick={nextMonth}
              className="p-1 rounded text-slate-400 hover:text-cyan-400 hover:bg-white/5 transition-colors"
              aria-label="Next month"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </button>

            <button
              type="button"
              onClick={nextYear}
              className="p-1 rounded text-slate-400 hover:text-cyan-400 hover:bg-white/5 transition-colors"
              aria-label="Next year"
            >
              <ChevronRight className="h-3 w-3" />
            </button>
          </div>

          {/* Day-of-week headers */}
          <div className="grid grid-cols-7 px-2 pb-1">
            {DAYS_SHORT.map(d => (
              <div key={d} className="text-center text-[10px] font-semibold text-slate-500 py-1">
                {d}
              </div>
            ))}
          </div>

          {/* Day grid */}
          <div className="grid grid-cols-7 px-2 pb-3 gap-y-0.5">
            {grid.map((day, i) => {
              if (!day) return <div key={`empty-${i}`} />;

              const isSelected = parsedDate ? isSameDay(day, parsedDate) : false;
              const isToday = isSameDay(day, today);

              return (
                <button
                  key={day.toISOString()}
                  type="button"
                  onClick={() => handleDayClick(day)}
                  className={cn(
                    "h-8 w-8 mx-auto rounded-lg text-xs font-medium transition-colors",
                    "focus:outline-none focus-visible:ring-1 focus-visible:ring-cyan-500",
                    isSelected
                      ? "bg-cyan-500 text-white font-bold"
                      : isToday
                      ? "border border-cyan-500/60 text-cyan-400 hover:bg-cyan-500/20"
                      : "text-slate-300 hover:bg-white/8 hover:text-white"
                  )}
                >
                  {day.getDate()}
                </button>
              );
            })}
          </div>

          {/* "Today" shortcut */}
          <div className="border-t border-[#1e294b] px-3 py-2 flex justify-between items-center">
            <button
              type="button"
              onClick={() => handleDayClick(today)}
              className="text-[10px] font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              Today
            </button>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="text-[10px] font-semibold text-slate-500 hover:text-slate-300 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
