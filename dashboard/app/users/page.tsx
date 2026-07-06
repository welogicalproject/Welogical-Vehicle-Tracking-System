"use client";

import { Users, Shield, Plus } from "lucide-react";
import { Button } from "../../components/ui/button";

export default function UsersPage() {
  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-wide">Users & Access Control</h2>
          <p className="text-slate-400 text-sm mt-1">
            Manage console operator accounts, drivers, and credential permissions.
          </p>
        </div>
        <Button variant="secondary" className="flex items-center gap-2">
          <Plus className="h-4 w-4" /> Add Operator
        </Button>
      </div>

      <div className="border border-[#1e294b]/60 rounded-xl bg-[#131a2d]/40 p-12 text-center max-w-2xl mx-auto mt-12">
        <div className="h-12 w-12 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400 mx-auto mb-4 border border-cyan-500/20">
          <Users className="h-6 w-6" />
        </div>
        <h3 className="text-lg font-bold text-white">Security Directory Connected</h3>
        <p className="text-slate-400 text-sm mt-2 max-w-md mx-auto">
          Currently running as single administrator operator dashboard. User directory integrations (OAuth / LDAP / Active Directory) are loaded dynamically.
        </p>
        <div className="mt-6 flex items-center gap-2 justify-center text-xs text-slate-400 bg-[#080d17]/50 border border-[#1e294b]/40 px-4 py-2 rounded-lg w-fit mx-auto">
          <Shield className="h-4 w-4 text-cyan-400" />
          <span>Security Role: Administrator (Full read/write permissions for configurations & commands)</span>
        </div>
      </div>
    </div>
  );
}
