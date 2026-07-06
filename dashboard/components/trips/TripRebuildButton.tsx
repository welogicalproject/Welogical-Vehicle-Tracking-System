import React, { useState } from "react";
import { Hammer, RefreshCw, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "../ui/button";
import { api } from "../../lib/api";

interface TripRebuildButtonProps {
  vehicleId: number;
  onRebuildComplete: () => void;
}

export function TripRebuildButton({ vehicleId, onRebuildComplete }: TripRebuildButtonProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error" | null; text: string }>({
    type: null,
    text: "",
  });

  const handleRebuild = async () => {
    setLoading(true);
    setStatusMsg({ type: null, text: "" });
    try {
      const res = await api.rebuildVehicleTrips(vehicleId);
      if (res.result) {
        setStatusMsg({
          type: "success",
          text: `Trip history successfully rebuilt. Generated ${res.trips_created} trips!`,
        });
        onRebuildComplete();
      } else {
        setStatusMsg({
          type: "error",
          text: "Failed to rebuild trip logs history.",
        });
      }
    } catch (err: any) {
      console.error(err);
      setStatusMsg({
        type: "error",
        text: err.message || "An error occurred during rebuild execution.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-2 text-left shrink-0">
      <Button
        variant="secondary"
        size="sm"
        onClick={handleRebuild}
        className="flex items-center gap-2 h-9"
        disabled={loading}
      >
        <Hammer className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        {loading ? "Rebuilding..." : "Rebuild Trips"}
      </Button>

      {statusMsg.type && (
        <div
          className={`flex items-start gap-1.5 p-2 rounded text-[10px] max-w-[280px] font-semibold border ${
            statusMsg.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
              : "bg-red-500/10 border-red-500/20 text-red-400"
          }`}
        >
          {statusMsg.type === "success" ? (
            <CheckCircle className="h-3.5 w-3.5 shrink-0" />
          ) : (
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          )}
          <span>{statusMsg.text}</span>
        </div>
      )}
    </div>
  );
}
