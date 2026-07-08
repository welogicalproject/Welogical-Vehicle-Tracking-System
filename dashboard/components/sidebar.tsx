"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { 
  LayoutDashboard, 
  Car, 
  LineChart, 
  Database, 
  ChevronLeft, 
  ChevronRight,
  Activity,
  Bell,
  Settings,
  Send,
  MapPinned,
  Globe,
  FileText,
  Users,
  Sliders,
  Calendar,
  X
} from "lucide-react";
import { cn } from "../lib/utils";
import { api } from "../lib/api";
import { SystemStats } from "../types";

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [stats, setStats] = useState<SystemStats | null>(null);

  // Poll system stats for sidebar status footer
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await api.getStats();
        setStats(res);
      } catch (err) {
        console.warn("Failed to fetch sidebar system stats", err);
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  // Listen to mobile menu toggle event
  useEffect(() => {
    const handleToggle = () => setMobileOpen((prev) => !prev);
    window.addEventListener("toggle-sidebar-drawer", handleToggle);
    return () => window.removeEventListener("toggle-sidebar-drawer", handleToggle);
  }, []);

  // Auto-collapse sidebar on tablet screen widths on mount and window resize
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768 && window.innerWidth < 1024) {
        setCollapsed(true);
      } else if (window.innerWidth >= 1024) {
        setCollapsed(false);
      }
    };
    handleResize(); // Run on mount
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Close mobile drawer when route changes
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  const sections = [
    {
      title: "OVERVIEW",
      items: [
        { name: "Dashboard", href: "/", icon: LayoutDashboard },
        { name: "Map Tracking", href: "/tracking", icon: MapPinned },
        { name: "Analytics", href: "/analytics", icon: LineChart },
        { name: "Events", href: "/events", icon: Bell },
        { name: "Vehicles", href: "/vehicles", icon: Car },
        { name: "Trips", href: "/trips", icon: Calendar },
      ]
    },
    {
      title: "MANAGEMENT",
      items: [
        { name: "Command Queue", href: "/commands", icon: Send },
        { name: "Configurations", href: "/configurations", icon: Settings },
        { name: "Geofences", href: "/geofences", icon: Globe },
        { name: "Reports", href: "/reports", icon: FileText },
      ]
    },
    {
      title: "SYSTEM",
      items: [
        { name: "Device Health", href: "/health", icon: Activity },
        { name: "Users & Roles", href: "/users", icon: Users },
        { name: "Settings", href: "/settings", icon: Sliders },
        { name: "Database Explorer", href: "/explorer", icon: Database },
      ]
    }
  ];

  // Derive status details
  const totalVehicles = stats ? stats.total_vehicles : 0;
  const onlineCount = stats ? (stats.vehicles_online + stats.vehicles_idle) : 0;
  const isOnline = stats ? (stats.vehicles_online > 0 || stats.vehicles_idle > 0) : false;

  return (
    <>
      {/* Mobile Drawer Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 md:hidden transition-all duration-200"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        className={cn(
          "h-screen bg-[#0b0f19] border-r border-[#1e294b]/60 flex flex-col transition-all duration-300 shrink-0",
          // Sticky on tablet/desktop, overlay drawer on mobile
          "md:sticky md:top-0 md:z-30 md:translate-x-0",
          "fixed inset-y-0 left-0 z-50 transform",
          // Collapsed state on tablet/desktop vs mobile width
          collapsed ? "md:w-16" : "md:w-64",
          "w-64",
          // Open state toggle on mobile
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-[#1e294b]/60">
          {(!collapsed || mobileOpen) && (
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20">
                <MapPinned className="h-5 w-5 text-cyan-400" />
              </div>
              <div className="flex flex-col text-left">
                <span className="font-extrabold text-sm tracking-wider text-white">VTS</span>
                <span className="text-[10px] text-slate-500 font-semibold tracking-wider uppercase">Vehicle Tracking</span>
              </div>
            </div>
          )}
          {collapsed && !mobileOpen && (
            <div className="h-8 w-8 rounded-lg bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20 mx-auto">
              <MapPinned className="h-5 w-5 text-cyan-400" />
            </div>
          )}
          
          {mobileOpen ? (
            <button
              onClick={() => setMobileOpen(false)}
              className="md:hidden p-1.5 hover:bg-[#1e294b]/60 rounded-lg text-slate-400 hover:text-white transition-colors"
            >
              <X size={16} />
            </button>
          ) : (
            !collapsed && (
              <button
                onClick={() => setCollapsed(true)}
                className="hidden md:block p-1.5 hover:bg-[#1e294b]/60 rounded-lg text-slate-400 hover:text-white transition-colors"
              >
                <ChevronLeft size={16} />
              </button>
            )
          )}
        </div>

        {/* Collapse Trigger on collapsed mode */}
        {collapsed && !mobileOpen && (
          <div className="hidden md:flex justify-center py-2 border-b border-[#1e294b]/40">
            <button
              onClick={() => setCollapsed(false)}
              className="p-1.5 hover:bg-[#1e294b]/60 rounded-lg text-slate-400 hover:text-white transition-colors"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        )}

        {/* Nav Menu */}
        <div className="flex-1 overflow-y-auto py-4 px-3 space-y-4 select-none">
          {sections.map((section) => (
            <div key={section.title} className="space-y-1">
              {(!collapsed || mobileOpen) && (
                <h3 className="px-3 text-[10px] font-bold text-slate-500 tracking-wider uppercase mb-1 text-left">
                  {section.title}
                </h3>
              )}
              <nav className="space-y-0.5">
                {section.items.map((item) => {
                  const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      title={(collapsed && !mobileOpen) ? item.name : undefined}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold tracking-wide transition-all group relative",
                        isActive 
                          ? "bg-[#132238] text-cyan-400 border border-cyan-500/20" 
                          : "text-slate-400 hover:bg-[#131a2d]/60 hover:text-slate-200"
                      )}
                    >
                      <Icon 
                        className={cn(
                          "h-4 w-4 shrink-0 transition-colors",
                          isActive ? "text-cyan-400" : "text-slate-400 group-hover:text-slate-300"
                        )} 
                      />
                      {(!collapsed || mobileOpen) && <span>{item.name}</span>}
                      {isActive && (
                        <span className="absolute left-0 top-1/4 bottom-1/4 w-0.5 bg-cyan-400 rounded-r" />
                      )}
                    </Link>
                  );
                })}
              </nav>
            </div>
          ))}
        </div>

        {/* Footer Info */}
        <div className="p-4 border-t border-[#1e294b]/60 bg-[#080d17]/50">
          {(!collapsed || mobileOpen) ? (
            <div className="space-y-2 text-left">
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>Connected Devices</span>
                <span className="font-bold text-white font-mono">{stats ? `${onlineCount}/${totalVehicles}` : "0/0"}</span>
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>System Status</span>
                <span className="flex items-center gap-1.5 font-bold text-white">
                  <span className={cn(
                    "h-1.5 w-1.5 rounded-full animate-pulse", 
                    isOnline ? "bg-emerald-500" : "bg-red-500"
                  )} />
                  {isOnline ? "Online" : "Offline"}
                </span>
              </div>
              <div className="pt-1 border-t border-[#1e294b]/20 flex items-center justify-between text-[10px] text-slate-500">
                <span>Version</span>
                <span className="font-mono">VTS v1.0.0</span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <span className={cn(
                "h-2 w-2 rounded-full animate-pulse", 
                isOnline ? "bg-emerald-500" : "bg-red-500"
              )} title={isOnline ? "System Online" : "System Offline"} />
              <span className="text-[9px] text-slate-500 font-mono">v1.0</span>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
  );
}

