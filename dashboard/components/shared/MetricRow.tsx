import React from "react";

export function MetricRow({ label, val, icon }: { label: string; val: React.ReactNode; icon: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-[#1e294b]/20 pb-2 text-xs">
      <div className="flex items-center gap-2 text-slate-400 font-semibold">
        {icon}
        <span>{label}</span>
      </div>
      <div className="text-slate-100 font-bold text-right truncate max-w-[160px] font-sans">
        {val}
      </div>
    </div>
  );
}
