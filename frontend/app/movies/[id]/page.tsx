"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, FilmResponse } from "@/lib/api";

export default function FilmDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [film, setFilm] = useState<FilmResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const filmId = params.id as string;

  useEffect(() => {
    if (!api.isAuthenticated()) {
      router.push("/login");
      return;
    }
    fetchFilm();
  }, [filmId, router]);

  const fetchFilm = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getFilmById(parseInt(filmId));
      setFilm(data);
    } catch (err) {
      console.error("Failed to fetch film:", err);
      setError("Failed to load movie details. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const formatRuntime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const formatBudget = (amount: number) => {
    if (amount === 0) return "N/A";
    if (amount >= 1_000_000_000) return `$${(amount / 1_000_000_000).toFixed(1)}B`;
    if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`;
    if (amount >= 1_000) return `$${(amount / 1_000).toFixed(1)}K`;
    return `$${amount}`;
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "N/A";
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="bg-surface border-b border-border px-4 py-4 sticky top-0 z-10">
          <div className="max-w-6xl mx-auto">
            <Link href="/movies" className="text-primary hover:text-primary/80 transition-colors flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Movies
            </Link>
          </div>
        </header>

        <main className="max-w-6xl mx-auto px-4 py-8">
          <div className="animate-pulse">
            <div className="flex flex-col md:flex-row gap-8">
              <div className="w-64 h-96 bg-border rounded-xl flex-shrink-0" />
              <div className="flex-1 space-y-4">
                <div className="h-10 bg-border rounded w-3/4" />
                <div className="h-6 bg-border rounded w-1/2" />
                <div className="h-32 bg-border rounded w-full" />
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error || !film) {
    return (
      <div className="min-h-screen bg-background">
        <header className="bg-surface border-b border-border px-4 py-4 sticky top-0 z-10">
          <div className="max-w-6xl mx-auto">
            <Link href="/movies" className="text-primary hover:text-primary/80 transition-colors flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Movies
            </Link>
          </div>
        </header>

        <main className="max-w-6xl mx-auto px-4 py-8">
          <div className="bg-error/10 border border-error rounded-xl p-8 text-center">
            <p className="text-error text-lg mb-4">{error || "Film not found"}</p>
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
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <Link href="/movies" className="text-primary hover:text-primary/80 transition-colors flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Movies
          </Link>
          <h1 className="text-xl font-bold text-primary">🎬 CineBook</h1>
        </div>
      </header>

      {/* Hero Section with Backdrop */}
      {film.backdrop_url && (
        <div className="relative h-64 md:h-80 overflow-hidden">
          <img
            src={film.backdrop_url}
            alt={film.title}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background via-background/80 to-transparent" />
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 -mt-20 relative z-10 pb-16">
        <div className="flex flex-col md:flex-row gap-8">
          {/* Poster */}
          <div className="flex-shrink-0">
            <div className="w-64 rounded-xl overflow-hidden shadow-2xl shadow-black/50 bg-surface">
              {film.poster_url ? (
                <img
                  src={film.poster_url}
                  alt={film.title}
                  className="w-full h-auto"
                />
              ) : (
                <div className="aspect-[2/3] bg-border flex items-center justify-center text-6xl">
                  🎬
                </div>
              )}
            </div>
          </div>

          {/* Details */}
          <div className="flex-1 pt-4 md:pt-20">
            {/* Title */}
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
              {film.title}
            </h1>
            {film.original_title && film.original_title !== film.title && (
              <p className="text-lg text-text-muted mb-4">{film.original_title}</p>
            )}

            {/* Tagline */}
            {film.tagline && (
              <p className="text-xl text-primary italic mb-4">"{film.tagline}"</p>
            )}

            {/* Quick Info */}
            <div className="flex flex-wrap items-center gap-4 mb-6">
              {film.release_date && (
                <span className="text-text-muted">{formatDate(film.release_date)}</span>
              )}
              {film.runtime && (
                <span className="text-text-muted flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {formatRuntime(film.runtime)}
                </span>
              )}
              {film.status && (
                <span className="px-3 py-1 bg-primary/20 text-primary rounded-full text-sm">
                  {film.status}
                </span>
              )}
            </div>

            {/* Genres */}
            {film.genres && film.genres.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {film.genres.map((genre) => (
                  <span
                    key={genre}
                    className="px-3 py-1 bg-surface border border-border rounded-full text-sm text-text-muted"
                  >
                    {genre}
                  </span>
                ))}
              </div>
            )}

            {/* Rating */}
            <div className="flex items-center gap-4 mb-8">
              <div className="flex items-center gap-2">
                <svg className="w-6 h-6 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
                <span className="text-2xl font-bold text-white">{film.vote_average.toFixed(1)}</span>
                <span className="text-text-muted">/ 10</span>
              </div>
              <span className="text-text-muted">({film.vote_count.toLocaleString()} votes)</span>
            </div>

            {/* Overview */}
            {film.overview && (
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-white mb-2">Overview</h2>
                <p className="text-text-muted leading-relaxed">{film.overview}</p>
              </div>
            )}

            {/* Additional Info Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mb-8">
              {film.spoken_languages && film.spoken_languages.length > 0 && (
                <div>
                  <h3 className="text-sm text-text-muted mb-1">Spoken Languages</h3>
                  <p className="text-white">{film.spoken_languages.join(", ")}</p>
                </div>
              )}
              {film.production_countries && film.production_countries.length > 0 && (
                <div>
                  <h3 className="text-sm text-text-muted mb-1">Production Countries</h3>
                  <p className="text-white">{film.production_countries.join(", ")}</p>
                </div>
              )}
              {film.budget > 0 && (
                <div>
                  <h3 className="text-sm text-text-muted mb-1">Budget</h3>
                  <p className="text-white">{formatBudget(film.budget)}</p>
                </div>
              )}
              {film.revenue > 0 && (
                <div>
                  <h3 className="text-sm text-text-muted mb-1">Box Office</h3>
                  <p className="text-white">{formatBudget(film.revenue)}</p>
                </div>
              )}
              {film.original_language && (
                <div>
                  <h3 className="text-sm text-text-muted mb-1">Original Language</h3>
                  <p className="text-white uppercase">{film.original_language}</p>
                </div>
              )}
              {film.tmdb_id && (
                <div>
                  <h3 className="text-sm text-text-muted mb-1">TMDB ID</h3>
                  <p className="text-white">{film.tmdb_id}</p>
                </div>
              )}
            </div>

            {/* Production Companies */}
            {film.production_companies && film.production_companies.length > 0 && (
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-white mb-2">Production</h2>
                <p className="text-text-muted">{film.production_companies.join(", ")}</p>
              </div>
            )}

            {/* Homepage Link */}
            {film.homepage && (
              <div className="mb-8">
                <a
                  href={film.homepage}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:text-primary/80 transition-colors flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  Official Website
                </a>
              </div>
            )}

            {/* Book Now Button */}
            <button
              onClick={() => router.push(`/movies/${film.id}/book`)}
              className="px-8 py-4 bg-primary hover:bg-primary-hover text-white text-lg font-semibold rounded-xl transition-colors shadow-lg shadow-primary/25"
            >
              Book Tickets Now
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
