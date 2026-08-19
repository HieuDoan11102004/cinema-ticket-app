"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, FilmResponse } from "@/lib/api";
import { FilmCard } from "@/components/FilmCard";

export default function MoviesPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ first_name: string; last_name: string } | null>(null);
  const [films, setFilms] = useState<FilmResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check authentication
    if (!api.isAuthenticated()) {
      router.push("/login");
      return;
    }

    // Get user data
    const userData = api.getUser();
    if (userData) {
      setUser(userData);
    }

    // Fetch films
    fetchFilms();
  }, [router]);

  const fetchFilms = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getFilms(1, 20);
      setFilms(data.films);
    } catch (err) {
      console.error("Failed to fetch films:", err);
      setError("Failed to load movies. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleBookNow = (film: FilmResponse) => {
    // Future: Navigate to booking page
    console.log("Booking:", film.title);
    alert(`Booking for "${film.title}" - Coming soon!`);
  };

  const handleLogout = async () => {
    await api.logout();
    router.push("/login");
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-text-muted">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-surface border-b border-border px-4 py-4 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-primary">🎬 CineBook</h1>
          <div className="flex items-center gap-4">
            <span className="text-white text-sm">
              Welcome, {user.first_name}
            </span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm bg-surface border border-border rounded-lg text-white hover:bg-border transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-white">Now Showing</h2>
          <span className="text-sm text-text-muted">{films.length} movies</span>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex gap-4 bg-surface rounded-xl p-4 border border-border animate-pulse">
                <div className="w-20 h-30 bg-border rounded-lg" />
                <div className="flex-1 space-y-3">
                  <div className="h-5 bg-border rounded w-3/4" />
                  <div className="flex gap-2">
                    <div className="h-5 bg-border rounded w-16" />
                    <div className="h-5 bg-border rounded w-20" />
                  </div>
                  <div className="space-y-1">
                    <div className="h-3 bg-border rounded w-full" />
                    <div className="h-3 bg-border rounded w-2/3" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-error/10 border border-error rounded-xl p-6 text-center">
            <p className="text-error mb-4">{error}</p>
            <button
              onClick={fetchFilms}
              className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Film List */}
        {!loading && !error && (
          <div className="space-y-4">
            {films.length === 0 ? (
              <div className="bg-surface rounded-xl p-8 text-center border border-border">
                <p className="text-text-muted text-lg mb-2">No movies available</p>
                <p className="text-text-muted text-sm">Check back later for new releases</p>
              </div>
            ) : (
              films.map((film) => (
                <FilmCard
                  key={film.id}
                  film={film}
                  onBookNow={handleBookNow}
                />
              ))
            )}
          </div>
        )}
      </main>
    </div>
  );
}
