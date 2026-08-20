"use client";

import Link from "next/link";
import { FilmResponse } from "@/lib/api";

interface HeroSectionProps {
  film: FilmResponse;
  onBookNow: (film: FilmResponse) => void;
}

export function HeroSection({ film, onBookNow }: HeroSectionProps) {
  const year = film.release_date ? new Date(film.release_date).getFullYear() : null;

  return (
    <section className="relative h-[500px] rounded-2xl overflow-hidden mb-8">
      {/* Backdrop Image */}
      <div className="absolute inset-0">
        {film.backdrop_url ? (
          <img
            src={film.backdrop_url}
            alt={film.title}
            className="w-full h-full object-cover"
          />
        ) : film.poster_url ? (
          <img
            src={film.poster_url}
            alt={film.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full bg-surface" />
        )}
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-black/90 via-black/70 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
      </div>

      {/* Content */}
      <div className="relative h-full flex items-center px-8 md:px-12">
        <div className="max-w-xl">
          {/* Featured Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/20 border border-primary/30 rounded-full text-primary text-sm font-medium mb-4">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            Featured
          </div>

          {/* Title */}
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-2">{film.title}</h1>

          {/* Tagline */}
          {film.tagline && (
            <p className="text-lg text-text-muted italic mb-4">&quot;{film.tagline}&quot;</p>
          )}

          {/* Meta Info */}
          <div className="flex flex-wrap items-center gap-3 mb-4">
            {film.vote_average > 0 && (
              <div className="flex items-center gap-1 text-yellow-400">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
                <span className="font-semibold">{film.vote_average.toFixed(1)}</span>
              </div>
            )}
            {year && (
              <span className="text-text-muted border-l border-border pl-3">{year}</span>
            )}
            {film.runtime && (
              <span className="text-text-muted border-l border-border pl-3">{film.runtime} min</span>
            )}
          </div>

          {/* Genres */}
          {film.genres && film.genres.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-6">
              {film.genres.slice(0, 4).map((genre) => (
                <span
                  key={genre}
                  className="px-3 py-1 text-sm bg-white/10 backdrop-blur-sm rounded-full text-white/90 border border-white/20"
                >
                  {genre}
                </span>
              ))}
            </div>
          )}

          {/* Overview */}
          {film.overview && (
            <p className="text-text-muted line-clamp-2 mb-6 leading-relaxed">
              {film.overview}
            </p>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={() => onBookNow(film)}
              className="px-6 py-3 bg-primary hover:bg-primary-hover text-white font-semibold rounded-xl transition-colors flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
              </svg>
              Book Now
            </button>
            {film.trailer_url && (
              <a
                href={film.trailer_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3 bg-white/10 hover:bg-white/20 backdrop-blur-sm text-white font-semibold rounded-xl transition-colors flex items-center gap-2 border border-white/20"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Watch Trailer
              </a>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
