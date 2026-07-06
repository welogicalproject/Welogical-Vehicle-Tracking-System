import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "../ui/button";

interface ExplorerPaginationProps {
  page: number;
  onPrevPage: () => void;
  onNextPage: () => void;
  nextDisabled: boolean;
}

export function ExplorerPagination({
  page,
  onPrevPage,
  onNextPage,
  nextDisabled,
}: ExplorerPaginationProps) {
  return (
    <div className="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={onPrevPage}
        disabled={page === 1}
        className="border-[#1e294b]/60 hover:bg-[#1e294b] text-xs"
      >
        <ChevronLeft size={15} /> Prev
      </Button>
      <span className="text-xs text-white font-bold font-mono bg-[#0b0f19]/30 px-3 py-1.5 rounded-lg border border-[#1e294b]/60">
        Page {page}
      </span>
      <Button
        variant="outline"
        size="sm"
        onClick={onNextPage}
        disabled={nextDisabled}
        className="border-[#1e294b]/60 hover:bg-[#1e294b] text-xs"
      >
        Next <ChevronRight size={15} />
      </Button>
    </div>
  );
}
