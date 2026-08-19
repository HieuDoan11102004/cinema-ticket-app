"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function MoviesPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ first_name: string; last_name: string } | null>(null);

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
  }, [router]);

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
      <header className="bg-surface border-b border-border px-4 py-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-primary">🎬 CineBook</h1>
          <div className="flex items-center gap-4">
            <span className="text-white">
              Welcome, {user.first_name} {user.last_name}
            </span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm bg-surface border border-border rounded-[10px] text-white hover:bg-border transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        <h2 className="text-3xl font-semibold text-white mb-6">Now Showing</h2>
        <p className="text-text-muted">
          Movies page coming soon... This is where the movie listing will appear.
        </p>
      </main>
    </div>
  );
}
