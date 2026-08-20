"use client";

interface GenreFilterProps {
  selectedGenres: string[];
  onGenresChange: (genres: string[]) => void;
  availableGenres?: string[];
}

const POPULAR_GENRES = [
  "Action",
  "Adventure",
  "Animation",
  "Comedy",
  "Crime",
  "Documentary",
  "Drama",
  "Family",
  "Fantasy",
  "History",
  "Horror",
  "Music",
  "Mystery",
  "Romance",
  "Science Fiction",
  "Thriller",
  "War",
  "Western",
];

export function GenreFilter({ selectedGenres, onGenresChange, availableGenres = POPULAR_GENRES }: GenreFilterProps) {
  const toggleGenre = (genre: string) => {
    if (selectedGenres.includes(genre)) {
      onGenresChange(selectedGenres.filter((g) => g !== genre));
    } else {
      onGenresChange([...selectedGenres, genre]);
    }
  };

  const clearGenres = () => {
    onGenresChange([]);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-sm text-text-muted">Genre:</span>
        {selectedGenres.length > 0 && (
          <button
            onClick={clearGenres}
            className="text-xs text-primary hover:text-primary-hover transition-colors"
          >
            Clear all
          </button>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        {availableGenres.map((genre) => (
          <button
            key={genre}
            onClick={() => toggleGenre(genre)}
            className={`px-3 py-1.5 text-sm rounded-full border transition-all ${
              selectedGenres.includes(genre)
                ? "bg-primary text-white border-primary"
                : "bg-surface text-text-muted border-border hover:border-primary/50 hover:text-white"
            }`}
          >
            {genre}
          </button>
        ))}
      </div>
    </div>
  );
}
