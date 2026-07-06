import React, { useMemo } from "react";
import { Search } from "lucide-react";
import { Event } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Input } from "../ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { Button } from "../ui/button";
import { SeverityBadge } from "./VehicleBadges";
import { formatDate } from "../../lib/date";

interface EventsTabProps {
  events: Event[];
  eventSearch: string;
  setEventSearch: (val: string) => void;
  eventPage: number;
  setEventPage: (updater: number | ((prev: number) => number)) => void;
}

export function EventsTab({
  events,
  eventSearch,
  setEventSearch,
  eventPage,
  setEventPage,
}: EventsTabProps) {
  const filteredEvents = useMemo(() => {
    const term = eventSearch.toLowerCase();
    return events.filter(
      (event) =>
        event.event_type.toLowerCase().includes(term) ||
        event.description.toLowerCase().includes(term) ||
        event.severity.toLowerCase().includes(term)
    );
  }, [events, eventSearch]);

  const pagedEvents = useMemo(() => {
    return filteredEvents.slice(eventPage * 10, eventPage * 10 + 10);
  }, [filteredEvents, eventPage]);

  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
      <CardHeader className="gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle className="text-white text-sm">Event Log</CardTitle>
        </div>
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
          <Input
            value={eventSearch}
            onChange={(event) => {
              setEventSearch(event.target.value);
              setEventPage(0);
            }}
            placeholder="Search events..."
            className="pl-9 bg-[#0b0f19] border-[#1e294b]"
          />
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-[#1e294b]/40 hover:bg-transparent">
              <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
                Time
              </TableHead>
              <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
                Event Type
              </TableHead>
              <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
                Severity
              </TableHead>
              <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
                Description
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {pagedEvents.map((event) => (
              <TableRow
                key={event.id}
                className="border-[#1e294b]/20 hover:bg-[#131a2d]/20 transition-colors"
              >
                <TableCell className="text-xs text-slate-400">
                  {formatDate(event.created_at)}
                </TableCell>
                <TableCell className="font-semibold text-cyan-300 text-xs">
                  {event.event_type}
                </TableCell>
                <TableCell>
                  <SeverityBadge severity={event.severity} />
                </TableCell>
                <TableCell className="text-xs text-slate-300">{event.description}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {pagedEvents.length === 0 && (
          <div className="py-8 text-center text-xs text-slate-400">No events logged</div>
        )}
        <div className="mt-4 flex justify-end gap-2">
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={eventPage === 0}
            onClick={() => setEventPage((page) => Math.max(0, page - 1))}
          >
            Previous
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={(eventPage + 1) * 10 >= filteredEvents.length}
            onClick={() => setEventPage((page) => page + 1)}
          >
            Next
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
