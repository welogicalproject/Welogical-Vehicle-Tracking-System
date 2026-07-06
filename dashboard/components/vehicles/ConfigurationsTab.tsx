import React from "react";
import { VehicleTrackingSnapshot } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Config } from "./VehicleBadges";

interface ConfigurationsTabProps {
  snapshot: VehicleTrackingSnapshot;
}

export function ConfigurationsTab({ snapshot }: ConfigurationsTabProps) {
  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
      <CardHeader>
        <CardTitle className="text-white text-sm">Device Settings Profiles</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        <Config label="APN Link" value={snapshot.device_config?.apn} />
        <Config label="Server IP Address" value={snapshot.device_config?.server_ip} />
        <Config label="Server Port" value={snapshot.device_config?.server_port} />
        <Config
          label="Reporting Limit (Seconds)"
          value={
            snapshot.device_config?.reporting_interval
              ? `${snapshot.device_config.reporting_interval}s`
              : null
          }
        />
        <Config
          label="Overspeed Limit"
          value={
            snapshot.device_config?.speed_limit ? `${snapshot.device_config.speed_limit} km/h` : null
          }
        />
        <Config label="Active Timezone" value={snapshot.device_config?.timezone} />
      </CardContent>
    </Card>
  );
}
