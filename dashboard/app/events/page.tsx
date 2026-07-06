"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  Search, 
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown
} from "lucide-react";
import { api } from "../../lib/api";
import { Event, Vehicle } from "../../types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { cn } from "../../lib/utils";
import Link from "next/link";
import { formatDate } from "../../lib/date";


export default function EventsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter, search, and pagination state
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [vehicleFilter, setVehicleFilter] = useState("all");
  const [sortOrder, setSortOrder] = useState("desc");
  const [page, setPage] = useState(1);
  const LIMIT = 20;

  const loadData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    try {
      // 1. Fetch vehicles for the filter dropdown
      const vehiclesRes = await api.getVehicles(0, 100);
      setVehicles(vehiclesRes);

      // 2. Fetch events using active filters
      const vId = vehicleFilter === "all" ? undefined : parseInt(vehicleFilter);
      const sev = severityFilter === "all" ? undefined : severityFilter;
      
      const skip = (page - 1) * LIMIT;
      const eventsRes = await api.getEvents(vId, undefined, sev, skip, LIMIT + 1, sortOrder);
      
      setEvents(eventsRes);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to retrieve fleet events data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [vehicleFilter, severityFilter, page, sortOrder]);

  // Initial load and periodic refresh
  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(true), 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Handle pagination pages change
  const hasMore = events.length > LIMIT;
  const displayedEvents = events.slice(0, LIMIT);

  // Client-side search filtering on event type and description
  const filteredEvents = displayedEvents.filter((ev) => {
    const matchesSearch = 
      ev.event_type.toLowerCase().includes(search.toLowerCase()) ||
      ev.description.toLowerCase().includes(search.toLowerCase()) ||
      (ev.vehicle_name && ev.vehicle_name.toLowerCase().includes(search.toLowerCase())) ||
      (ev.device_uid && ev.device_uid.toLowerCase().includes(search.toLowerCase()));
    return matchesSearch;
  });

  return (
    <div className="p-8 space-y-8 select-none">
      {/* Top Filter and Action Bar */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4 bg-[#131a2d]/40 border border-[#1e294b]/60 rounded-xl px-4 py-3">
        <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {/* Search box */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search alert log..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="pl-9 bg-[#0b0f19] border-[#1e294b] text-xs h-9"
            />
          </div>

          {/* Vehicle Filter */}
          <select
            value={vehicleFilter}
            onChange={(e) => { setVehicleFilter(e.target.value); setPage(1); }}
            className="w-full bg-[#0b0f19] border border-[#1e294b] rounded-lg px-3 py-1.5 text-xs text-slate-300 font-semibold focus:outline-none transition-all"
          >
            <option value="all">All Vehicles</option>
            {vehicles.map((v) => (
              <option key={v.id} value={v.id.toString()}>{v.vehicle_name}</option>
            ))}
          </select>

          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
            className="w-full bg-[#0b0f19] border border-[#1e294b] rounded-lg px-3 py-1.5 text-xs text-slate-300 font-semibold focus:outline-none transition-all"
          >
            <option value="all">All Severities</option>
            <option value="Critical">Critical</option>
            <option value="Warning">Warning</option>
            <option value="Info">Info</option>
          </select>

          {/* Sort Order Toggle */}
          <button
            onClick={() => { setSortOrder(sortOrder === "desc" ? "asc" : "desc"); setPage(1); }}
            className="bg-[#0b0f19] hover:bg-[#131a2d] border border-[#1e294b]/60 rounded-lg px-3 py-1.5 text-xs text-slate-300 font-semibold flex items-center justify-between transition-all"
          >
            <span className="flex items-center gap-1.5">
              <ArrowUpDown className="h-3.5 w-3.5 text-cyan-400" />
              Sort: {sortOrder === "desc" ? "Newest First" : "Oldest First"}
            </span>
          </button>
        </div>

        <button
          onClick={() => loadData(true)}
          disabled={refreshing}
          className="flex items-center gap-2 bg-[#131a2d] hover:bg-[#1e294b] border border-[#1e294b] text-slate-200 font-semibold text-xs px-3.5 py-2 rounded-lg transition-all"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", refreshing ? "animate-spin" : "")} />
          Refresh Feed
        </button>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm font-semibold">
          {error}
        </div>
      )}

      {/* Events List Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl overflow-hidden">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-[#1e294b]/40 hover:bg-transparent">
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Ingested Time</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Vehicle Node</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Alert Type</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Severity</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Description / Log details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEvents.map((ev) => (
                <TableRow key={ev.id} className="border-[#1e294b]/20 hover:bg-[#131a2d]/20 transition-colors">
                  <TableCell className="text-xs font-mono text-slate-400 py-3.5">
                    {formatDate(ev.created_at)}
                  </TableCell>
                  <TableCell className="font-bold text-white text-xs py-3.5">
                    <Link href={`/vehicles/${ev.vehicle_id}`} className="text-cyan-400 hover:text-cyan-300 transition-all underline">
                      {ev.vehicle_name || ev.device_uid || `Vehicle #${ev.vehicle_id}`}
                    </Link>
                  </TableCell>
                  <TableCell className="text-xs font-bold text-cyan-400 py-3.5">{ev.event_type}</TableCell>
                  <TableCell className="py-3.5">
                    <span className={cn(
                      "inline-flex items-center px-2 py-0.5 rounded text-[10px] font-extrabold uppercase border",
                      ev.severity === "Critical" 
                        ? "bg-rose-500/10 text-rose-400 border-rose-500/20" 
                        : ev.severity === "Warning" 
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/20" 
                          : "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                    )}>
                      {ev.severity}
                    </span>
                  </TableCell>
                  <TableCell className="text-xs text-slate-300 max-w-sm truncate py-3.5" title={ev.description}>
                    {ev.description}
                  </TableCell>
                </TableRow>
              ))}
              {filteredEvents.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-12 text-slate-400 text-xs">
                    {loading ? "Loading event archives..." : "No alert logs found"}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Pagination Controls */}
      <div className="flex justify-between items-center bg-[#131a2d]/40 border border-[#1e294b]/60 rounded-xl px-4 py-3 max-w-sm mx-auto">
        <Button 
          type="button" 
          size="sm" 
          variant="outline" 
          disabled={page === 1} 
          onClick={() => setPage(p => Math.max(1, p - 1))}
          className="flex items-center gap-1.5"
        >
          <ChevronLeft className="h-4 w-4" /> Prev
        </Button>
        <span className="text-xs text-slate-400 font-bold">
          Page {page}
        </span>
        <Button 
          type="button" 
          size="sm" 
          variant="outline" 
          disabled={!hasMore} 
          onClick={() => setPage(p => p + 1)}
          className="flex items-center gap-1.5"
        >
          Next <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
