"use client"

import { useRef, useEffect, useState, useCallback } from "react"
import { useVirtualizer } from "@tanstack/react-virtual"
import { VoiceCard } from "@/components/voice/VoiceCard"
import { Skeleton } from "@/components/ui/skeleton"
import type { VoiceProfile } from "@/types"

interface VoiceGridProps {
  voices: VoiceProfile[]
  loading?: boolean
  selectedId?: string | null
  onSelect?: (voice: VoiceProfile) => void
  onOpenDetails?: (voice: VoiceProfile) => void
  onEdit?: (voice: VoiceProfile) => void
  onDelete?: (voice: VoiceProfile) => void
  onToggleFavorite?: (voice: VoiceProfile) => void
}

const CARD_HEIGHT_ESTIMATE = 140
const OVERSCAN = 3

function useColumnCount(containerRef: React.RefObject<HTMLDivElement | null>) {
  const [columns, setColumns] = useState(3)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const calc = () => {
      const width = el.offsetWidth
      if (width >= 1280) setColumns(3)
      else if (width >= 640) setColumns(2)
      else setColumns(1)
    }

    calc()
    const observer = new ResizeObserver(calc)
    observer.observe(el)
    return () => observer.disconnect()
  }, [containerRef])

  return columns
}

export function VoiceGrid({
  voices,
  loading,
  selectedId,
  onSelect,
  onOpenDetails,
  onEdit,
  onDelete,
  onToggleFavorite,
}: VoiceGridProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const columns = useColumnCount(containerRef)

  const rowCount = Math.ceil(voices.length / columns)

  const virtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: useCallback(() => scrollRef.current, []),
    estimateSize: () => CARD_HEIGHT_ESTIMATE,
    overscan: OVERSCAN,
  })

  if (loading) {
    return (
      <div ref={containerRef} className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-[124px] w-full rounded-xl" />
        ))}
      </div>
    )
  }

  if (voices.length === 0) return null

  return (
    <div ref={containerRef}>
      <div
        ref={scrollRef}
        className="overflow-auto"
        style={{ maxHeight: "calc(100vh - 380px)" }}
      >
        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            position: "relative",
          }}
        >
          {virtualizer.getVirtualItems().map((virtualRow) => {
            const rowIndex = virtualRow.index
            const startIdx = rowIndex * columns
            const rowItems = voices.slice(startIdx, startIdx + columns)

            return (
              <div
                key={virtualRow.key}
                data-index={virtualRow.index}
                ref={virtualizer.measureElement}
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  width: "100%",
                  transform: `translateY(${virtualRow.start}px)`,
                }}
                className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4"
              >
                {rowItems.map((voice) => (
                  <VoiceCard
                    key={voice.id}
                    voice={voice}
                    selected={selectedId === voice.id}
                    onSelect={onSelect}
                    onOpenDetails={onOpenDetails}
                    onEdit={onEdit}
                    onDelete={onDelete}
                    onToggleFavorite={onToggleFavorite}
                  />
                ))}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
