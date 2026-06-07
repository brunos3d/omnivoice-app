"use client"

import { ChevronDown, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"

interface PaginationControlsProps {
  currentCount: number
  hasNextPage: boolean
  isFetchingNextPage: boolean
  onLoadMore: () => void
}

export function PaginationControls({
  currentCount,
  hasNextPage,
  isFetchingNextPage,
  onLoadMore,
}: PaginationControlsProps) {
  return (
    <div className="flex flex-col items-center gap-3 pt-2 pb-6">
      <p className="text-xs text-muted-foreground">
        Showing{" "}
        <span className="font-medium text-foreground">{currentCount}</span> voice
        {currentCount !== 1 ? "s" : ""}
      </p>
      {hasNextPage && (
        <Button
          variant="outline"
          size="sm"
          className="gap-2"
          onClick={onLoadMore}
          disabled={isFetchingNextPage}
        >
          {isFetchingNextPage ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
          {isFetchingNextPage ? "Loading…" : "Load more"}
        </Button>
      )}
    </div>
  )
}
