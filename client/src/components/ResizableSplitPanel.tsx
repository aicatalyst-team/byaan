import React, { useState, useRef, useEffect, useCallback } from 'react'

interface ResizableSplitPanelProps {
  leftPanel: React.ReactNode
  rightPanel: React.ReactNode
  defaultLeftWidth?: number // percentage (0-100)
  minLeftWidth?: number // percentage
  maxLeftWidth?: number // percentage
  isRightPanelOpen?: boolean
}

interface ResizableVerticalPanelProps {
  topPanel: React.ReactNode
  bottomPanel: React.ReactNode
  defaultTopHeight?: number // percentage (0-100)
  minTopHeight?: number // percentage
  maxTopHeight?: number // percentage
}

export function ResizableSplitPanel({
  leftPanel,
  rightPanel,
  defaultLeftWidth = 40,
  minLeftWidth = 25,
  maxLeftWidth = 60,
  isRightPanelOpen = true,
}: ResizableSplitPanelProps) {
  const clampLeftWidth = useCallback(
    (width: number) => Math.min(Math.max(width, minLeftWidth), maxLeftWidth),
    [minLeftWidth, maxLeftWidth]
  )
  const [leftWidth, setLeftWidth] = useState(() => clampLeftWidth(defaultLeftWidth))
  const [isDragging, setIsDragging] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const rafIdRef = useRef<number | null>(null)
  const pendingWidthRef = useRef<number | null>(null)

  useEffect(() => {
    setLeftWidth((currentWidth) => clampLeftWidth(currentWidth))
  }, [clampLeftWidth])

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!containerRef.current) return

      const container = containerRef.current
      const containerRect = container.getBoundingClientRect()
      const mouseX = e.clientX - containerRect.left
      const newLeftWidth = (mouseX / containerRect.width) * 100

      // Clamp the width between min and max
      const clampedWidth = clampLeftWidth(newLeftWidth)

      // Store the pending width update
      pendingWidthRef.current = clampedWidth

      // Cancel any pending animation frame
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current)
      }

      rafIdRef.current = requestAnimationFrame(() => {
        if (pendingWidthRef.current !== null) {
          setLeftWidth(pendingWidthRef.current)
          pendingWidthRef.current = null
        }
        rafIdRef.current = null
      })
    },
    [clampLeftWidth]
  )

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
    if (rafIdRef.current !== null) {
      cancelAnimationFrame(rafIdRef.current)
      rafIdRef.current = null
    }
    if (pendingWidthRef.current !== null) {
      setLeftWidth(pendingWidthRef.current)
      pendingWidthRef.current = null
    }
  }, [])

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'

      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
        if (rafIdRef.current !== null) {
          cancelAnimationFrame(rafIdRef.current)
          rafIdRef.current = null
        }
      }
    }
  }, [isDragging, handleMouseMove, handleMouseUp])

  return (
    <div ref={containerRef} className="resizable-split-panel flex h-full w-full min-w-0 relative">
      {/* Left Panel */}
      <div
        style={{
          flexGrow: isRightPanelOpen ? 0 : 1,
          flexShrink: isRightPanelOpen ? 0 : 1,
          flexBasis: isRightPanelOpen ? `${leftWidth}%` : '100%',
          maxWidth: isRightPanelOpen ? `${maxLeftWidth}%` : '100%',
          minWidth: isRightPanelOpen ? `${minLeftWidth}%` : 0,
          transition: !isDragging
            ? 'flex-basis var(--split-panel-duration) var(--split-panel-easing), max-width var(--split-panel-duration) var(--split-panel-easing), min-width var(--split-panel-duration) var(--split-panel-easing)'
            : 'none',
          willChange: isDragging ? 'flex-basis' : 'auto',
          pointerEvents: isDragging ? 'none' : 'auto',
          contain: isDragging ? 'layout style paint' : 'none',
        }}
        className="flex-shrink-0 h-full overflow-hidden"
      >
        {leftPanel}
      </div>

      {/* Resizable Divider */}
      <div
        onMouseDown={handleMouseDown}
        aria-label="Resize preview"
        role="separator"
        style={{
          flexBasis: isRightPanelOpen ? 4 : 0,
          width: isRightPanelOpen ? 4 : 0,
          opacity: isRightPanelOpen ? 1 : 0,
          pointerEvents: isRightPanelOpen ? 'auto' : 'none',
          transition: !isDragging
            ? 'flex-basis var(--split-panel-duration) var(--split-panel-easing), width var(--split-panel-duration) var(--split-panel-easing), opacity 160ms ease'
            : 'none',
        }}
        className={`bg-[#2a2a2a] hover:bg-[#404040] cursor-col-resize flex-shrink-0 relative group overflow-hidden ${
          isDragging ? 'bg-[#4a9eff]' : 'transition-colors'
        }`}
      >
        {/* Drag handle indicator */}
        <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-1 group-hover:w-1 transition-all">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="w-0.5 h-1 bg-gray-500 rounded-full"></div>
            <div className="w-0.5 h-1 bg-gray-500 rounded-full"></div>
            <div className="w-0.5 h-1 bg-gray-500 rounded-full"></div>
          </div>
        </div>
      </div>

      {/* Right Panel */}
      <div
        className="h-full overflow-hidden"
        style={{
          flexGrow: isRightPanelOpen ? 1 : 0,
          flexShrink: 1,
          flexBasis: 0,
          minWidth: 0,
          opacity: isRightPanelOpen ? 1 : 0,
          pointerEvents: isRightPanelOpen ? 'auto' : 'none',
          transition: !isDragging
            ? 'opacity 180ms ease'
            : 'none',
          willChange: isDragging ? 'flex-basis' : 'auto',
          contain: isDragging ? 'layout style paint' : 'none',
        }}
      >
        {rightPanel}
      </div>
    </div>
  )
}

export function ResizableVerticalPanel({
  topPanel,
  bottomPanel,
  defaultTopHeight = 40,
  minTopHeight = 20,
  maxTopHeight = 70,
}: ResizableVerticalPanelProps) {
  const [topHeight, setTopHeight] = useState(defaultTopHeight)
  const [isDragging, setIsDragging] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const rafIdRef = useRef<number | null>(null)
  const pendingHeightRef = useRef<number | null>(null)

  // Sync height when defaultTopHeight changes
  useEffect(() => {
    setTopHeight(defaultTopHeight)
  }, [defaultTopHeight])

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!containerRef.current) return

      const container = containerRef.current
      const containerRect = container.getBoundingClientRect()
      const mouseY = e.clientY - containerRect.top
      const newTopHeight = (mouseY / containerRect.height) * 100

      const clampedHeight = Math.min(Math.max(newTopHeight, minTopHeight), maxTopHeight)

      pendingHeightRef.current = clampedHeight

      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current)
      }

      rafIdRef.current = requestAnimationFrame(() => {
        if (pendingHeightRef.current !== null) {
          setTopHeight(pendingHeightRef.current)
          pendingHeightRef.current = null
        }
        rafIdRef.current = null
      })
    },
    [minTopHeight, maxTopHeight]
  )

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
    if (rafIdRef.current !== null) {
      cancelAnimationFrame(rafIdRef.current)
      rafIdRef.current = null
    }
    if (pendingHeightRef.current !== null) {
      setTopHeight(pendingHeightRef.current)
      pendingHeightRef.current = null
    }
  }, [])

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'row-resize'
      document.body.style.userSelect = 'none'

      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
        if (rafIdRef.current !== null) {
          cancelAnimationFrame(rafIdRef.current)
          rafIdRef.current = null
        }
      }
    }
  }, [isDragging, handleMouseMove, handleMouseUp])

  return (
    <div ref={containerRef} className="flex flex-col h-full w-full relative">
      <div
        style={{
          height: `${topHeight}%`,
          willChange: isDragging ? 'height' : 'auto',
          pointerEvents: isDragging ? 'none' : 'auto',
          contain: isDragging ? 'layout style paint' : 'none'
        }}
        className="flex-shrink-0 w-full overflow-hidden"
      >
        {topPanel}
      </div>

      <div
        onMouseDown={handleMouseDown}
        className={`h-1 bg-[#232323] hover:bg-[#404040] cursor-row-resize flex-shrink-0 relative group ${
          isDragging ? 'bg-[#4a9eff]' : 'transition-colors'
        }`}
      >
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-1 group-hover:h-1 transition-all">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="w-1 h-0.5 bg-gray-500 rounded-full"></div>
            <div className="w-1 h-0.5 bg-gray-500 rounded-full"></div>
            <div className="w-1 h-0.5 bg-gray-500 rounded-full"></div>
          </div>
        </div>
      </div>

      <div
        className="flex-1 w-full overflow-hidden"
        style={{
          willChange: isDragging ? 'height' : 'auto',
          pointerEvents: isDragging ? 'none' : 'auto',
          contain: isDragging ? 'layout style paint' : 'none'
        }}
      >
        {bottomPanel}
      </div>
    </div>
  )
}
