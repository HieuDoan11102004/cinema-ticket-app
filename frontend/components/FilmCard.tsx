"use client";

import { FilmResponse } from "@/lib/api";

interface FilmCardProps {
  film: FilmResponse;
  onBookNow?: (film: FilmResponse) => void;
}

export function FilmCard({ film, onBookNow }: FilmCardProps) {
  const year = film.release_date ? new Date(film.release_date).getFullYear() : null;

  return (
    <div className="flex gap-4 bg-surface rounded-xl p-4 border border-border hover:border-primary/50 transition-all duration-200 hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-0.5">
      {/* Poster */}
      <div className="flex-shrink-0 w-20 h-30 bg-border rounded-lg overflow-hidden">
        {film.poster_url ? (
          <img
            src={film.poster_url}
            alt={film.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-text-muted text-2xl">
            🎬
          </div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0 flex flex-col justify-between">
        <div>
          <div className="flex items-start justify-between gap-2 mb-1">
            <h3 className="text-lg font-semibold text-white truncate">{film.title}</h3>
            {year && (
              <span className="flex-shrink-0 text-sm text-text-muted bg-surface px-2 py-0.5 rounded">
                {year}
              </span>
            )}
          </div>

          {/* Genres */}
          {film.genres && film.genres.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-2">
              {film.genres.slice(0, 3).map((genre) => (
                <span
                  key={genre}
                  className="text-xs px-2 py-0.5 rounded-full bg-primary/20 text-primary border border-primary/30"
                >
                  {genre}
                </span>
              ))}
              {film.genres.length > 3 && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-border text-text-muted">
                  +{film.genres.length - 3}
                </span>
              )}
            </div>
          )}

          {/* Overview */}
          {film.overview && (
            <p className="text-sm text-text-muted line-clamp-2 leading-relaxed">
              {film.overview}
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 mt-3">
          {film.duration_min && (
            <span className="text-xs text-text-muted flex items-center gap-1">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {film.duration_min} min
            </span>
          )}
          <button
            onClick={() => onBookNow?.(film)}
            className="ml-auto px-4 py-1.5 bg-primary hover:bg-primary-hover text-white text-sm font-medium rounded-lg transition-colors"
          >
            Book Now
          </button>
        </div>
      </div>
    </div>
  );
}
