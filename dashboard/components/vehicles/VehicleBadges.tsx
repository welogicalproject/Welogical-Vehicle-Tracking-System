import React from "react";
import type { ReactNode } from "react";
import { Clock } from "lucide-react";
import { DeviceCommand, Event } from "../../types";
import { formatDate } from "../../lib/date";

export function Detail({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-[#1e294b]/30 pb-2 text-xs">
      <span className="text-slate-500 font-semibold">{label}</span>
      <span
        className={`max-w-[200px] truncate text-right ${
          mono ? "font-mono text-[10px] text-cyan-300" : "font-bold text-slate-200"
        }`}
      >
        {value}
      </span>
    </div>
  );
}

export function Metric({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-[#1e294b]/60 bg-[#131a2d]/40 p-4 text-left">
      <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase text-slate-500">
        {icon}
        {label}
      </div>
      <div className="mt-1.5 text-xl font-extrabold text-white">{value}</div>
    </div>
  );
}

export function SeverityBadge({ severity }: { severity: Event["severity"] }) {
  const cls =
    severity === "Critical"
      ? "border-rose-500/20 bg-rose-500/10 text-rose-400"
      : severity === "Warning"
      ? "border-amber-500/20 bg-amber-500/10 text-amber-400"
      : "border-cyan-500/20 bg-cyan-500/10 text-cyan-400";
  return (
    <span className={`rounded px-1.5 py-0.5 text-[9px] font-extrabold uppercase border ${cls}`}>
      {severity}
    </span>
  );
}

export function CommandBadge({ status }: { status: DeviceCommand["status"] }) {
  const cls =
    status === "FAILED"
      ? "border-rose-500/20 bg-rose-500/10 text-rose-400"
      : status === "EXECUTED"
      ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
      : status === "SENT"
      ? "border-cyan-500/20 bg-cyan-500/10 text-cyan-400"
      : "border-amber-500/20 bg-amber-500/10 text-amber-400";
  return (
    <span className={`rounded px-1.5 py-0.5 text-[9px] font-extrabold uppercase border ${cls}`}>
      {status}
    </span>
  );
}

export function TimelineStep({
  label,
  active,
  timestamp,
  failed = false,
}: {
  label: string;
  active: boolean;
  timestamp?: string | null;
  failed?: boolean;
}) {
  return (
    <div
      className={`rounded-lg border p-2 text-left ${
        active
          ? failed
            ? "border-rose-500/30 bg-rose-500/5"
            : "border-cyan-500/30 bg-cyan-500/5"
          : "border-[#1e294b]/60 bg-[#0b0f19]/25"
      }`}
    >
      <div className="flex items-center gap-1.5">
        <Clock
          className={`h-3 w-3 ${
            active ? (failed ? "text-rose-400" : "text-cyan-400") : "text-slate-600"
          }`}
        />
        <span className="font-bold text-white text-[10px]">{label}</span>
      </div>
      <div className="mt-0.5 text-[9px] text-slate-500">
        {timestamp ? formatDate(timestamp) : active ? "Active" : "Pending"}
      </div>
    </div>
  );
}

export function Config({
  label,
  value,
}: {
  label: string;
  value: string | number | null | undefined;
}) {
  return (
    <div className="rounded-xl border border-[#1e294b]/60 bg-[#131a2d]/40 p-4 text-left">
      <div className="text-[10px] font-bold tracking-wider uppercase text-slate-500">
        {label}
      </div>
      <div className="mt-1.5 text-xs font-bold text-white truncate" title={String(value ?? "")}>
        {value ?? "N/A"}
      </div>
    </div>
  );
}
