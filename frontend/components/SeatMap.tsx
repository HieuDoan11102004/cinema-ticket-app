"use client";

import { useState, useCallback, useEffect } from "react";
import Button from "@/components/ui/Button";

interface Seat {
  id: number;
  showtime_id: number;
  seat_label: string;
  status: "available" | "held" | "booked";
}

interface SeatMapProps {
  seats: Seat[];
  showtimeId: number;
  basePrice: number;
  onSelectionChange: (selectedSeats: Seat[], totalPrice: number) => void;
  cinemaRoom: string;
}

export default function SeatMap({
  seats,
  showtimeId,
  basePrice,
  onSelectionChange,
  cinemaRoom,
}: SeatMapProps) {
  const [selectedSeats, setSelectedSeats] = useState<Set<number>>(new Set());

  // Organize seats by row (first character is the row label)
  const seatsByRow = seats.reduce((acc, seat) => {
    const row = seat.seat_label.charAt(0);
    if (!acc[row]) {
      acc[row] = [];
    }
    acc[row].push(seat);
    return acc;
  }, {} as Record<string, Seat[]>);

  // Sort seats within each row by number
  Object.keys(seatsByRow).forEach((row) => {
    seatsByRow[row].sort((a, b) => {
      const numA = parseInt(a.seat_label.slice(1));
      const numB = parseInt(b.seat_label.slice(1));
      return numA - numB;
    });
  });

  // Get sorted row labels
  const sortedRows = Object.keys(seatsByRow).sort();

  const handleSeatClick = useCallback((seat: Seat) => {
    if (seat.status !== "available") return;

    setSelectedSeats((prev) => {
      const newSelected = new Set(prev);
      if (newSelected.has(seat.id)) {
        newSelected.delete(seat.id);
      } else {
        newSelected.add(seat.id);
      }
      return newSelected;
    });
  }, []);

  // Update parent when selection changes
  useEffect(() => {
    const selected = seats.filter((s) => selectedSeats.has(s.id));
    onSelectionChange(selected, selected.length * basePrice);
  }, [selectedSeats, seats, basePrice, onSelectionChange]);

  const getSeatClass = (seat: Seat) => {
    const base =
      "w-10 h-10 rounded-lg flex items-center justify-center text-sm font-medium transition-all cursor-pointer";

    if (seat.status === "booked") {
      return `${base} bg-[#9A9BA3]/30 text-[#9A9BA3]/50 cursor-not-allowed`;
    }
    if (seat.status === "held") {
      return `${base} bg-yellow-500/30 text-yellow-500 cursor-not-allowed`;
    }
    if (selectedSeats.has(seat.id)) {
      return `${base} bg-[#D98639] text-white ring-2 ring-[#D98639] ring-offset-2 ring-offset-[#1E1F27]`;
    }
    return `${base} bg-[#2A2B33] border border-[#3A3B44] hover:border-[#D98639] hover:bg-[#D98639]/20`;
  };

  const clearSelection = () => {
    setSelectedSeats(new Set());
  };

  return (
    <div className="space-y-6">
      {/* Screen indicator */}
      <div className="relative">
        <div className="h-1 bg-gradient-to-r from-transparent via-[#D98639]/50 to-transparent rounded-full" />
        <p className="text-center text-[#9A9BA3] text-sm mt-2">SCREEN</p>
      </div>

      {/* Cinema Room Label */}
      <div className="text-center">
        <span className="text-lg font-semibold text-white">{cinemaRoom}</span>
      </div>

      {/* Legend */}
      <div className="flex justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-[#2A2B33] border border-[#3A3B44]" />
          <span className="text-[#9A9BA3]">Available</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-[#D98639]" />
          <span className="text-[#9A9BA3]">Selected</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-[#9A9BA3]/30" />
          <span className="text-[#9A9BA3]">Booked</span>
        </div>
      </div>

      {/* Seat Grid */}
      <div className="overflow-x-auto pb-4">
        <div className="min-w-max space-y-2">
          {sortedRows.map((row) => (
            <div key={row} className="flex items-center gap-2">
              <span className="w-6 text-center text-[#9A9BA3] font-medium">
                {row}
              </span>
              <div className="flex gap-2">
                {seatsByRow[row].map((seat) => (
                  <button
                    key={seat.id}
                    onClick={() => handleSeatClick(seat)}
                    className={getSeatClass(seat)}
                    disabled={seat.status !== "available"}
                    title={
                      seat.status === "available"
                        ? seat.seat_label
                        : `${seat.seat_label} (${seat.status})`
                    }
                  >
                    {seat.seat_label.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Selection Summary */}
      <div className="bg-[#2A2B33] rounded-xl p-4 border border-[#3A3B44]">
        <div className="flex justify-between items-center mb-4">
          <h4 className="font-semibold text-white">Selected Seats</h4>
          {selectedSeats.size > 0 && (
            <button
              onClick={clearSelection}
              className="text-sm text-[#D98639] hover:text-[#C77A32]"
            >
              Clear All
            </button>
          )}
        </div>

        {selectedSeats.size === 0 ? (
          <p className="text-[#9A9BA3] text-center py-4">No seats selected</p>
        ) : (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              {Array.from(selectedSeats).map((id) => {
                const seat = seats.find((s) => s.id === id);
                return (
                  <span
                    key={id}
                    className="px-3 py-1 bg-[#D98639]/20 text-[#D98639] rounded-lg text-sm"
                  >
                    {seat?.seat_label}
                  </span>
                );
              })}
            </div>
            <div className="flex justify-between items-center pt-2 border-t border-[#3A3B44]">
              <span className="text-[#9A9BA3]">
                {selectedSeats.size} seat{selectedSeats.size !== 1 ? "s" : ""}
              </span>
              <span className="text-xl font-bold text-white">
                ${(selectedSeats.size * basePrice).toFixed(2)}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
