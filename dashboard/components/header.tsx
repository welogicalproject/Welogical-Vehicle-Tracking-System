"use client";

import { usePathname } from "next/navigation";
import { useState } from "react";
import { Bell, User, Menu, Database, Loader2 } from "lucide-react";
import { api } from "../lib/api";

export function Header() {
  const pathname = usePathname();
  const [resetting, setResetting] = useState(false);

  const handleDevReset = async () => {
    if (!confirm("Are you sure you want to reset the database? This will clear all application data (vehicles, locations, routes, assignments, events) while preserving migrations.")) return;
    setResetting(true);
    try {
      await api.devReset();
      alert("Database reset completed successfully! You can now start the demo workflow.");
      window.location.reload();
    } catch (err: any) {
      console.error(err);
      alert(err.message || "Failed to reset database. Make sure app is in development mode.");
    } finally {
      setResetting(false);
    }
  };

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
    <header className="h-16 border-b border-[#1e294b]/60 bg-[#0b0f19] px-4 md:px-8 flex items-center justify-between sticky top-0 z-20 shrink-0">
      {/* View Title */}
      <div className="flex items-center min-w-0">
        {/* Mobile Hamburger menu */}
        <button
          onClick={() => window.dispatchEvent(new CustomEvent("toggle-sidebar-drawer"))}
          className="md:hidden mr-3 p-1.5 hover:bg-[#1e294b]/60 rounded-lg text-slate-400 hover:text-white transition-colors"
          aria-label="Toggle Navigation Sidebar"
        >
          <Menu className="h-5 w-5" />
        </button>
        <h1 className="text-sm md:text-xl font-bold text-white tracking-wide truncate">
          {getPageTitle()}
        </h1>
      </div>

      {/* Notifications & Admin Profile */}
      <div className="flex items-center gap-3 md:gap-4 shrink-0">
        {/* Dev Reset Button */}
        <button
          onClick={handleDevReset}
          disabled={resetting}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-rose-400 hover:text-white bg-rose-500/10 hover:bg-rose-600 border border-rose-500/20 hover:border-rose-500 rounded-lg transition-all"
          title="Development DB Reset"
        >
          {resetting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Database className="h-4 w-4" />
          )}
          <span>Reset DB</span>
        </button>

        {/* Notification Icon */}
        <button className="relative p-2 text-slate-400 hover:text-white bg-[#131a2d]/40 hover:bg-[#1e294b]/40 border border-[#1e294b]/40 rounded-lg transition-all animate-in fade-in duration-200">
          <Bell className="h-4.5 w-4.5" />
          <span className="absolute -top-1 -right-1 h-4 w-4 bg-rose-500 rounded-full flex items-center justify-center text-[9px] font-extrabold text-white animate-pulse">
            8
          </span>
        </button>

        {/* User Profile Container */}
        <div className="flex items-center gap-3 pl-2 border-l border-[#1e294b]/60">
          <div className="hidden sm:block text-right">
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
