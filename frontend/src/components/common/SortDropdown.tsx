"use client"

import { ArrowDownAZ, ArrowUpAZ, ListOrdered } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import type { SortField } from "@/types"

const SORT_OPTIONS: { value: SortField; label: string }[] = [
  { value: "last_used_at", label: "Last Used" },
  { value: "created_at", label: "Created Date" },
  { value: "name", label: "Name" },
  { value: "language", label: "Language" },
  { value: "usage_count", label: "Usage Count" },
]

interface SortDropdownProps {
  sortBy: SortField
  sortDir: "asc" | "desc"
  onSortByChange: (value: SortField) => void
  onSortDirChange: (value: "asc" | "desc") => void
}

export function SortDropdown({ sortBy, sortDir, onSortByChange, onSortDirChange }: SortDropdownProps) {
  const current = SORT_OPTIONS.find((o) => o.value === sortBy)
  return (
    <div className="flex items-center gap-1">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="gap-2">
            <ListOrdered className="h-4 w-4" />
            {current?.label ?? "Sort"}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuRadioGroup value={sortBy} onValueChange={(v) => onSortByChange(v as SortField)}>
            {SORT_OPTIONS.map((opt) => (
              <DropdownMenuRadioItem key={opt.value} value={opt.value}>
                {opt.label}
              </DropdownMenuRadioItem>
            ))}
          </DropdownMenuRadioGroup>
          <DropdownMenuSeparator />
          <DropdownMenuRadioGroup value={sortDir} onValueChange={(v) => onSortDirChange(v as "asc" | "desc")}>
            <DropdownMenuRadioItem value="desc">
              <ArrowDownAZ className="h-4 w-4 mr-2" /> Descending
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="asc">
              <ArrowUpAZ className="h-4 w-4 mr-2" /> Ascending
            </DropdownMenuRadioItem>
          </DropdownMenuRadioGroup>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
