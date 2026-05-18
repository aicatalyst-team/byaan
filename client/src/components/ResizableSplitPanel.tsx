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
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth)
  const isDraggingRef = useRef(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const leftPanelRef = useRef<HTMLDivElement>(null)
  const rightPanelRef = useRef<HTMLDivElement>(null)
  const currentWidthRef = useRef(defaultLeftWidth)

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    isDraggingRef.current = true
    if (leftPanelRef.current) leftPanelRef.current.style.transition = 'none'
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [])

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDraggingRef.current || !containerRef.current) return

      const containerRect = containerRef.current.getBoundingClientRect()
      const mouseX = e.clientX - containerRect.left
      const newLeftWidth = (mouseX / containerRect.width) * 100
      const clamped = Math.min(Math.max(newLeftWidth, minLeftWidth), maxLeftWidth)

      currentWidthRef.current = clamped

      if (leftPanelRef.current) leftPanelRef.current.style.width = `${clamped}%`
    },
    [minLeftWidth, maxLeftWidth]
  )

  const handleMouseUp = useCallback(() => {
    if (!isDraggingRef.current) return
    isDraggingRef.current = false
    if (leftPanelRef.current) leftPanelRef.current.style.transition = ''
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    setLeftWidth(currentWidthRef.current)
  }, [])

  useEffect(() => {
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [handleMouseMove, handleMouseUp])

  return (
    <div ref={containerRef} className="flex h-full w-full relative">
      <div
        ref={leftPanelRef}
        style={{
          width: isRightPanelOpen ? `${leftWidth}%` : '100%',
          transition: 'width 300ms cubic-bezier(0.4, 0, 0.2, 1)',
        }}
        className="flex-shrink-0 h-full overflow-hidden"
      >
        {leftPanel}
      </div>

      <div
        onMouseDown={handleMouseDown}
        style={{ display: isRightPanelOpen ? undefined : 'none' }}
        className="w-1 bg-[#2a2a2a] hover:bg-[#404040] active:bg-[#4a9eff] cursor-col-resize flex-shrink-0 relative group transition-colors"
      >
        <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-1 group-hover:w-1 transition-all">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="w-0.5 h-1 bg-gray-500 rounded-full"></div>
            <div className="w-0.5 h-1 bg-gray-500 rounded-full"></div>
            <div className="w-0.5 h-1 bg-gray-500 rounded-full"></div>
          </div>
        </div>
      </div>

      <div
        ref={rightPanelRef}
        className="h-full overflow-hidden"
        style={{
          flex: isRightPanelOpen ? '1' : '0 0 0px',
          width: isRightPanelOpen ? undefined : 0,
          pointerEvents: isRightPanelOpen ? 'auto' : 'none',
          transition: 'flex 300ms cubic-bezier(0.4, 0, 0.2, 1), width 300ms cubic-bezier(0.4, 0, 0.2, 1)',
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
  const isDraggingRef = useRef(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const topPanelRef = useRef<HTMLDivElement>(null)
  const currentHeightRef = useRef(defaultTopHeight)

  useEffect(() => {
    setTopHeight(defaultTopHeight)
    currentHeightRef.current = defaultTopHeight
  }, [defaultTopHeight])

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    isDraggingRef.current = true
    if (topPanelRef.current) topPanelRef.current.style.transition = 'none'
    document.body.style.cursor = 'row-resize'
    document.body.style.userSelect = 'none'
  }, [])

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDraggingRef.current || !containerRef.current) return

      const containerRect = containerRef.current.getBoundingClientRect()
      const mouseY = e.clientY - containerRect.top
      const newTopHeight = (mouseY / containerRect.height) * 100
      const clamped = Math.min(Math.max(newTopHeight, minTopHeight), maxTopHeight)

      currentHeightRef.current = clamped

      if (topPanelRef.current) topPanelRef.current.style.height = `${clamped}%`
    },
    [minTopHeight, maxTopHeight]
  )

  const handleMouseUp = useCallback(() => {
    if (!isDraggingRef.current) return
    isDraggingRef.current = false
    if (topPanelRef.current) topPanelRef.current.style.transition = ''
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    setTopHeight(currentHeightRef.current)
  }, [])

  useEffect(() => {
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [handleMouseMove, handleMouseUp])

  return (
    <div ref={containerRef} className="flex flex-col h-full w-full relative">
      <div
        ref={topPanelRef}
        style={{ height: `${topHeight}%` }}
        className="flex-shrink-0 w-full overflow-hidden"
      >
        {topPanel}
      </div>

      <div
        onMouseDown={handleMouseDown}
        className="h-1 bg-[#232323] hover:bg-[#404040] active:bg-[#4a9eff] cursor-row-resize flex-shrink-0 relative group transition-colors"
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
      >
        {bottomPanel}
      </div>
    </div>
  )
}
