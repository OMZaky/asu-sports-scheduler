"use client";

import { useState, useEffect } from "react";

const DAYS = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"];
// Football tournaments usually happen in evenings/weekends, let's allow 10 AM to 8 PM for now.
const START_HOUR = 10;
const END_HOUR = 20;

export interface Slot {
  day: string;
  time: string; // e.g. "16:00", "16:30"
}

export default function TimeGrid({ onChange }: { onChange: (selected: Slot[]) => void }) {
  const [selectedSlots, setSelectedSlots] = useState<Set<string>>(new Set());
  const [isDragging, setIsDragging] = useState(false);
  const [dragMode, setDragMode] = useState<"select" | "deselect" | null>(null);

  // Generate 30-min intervals
  const times: string[] = [];
  for (let i = START_HOUR; i <= END_HOUR; i++) {
    times.push(`${i}:00`);
    if (i !== END_HOUR) times.push(`${i}:30`);
  }

  const getSlotId = (day: string, time: string) => `${day}-${time}`;

  const toggleSlot = (day: string, time: string, mode: "select" | "deselect") => {
    const id = getSlotId(day, time);
    setSelectedSlots((prev) => {
      const next = new Set(prev);
      if (mode === "select") next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const handleMouseDown = (day: string, time: string) => {
    setIsDragging(true);
    const id = getSlotId(day, time);
    const mode = selectedSlots.has(id) ? "deselect" : "select";
    setDragMode(mode);
    toggleSlot(day, time, mode);
  };

  const handleMouseEnter = (day: string, time: string) => {
    if (isDragging && dragMode) {
      toggleSlot(day, time, dragMode);
    }
  };

  const handleMouseUp = () => {
    if (isDragging) {
      setIsDragging(false);
      setDragMode(null);
    }
  };

  const handleTouchStart = (day: string, time: string) => {
    setIsDragging(true);
    const id = getSlotId(day, time);
    const mode = selectedSlots.has(id) ? "deselect" : "select";
    setDragMode(mode);
    toggleSlot(day, time, mode);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDragging || !dragMode) return;
    
    // On mobile, dragging across slots should select them instead of scrolling
    if (e.cancelable) {
      e.preventDefault();
    }
    
    const touch = e.touches[0];
    const element = document.elementFromPoint(touch.clientX, touch.clientY);
    
    if (element) {
      const day = element.getAttribute("data-day");
      const time = element.getAttribute("data-time");
      if (day && time) {
        toggleSlot(day, time, dragMode);
      }
    }
  };

  // Sync to parent without loop
  useEffect(() => {
    if (!isDragging) {
      const slots = Array.from(selectedSlots).map(id => {
        const [day, time] = id.split("-");
        return { day, time };
      });
      onChange(slots);
    }
  }, [isDragging, selectedSlots]); // Intentionally omitting onChange to prevent infinite loops if not memoized

  useEffect(() => {
    window.addEventListener("mouseup", handleMouseUp);
    window.addEventListener("touchend", handleMouseUp);
    return () => {
      window.removeEventListener("mouseup", handleMouseUp);
      window.removeEventListener("touchend", handleMouseUp);
    };
  }, [isDragging]);

  const formatTime12 = (time24: string) => {
    const [h, m] = time24.split(":");
    const hour = parseInt(h, 10);
    const ampm = hour >= 12 ? "PM" : "AM";
    const hour12 = hour % 12 || 12;
    return `${hour12}:${m} ${ampm}`;
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-secondary rounded-2xl p-6 border border-border shadow-2xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Select Available Times</h2>
          <p className="text-sm text-muted mt-1">Click and drag to select your free slots.</p>
        </div>
      </div>

      {/* DESKTOP VIEW: Full Grid */}
      <div className="hidden md:block overflow-x-auto pb-4">
        <div className="min-w-[700px] select-none">
          {/* Header Row */}
          <div className="grid grid-cols-7 gap-2 mb-3">
            <div className="w-24"></div>
            {DAYS.map(day => (
              <div key={day} className="text-center font-bold text-sm text-foreground bg-background/50 rounded-lg py-2 uppercase tracking-widest shadow-sm border border-border/50">
                {day.substring(0, 3)}
              </div>
            ))}
          </div>

          {/* Grid Body */}
          <div className="flex flex-col gap-1">
            {times.map((time, i) => (
              <div key={time} className="grid grid-cols-7 gap-2">
                {/* Time Label */}
                <div className="w-24 text-right pr-3 text-sm font-bold text-primary drop-shadow-[0_0_10px_rgba(16,185,129,0.8)] flex items-center justify-end tracking-wide whitespace-nowrap">
                  {formatTime12(time)}
                </div>

                {/* Day Slots */}
                {DAYS.map(day => {
                  const id = getSlotId(day, time);
                  const isSelected = selectedSlots.has(id);

                  return (
                    <div
                      key={id}
                      data-day={day}
                      data-time={time}
                      onMouseDown={() => handleMouseDown(day, time)}
                      onMouseEnter={() => handleMouseEnter(day, time)}
                      onTouchStart={() => handleTouchStart(day, time)}
                      onTouchMove={handleTouchMove}
                      className={`
                        h-10 rounded-md transition-all duration-150 cursor-pointer border border-border/50
                        ${isSelected
                          ? 'bg-primary border-primary-hover shadow-[0_0_12px_rgba(16,185,129,0.4)] scale-[1.02]'
                          : 'bg-background hover:bg-border hover:scale-105 touch-none'}
                      `}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* MOBILE VIEW: Day Stack */}
      <div className="block md:hidden space-y-6 pb-4">
        {DAYS.map(day => (
          <div key={day} className="bg-background/50 rounded-xl p-4 sm:p-5 border border-border/50 shadow-sm">
            <h3 className="font-bold text-xl mb-4 text-primary tracking-wide drop-shadow-[0_0_5px_rgba(16,185,129,0.5)]">{day}</h3>
            <div className="grid grid-cols-3 gap-2">
              {times.map(time => {
                const id = getSlotId(day, time);
                const isSelected = selectedSlots.has(id);
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => toggleSlot(day, time, isSelected ? "deselect" : "select")}
                    className={`
                      py-2 px-1 text-xs sm:text-sm font-semibold rounded-lg border transition-all duration-150 text-center w-full
                      ${isSelected 
                        ? 'bg-primary border-primary text-white shadow-[0_0_10px_rgba(16,185,129,0.6)] scale-[1.02]' 
                        : 'bg-background border-border text-muted hover:bg-border hover:text-foreground'}
                    `}
                  >
                    {formatTime12(time)}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 flex justify-end items-center gap-6 pt-4 border-t border-border">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 bg-background border border-border rounded"></div>
          <span className="text-sm font-medium text-muted">Busy</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 bg-primary rounded shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
          <span className="text-sm font-medium text-foreground">Available</span>
        </div>
      </div>
    </div>
  );
}
