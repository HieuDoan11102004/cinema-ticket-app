"use client";

import { useState, useEffect } from "react";
import { api, ShowtimeResponse } from "@/lib/api";

interface ShowtimeSelectorProps {
  filmId: number;
  onSelect: (showtime: ShowtimeResponse) => void;
}

interface ShowtimesByDate {
  date: string;
  displayDate: string;
  showtimes: ShowtimeResponse[];
}

function formatDate(dateStr: string): { date: string; display: string } {
  const date = new Date(dateStr);
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  const dateStrOnly = dateStr.split("T")[0];

  if (dateStrOnly === today.toISOString().split("T")[0]) {
    return { date: dateStrOnly, display: "Today" };
  }
  if (dateStrOnly === tomorrow.toISOString().split("T")[0]) {
    return { date: dateStrOnly, display: "Tomorrow" };
  }

  return {
    date: dateStrOnly,
    display: date.toLocaleDateString("en-US", {
      weekday: "long",
      month: "short",
      day: "numeric",
    }),
  };
}

function formatTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

export default function ShowtimeSelector({ filmId, onSelect }: ShowtimeSelectorProps) {
  const [showtimes, setShowtimes] = useState<ShowtimeResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedShowtime, setSelectedShowtime] = useState<ShowtimeResponse | null>(null);

  useEffect(() => {
    async function fetchShowtimes() {
      try {
        setLoading(true);
        const data = await api.getFilmShowtimes(filmId);
        setShowtimes(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load showtimes");
      } finally {
        setLoading(false);
      }
    }

    fetchShowtimes();
  }, [filmId]);

  // Group showtimes by date
  const showtimesByDate: ShowtimesByDate[] = showtimes.reduce((acc, showtime) => {
    const { date, display } = formatDate(showtime.start_time);
    const existing = acc.find((item) => item.date === date);

    if (existing) {
      existing.showtimes.push(showtime);
    } else {
      acc.push({
        date,
        displayDate: display,
        showtimes: [showtime],
      });
    }

    return acc;
  }, [] as ShowtimesByDate[]);

  // Sort showtimes within each date by time
  showtimesByDate.forEach((group) => {
    group.showtimes.sort(
      (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
    );
  });

  const handleSelect = (showtime: ShowtimeResponse) => {
    setSelectedShowtime(showtime);
    onSelect(showtime);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-400 mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (showtimes.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-[#A0A0A8]">No showtimes available for this film.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-white mb-4">Select a Showtime</h3>

      {showtimesByDate.map((group) => (
        <div key={group.date} className="mb-6">
          <h4 className="text-[#A0A0A8] text-sm font-medium mb-3">{group.displayDate}</h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {group.showtimes.map((showtime) => {
              const isSelected = selectedShowtime?.id === showtime.id;

              return (
                <button
                  key={showtime.id}
                  onClick={() => handleSelect(showtime)}
                  className={`
                    flex flex-col items-center p-4 rounded-xl border-2 transition-all
                    ${
                      isSelected
                        ? "border-primary bg-primary/10"
                        : "border-[#3A3B44] bg-[#2A2B33] hover:border-primary/50 hover:bg-[#3A3B44]"
                    }
                  `}
                >
                  <span className="text-xl font-bold text-white mb-1">
                    {formatTime(showtime.start_time)}
                  </span>
                  <span className="text-sm text-[#A0A0A8]">{showtime.cinema_room}</span>
                  <span className="text-sm font-semibold text-primary mt-2">
                    ${showtime.base_price.toFixed(2)}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
