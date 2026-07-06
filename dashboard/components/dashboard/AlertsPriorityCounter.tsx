import React from "react";
import { ShieldAlert, AlertTriangle, Bell } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { EventStats } from "../../types";

interface AlertsPriorityCounterProps {
  eventsStats: EventStats | null;
}

export function AlertsPriorityCounter({ eventsStats }: AlertsPriorityCounterProps) {
  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl lg:col-span-2">
      <CardHeader className="pb-2">
        <CardTitle className="text-white text-base">Alerts Priority Counter</CardTitle>
        <CardDescription>Critical threshold violations log counts.</CardDescription>
      </CardHeader>
      <CardContent className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
        <div className="border border-rose-500/20 bg-rose-500/5 rounded-xl p-4 flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-rose-400 uppercase tracking-wider block">
              Critical
            </span>
            <span className="text-xl font-extrabold text-rose-500 mt-1 block">
              {eventsStats ? eventsStats.critical : 0}
            </span>
          </div>
          <ShieldAlert className="h-6 w-6 text-rose-500 animate-bounce" />
        </div>
        <div className="border border-amber-500/20 bg-amber-500/5 rounded-xl p-4 flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-amber-400 uppercase tracking-wider block">
              Warning
            </span>
            <span className="text-xl font-extrabold text-amber-500 mt-1 block">
              {eventsStats ? eventsStats.warning : 0}
            </span>
          </div>
          <AlertTriangle className="h-6 w-6 text-amber-500" />
        </div>
        <div className="border border-cyan-500/20 bg-cyan-500/5 rounded-xl p-4 flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider block">
              Information
            </span>
            <span className="text-xl font-extrabold text-cyan-500 mt-1 block">
              {eventsStats ? eventsStats.info : 0}
            </span>
          </div>
          <Bell className="h-6 w-6 text-cyan-500" />
        </div>
      </CardContent>
    </Card>
  );
}
