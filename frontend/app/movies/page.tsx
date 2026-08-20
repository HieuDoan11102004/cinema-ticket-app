"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, FilmResponse } from "@/lib/api";
import { FilmCard } from "@/components/FilmCard";
import { SearchBar } from "@/components/SearchBar";
import { GenreFilter } from "@/components/GenreFilter";

const STATUS_OPTIONS = [
  { value: "", label: "All" },
  { value: "Released", label: "Released" },
  { value: "In Production", label: "In Production" },
  { value: "Post Production", label: "Post Production" },
  { value: "Planned", label: "Planned" },
];

function MoviesPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [user, setUser] = useState<{ first_name: string } | null>(null);
  const [films, setFilms] = useState<FilmResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalFilms, setTotalFilms] = useState(0);

  // Search/filter state
  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || "");
  const [selectedGenres, setSelectedGenres] = useState<string[]>(
    searchParams.get("genres")?.split(",").filter(Boolean) || []
  );
  const [selectedStatus, setSelectedStatus] = useState(searchParams.get("status") || "");

  // Pagination state
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const LIMIT = 12;

  useEffect(() => {
    // Check authentication
    if (!api.isAuthenticated()) {
      router.push("/login");
      return;
    }

    // Get user data
    const userData = api.getUser();
    if (userData) {
      setUser({ first_name: userData.first_name });
    }

    // Initialize from URL params
    setSearchQuery(searchParams.get("q") || "");
    setSelectedGenres(searchParams.get("genres")?.split(",").filter(Boolean) || []);
    setSelectedStatus(searchParams.get("status") || "");
  }, [router, searchParams]);

  const fetchFilms = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await api.searchFilms({
        q: searchQuery || undefined,
        genres: selectedGenres.length > 0 ? selectedGenres : undefined,
        status: selectedStatus || undefined,
        skip: (page - 1) * LIMIT,
        limit: LIMIT,
      });

      setFilms(data.films);
      setTotalFilms(data.total);
      setTotalPages(Math.ceil(data.total / LIMIT));
    } catch (err) {
      console.error("Failed to fetch films:", err);
      setError("Failed to load movies. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedGenres, selectedStatus, page]);

  useEffect(() => {
    fetchFilms();
  }, [fetchFilms]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setPage(1);
  };

  const handleGenresChange = (genres: string[]) => {
    setSelectedGenres(genres);
    setPage(1);
  };

  const handleStatusChange = (status: string) => {
    setSelectedStatus(status);
    setPage(1);
  };

  const handleClearFilters = () => {
    setSearchQuery("");
    setSelectedGenres([]);
    setSelectedStatus("");
    setPage(1);
  };

  const handleBookNow = (film: FilmResponse) => {
    console.log("Booking:", film.title);
    alert(`Booking for "${film.title}" - Coming soon!`);
  };

  const handleLogout = async () => {
    await api.logout();
    router.push("/login");
  };

  const hasActiveFilters = searchQuery || selectedGenres.length > 0 || selectedStatus;

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
      <header className="bg-surface border-b border-border px-4 py-4 sticky top-0 z-20">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-primary">🎬 CineBook</h1>
          <div className="flex items-center gap-4">
            <span className="text-white text-sm">Welcome, {user.first_name}</span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm bg-surface border border-border rounded-lg text-text-muted hover:text-white transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Search Bar */}
        <div className="mb-6">
          <SearchBar
            onSearch={handleSearch}
            placeholder="Search for movies..."
          />
        </div>

        {/* Filters */}
        <div className="bg-surface rounded-xl p-4 mb-6 border border-border">
          {/* Status Filter */}
          <div className="flex items-center gap-4 mb-4 pb-4 border-b border-border">
            <span className="text-sm text-text-muted">Status:</span>
            <div className="flex flex-wrap gap-2">
              {STATUS_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleStatusChange(option.value)}
                  className={`px-3 py-1.5 text-sm rounded-lg border transition-all ${
                    selectedStatus === option.value
                      ? "bg-primary text-white border-primary"
                      : "bg-background text-text-muted border-border hover:border-primary/50 hover:text-white"
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Genre Filter */}
          <GenreFilter
            selectedGenres={selectedGenres}
            onGenresChange={handleGenresChange}
          />
        </div>

        {/* Results Info & Clear */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-text-muted">
            {loading ? (
              "Searching..."
            ) : (
              <>
                Found <span className="text-white font-medium">{totalFilms}</span> movies
              </>
            )}
          </span>
          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="text-sm text-primary hover:text-primary-hover transition-colors flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Clear filters
            </button>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
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

        {/* Film Grid */}
        {!loading && !error && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {films.length === 0 ? (
                <div className="col-span-full bg-surface rounded-xl p-8 text-center border border-border">
                  <p className="text-text-muted text-lg mb-2">No movies found</p>
                  <p className="text-text-muted text-sm">Try adjusting your search or filters</p>
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

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-8">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-surface border border-border rounded-lg text-white hover:bg-border disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>

                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (page <= 3) {
                      pageNum = i + 1;
                    } else if (page >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = page - 2 + i;
                    }

                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPage(pageNum)}
                        className={`w-10 h-10 rounded-lg border transition-colors ${
                          page === pageNum
                            ? "bg-primary text-white border-primary"
                            : "bg-surface border-border text-white hover:bg-border"
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 bg-surface border border-border rounded-lg text-white hover:bg-border disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function MoviesLoading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-primary mb-2">🎬 CineBook</h1>
        <p className="text-text-muted">Loading...</p>
      </div>
    </div>
  );
}

export default function MoviesPage() {
  return (
    <Suspense fallback={<MoviesLoading />}>
      <MoviesPageContent />
    </Suspense>
  );
}
