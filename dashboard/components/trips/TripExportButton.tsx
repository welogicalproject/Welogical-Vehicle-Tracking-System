import React from "react";
import { Download } from "lucide-react";
import { Button } from "../ui/button";
import { api } from "../../lib/api";

interface TripExportButtonProps {
  vehicleId: number;
  tripId: number;
}

export function TripExportButton({ vehicleId, tripId }: TripExportButtonProps) {
  const handleExport = () => {
    const downloadUrl = api.getTripExportUrl(vehicleId, tripId);
    // Open in a new tab to trigger standard HTTP attachment download response
    window.open(downloadUrl, "_blank");
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleExport}
      className="flex items-center gap-2 text-slate-400 hover:text-white"
    >
      <Download className="h-4 w-4" />
      Export CSV
    </Button>
  );
}
