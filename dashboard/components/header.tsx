"use client";

import { usePathname } from "next/navigation";
import { useState } from "react";
import { Bell, User, Menu, Database, Loader2, LogOut, Settings as SettingsIcon, ShieldAlert } from "lucide-react";
import { api } from "../lib/api";
import { useFleet } from "../context/FleetContext";
import { cn } from "../lib/utils";

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

  const { recentEvents } = useFleet();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showAdminMenu, setShowAdminMenu] = useState(false);
  const [readEventIds, setReadEventIds] = useState<Set<number>>(new Set());

  const unreadEvents = recentEvents.filter((e) => !readEventIds.has(e.id));
  const unreadCount = unreadEvents.length;

  const handleMarkAllRead = () => {
    const newRead = new Set(readEventIds);
    recentEvents.forEach((e) => newRead.add(e.id));
    setReadEventIds(newRead);
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
        <div className="relative">
          <button
            onClick={() => {
              setShowNotifications(!showNotifications);
              setShowAdminMenu(false);
            }}
            className="relative p-2 text-slate-400 hover:text-white bg-[#131a2d]/40 hover:bg-[#1e294b]/40 border border-[#1e294b]/40 rounded-lg transition-all"
            title="Notifications"
          >
            <Bell className="h-4.5 w-4.5" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 h-4 w-4 bg-rose-500 rounded-full flex items-center justify-center text-[9px] font-extrabold text-white animate-pulse">
                {unreadCount}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-[#131a2d] border border-[#1e294b] rounded-xl shadow-2xl p-4 z-50 space-y-3">
              <div className="flex justify-between items-center pb-2 border-b border-[#1e294b]/60">
                <span className="text-xs font-bold text-white">System Notifications</span>
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllRead}
                    className="text-[10px] font-extrabold text-cyan-400 hover:text-cyan-300 uppercase tracking-wider"
                  >
                    Mark read
                  </button>
                )}
              </div>
              <div className="max-h-60 overflow-y-auto space-y-2">
                {recentEvents.length === 0 ? (
                  <div className="text-center py-6 text-xs text-slate-500">
                    No notifications available.
                  </div>
                ) : (
                  recentEvents.slice(0, 5).map((e) => (
                    <div
                      key={e.id}
                      className={cn(
                        "p-2 rounded-lg text-left text-xs transition-colors",
                        readEventIds.has(e.id) ? "bg-[#0b0f19]/30 text-slate-400" : "bg-[#0b0f19] text-white border-l-2 border-cyan-400"
                      )}
                    >
                      <div className="flex justify-between items-start">
                        <span className="font-bold truncate max-w-[150px]">{e.description}</span>
                        <span className={cn(
                          "text-[9px] px-1 rounded uppercase font-bold",
                          e.severity === "Critical" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        )}>
                          {e.severity}
                        </span>
                      </div>
                      <span className="text-[9px] text-slate-500 font-mono block mt-1">
                        {new Date(e.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Profile Dropdown Container */}
        <div className="relative">
          <button
            onClick={() => {
              setShowAdminMenu(!showAdminMenu);
              setShowNotifications(false);
            }}
            className="flex items-center gap-3 pl-2 border-l border-[#1e294b]/60 text-left hover:opacity-90 animate-in fade-in duration-200"
            title="User Profile Menu"
          >
            <div className="hidden sm:block text-right">
              <div className="text-xs font-bold text-white leading-tight">Admin</div>
              <div className="text-[10px] text-slate-500 font-semibold tracking-wider uppercase leading-tight">
                Administrator
              </div>
            </div>
            
            <div className="h-9 w-9 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <User className="h-5 w-5" />
            </div>
          </button>

          {showAdminMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-[#131a2d] border border-[#1e294b] rounded-xl shadow-2xl p-2 z-50 space-y-1">
              <div className="p-3 border-b border-[#1e294b]/60">
                <span className="text-xs font-bold text-white block">Active Account</span>
                <span className="text-[10px] text-slate-500 font-mono block">Role: Administrator</span>
              </div>
              <a
                href="/settings"
                onClick={() => setShowAdminMenu(false)}
                className="flex items-center gap-2 w-full text-left p-2.5 hover:bg-[#1b253b]/50 rounded-lg text-xs text-slate-300 hover:text-white transition-colors"
              >
                <SettingsIcon className="h-4 w-4 text-cyan-400" />
                Global Settings
              </a>
              <button
                onClick={() => {
                  setShowAdminMenu(false);
                  alert("Simulation System Logout successfully triggered.");
                }}
                className="flex items-center gap-2 w-full text-left p-2.5 hover:bg-rose-500/10 rounded-lg text-xs text-rose-400 hover:text-rose-300 transition-colors"
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
