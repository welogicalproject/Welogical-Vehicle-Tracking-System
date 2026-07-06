"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  Car, 
  Search, 
  RefreshCw,
  Eye,
  Plus,
  Edit2,
  Trash2,
  CheckCircle,
  XCircle,
  X
} from "lucide-react";
import { api } from "../../lib/api";
import { Vehicle } from "../../types";
import { Card, CardContent } from "../../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { Input } from "../../components/ui/input";
import Link from "next/link";
import { cn } from "../../lib/utils";
import { formatDate } from "../../lib/date";

function getStatus(lastSeen: string | null): "online" | "idle" | "offline" {
  if (!lastSeen) return "offline";
  const lastSeenStr = lastSeen.endsWith("Z") ? lastSeen : `${lastSeen}Z`;
  const lastSeenDate = new Date(lastSeenStr);
  const now = new Date();
  const diffMinutes = (now.getTime() - lastSeenDate.getTime()) / 60000;

  if (diffMinutes < 5) return "online";
  if (diffMinutes <= 30) return "idle";
  return "offline";
}

export default function VehiclesPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Search & Filter state
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  // Modal form states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);

  // Form Fields
  const [deviceUid, setDeviceUid] = useState("");
  const [vehicleName, setVehicleName] = useState("");
  const [vehicleType, setVehicleType] = useState("");
  const [vehicleNumber, setVehicleNumber] = useState("");
  const [manufacturer, setManufacturer] = useState("");
  const [model, setModel] = useState("");
  const [year, setYear] = useState("");
  const [vin, setVin] = useState("");
  const [imei, setImei] = useState("");
  const [simNumber, setSimNumber] = useState("");
  const [fuelType, setFuelType] = useState("");
  const [capacity, setCapacity] = useState("");
  const [status, setStatus] = useState("Enabled");
  const [notes, setNotes] = useState("");

  const loadData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    try {
      const res = await api.getVehicles(0, 100);
      setVehicles(res);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to retrieve vehicle inventory.");
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

  const openAddModal = () => {
    setEditingVehicle(null);
    setDeviceUid("");
    setVehicleName("");
    setVehicleType("Car");
    setVehicleNumber("");
    setManufacturer("");
    setModel("");
    setYear("");
    setVin("");
    setImei("");
    setSimNumber("");
    setFuelType("Petrol");
    setCapacity("");
    setStatus("Enabled");
    setNotes("");
    setIsModalOpen(true);
  };

  const openEditModal = (v: Vehicle) => {
    setEditingVehicle(v);
    setDeviceUid(v.device_uid);
    setVehicleName(v.vehicle_name);
    setVehicleType(v.vehicle_type || "Car");
    setVehicleNumber(v.vehicle_number || "");
    setManufacturer(v.manufacturer || "");
    setModel(v.model || "");
    setYear(v.year ? String(v.year) : "");
    setVin(v.vin || "");
    setImei(v.imei || "");
    setSimNumber(v.sim_number || "");
    setFuelType(v.fuel_type || "Petrol");
    setCapacity(v.capacity ? String(v.capacity) : "");
    setStatus(v.status || "Enabled");
    setNotes(v.notes || "");
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deviceUid || !vehicleName) {
      alert("Device UID and Vehicle Name are required.");
      return;
    }

    const payload = {
      device_uid: deviceUid,
      vehicle_name: vehicleName,
      vehicle_type: vehicleType,
      vehicle_number: vehicleNumber || null,
      manufacturer: manufacturer || null,
      model: model || null,
      year: year ? parseInt(year) : null,
      vin: vin || null,
      imei: imei || null,
      sim_number: simNumber || null,
      fuel_type: fuelType || null,
      capacity: capacity ? parseFloat(capacity) : null,
      status: status,
      notes: notes || null
    };

    try {
      if (editingVehicle) {
        await api.updateVehicle(editingVehicle.id, payload);
      } else {
        await api.createVehicle(payload);
      }
      setIsModalOpen(false);
      loadData(true);
    } catch (err: any) {
      alert(err.message || "Failed to save vehicle details.");
    }
  };

  const toggleStatus = async (v: Vehicle) => {
    const nextStatus = v.status === "Enabled" ? "Disabled" : "Enabled";
    try {
      await api.updateVehicle(v.id, { status: nextStatus });
      loadData(true);
    } catch (err: any) {
      alert(err.message || "Failed to update lifecycle status.");
    }
  };

  const archiveVehicle = async (v: Vehicle) => {
    if (!confirm(`Are you sure you want to archive "${v.vehicle_name}"? This soft-deletes the vehicle from directory listings but preserves historical tracks.`)) return;
    try {
      await api.deleteVehicle(v.id);
      loadData(true);
    } catch (err: any) {
      alert(err.message || "Failed to archive vehicle.");
    }
  };

  // Extract unique vehicle types
  const vehicleTypes = Array.from(
    new Set(vehicles.map((v) => v.vehicle_type).filter(Boolean))
  );

  // Filter vehicles
  const filteredVehicles = vehicles.filter((v) => {
    const matchesSearch = 
      v.vehicle_name.toLowerCase().includes(search.toLowerCase()) ||
      v.device_uid.toLowerCase().includes(search.toLowerCase()) ||
      (v.vehicle_number && v.vehicle_number.toLowerCase().includes(search.toLowerCase()));
      
    const matchesType = 
      typeFilter === "all" || 
      v.vehicle_type === typeFilter;

    const matchesStatus =
      statusFilter === "all" ||
      v.status === statusFilter;
      
    return matchesSearch && matchesType && matchesStatus;
  });

  return (
    <div className="p-8 space-y-8 select-none">
      {/* Top Filter and Action Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#131a2d]/40 border border-[#1e294b]/60 rounded-xl px-4 py-3">
        <div className="flex-1 flex flex-wrap items-center gap-3">
          {/* Search box */}
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search by name, uid, or plate..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 bg-[#0b0f19] border-[#1e294b] text-xs h-9"
            />
          </div>

          {/* Type Filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-[#0b0f19] border border-[#1e294b] rounded-lg px-3 py-1.5 text-xs text-slate-300 font-semibold focus:outline-none transition-all"
          >
            <option value="all">All Vehicle Types</option>
            {vehicleTypes.map((type) => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#0b0f19] border border-[#1e294b] rounded-lg px-3 py-1.5 text-xs text-slate-300 font-semibold focus:outline-none transition-all"
          >
            <option value="all">All Lifecycles</option>
            <option value="Enabled">Enabled Only</option>
            <option value="Disabled">Disabled Only</option>
          </select>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={openAddModal}
            className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs px-3.5 py-2 rounded-lg transition-all"
          >
            <Plus className="h-4 w-4" />
            Add Vehicle
          </button>

          <button
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="flex items-center gap-2 bg-[#131a2d] hover:bg-[#1e294b] border border-[#1e294b] text-slate-200 font-semibold text-xs px-3.5 py-2 rounded-lg transition-all"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", refreshing ? "animate-spin" : "")} />
            Refresh List
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm font-semibold">
          {error}
        </div>
      )}

      {/* Vehicles Table Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl overflow-hidden">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-[#1e294b]/40 hover:bg-transparent">
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Vehicle Name</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Plate / UID</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Asset details</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Telemetry</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Lifecycle</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredVehicles.map((v) => {
                const telemetryStatus = getStatus(v.last_seen);
                return (
                  <TableRow key={v.id} className="border-[#1e294b]/20 hover:bg-[#131a2d]/20 transition-colors">
                    <TableCell className="font-bold text-white text-sm py-4 text-left">
                      <div>{v.vehicle_name}</div>
                      <div className="text-[10px] text-slate-500 font-mono mt-0.5">{v.vin || "No VIN registered"}</div>
                    </TableCell>
                    <TableCell className="font-mono text-xs text-cyan-400 py-4 text-left">
                      <div className="font-bold">{v.vehicle_number || "No Plate"}</div>
                      <div className="text-[10px] text-slate-500 font-mono">UID: {v.device_uid}</div>
                    </TableCell>
                    <TableCell className="text-xs text-slate-300 py-4 text-left">
                      <div>{v.manufacturer || ""} {v.model || ""} {v.year ? `(${v.year})` : ""}</div>
                      <div className="text-[10px] text-slate-400">{v.vehicle_type} &bull; {v.fuel_type || "N/A"}</div>
                    </TableCell>
                    <TableCell className="py-4 text-left">
                      <span className={cn(
                        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wide border",
                        telemetryStatus === "online" 
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                          : telemetryStatus === "idle" 
                            ? "bg-amber-500/10 text-amber-400 border-amber-500/20" 
                            : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                      )}>
                        <span className={cn(
                          "h-1.5 w-1.5 rounded-full",
                          telemetryStatus === "online" ? "bg-emerald-400 animate-pulse" : telemetryStatus === "idle" ? "bg-amber-400" : "bg-slate-400"
                        )} />
                        {telemetryStatus}
                      </span>
                    </TableCell>
                    <TableCell className="py-4 text-left">
                      <span className={cn(
                        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wide border",
                        v.status === "Enabled" 
                          ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20" 
                          : "bg-red-500/10 text-red-400 border-red-500/20"
                      )}>
                        {v.status || "Enabled"}
                      </span>
                    </TableCell>
                    <TableCell className="text-right py-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => toggleStatus(v)}
                          title={v.status === "Enabled" ? "Disable Vehicle" : "Enable Vehicle"}
                          className="bg-[#131a2d] hover:bg-[#1e294b] text-xs p-2 rounded-lg border border-[#1e294b] text-slate-300 transition-all"
                        >
                          {v.status === "Enabled" ? (
                            <XCircle className="h-3.5 w-3.5 text-amber-500" />
                          ) : (
                            <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                          )}
                        </button>

                        <button
                          onClick={() => openEditModal(v)}
                          title="Edit Vehicle Metadata"
                          className="bg-[#131a2d] hover:bg-[#1e294b] text-xs p-2 rounded-lg border border-[#1e294b] text-cyan-400 transition-all"
                        >
                          <Edit2 className="h-3.5 w-3.5" />
                        </button>

                        <button
                          onClick={() => archiveVehicle(v)}
                          title="Archive (Soft Delete)"
                          className="bg-[#131a2d] hover:bg-[#1e294b] text-xs p-2 rounded-lg border border-[#1e294b] text-red-400 transition-all"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>

                        <Link
                          href={`/vehicles/${v.id}`}
                          className="bg-[#131a2d] hover:bg-[#1e294b] text-xs text-cyan-400 font-bold border border-[#1e294b] px-3 py-1.5 rounded-lg transition-all inline-flex items-center gap-1.5"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          Inspect
                        </Link>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
              {filteredVehicles.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12 text-slate-400 text-xs">
                    {loading ? "Loading asset directory..." : "No assets match search filters"}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Add / Edit Dialog Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs">
          <div className="w-full max-w-2xl bg-[#0b0f19] border border-[#1e294b]/80 rounded-xl shadow-2xl flex flex-col max-h-[90vh]">
            <div className="p-5 border-b border-[#1e294b]/60 flex items-center justify-between shrink-0">
              <h3 className="text-sm font-black text-white uppercase tracking-wider flex items-center gap-2">
                <Car className="h-4.5 w-4.5 text-cyan-400" />
                {editingVehicle ? `Edit Asset: ${editingVehicle.vehicle_name}` : "Register New Vehicle Asset"}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white transition-colors">
                <X className="h-4.5 w-4.5" />
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-4 text-left">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Vehicle Name *</label>
                  <Input value={vehicleName} onChange={(e) => setVehicleName(e.target.value)} required placeholder="e.g. Surat Express" className="bg-[#131a2d] border-[#1e294b] text-xs h-9" />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Device Hardware UID *</label>
                  <Input value={deviceUid} onChange={(e) => setDeviceUid(e.target.value)} required placeholder="e.g. VTS-006" disabled={!!editingVehicle} className="bg-[#131a2d] border-[#1e294b] text-xs h-9" />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Vehicle Type</label>
                  <select value={vehicleType} onChange={(e) => setVehicleType(e.target.value)} className="w-full bg-[#131a2d] border border-[#1e294b] rounded-lg px-3 py-1.5 text-xs text-slate-300 font-semibold focus:outline-none transition-all h-9">
                    <option value="Car">Car</option>
                    <option value="Truck">Truck</option>
                    <option value="Bus">Bus</option>
                    <option value="Bike">Bike</option>
                    <option value="Van">Van</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Plate Number</label>
                  <Input value={vehicleNumber} onChange={(e) => setVehicleNumber(e.target.value)} placeholder="e.g. GJ-05-AA-1234" className="bg-[#131a2d] border-[#1e294b] text-xs h-9" />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Lifecycle Status</label>
                  <select value={status} onChange={(e) => setStatus(e.target.value)} className="w-full bg-[#131a2d] border border-[#1e294b] rounded-lg px-3 py-1.5 text-xs text-slate-300 font-semibold focus:outline-none transition-all h-9">
                    <option value="Enabled">Enabled</option>
                    <option value="Disabled">Disabled</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Manufacturer</label>
                  <Input value={manufacturer} onChange={(e) => setManufacturer(e.target.value)} placeholder="Tata, Mahindra..." className="bg-[#131a2d] border-[#1e294b] text-xs h-9" />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Model</label>
                  <Input value={model} onChange={(e) => setModel(e.target.value)} placeholder="e.g. Signa 4825" className="bg-[#131a2d] border-[#1e294b] text-xs h-9" />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Year</label>
                  <Input type="number" value={year} onChange={(e) => setYear(e.target.value)} placeholder="2026" className="bg-[#131a2d] border-[#1e294b] text-xs h-9" />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">VIN</label>
                  <Input value={vin} onChange={(e) => setVin(e.target.value)} placeholder="Chassis number..." className="bg-[#131a2d] border-[#1e294b] text-xs h-9" />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">IMEI</label>
                  <Input value={imei} onChange={(e) => setImei(e.target.value)} placeholder="Device IMEI..." className="bg-[#131a2d] border-[#1e294b] text-xs h-9" />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">SIM Number</label>
                  <Input value={simNumber} onChange={(e) => setSimNumber(e.target.value)} placeholder="Sim Card Number..." className="bg-[#131a2d] border-[#1e294b] text-xs h-9" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Fuel Type</label>
                  <select value={fuelType} onChange={(e) => setFuelType(e.target.value)} className="w-full bg-[#131a2d] border border-[#1e294b] rounded-lg px-3 py-1.5 text-xs text-slate-300 font-semibold focus:outline-none transition-all h-9">
                    <option value="Petrol">Petrol</option>
                    <option value="Diesel">Diesel</option>
                    <option value="Electric">Electric</option>
                    <option value="CNG">CNG</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Fuel Capacity (Liters)</label>
                  <Input type="number" step="0.1" value={capacity} onChange={(e) => setCapacity(e.target.value)} placeholder="e.g. 350" className="bg-[#131a2d] border-[#1e294b] text-xs h-9" />
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Administrative Notes</label>
                <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Add specific fleet details, maintenance parameters, or alerts details..." className="w-full min-h-[80px] bg-[#131a2d] border border-[#1e294b] rounded-lg p-3 text-xs text-white focus:outline-none focus:border-cyan-400 transition-all" />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#1e294b]/60 shrink-0">
                <button type="button" onClick={() => setIsModalOpen(false)} className="bg-[#131a2d] hover:bg-[#1e294b] text-slate-300 font-bold text-xs px-4 py-2 rounded-lg border border-[#1e294b] transition-all">
                  Cancel
                </button>
                <button type="submit" className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs px-5 py-2 rounded-lg transition-all">
                  {editingVehicle ? "Save Metadata Updates" : "Create Vehicle Asset"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
