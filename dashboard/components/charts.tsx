"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell
} from "recharts";

// 1. Speed vs Time
export function SpeedTimeChart({ data }: { data: { time: string; speed: number }[] }) {
  return (
    <div className="h-[250px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e294b" vertical={false} />
          <XAxis 
            dataKey="time" 
            stroke="#94a3b8" 
            fontSize={11}
            tickLine={false}
          />
          <YAxis 
            stroke="#94a3b8" 
            fontSize={11}
            tickLine={false}
            unit=" km/h"
          />
          <Tooltip
            contentStyle={{ backgroundColor: "#131a2d", borderColor: "#1e294b", color: "#fff" }}
            itemStyle={{ color: "#06b6d4" }}
          />
          <Line 
            type="monotone" 
            dataKey="speed" 
            stroke="#06b6d4" 
            strokeWidth={2.5} 
            dot={{ r: 2, fill: "#06b6d4", strokeWidth: 0 }}
            activeDot={{ r: 4 }}
            name="Speed"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// 2. Records per Day
export function RecordsPerDayChart({ data }: { data: { date: string; count: number }[] }) {
  return (
    <div className="h-[250px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="areaColor" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e294b" vertical={false} />
          <XAxis 
            dataKey="date" 
            stroke="#94a3b8" 
            fontSize={11}
            tickLine={false}
          />
          <YAxis 
            stroke="#94a3b8" 
            fontSize={11}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{ backgroundColor: "#131a2d", borderColor: "#1e294b", color: "#fff" }}
            itemStyle={{ color: "#10b981" }}
          />
          <Area 
            type="monotone" 
            dataKey="count" 
            stroke="#10b981" 
            fillOpacity={1} 
            fill="url(#areaColor)" 
            strokeWidth={2}
            name="Records Logged"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// 3. Vehicle Activity
export function VehicleActivityChart({ data }: { data: { vehicleName: string; count: number }[] }) {
  return (
    <div className="h-[250px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e294b" vertical={false} />
          <XAxis 
            dataKey="vehicleName" 
            stroke="#94a3b8" 
            fontSize={10}
            tickLine={false}
          />
          <YAxis 
            stroke="#94a3b8" 
            fontSize={11}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{ backgroundColor: "#131a2d", borderColor: "#1e294b", color: "#fff" }}
            itemStyle={{ color: "#06b6d4" }}
          />
          <Bar 
            dataKey="count" 
            fill="#06b6d4" 
            radius={[4, 4, 0, 0]} 
            maxBarSize={30}
            name="Ingested Packets"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// 4. Event Distribution (Pie Chart)
export function EventDistributionChart({ data }: { data: { name: string; value: number; color: string }[] }) {
  return (
    <div className="h-[250px] w-full flex items-center justify-center">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ backgroundColor: "#131a2d", borderColor: "#1e294b", color: "#fff" }}
          />
          <Legend 
            verticalAlign="bottom" 
            height={36} 
            formatter={(value) => <span className="text-xs text-slate-300">{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

// 5. Event Trend (Area Chart)
export function EventTrendChart({ data }: { data: { time: string; count: number }[] }) {
  return (
    <div className="h-[250px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="eventColor" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e294b" vertical={false} />
          <XAxis 
            dataKey="time" 
            stroke="#94a3b8" 
            fontSize={11}
            tickLine={false}
          />
          <YAxis 
            stroke="#94a3b8" 
            fontSize={11}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{ backgroundColor: "#131a2d", borderColor: "#1e294b", color: "#fff" }}
            itemStyle={{ color: "#ef4444" }}
          />
          <Area 
            type="monotone" 
            dataKey="count" 
            stroke="#ef4444" 
            fillOpacity={1} 
            fill="url(#eventColor)" 
            strokeWidth={2}
            name="Events Logged"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// 6. Command Analytics (Bar Chart)
export function CommandAnalyticsChart({ data }: { data: { name: string; count: number; color: string }[] }) {
  return (
    <div className="h-[250px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e294b" vertical={false} />
          <XAxis 
            dataKey="name" 
            stroke="#94a3b8" 
            fontSize={11}
            tickLine={false}
          />
          <YAxis 
            stroke="#94a3b8" 
            fontSize={11}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{ backgroundColor: "#131a2d", borderColor: "#1e294b", color: "#fff" }}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={45} name="Total Commands">
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
