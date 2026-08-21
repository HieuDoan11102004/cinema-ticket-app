"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, FilmResponse } from "@/lib/api";
import { HeroSection } from "@/components/HeroSection";
import { FilmRow } from "@/components/FilmRow";

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState<{ first_name: string } | null>(null);
  const [films, setFilms] = useState<FilmResponse[]>([]);
  const [loading, setLoading] = useState(true);

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

    // Fetch all films for homepage sections
    fetchFilms();
  }, [router]);

  const fetchFilms = async () => {
    try {
      setLoading(true);
      // Fetch popular films (limit to get variety)
      const data = await api.searchFilms({ limit: 50 });
      setFilms(data.films);
    } catch (err) {
      console.error("Failed to fetch films:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleBookNow = (film: FilmResponse) => {
    router.push(`/movies/${film.id}/book`);
  };

  const handleLogout = async () => {
    await api.logout();
    router.push("/login");
  };

  // Separate films by status for sections
  const popularFilms = films.filter((f) => f.popularity > 0).slice(0, 10);
  const nowPlayingFilms = films
    .filter((f) => f.status === "Released" || f.status === "Now Playing")
    .slice(0, 10);
  const upcomingFilms = films
    .filter((f) => f.status === "In Production" || f.status === "Planned" || f.status === "Post Production")
    .slice(0, 10);

  // Featured film (highest rating with backdrop)
  const featuredFilm = films.find(
    (f) => f.backdrop_url && f.vote_average > 0
  ) || films.find((f) => f.poster_url && f.vote_average > 0) || films[0];

  if (!user && loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-primary mb-2">🎬 CineBook</h1>
          <p className="text-text-muted">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-surface border-b border-border px-4 py-4 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-primary">🎬 CineBook</h1>
          <nav className="flex items-center gap-6">
            <a href="/movies" className="text-white hover:text-primary transition-colors font-medium">
              Movies
            </a>
            <a href="#" className="text-text-muted hover:text-white transition-colors">
              About
            </a>
          </nav>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white font-semibold text-sm">
                {user?.first_name?.charAt(0).toUpperCase() || "U"}
              </div>
              <span className="text-white text-sm">{user?.first_name}</span>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm bg-surface border border-border rounded-lg text-text-muted hover:text-white hover:border-border transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 md:px-8 py-8">
        {loading ? (
          <div className="space-y-8 animate-pulse">
            <div className="h-[500px] bg-surface rounded-2xl" />
            <div className="h-8 bg-surface rounded w-48" />
            <div className="flex gap-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="w-36 h-52 bg-surface rounded-lg" />
              ))}
            </div>
          </div>
        ) : (
          <>
            {/* Hero Section */}
            {featuredFilm && (
              <HeroSection film={featuredFilm} onBookNow={handleBookNow} />
            )}

            {/* Film Sections */}
            {popularFilms.length > 0 && (
              <FilmRow
                title="Popular Movies"
                films={popularFilms}
                viewAllHref="/movies?status=Popular"
                onFilmClick={handleBookNow}
              />
            )}

            {nowPlayingFilms.length > 0 && (
              <FilmRow
                title="Now Playing"
                films={nowPlayingFilms}
                viewAllHref="/movies?status=Released"
                onFilmClick={handleBookNow}
              />
            )}

            {upcomingFilms.length > 0 && (
              <FilmRow
                title="Coming Soon"
                films={upcomingFilms}
                viewAllHref="/movies?status=Upcoming"
                onFilmClick={handleBookNow}
              />
            )}

            {films.length === 0 && (
              <div className="text-center py-16">
                <p className="text-text-muted text-lg mb-4">No movies available</p>
                <p className="text-text-muted text-sm">Check back later for new releases</p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
