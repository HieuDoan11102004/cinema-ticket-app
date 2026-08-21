"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, FilmResponse, ShowtimeResponse, SeatResponse } from "@/lib/api";
import ShowtimeSelector from "@/components/ShowtimeSelector";
import SeatMap from "@/components/SeatMap";
import Button from "@/components/ui/Button";

type BookingStep = "showtime" | "seats" | "confirm";

export default function BookingPage() {
  const params = useParams();
  const router = useRouter();
  const [film, setFilm] = useState<FilmResponse | null>(null);
  const [step, setStep] = useState<BookingStep>("showtime");
  const [selectedShowtime, setSelectedShowtime] = useState<ShowtimeResponse | null>(null);
  const [seats, setSeats] = useState<SeatResponse[]>([]);
  const [selectedSeats, setSelectedSeats] = useState<SeatResponse[]>([]);
  const [totalPrice, setTotalPrice] = useState(0);
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

  // Fetch seats when showtime is selected
  useEffect(() => {
    if (selectedShowtime && step === "seats") {
      fetchSeats();
    }
  }, [selectedShowtime, step]);

  const fetchSeats = async () => {
    if (!selectedShowtime) return;

    try {
      setLoading(true);
      setError(null);
      const response = await api.getShowtimeSeats(selectedShowtime.id);
      setSeats(response.seats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load seats");
    } finally {
      setLoading(false);
    }
  };

  const handleShowtimeSelect = (showtime: ShowtimeResponse) => {
    setSelectedShowtime(showtime);
    setStep("seats");
  };

  const handleSelectionChange = useCallback((seats: SeatResponse[], price: number) => {
    setSelectedSeats(seats);
    setTotalPrice(price);
  }, []);

  const handleHoldSeats = async () => {
    if (selectedSeats.length === 0 || !selectedShowtime) return;

    try {
      setLoading(true);
      setError(null);
      await api.holdSeats(
        selectedSeats.map((s) => s.id),
        selectedShowtime.id
      );
      setStep("confirm");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to hold seats");
    } finally {
      setLoading(false);
    }
  };

  const handleReleaseSeats = async () => {
    if (selectedSeats.length === 0 || !selectedShowtime) return;

    try {
      await api.releaseSeats(
        selectedSeats.map((s) => s.id),
        selectedShowtime.id
      );
    } catch (err) {
      console.error("Failed to release seats:", err);
    }
  };

  const handleBack = () => {
    if (step === "seats") {
      handleReleaseSeats();
      setSelectedShowtime(null);
      setSeats([]);
      setSelectedSeats([]);
      setTotalPrice(0);
      setStep("showtime");
    } else if (step === "confirm") {
      setStep("seats");
    }
  };

  // Release seats when leaving page
  useEffect(() => {
    return () => {
      if (selectedSeats.length > 0) {
        handleReleaseSeats();
      }
    };
  }, []);

  if (loading && !film) {
    return (
      <div className="min-h-screen bg-[#1E1F27]">
        <header className="bg-[#2A2B33] border-b border-[#3A3B44] px-4 py-4 sticky top-0 z-10">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between">
              <Link
                href={`/movies/${filmId}`}
                className="text-[#D98639] hover:text-[#C77A32] transition-colors flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Movie
              </Link>
              <h1 className="text-xl font-bold text-[#D98639]">🎬 CineBook</h1>
            </div>
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 py-8">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-[#3A3B44] rounded w-1/2" />
            <div className="h-4 bg-[#3A3B44] rounded w-1/4" />
            <div className="h-64 bg-[#3A3B44] rounded-xl mt-6" />
          </div>
        </main>
      </div>
    );
  }

  if ((error || !film) && !loading) {
    return (
      <div className="min-h-screen bg-[#1E1F27]">
        <header className="bg-[#2A2B33] border-b border-[#3A3B44] px-4 py-4 sticky top-0 z-10">
          <div className="max-w-4xl mx-auto">
            <Link
              href="/movies"
              className="text-[#D98639] hover:text-[#C77A32] transition-colors flex items-center gap-2"
            >
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
              className="px-6 py-3 bg-[#D98639] hover:bg-[#C77A32] text-white rounded-lg transition-colors inline-block"
            >
              Browse Movies
            </Link>
          </div>
        </main>
      </div>
    );
  }

  // Step 1: Showtime Selection
  if (step === "showtime") {
    return (
      <div className="min-h-screen bg-[#1E1F27]">
        <header className="bg-[#2A2B33] border-b border-[#3A3B44] px-4 py-4 sticky top-0 z-10">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between">
              <Link
                href={`/movies/${filmId}`}
                className="text-[#D98639] hover:text-[#C77A32] transition-colors flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Movie
              </Link>
              <h1 className="text-xl font-bold text-[#D98639]">🎬 CineBook</h1>
            </div>
          </div>
        </header>

        {/* Film Info Banner */}
        {film && (
          <div className="bg-[#2A2B33] border-b border-[#3A3B44]">
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
                  <p className="text-sm text-[#9A9BA3]">
                    {film.genres?.slice(0, 3).join(" • ")}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        <main className="max-w-4xl mx-auto px-4 py-8">
          <h1 className="text-2xl font-bold text-white mb-6">Book Tickets</h1>
          <ShowtimeSelector filmId={parseInt(filmId)} onSelect={handleShowtimeSelect} />
        </main>
      </div>
    );
  }

  // Step 2: Seat Selection
  if (step === "seats" && selectedShowtime) {
    return (
      <div className="min-h-screen bg-[#1E1F27]">
        <header className="bg-[#2A2B33] border-b border-[#3A3B44] px-4 py-4 sticky top-0 z-10">
          <div className="max-w-4xl mx-auto flex justify-between items-center">
            <button
              onClick={handleBack}
              className="text-[#D98639] hover:text-[#C77A32] transition-colors flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back
            </button>
            <h1 className="text-xl font-bold text-white">Select Seats</h1>
            <div className="w-20" />
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 py-8">
          {loading && seats.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-[#D98639] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : error && seats.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-red-400 mb-4">{error}</p>
              <button
                onClick={fetchSeats}
                className="px-4 py-2 bg-[#D98639] hover:bg-[#C77A32] text-white rounded-lg"
              >
                Retry
              </button>
            </div>
          ) : (
            <>
              <SeatMap
                seats={seats}
                showtimeId={selectedShowtime.id}
                basePrice={selectedShowtime.base_price}
                onSelectionChange={handleSelectionChange}
                cinemaRoom={selectedShowtime.cinema_room}
              />

              {error && <p className="text-red-400 text-sm mt-4 text-center">{error}</p>}

              <div className="mt-6 flex justify-end">
                <Button
                  onClick={handleHoldSeats}
                  disabled={selectedSeats.length === 0}
                  isLoading={loading}
                  className="min-w-[200px]"
                >
                  Continue to Payment
                </Button>
              </div>
            </>
          )}
        </main>
      </div>
    );
  }

  // Step 3: Confirmation
  if (step === "confirm" && selectedShowtime) {
    return (
      <div className="min-h-screen bg-[#1E1F27]">
        <header className="bg-[#2A2B33] border-b border-[#3A3B44] px-4 py-4 sticky top-0 z-10">
          <div className="max-w-4xl mx-auto flex justify-between items-center">
            <button
              onClick={handleBack}
              className="text-[#D98639] hover:text-[#C77A32] transition-colors flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Seats
            </button>
            <h1 className="text-xl font-bold text-white">Confirm Booking</h1>
            <div className="w-20" />
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 py-8">
          <div className="bg-[#2A2B33] rounded-xl p-6 border border-[#3A3B44]">
            <h3 className="text-lg font-semibold text-white mb-4">Booking Summary</h3>

            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-[#9A9BA3]">Movie</span>
                <span className="text-white">{selectedShowtime.film_title}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#9A9BA3]">Date & Time</span>
                <span className="text-white">
                  {new Date(selectedShowtime.start_time).toLocaleDateString("en-US", {
                    weekday: "long",
                    month: "short",
                    day: "numeric",
                  })}{" "}
                  at{" "}
                  {new Date(selectedShowtime.start_time).toLocaleTimeString("en-US", {
                    hour: "numeric",
                    minute: "2-digit",
                    hour12: true,
                  })}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#9A9BA3]">Room</span>
                <span className="text-white">{selectedShowtime.cinema_room}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#9A9BA3]">Seats</span>
                <span className="text-white">{selectedSeats.map((s) => s.seat_label).join(", ")}</span>
              </div>
              <div className="flex justify-between pt-4 border-t border-[#3A3B44]">
                <span className="text-lg font-semibold text-white">Total</span>
                <span className="text-xl font-bold text-[#D98639]">${totalPrice.toFixed(2)}</span>
              </div>
            </div>

            <div className="mt-6">
              <Button className="w-full" size="large">
                Proceed to Payment
              </Button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return null;
}
