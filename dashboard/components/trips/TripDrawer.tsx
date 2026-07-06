import React, { useState, useEffect } from "react";
import { Trip, TripSummary as TripSummaryType, ReplayPoint, Vehicle } from "../../types";
import { api } from "../../lib/api";
import { TripSummary } from "./TripSummary";
import { TripReplay } from "./TripReplay";
import { TripExportButton } from "./TripExportButton";
import { X, Info, Map, Download, Calendar } from "lucide-react";
import { Button } from "../ui/button";

interface TripDrawerProps {
  trip: Trip | null;
  onClose: () => void;
  vehicles: Vehicle[];
}

export function TripDrawer({ trip, onClose, vehicles }: TripDrawerProps) {
  const [activeTab, setActiveTab] = useState<"summary" | "replay">("summary");
  const [summary, setSummary] = useState<TripSummaryType | null>(null);
  const [replayPoints, setReplayPoints] = useState<ReplayPoint[]>([]);
  const [loadingSummary, setLoadingSummary] = useState<boolean>(false);
  const [loadingReplay, setLoadingReplay] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const vehicle = trip ? vehicles.find((v) => v.id === trip.vehicle_id) || null : null;

  // Load summary and replay points when trip ID changes
  useEffect(() => {
    if (!trip) {
      setSummary(null);
      setReplayPoints([]);
      setError(null);
      return;
    }

    const fetchData = async () => {
      setError(null);
      
      // Load summary
      setLoadingSummary(true);
      try {
        const sumData = await api.getTripSummary(trip.vehicle_id, trip.id);
        setSummary(sumData);
      } catch (err: any) {
        console.error(err);
        setError("Failed to fetch trip metrics summary.");
      } finally {
        setLoadingSummary(false);
      }

      // Load replay points
      setLoadingReplay(true);
      try {
        const repData = await api.getTripReplay(trip.vehicle_id, trip.id);
        setReplayPoints(repData.points);
      } catch (err: any) {
        console.error(err);
      } finally {
        setLoadingReplay(false);
      }
    };

    fetchData();
    // Default to summary tab
    setActiveTab("summary");
  }, [trip]);

  if (!trip) return null;

  return (
    <>
      {/* Backdrop overlay */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Slide-in drawer container */}
      <div className="fixed inset-y-0 right-0 z-50 w-full max-w-4xl bg-[#0b0f19] border-l border-[#1e294b]/80 shadow-2xl flex flex-col h-full select-none text-white">
        
        {/* Drawer Header */}
        <div className="p-6 border-b border-[#1e294b]/60 flex items-center justify-between shrink-0">
          <div className="text-left">
            <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider block">
              Trip Details View
            </span>
            <h2 className="text-lg font-black text-white flex items-center gap-2">
              <Calendar className="h-5 w-5 text-indigo-400" />
              {vehicle ? vehicle.vehicle_name : `Vehicle ${trip.vehicle_id}`} 
              <span className="text-slate-500 font-mono font-normal text-sm">#{trip.id}</span>
            </h2>
            <span className="text-[10px] font-mono text-slate-500 block">
              UID: {vehicle ? vehicle.device_uid : "-"}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <TripExportButton vehicleId={trip.vehicle_id} tripId={trip.id} />
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-[#1e294b] rounded-lg text-slate-400 hover:text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="px-6 py-2 border-b border-[#1e294b]/20 bg-[#0c1221] flex gap-2 shrink-0">
          <button
            onClick={() => setActiveTab("summary")}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-bold rounded-lg transition-colors ${
              activeTab === "summary"
                ? "bg-[#132238] text-cyan-400 border border-cyan-500/20"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Info className="h-4 w-4" />
            Overview & Stats
          </button>
          <button
            onClick={() => setActiveTab("replay")}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-bold rounded-lg transition-colors ${
              activeTab === "replay"
                ? "bg-[#132238] text-cyan-400 border border-cyan-500/20"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Map className="h-4 w-4" />
            Route Playback
          </button>
        </div>

        {/* Tab Content Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm font-semibold mb-4 text-left">
              {error}
            </div>
          )}

          {activeTab === "summary" ? (
            <TripSummary
              trip={trip}
              summary={summary}
              loading={loadingSummary}
            />
          ) : (
            <TripReplay
              trip={trip}
              points={replayPoints}
              loading={loadingReplay}
              vehicle={vehicle}
            />
          )}
        </div>
      </div>
    </>
  );
}
