import React, { useMemo } from "react";
import { DeviceCommand } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { CommandBadge, TimelineStep } from "./VehicleBadges";
import { formatDate } from "../../lib/date";

interface CommandsTabProps {
  commands: DeviceCommand[];
}

export function CommandsTab({ commands }: CommandsTabProps) {
  const commandGroups = useMemo(() => {
    return {
      Queued: commands.filter((command) => ["Queued", "PENDING"].includes(command.status)),
      Active: commands.filter((command) => ["Sending", "Delivered", "Acknowledged", "Executing", "SENT"].includes(command.status)),
      Completed: commands.filter((command) => ["Completed", "EXECUTED"].includes(command.status)),
      Failed: commands.filter((command) => ["Failed", "Timed Out", "Cancelled", "FAILED"].includes(command.status)),
    };
  }, [commands]);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {Object.entries(commandGroups).map(([status, rows]) => (
          <div
            key={status}
            className="rounded-xl border border-[#1e294b]/60 bg-[#131a2d]/40 p-4 text-left"
          >
            <div className="text-[10px] font-bold tracking-wider uppercase text-slate-500">
              {status}
            </div>
            <div className="mt-1 text-xl font-extrabold text-white">{rows.length}</div>
          </div>
        ))}
      </div>
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
        <CardHeader>
          <CardTitle className="text-white text-sm">Command History Timeline</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {commands.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">No commands dispatched</div>
          ) : (
            commands.map((command) => {
              const isFailed = ["Failed", "Timed Out", "Cancelled", "FAILED"].includes(command.status);
              const isCompleted = ["Completed", "EXECUTED"].includes(command.status);
              return (
                <div
                  key={command.id}
                  className="rounded-xl border border-[#1e294b]/60 bg-[#0f172a]/30 p-4 text-left"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="font-bold text-white text-sm">
                        {command.command_name}
                        {command.command_value ? `=${command.command_value}` : ""}
                      </div>
                      <div className="text-[10px] text-slate-500 font-semibold mt-1">
                        Queued: {formatDate(command.created_at)}
                      </div>
                    </div>
                    <CommandBadge status={command.status} />
                  </div>
                  <div className="mt-4 grid grid-cols-3 gap-2 text-[10px]">
                    <TimelineStep label="Pending" active />
                    <TimelineStep
                      label="Sent"
                      active={Boolean(command.sent_at)}
                      timestamp={command.sent_at}
                    />
                    <TimelineStep
                      label={isFailed ? "Failed" : "Executed"}
                      active={Boolean(command.completed_at || command.executed_at)}
                      timestamp={command.completed_at || command.executed_at}
                      failed={isFailed}
                    />
                  </div>
                </div>
              );
            })
          )}
        </CardContent>
      </Card>
    </div>
  );
}
