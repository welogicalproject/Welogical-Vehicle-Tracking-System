"use client";

import { usePathname } from "next/navigation";
import { Bell, User } from "lucide-react";

export function Header() {
  const pathname = usePathname();

  // Resolve page title based on path
  const getPageTitle = () => {
    if (pathname === "/") return "Dashboard Overview";
    if (pathname === "/tracking") return "Live Vehicle Tracking";
    if (pathname === "/analytics") return "Fleet Analytics";
    if (pathname === "/events") return "System Events Log";
    if (pathname === "/vehicles") return "Vehicle Inventory";
    if (pathname.startsWith("/vehicles/")) return "Vehicle Profile Analyzer";
    if (pathname === "/commands") return "Command Dispatcher Queue";
    if (pathname === "/configurations") return "Hardware Configurations";
    if (pathname === "/health") return "Device Health Diagnostics";
    if (pathname === "/explorer") return "Database Schema Explorer";
    if (pathname === "/geofences") return "Geofence Management";
    if (pathname === "/reports") return "Data Reports & Export";
    if (pathname === "/users") return "Users & Access Roles";
    if (pathname === "/settings") return "Global System Settings";
    return "Vehicle Tracking System";
  };

  return (
    <header className="h-16 border-b border-[#1e294b]/60 bg-[#0b0f19] px-8 flex items-center justify-between sticky top-0 z-20">
      {/* View Title */}
      <div>
        <h1 className="text-xl font-bold text-white tracking-wide">
          {getPageTitle()}
        </h1>
      </div>

      {/* Notifications & Admin Profile */}
      <div className="flex items-center gap-6">
        {/* Notification Icon */}
        <button className="relative p-2 text-slate-400 hover:text-white bg-[#131a2d]/40 hover:bg-[#1e294b]/40 border border-[#1e294b]/40 rounded-lg transition-all">
          <Bell className="h-4.5 w-4.5" />
          <span className="absolute -top-1 -right-1 h-4 w-4 bg-rose-500 rounded-full flex items-center justify-center text-[9px] font-extrabold text-white animate-pulse">
            8
          </span>
        </button>

        {/* User Profile Container */}
        <div className="flex items-center gap-3 pl-2 border-l border-[#1e294b]/60">
          <div className="text-right">
            <div className="text-xs font-bold text-white leading-tight">Admin</div>
            <div className="text-[10px] text-slate-500 font-semibold tracking-wider uppercase leading-tight">
              Administrator
            </div>
          </div>
          
          <div className="h-9 w-9 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <User className="h-5 w-5" />
          </div>
        </div>
      </div>
    </header>
  );
}
