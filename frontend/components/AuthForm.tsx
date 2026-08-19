"use client";

import Link from "next/link";
import MovieBackground from "./MovieBackground";

interface AuthFormProps {
  children: React.ReactNode;
  title: string;
  subtitle: string;
  linkText: string;
  linkHref: string;
  linkLabel: string;
}

export default function AuthForm({
  children,
  title,
  subtitle,
  linkText,
  linkHref,
  linkLabel,
}: AuthFormProps) {
  return (
    <MovieBackground>
      <main className="min-h-screen flex flex-col items-center justify-center px-4 py-8">
        {/* Logo */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-primary mb-2">🎬 CineBook</h1>
          <p className="text-text-muted text-sm">Your favorite movies, one tap away</p>
        </div>

        {/* Form Card */}
        <div className="w-full max-w-[330px] bg-surface/50 backdrop-blur-xl rounded-[20px] p-6 shadow-2xl border border-border/50">
          {/* Header */}
          <div className="mb-6">
            <h2 className="text-2xl font-semibold text-white mb-1">{title}</h2>
            <p className="text-text-muted text-sm">{subtitle}</p>
          </div>

          {/* Form Content */}
          {children}
        </div>

        {/* Link */}
        <p className="mt-6 text-text-muted text-sm">
          {linkText}{" "}
          <Link
            href={linkHref}
            className="text-primary hover:text-primary-hover transition-colors font-medium"
          >
            {linkLabel}
          </Link>
        </p>

        {/* Footer */}
        <p className="mt-8 text-text-muted/50 text-xs">
          By continuing, you agree to our Terms of Service and Privacy Policy
        </p>
      </main>
    </MovieBackground>
  );
}
