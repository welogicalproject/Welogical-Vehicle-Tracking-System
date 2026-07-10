import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { VehicleTrackingSnapshot, Driver, DriverAssignment, Trip, Vehicle } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Detail } from "./VehicleBadges";
import { formatDate } from "../../lib/date";
import { api } from "../../lib/api";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { DatePickerInput } from "../ui/date-picker";
import { 
  Car, 
  Shield, 
  Activity, 
  Cpu, 
  Play, 
  CheckCircle, 
  XCircle, 
  Trash2, 
  Edit2, 
  Plus, 
  Search, 
  X,
  User,
  Calendar,
  Compass,
  Link2,
  UserPlus
} from "lucide-react";
import { cn } from "../../lib/utils";

interface OverviewTabProps {
  snapshot: VehicleTrackingSnapshot;
  vehicleId: number;
  onAssignmentChange?: () => void;
  trips: Trip[];
}

function gpsStatus(snapshot: VehicleTrackingSnapshot | null) {
  const gps =
    snapshot?.latest_location?.extra_data?.gps_details ??
    snapshot?.latest_location?.extra_data?.gps;
  if (gps?.fix === "A") return `Valid${gps.sat ? ` (${gps.sat} sats)` : ""}`;
  if (gps?.fix === "V") return "No fix";
  return "N/A";
}

function getStatus(lastSeen: string | null, isConnected?: boolean): "online" | "idle" | "offline" {
  if (isConnected === false) return "offline";
  if (!lastSeen) return "offline";
  const lastSeenStr = lastSeen.endsWith("Z") ? lastSeen : `${lastSeen}Z`;
  const lastSeenDate = new Date(lastSeenStr);
  const now = new Date();
  const diffMinutes = (now.getTime() - lastSeenDate.getTime()) / 60000;

  if (diffMinutes < 5) return "online";
  if (diffMinutes <= 30) return "idle";
  return "offline";
}

export function OverviewTab({ snapshot, vehicleId, onAssignmentChange, trips }: OverviewTabProps) {
  const router = useRouter();

  // Assign Driver Modal states
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  // "select" = pick existing, "create" = create new driver
  const [assignMode, setAssignMode] = useState<"select" | "create">("select");
  const [availableDrivers, setAvailableDrivers] = useState<Driver[]>([]);
  const [driversLoading, setDriversLoading] = useState(false);
  const [selectedDriverId, setSelectedDriverId] = useState("");
  const [assignSubmitting, setAssignSubmitting] = useState(false);
  const [assignError, setAssignError] = useState<string | null>(null);

  // New driver form state
  const [newDriverName, setNewDriverName] = useState("");
  const [newDriverPhone, setNewDriverPhone] = useState("");
  const [newDriverEmail, setNewDriverEmail] = useState("");
  const [newDriverLicense, setNewDriverLicense] = useState("");
  const [newDriverLicenseExpiry, setNewDriverLicenseExpiry] = useState("");
  const [newDriverEmergencyContact, setNewDriverEmergencyContact] = useState("");
  const [newDriverStatus, setNewDriverStatus] = useState<"ACTIVE" | "SUSPENDED" | "INACTIVE">("ACTIVE");
  const [newDriverAddress, setNewDriverAddress] = useState("");
  const [newDriverNotes, setNewDriverNotes] = useState("");

  // Edit Vehicle Modal states
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editSubmitting, setEditSubmitting] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  // Form Fields for Edit Vehicle
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

  // History states
  const [history, setHistory] = useState<DriverAssignment[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const rows = await api.getVehicleAssignmentHistory(vehicleId);
      setHistory(rows);
    } catch (err) {
      console.error("Failed to load assignment history:", err);
    } finally {
      setHistoryLoading(false);
    }
  }, [vehicleId]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const resetNewDriverForm = () => {
    setNewDriverName("");
    setNewDriverPhone("");
    setNewDriverEmail("");
    setNewDriverLicense("");
    setNewDriverLicenseExpiry("");
    setNewDriverEmergencyContact("");
    setNewDriverStatus("ACTIVE");
    setNewDriverAddress("");
    setNewDriverNotes("");
  };

  const openAssignModal = async () => {
    setIsAssignModalOpen(true);
    setAssignMode("select");
    setDriversLoading(true);
    setAssignError(null);
    setSelectedDriverId("");
    resetNewDriverForm();
    try {
      const list = await api.getDrivers(0, 100);
      const activeList = list.filter((d) => d.status === "ACTIVE");
      setAvailableDrivers(activeList);
    } catch (err) {
      console.error("Failed to load drivers:", err);
    } finally {
      setDriversLoading(false);
    }
  };

  const handleAssign = async () => {
    if (!selectedDriverId) return;
    setAssignSubmitting(true);
    setAssignError(null);
    try {
      await api.assignDriver(vehicleId, Number(selectedDriverId));
      setIsAssignModalOpen(false);
      loadHistory();
      if (onAssignmentChange) onAssignmentChange();
    } catch (err: any) {
      setAssignError(err.message || "Failed to assign driver.");
    } finally {
      setAssignSubmitting(false);
    }
  };

  const handleCreateAndAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    // Frontend validation
    if (!newDriverName.trim()) { setAssignError("Driver Name is required."); return; }
    if (!newDriverPhone.trim()) { setAssignError("Phone Number is required."); return; }
    if (!newDriverLicense.trim()) { setAssignError("License Number is required."); return; }
    if (!newDriverLicenseExpiry) { setAssignError("License Expiry Date is required."); return; }
    if (!newDriverEmergencyContact.trim()) { setAssignError("Emergency Contact is required."); return; }

    setAssignSubmitting(true);
    setAssignError(null);
    try {
      // 1. Create the driver
      const created = await api.createDriver({
        driver_name: newDriverName.trim(),
        phone_number: newDriverPhone.trim(),
        email: newDriverEmail.trim() || null,
        license_number: newDriverLicense.trim(),
        // Ensure we send a full ISO datetime; DatePickerInput gives YYYY-MM-DDT00:00
        license_expiry: newDriverLicenseExpiry.endsWith("Z") ? newDriverLicenseExpiry : `${newDriverLicenseExpiry}:00`,
        emergency_contact: newDriverEmergencyContact.trim(),
        status: newDriverStatus,
        notes: newDriverNotes.trim() || null,
      });
      // 2. Assign to this vehicle
      await api.assignDriver(vehicleId, created.id);
      setIsAssignModalOpen(false);
      resetNewDriverForm();
      loadHistory();
      if (onAssignmentChange) onAssignmentChange();
    } catch (err: any) {
      setAssignError(err.message || "Failed to create or assign driver.");
    } finally {
      setAssignSubmitting(false);
    }
  };

  const handleRemoveDriver = async () => {
    if (!confirm("Are you sure you want to remove the current driver?")) return;
    try {
      await api.releaseDriver(vehicleId);
      loadHistory();
      if (onAssignmentChange) onAssignmentChange();
    } catch (err: any) {
      alert(err.message || "Failed to remove driver.");
    }
  };

  // Quick Actions: Enable / Disable
  const handleToggleStatus = async () => {
    const nextStatus = snapshot.vehicle.status === "Enabled" ? "Disabled" : "Enabled";
    try {
      await api.updateVehicle(vehicleId, { status: nextStatus });
      if (onAssignmentChange) onAssignmentChange();
    } catch (err: any) {
      alert(err.message || "Failed to update lifecycle status.");
    }
  };

  // Quick Actions: Archive
  const handleArchiveVehicle = async () => {
    if (!confirm(`Are you sure you want to archive "${snapshot.vehicle.vehicle_name}"? This soft-deletes the vehicle from directory listings but preserves historical tracks.`)) return;
    try {
      await api.deleteVehicle(vehicleId);
      router.push("/vehicles");
    } catch (err: any) {
      alert(err.message || "Failed to archive vehicle.");
    }
  };

  // Quick Actions: Edit (Open Modal)
  const openEditModal = () => {
    const v = snapshot.vehicle;
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
    setEditError(null);
    setIsEditModalOpen(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vehicleName) {
      setEditError("Vehicle Name is required.");
      return;
    }
    setEditSubmitting(true);
    setEditError(null);

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
      await api.updateVehicle(vehicleId, payload);
      setIsEditModalOpen(false);
      if (onAssignmentChange) onAssignmentChange();
    } catch (err: any) {
      setEditError(err.message || "Failed to save vehicle updates.");
    } finally {
      setEditSubmitting(false);
    }
  };

  // Activity stats calculations
  const totalTrips = trips.length;
  const totalDistance = trips.reduce((sum, t) => sum + (t.distance || 0), 0);
  const lastTrip = trips.length > 0 ? trips[0] : null;
  const connectionStatus = getStatus(snapshot.vehicle.last_seen, snapshot.vehicle.is_connected);

  return (
    <div className="space-y-6">
      {/* Responsive Grid for all Info sections */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        
        {/* 1. Vehicle Overview Card */}
        <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
          <CardHeader className="flex flex-row items-center gap-2 pb-2">
            <Car className="h-5 w-5 text-cyan-400" />
            <CardTitle className="text-white text-sm font-bold">Vehicle Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-left">
            <Detail label="Vehicle Name" value={snapshot.vehicle.vehicle_name} />
            <Detail label="Vehicle Number" value={snapshot.vehicle.vehicle_number || "N/A"} />
            <Detail label="Vehicle Type" value={snapshot.vehicle.vehicle_type} />
            
            <div className="flex items-center justify-between gap-4 border-b border-[#1e294b]/30 pb-2 text-xs">
              <span className="text-slate-500 font-semibold">Current Status</span>
              <span className={cn(
                "px-2 py-0.5 rounded text-[10px] font-extrabold uppercase border",
                snapshot.movement_status === "Moving" 
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                  : snapshot.movement_status === "Stopped" 
                    ? "bg-amber-500/10 text-amber-400 border-amber-500/20" 
                    : "bg-slate-500/10 text-slate-400 border-slate-500/20"
              )}>
                {snapshot.movement_status}
              </span>
            </div>

            <div className="flex items-center justify-between gap-4 border-b border-[#1e294b]/30 pb-2 text-xs">
              <span className="text-slate-500 font-semibold">Health Status</span>
              <span className={cn(
                "px-2 py-0.5 rounded text-[10px] font-extrabold uppercase border",
                snapshot.health_status === "Healthy" 
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                  : snapshot.health_status === "Warning" 
                    ? "bg-amber-500/10 text-amber-400 border-amber-500/20" 
                    : "bg-rose-500/10 text-rose-400 border-rose-500/20"
              )}>
                {snapshot.health_status}
              </span>
            </div>

            <Detail label="Manufacturer" value={snapshot.vehicle.manufacturer || "N/A"} />
            <Detail label="Model" value={snapshot.vehicle.model || "N/A"} />
            <Detail label="Year" value={snapshot.vehicle.year ? String(snapshot.vehicle.year) : "N/A"} />
            <Detail label="VIN" value={snapshot.vehicle.vin || "N/A"} mono />
            <Detail label="IMEI" value={snapshot.vehicle.imei || "N/A"} mono />
            <Detail label="SIM Number" value={snapshot.vehicle.sim_number || "N/A"} mono />
            <Detail label="Fuel Type" value={snapshot.vehicle.fuel_type || "N/A"} />
            <Detail label="Capacity" value={snapshot.vehicle.capacity ? `${snapshot.vehicle.capacity} L` : "N/A"} />
            <Detail label="Notes" value={snapshot.vehicle.notes || "None"} />
          </CardContent>
        </Card>

        {/* 2. Current Driver Card */}
        <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-cyan-400" />
              <CardTitle className="text-white text-sm font-bold">Current Driver</CardTitle>
            </div>
            {snapshot.vehicle.current_driver ? (
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={openAssignModal} className="h-7 text-[10px] px-2 border-[#1e294b] text-slate-300 hover:text-white">
                  Change
                </Button>
                <Button size="sm" variant="danger" onClick={handleRemoveDriver} className="h-7 text-[10px] px-2 bg-red-950 hover:bg-red-900 border-red-800 text-red-300">
                  Remove
                </Button>
              </div>
            ) : (
              <Button size="sm" variant="secondary" onClick={openAssignModal} className="h-7 text-[10px] px-2 bg-cyan-950 hover:bg-cyan-900 border-cyan-800 text-cyan-300">
                Assign Driver
              </Button>
            )}
          </CardHeader>
          <CardContent className="space-y-3 text-left">
            {snapshot.vehicle.current_driver ? (
              <>
                <Detail label="Driver Name" value={snapshot.vehicle.current_driver.driver_name} />
                <Detail label="Phone Number" value={snapshot.vehicle.current_driver.phone_number} />
                <Detail label="License Number" value={snapshot.vehicle.current_driver.license_number} mono />
                <Detail label="License Expiry" value={new Date(snapshot.vehicle.current_driver.license_expiry).toLocaleDateString()} />
                <div className="flex items-center justify-between gap-4 border-b border-[#1e294b]/30 pb-2 text-xs">
                  <span className="text-slate-500 font-semibold">Driver Status</span>
                  <span className={cn(
                    "px-2 py-0.5 rounded text-[10px] font-extrabold uppercase border",
                    snapshot.vehicle.current_driver.status === "ACTIVE" 
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                      : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                  )}>
                    {snapshot.vehicle.current_driver.status}
                  </span>
                </div>
              </>
            ) : (
              <div className="py-12 text-center text-slate-400 text-sm border border-dashed border-[#1e294b]/40 rounded-lg bg-[#080d17]/40">
                No active driver assignment.
              </div>
            )}
          </CardContent>
        </Card>

        {/* 4. Vehicle Activity Card */}
        <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
          <CardHeader className="flex flex-row items-center gap-2 pb-2">
            <Activity className="h-5 w-5 text-cyan-400" />
            <CardTitle className="text-white text-sm font-bold">Vehicle Activity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-left">
            <Detail 
              label="Current Location" 
              value={snapshot.latest_location ? `${snapshot.latest_location.latitude.toFixed(6)}, ${snapshot.latest_location.longitude.toFixed(6)}` : "N/A"} 
              mono 
            />
            <Detail label="Last Telemetry Time" value={snapshot.latest_location ? formatDate(snapshot.latest_location.timestamp) : "N/A"} />
            <Detail label="Current Speed" value={snapshot.latest_location ? `${snapshot.latest_location.speed.toFixed(1)} km/h` : "Stopped"} />
            
            <div className="border-b border-[#1e294b]/30 pb-2 text-xs">
              <span className="text-slate-500 font-semibold block mb-1">Last Trip</span>
              {lastTrip ? (
                <div className="bg-[#0f172a]/50 p-2 rounded border border-[#1e294b]/40 text-slate-300 text-[11px] space-y-1">
                  <div><span className="font-bold text-white">Start:</span> {new Date(lastTrip.start_time).toLocaleString()}</div>
                  {lastTrip.end_time && (
                    <div><span className="font-bold text-white">End:</span> {new Date(lastTrip.end_time).toLocaleString()}</div>
                  )}
                  <div className="flex justify-between">
                    <span>Dist: {lastTrip.distance.toFixed(1)} km</span>
                    <span>Dur: {Math.round(lastTrip.duration / 60)} mins</span>
                  </div>
                </div>
              ) : (
                <span className="text-slate-400 font-bold">No trips recorded</span>
              )}
            </div>

            <Detail label="Total Trips" value={String(totalTrips)} />
            <Detail label="Total Distance" value={totalDistance > 0 ? `${totalDistance.toFixed(1)} km` : "N/A"} />
          </CardContent>
        </Card>

        {/* 5. Device Information Card */}
        <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
          <CardHeader className="flex flex-row items-center gap-2 pb-2">
            <Cpu className="h-5 w-5 text-cyan-400" />
            <CardTitle className="text-white text-sm font-bold">Device Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-left">
            <Detail label="Device UID" value={snapshot.vehicle.device_uid} mono />
            <Detail label="IMEI" value={snapshot.vehicle.imei || "N/A"} mono />
            <Detail label="SIM Number" value={snapshot.vehicle.sim_number || "N/A"} mono />
            <Detail label="Last Communication" value={formatDate(snapshot.vehicle.last_seen)} />
            
            <div className="flex items-center justify-between gap-4 border-b border-[#1e294b]/30 pb-2 text-xs">
              <span className="text-slate-500 font-semibold">Connection Status</span>
              <span className={cn(
                "px-2 py-0.5 rounded text-[10px] font-extrabold uppercase border flex items-center gap-1",
                connectionStatus === "online" 
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                  : connectionStatus === "idle" 
                    ? "bg-amber-500/10 text-amber-400 border-amber-500/20" 
                    : "bg-slate-500/10 text-slate-400 border-slate-500/20"
              )}>
                <span className={cn(
                  "h-1.5 w-1.5 rounded-full animate-pulse",
                  connectionStatus === "online" ? "bg-emerald-400" : connectionStatus === "idle" ? "bg-amber-400" : "bg-slate-400"
                )} />
                {connectionStatus}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* 6. Quick Actions Card */}
        <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
          <CardHeader className="flex flex-row items-center gap-2 pb-2">
            <Play className="h-5 w-5 text-cyan-400" />
            <CardTitle className="text-white text-sm font-bold">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 py-2">
            <Button 
              variant="outline" 
              onClick={handleToggleStatus} 
              className={cn(
                "w-full text-xs font-bold py-2 justify-start gap-2",
                snapshot.vehicle.status === "Enabled" 
                  ? "border-amber-500/30 text-amber-400 hover:bg-amber-500/10" 
                  : "border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10"
              )}
            >
              {snapshot.vehicle.status === "Enabled" ? (
                <>
                  <XCircle className="h-4 w-4" />
                  Disable Vehicle Asset
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4" />
                  Enable Vehicle Asset
                </>
              )}
            </Button>

            <Button 
              variant="outline" 
              onClick={openEditModal} 
              className="w-full text-xs font-bold py-2 justify-start gap-2 border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10"
            >
              <Edit2 className="h-4 w-4" />
              Edit Vehicle Profile
            </Button>

            <Button 
              variant="danger"
              onClick={handleArchiveVehicle} 
              className="w-full text-xs font-bold py-2 justify-start gap-2 bg-red-950/80 hover:bg-red-900 border border-red-800/40 text-red-300"
            >
              <Trash2 className="h-4 w-4" />
              Archive Vehicle (Soft Delete)
            </Button>
          </CardContent>
        </Card>

      </div>

      {/* 3. Assignment History Table Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
        <CardHeader>
          <CardTitle className="text-white text-sm font-bold flex items-center gap-2">
            <Calendar className="h-5 w-5 text-cyan-400" />
            Driver Assignment History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <div className="py-6 text-center text-slate-400 text-sm">Loading history...</div>
          ) : history.length === 0 ? (
            <div className="py-6 text-center text-slate-400 text-sm">No assignment history found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left text-slate-300">
                <thead className="text-xs uppercase text-slate-400 border-b border-[#1e294b]/60">
                  <tr>
                    <th className="py-3 px-4">Driver Name</th>
                    <th className="py-3 px-4">License Number</th>
                    <th className="py-3 px-4">Assigned At</th>
                    <th className="py-3 px-4">Released At</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e294b]/40">
                  {history.map((h) => (
                    <tr key={h.id} className="hover:bg-[#131a2d]/60">
                      <td className="py-3 px-4 font-medium text-white">{h.driver?.driver_name || "Unknown"}</td>
                      <td className="py-3 px-4 font-mono">{h.driver?.license_number || "N/A"}</td>
                      <td className="py-3 px-4">{new Date(h.assigned_at).toLocaleString()}</td>
                      <td className="py-3 px-4">{h.released_at ? new Date(h.released_at).toLocaleString() : "Active"}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${h.status === "Active" ? "bg-green-950 text-green-400 border border-green-800" : "bg-slate-900 text-slate-400 border border-slate-800"}`}>
                          {h.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Assign Driver Modal */}
      {isAssignModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-[#0f172a] border border-[#1e294b] rounded-xl max-w-lg w-full text-left relative shadow-2xl flex flex-col max-h-[90vh]">
            {/* Header */}
            <div className="p-5 border-b border-[#1e294b]/60 flex items-center justify-between shrink-0">
              <h3 className="text-sm font-black text-white uppercase tracking-wider flex items-center gap-2">
                <User className="h-4.5 w-4.5 text-cyan-400" />
                Assign Driver to Vehicle
              </h3>
              <button onClick={() => setIsAssignModalOpen(false)} className="text-slate-400 hover:text-white transition-colors">
                <X className="h-4.5 w-4.5" />
              </button>
            </div>

            {/* Mode toggle tabs */}
            <div className="flex border-b border-[#1e294b]/60 shrink-0">
              <button
                type="button"
                onClick={() => { setAssignMode("select"); setAssignError(null); }}
                className={cn(
                  "flex-1 py-2.5 text-xs font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2",
                  assignMode === "select"
                    ? "text-cyan-400 border-b-2 border-cyan-400 bg-cyan-500/5"
                    : "text-slate-500 hover:text-slate-300"
                )}
              >
                <User className="h-3.5 w-3.5" />
                Select Existing
              </button>
              <button
                type="button"
                onClick={() => { setAssignMode("create"); setAssignError(null); }}
                className={cn(
                  "flex-1 py-2.5 text-xs font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2",
                  assignMode === "create"
                    ? "text-cyan-400 border-b-2 border-cyan-400 bg-cyan-500/5"
                    : "text-slate-500 hover:text-slate-300"
                )}
              >
                <UserPlus className="h-3.5 w-3.5" />
                Create New Driver
              </button>
            </div>

            {/* ── SELECT EXISTING ── */}
            {assignMode === "select" && (
              <div className="p-5 space-y-4">
                {driversLoading ? (
                  <div className="py-8 text-center text-slate-400 text-sm">Loading active drivers...</div>
                ) : availableDrivers.length === 0 ? (
                  <div className="py-4 text-center text-amber-400 text-xs bg-amber-950/20 border border-amber-900/40 rounded-lg p-3">
                    No active drivers found. Use &ldquo;Create New Driver&rdquo; to register one.
                  </div>
                ) : (
                  <>
                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider">Select Active Driver</label>
                    <select
                      value={selectedDriverId}
                      onChange={(e) => setSelectedDriverId(e.target.value)}
                      className="w-full bg-[#131a2d] border border-[#1e294b] rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 text-sm"
                    >
                      <option value="">-- Choose an Active Driver --</option>
                      {availableDrivers.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.driver_name} ({d.license_number})
                        </option>
                      ))}
                    </select>
                  </>
                )}

                {assignError && (
                  <div className="text-red-400 text-xs bg-red-950/30 border border-red-900/40 p-2 rounded">
                    {assignError}
                  </div>
                )}

                <div className="flex justify-end gap-3 pt-2">
                  <Button variant="outline" size="sm" onClick={() => setIsAssignModalOpen(false)}>Cancel</Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleAssign}
                    disabled={!selectedDriverId || assignSubmitting}
                    className="bg-cyan-700 hover:bg-cyan-600 text-white border-cyan-600"
                  >
                    {assignSubmitting ? "Assigning..." : "Assign Driver"}
                  </Button>
                </div>
              </div>
            )}

            {/* ── CREATE NEW DRIVER ── */}
            {assignMode === "create" && (
              <form onSubmit={handleCreateAndAssign} className="flex-1 overflow-y-auto">
                <div className="p-5 space-y-4">
                  {assignError && (
                    <div className="text-red-400 text-xs bg-red-950/30 border border-red-900/40 p-2 rounded">
                      {assignError}
                    </div>
                  )}

                  {/* Row 1: Name + Phone */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Driver Name *</label>
                      <Input
                        value={newDriverName}
                        onChange={(e) => setNewDriverName(e.target.value)}
                        placeholder="Full name"
                        className="bg-[#131a2d] border-[#1e294b] text-xs h-9"
                        required
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Phone Number *</label>
                      <Input
                        value={newDriverPhone}
                        onChange={(e) => setNewDriverPhone(e.target.value)}
                        placeholder="+91 98765 43210"
                        className="bg-[#131a2d] border-[#1e294b] text-xs h-9"
                        required
                      />
                    </div>
                  </div>

                  {/* Row 2: Email + Emergency Contact */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Email</label>
                      <Input
                        type="email"
                        value={newDriverEmail}
                        onChange={(e) => setNewDriverEmail(e.target.value)}
                        placeholder="driver@company.com"
                        className="bg-[#131a2d] border-[#1e294b] text-xs h-9"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Emergency Contact *</label>
                      <Input
                        value={newDriverEmergencyContact}
                        onChange={(e) => setNewDriverEmergencyContact(e.target.value)}
                        placeholder="Name / Phone"
                        className="bg-[#131a2d] border-[#1e294b] text-xs h-9"
                        required
                      />
                    </div>
                  </div>

                  {/* Row 3: License + Expiry */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">License Number *</label>
                      <Input
                        value={newDriverLicense}
                        onChange={(e) => setNewDriverLicense(e.target.value)}
                        placeholder="GJ0120230012345"
                        className="bg-[#131a2d] border-[#1e294b] text-xs h-9 font-mono"
                        required
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">License Expiry *</label>
                      <DatePickerInput
                        value={newDriverLicenseExpiry}
                        onChange={setNewDriverLicenseExpiry}
                        mode="end"
                        placeholder="Pick expiry date"
                      />
                    </div>
                  </div>

                  {/* Row 4: Status */}
                  <div>
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Driver Status</label>
                    <select
                      value={newDriverStatus}
                      onChange={(e) => setNewDriverStatus(e.target.value as "ACTIVE" | "SUSPENDED" | "INACTIVE")}
                      className="w-full bg-[#131a2d] border border-[#1e294b] rounded-lg px-3 py-1.5 text-xs text-slate-300 font-semibold focus:outline-none transition-all h-9"
                    >
                      <option value="ACTIVE">ACTIVE</option>
                      <option value="SUSPENDED">SUSPENDED</option>
                      <option value="INACTIVE">INACTIVE</option>
                    </select>
                  </div>

                  {/* Row 5: Address (optional) */}
                  <div>
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Address (optional)</label>
                    <Input
                      value={newDriverAddress}
                      onChange={(e) => setNewDriverAddress(e.target.value)}
                      placeholder="Residential address"
                      className="bg-[#131a2d] border-[#1e294b] text-xs h-9"
                    />
                  </div>

                  {/* Row 6: Notes (optional) */}
                  <div>
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Notes (optional)</label>
                    <textarea
                      value={newDriverNotes}
                      onChange={(e) => setNewDriverNotes(e.target.value)}
                      placeholder="Any additional notes..."
                      rows={2}
                      className="w-full bg-[#131a2d] border border-[#1e294b] rounded-lg p-3 text-xs text-white focus:outline-none focus:border-cyan-400 transition-all resize-none"
                    />
                  </div>
                </div>

                {/* Sticky footer */}
                <div className="sticky bottom-0 bg-[#0f172a] border-t border-[#1e294b]/60 px-5 py-3 flex justify-end gap-3">
                  <Button type="button" variant="outline" size="sm" onClick={() => setIsAssignModalOpen(false)}>Cancel</Button>
                  <Button
                    type="submit"
                    size="sm"
                    disabled={assignSubmitting}
                    className="bg-cyan-700 hover:bg-cyan-600 text-white border-cyan-600"
                  >
                    {assignSubmitting ? "Creating & Assigning..." : "Create & Assign Driver"}
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Edit Vehicle Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-2xl bg-[#0b0f19] border border-[#1e294b]/80 rounded-xl shadow-2xl flex flex-col max-h-[90vh]">
            <div className="p-5 border-b border-[#1e294b]/60 flex items-center justify-between shrink-0">
              <h3 className="text-sm font-black text-white uppercase tracking-wider flex items-center gap-2">
                <Car className="h-4.5 w-4.5 text-cyan-400" />
                Edit Asset: {snapshot.vehicle.vehicle_name}
              </h3>
              <button onClick={() => setIsEditModalOpen(false)} className="text-slate-400 hover:text-white transition-colors">
                <X className="h-4.5 w-4.5" />
              </button>
            </div>
            
            <form onSubmit={handleEditSubmit} className="flex-1 overflow-y-auto p-6 space-y-4 text-left">
              {editError && (
                <div className="text-red-400 text-xs bg-red-950/30 border border-red-900/40 p-2 rounded">
                  {editError}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Vehicle Name *</label>
                  <Input value={vehicleName} onChange={(e) => setVehicleName(e.target.value)} required placeholder="e.g. Surat Express" className="bg-[#131a2d] border-[#1e294b] text-xs h-9" />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Device Hardware UID *</label>
                  <Input value={deviceUid} required disabled className="bg-[#131a2d]/50 border-[#1e294b] text-xs h-9 text-slate-400" />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Add specific fleet details..." className="w-full min-h-[80px] bg-[#131a2d] border border-[#1e294b] rounded-lg p-3 text-xs text-white focus:outline-none focus:border-cyan-400 transition-all" />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#1e294b]/60 shrink-0">
                <button type="button" onClick={() => setIsEditModalOpen(false)} className="bg-[#131a2d] hover:bg-[#1e294b] text-slate-300 font-bold text-xs px-4 py-2 rounded-lg border border-[#1e294b] transition-all">
                  Cancel
                </button>
                <button type="submit" disabled={editSubmitting} className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs px-5 py-2 rounded-lg transition-all">
                  {editSubmitting ? "Saving..." : "Save Metadata Updates"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
