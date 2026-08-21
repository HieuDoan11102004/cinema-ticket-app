"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, FilmResponse, ShowtimeResponse } from "@/lib/api";
import ShowtimeSelector from "@/components/ShowtimeSelector";

export default function BookingPage() {
  const params = useParams();
  const router = useRouter();
  const [film, setFilm] = useState<FilmResponse | null>(null);
  const [selectedShowtime, setSelectedShowtime] = useState<ShowtimeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const filmId = params.id as string;

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        // Check authentication
        if (!api.isAuthenticated()) {
          router.push("/login");
          return;
        }

        const filmData = await api.getFilmById(parseInt(filmId));
        setFilm(filmData);
      } catch (err) {
        console.error("Failed to fetch film:", err);
        setError("Failed to load movie details. Please try again.");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [filmId, router]);

  const handleShowtimeSelect = (showtime: ShowtimeResponse) => {
    setSelectedShowtime(showtime);
  };

  const handleContinue = () => {
    if (selectedShowtime) {
      // TODO: Navigate to seat selection
      alert(`Selected showtime:\n${selectedShowtime.film_title}\n${selectedShowtime.cinema_room}\n${new Date(selectedShowtime.start_time).toLocaleString()}\n$${selectedShowtime.base_price.toFixed(2)}\n\nSeat selection coming soon!`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <header className="bg-surface border-b border-border px-4 py-4 sticky top-0 z-10">
          <div className="max-w-4xl mx-auto flex justify-between items-center">
            <Link href={`/movies/${filmId}`} className="text-primary hover:text-primary/80 transition-colors flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Movie
            </Link>
            <h1 className="text-xl font-bold text-primary">🎬 CineBook</h1>
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 py-8">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-border rounded w-1/2" />
            <div className="h-4 bg-border rounded w-1/4" />
            <div className="h-64 bg-border rounded-xl mt-6" />
          </div>
        </main>
      </div>
    );
  }

  if (error || !film) {
    return (
      <div className="min-h-screen bg-background">
        <header className="bg-surface border-b border-border px-4 py-4 sticky top-0 z-10">
          <div className="max-w-4xl mx-auto">
            <Link href="/movies" className="text-primary hover:text-primary/80 transition-colors flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Movies
            </Link>
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 py-8">
          <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-8 text-center">
            <p className="text-red-400 text-lg mb-4">{error || "Film not found"}</p>
            <Link
              href="/movies"
              className="px-6 py-3 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors inline-block"
            >
              Browse Movies
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-surface border-b border-border px-4 py-4 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <Link href={`/movies/${filmId}`} className="text-primary hover:text-primary/80 transition-colors flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Movie
          </Link>
          <h1 className="text-xl font-bold text-primary">🎬 CineBook</h1>
        </div>
      </header>

      {/* Film Info Banner */}
      <div className="bg-surface border-b border-border">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            {film.poster_url && (
              <img
                src={film.poster_url}
                alt={film.title}
                className="w-12 h-18 object-cover rounded-lg"
              />
            )}
            <div>
              <h2 className="text-lg font-semibold text-white">{film.title}</h2>
              <p className="text-sm text-[#A0A0A8]">
                {film.genres?.slice(0, 3).join(" • ")}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <ShowtimeSelector filmId={parseInt(filmId)} onSelect={handleShowtimeSelect} />

        {/* Continue Button */}
        {selectedShowtime && (
          <div className="mt-8 pt-6 border-t border-border">
            <div className="bg-[#2A2B33] rounded-xl p-4 mb-4">
              <p className="text-sm text-[#A0A0A8] mb-1">Selected:</p>
              <p className="text-white font-semibold">
                {new Date(selectedShowtime.start_time).toLocaleDateString("en-US", {
                  weekday: "long",
                  month: "short",
                  day: "numeric",
                })} at{" "}
                {new Date(selectedShowtime.start_time).toLocaleTimeString("en-US", {
                  hour: "numeric",
                  minute: "2-digit",
                  hour12: true,
                })}
              </p>
              <p className="text-[#A0A0A8]">
                {selectedShowtime.cinema_room} • ${selectedShowtime.base_price.toFixed(2)}
              </p>
            </div>

            <button
              onClick={handleContinue}
              className="w-full px-8 py-4 bg-primary hover:bg-primary-hover text-white text-lg font-semibold rounded-xl transition-colors shadow-lg shadow-primary/25"
            >
              Continue to Seat Selection
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
