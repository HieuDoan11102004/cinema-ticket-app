"use client";

import Link from "next/link";
import { FilmResponse } from "@/lib/api";
import Image from "next/image";

interface FilmRowProps {
  title: string;
  films: FilmResponse[];
  viewAllHref?: string;
  onFilmClick?: (film: FilmResponse) => void;
}

export function FilmRow({ title, films, viewAllHref, onFilmClick }: FilmRowProps) {
  if (films.length === 0) return null;

  return (
    <section className="py-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-white">{title}</h2>
        {viewAllHref && (
          <Link
            href={viewAllHref}
            className="text-sm text-primary hover:text-primary-hover transition-colors flex items-center gap-1"
          >
            View all
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        )}
      </div>

      <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide">
        {films.map((film) => (
          <div
            key={film.id}
            className="flex-shrink-0 w-36 group cursor-pointer"
            onClick={() => onFilmClick?.(film)}
          >
            <Link href={`/movies/${film.id}`} className="block">
              <div className="relative aspect-[2/3] rounded-lg overflow-hidden bg-surface border border-border group-hover:border-primary/50 transition-all duration-200">
                {film.poster_url ? (
                  <img
                    src={film.poster_url}
                    alt={film.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-text-muted text-3xl">
                    🎬
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <h3 className="mt-2 text-sm font-medium text-white truncate group-hover:text-primary transition-colors">
                {film.title}
              </h3>
              {film.release_date && (
                <p className="text-xs text-text-muted">
                  {new Date(film.release_date).getFullYear()}
                </p>
              )}
            </Link>
          </div>
        ))}
      </div>
    </section>
  );
}
