"use client";

import { useEffect, useState, useCallback, Fragment } from "react";
import { 
  Terminal, 
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Clock,
  Cpu
} from "lucide-react";
import { api } from "../../lib/api";
import { RawPacket } from "../../types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { formatDate } from "../../lib/date";

export default function PacketsPage() {
  const [packets, setPackets] = useState<RawPacket[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Tracks which packet IDs are expanded for JSON view
  const [expandedPackets, setExpandedPackets] = useState<Record<number, boolean>>({});

  const loadData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    try {
      const res = await api.getRawPackets(0, 50); // Fetch latest 50 packets
      setPackets(res);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to retrieve raw packet logs.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(true), 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  const toggleExpand = (id: number) => {
    setExpandedPackets((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  return (
    <div className="p-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            Raw Packet Monitor
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Debug console mapping incoming hardware VTS packet transactions.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="flex items-center gap-2 bg-[#1e294b] hover:bg-[#2e3b5e] disabled:opacity-50 text-white font-medium text-sm px-4 py-2 rounded-lg transition-colors border border-[#3b4b72]"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Packet Table Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Terminal className="h-5 w-5 text-cyan-400" />
            VTS Telemetry Ingest Stream
          </CardTitle>
          <CardDescription>
            Lists raw JSON packets recorded in the `raw_packets` table. Expand rows to view full telemetry packets.
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          {loading && packets.length === 0 ? (
            <div className="text-center py-8 text-slate-400">Loading incoming packets...</div>
          ) : packets.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              No VTS telemetry packets received yet. Simulate packets using the Postman collection at `/vts/telemetry`.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12"></TableHead>
                  <TableHead>Packet ID</TableHead>
                  <TableHead>Device UID</TableHead>
                  <TableHead>Message ID (msgid)</TableHead>
                  <TableHead>Transaction Type (txn)</TableHead>
                  <TableHead>Ingested At</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {packets.map((p) => {
                  const isExpanded = !!expandedPackets[p.id];
                  const txnType = p.packet_data?.info?.txn || "N/A";
                  
                  return (
                    <Fragment key={p.id}>
                      {/* Base Row */}
                      <TableRow 
                        className="cursor-pointer hover:bg-slate-900/40"
                        onClick={() => toggleExpand(p.id)}
                      >
                        <TableCell>
                          {isExpanded ? (
                            <ChevronDown size={16} className="text-cyan-400" />
                          ) : (
                            <ChevronRight size={16} className="text-slate-400" />
                          )}
                        </TableCell>
                        <TableCell className="font-mono text-slate-400">{p.id}</TableCell>
                        <TableCell className="font-mono text-xs text-cyan-400 font-semibold">{p.device_uid || "Unknown"}</TableCell>
                        <TableCell className="font-mono text-xs">{p.message_id !== null ? p.message_id : "N/A"}</TableCell>
                        <TableCell>
                          <span className="bg-slate-800/80 px-2.5 py-1 rounded text-xs font-semibold text-slate-300 border border-[#1e294b]">
                            {txnType}
                          </span>
                        </TableCell>
                        <TableCell className="text-xs">
                          {formatDate(p.created_at)}
                        </TableCell>
                      </TableRow>

                      {/* Expanded JSON details */}
                      {isExpanded && (
                        <TableRow className="bg-[#0b101c]/40 hover:bg-transparent">
                          <TableCell colSpan={6} className="p-4 border-b border-[#1e294b]">
                            <div className="bg-[#070b13] border border-[#1e294b] rounded-lg p-4 font-mono text-xs text-slate-300 max-w-full overflow-x-auto shadow-inner">
                              <div className="flex justify-between items-center border-b border-[#1e294b] pb-2 mb-3">
                                <div className="flex items-center gap-2">
                                  <Cpu size={14} className="text-cyan-400" />
                                  <span className="text-cyan-400 font-bold">Packet Details</span>
                                </div>
                                <span className="text-[10px] text-slate-500 flex items-center gap-1">
                                  <Clock size={10} />
                                  UTC: {new Date(p.created_at.endsWith("Z") ? p.created_at : `${p.created_at}Z`).toISOString()}
                                </span>
                              </div>
                              <pre className="text-emerald-400 whitespace-pre-wrap leading-relaxed">
                                {JSON.stringify(p.packet_data, null, 2)}
                              </pre>
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </Fragment>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
