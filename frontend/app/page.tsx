"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem("access_token");
    if (token) {
      // User is logged in, show home page or redirect to movies
      router.push("/movies");
    } else {
      // User is not logged in, redirect to login
      router.push("/login");
    }
  }, [router]);

  // Loading state while checking auth
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-primary mb-2">🎬 CineBook</h1>
        <p className="text-text-muted">Loading...</p>
      </div>
    </div>
  );
}
