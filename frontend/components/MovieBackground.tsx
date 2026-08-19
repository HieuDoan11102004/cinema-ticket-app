"use client";

interface MovieBackgroundProps {
  children: React.ReactNode;
}

export default function MovieBackground({ children }: MovieBackgroundProps) {
  return (
    <div className="min-h-screen w-full relative overflow-hidden">
      {/* Dark gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#1E1F27] via-[#1a1b22] to-[#0f1014]" />

      {/* Blurred movie poster overlay */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1920&q=80')`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          filter: "blur(80px)",
        }}
      />

      {/* Gradient overlay for readability */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#1E1F27] via-[#1E1F27]/80 to-[#1E1F27]/40" />

      {/* Content */}
      <div className="relative z-10">{children}</div>
    </div>
  );
}
