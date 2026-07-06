"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { RefreshCw } from "lucide-react";
import { api } from "../../lib/api";
import { DeviceCommand, Vehicle, CommandLog } from "../../types";
import { cn } from "../../lib/utils";

// Extracted Components
import { DispatchCommandForm } from "../../components/commands/DispatchCommandForm";
import { CommandQueueTable } from "../../components/commands/CommandQueueTable";
import { CommandAuditLog } from "../../components/commands/CommandAuditLog";

export default function CommandsPage() {
  const [commands, setCommands] = useState<DeviceCommand[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Queue form state
  const [targetVehicle, setTargetVehicle] = useState("");
  const [commandName, setCommandName] = useState("STOPV");
  const [commandValue, setCommandValue] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Selected command for audit logs timeline/details
  const [selectedCommandId, setSelectedCommandId] = useState<number | null>(null);
  const [auditLogs, setAuditLogs] = useState<CommandLog[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);

  const loadData = useCallback(
    async (isSilent = false) => {
      if (!isSilent) setLoading(true);
      else setRefreshing(true);
      try {
        const [commandsRes, vehiclesRes] = await Promise.all([
          api.getCommands(undefined, undefined, 0, 100).catch(() => []),
          api.getVehicles(0, 100).catch(() => []),
        ]);
        setCommands(commandsRes);
        setVehicles(vehiclesRes);

        // Auto select first vehicle in form if empty
        if (vehiclesRes.length > 0 && !targetVehicle) {
          setTargetVehicle(vehiclesRes[0].id.toString());
        }

        setError(null);
      } catch (err: any) {
        console.error(err);
        setError(err.message || "Failed to retrieve command queue parameters.");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [targetVehicle]
  );

  // Load audit logs when a command is selected
  const fetchAuditLogs = async (cmdId: number) => {
    setSelectedCommandId(cmdId);
    setLoadingLogs(true);
    try {
      const logs = await api.getCommandLogs(cmdId);
      setAuditLogs(logs);
    } catch (err) {
      console.error("Failed to load command audit logs:", err);
      setAuditLogs([]);
    } finally {
      setLoadingLogs(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(true), 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Submit queue command
  const handleQueueCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetVehicle) return;

    setSubmitting(true);
    setError(null);
    try {
      await api.queueCommand({
        vehicle_id: parseInt(targetVehicle),
        command_name: commandName,
        command_value: commandValue.trim() || null,
      });
      setCommandValue("");
      // Reload queue
      await loadData(true);
    } catch (err: any) {
      setError(err.message || "Failed to enqueue device command.");
    } finally {
      setSubmitting(false);
    }
  };

  // Delete command
  const handleDeleteCommand = async (cmdId: number) => {
    if (!confirm("Are you sure you want to remove this queued command?")) return;
    try {
      await api.deleteCommand(cmdId);
      await loadData(true);
      if (selectedCommandId === cmdId) {
        setSelectedCommandId(null);
        setAuditLogs([]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to remove command from queue.");
    }
  };

  const selectedCommand = useMemo(() => {
    return commands.find((c) => c.id === selectedCommandId);
  }, [selectedCommandId, commands]);

  return (
    <div className="p-8 space-y-8 select-none">
      {/* Top Action Header */}
      <div className="flex items-center justify-between bg-[#131a2d]/40 border border-[#1e294b]/60 rounded-xl px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[#a855f7] animate-pulse" />
          <span className="text-xs font-semibold text-slate-400">
            Hardware Command Dispatch Queue
          </span>
        </div>
        <button
          onClick={() => loadData(true)}
          disabled={refreshing}
          className="flex items-center gap-2 bg-[#131a2d] hover:bg-[#1e294b] border border-[#1e294b] text-slate-200 font-semibold text-xs px-3.5 py-1.5 rounded-lg transition-all"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", refreshing ? "animate-spin" : "")} />
          Refresh Queue
        </button>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm font-semibold">
          {error}
        </div>
      )}

      {/* Main Grid: Form Left, Tables Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form panel */}
        <DispatchCommandForm
          vehicles={vehicles}
          targetVehicle={targetVehicle}
          setTargetVehicle={setTargetVehicle}
          commandName={commandName}
          setCommandName={setCommandName}
          commandValue={commandValue}
          setCommandValue={setCommandValue}
          submitting={submitting}
          onSubmit={handleQueueCommand}
        />

        {/* Command Queue Table and Audit Logs */}
        <div className="lg:col-span-2 space-y-6">
          <CommandQueueTable
            commands={commands}
            loading={loading}
            selectedCommandId={selectedCommandId}
            onSelectCommand={fetchAuditLogs}
            onDeleteCommand={handleDeleteCommand}
          />

          {/* Audit log for selected command */}
          <CommandAuditLog
            selectedCommandId={selectedCommandId}
            setSelectedCommandId={setSelectedCommandId}
            selectedCommand={selectedCommand}
            auditLogs={auditLogs}
            loadingLogs={loadingLogs}
          />
        </div>
      </div>
    </div>
  );
}
