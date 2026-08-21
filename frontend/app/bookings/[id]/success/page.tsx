"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, BookingResponse } from "@/lib/api";

export default function BookingSuccessPage() {
  const params = useParams();
  const router = useRouter();
  const [booking, setBooking] = useState<BookingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const bookingId = params.id as string;

  useEffect(() => {
    async function fetchBooking() {
      try {
        setLoading(true);
        const data = await api.getBookingById(parseInt(bookingId));
        setBooking(data);
      } catch (err) {
        console.error("Failed to fetch booking:", err);
        setError("Failed to load booking details");
      } finally {
        setLoading(false);
      }
    }

    fetchBooking();
  }, [bookingId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#1E1F27] flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-[#D98639] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="min-h-screen bg-[#1E1F27]">
        <header className="bg-[#2A2B33] border-b border-[#3A3B44] px-4 py-4">
          <div className="max-w-2xl mx-auto">
            <h1 className="text-xl font-bold text-[#D98639]">🎬 CineBook</h1>
          </div>
        </header>
        <main className="max-w-2xl mx-auto px-4 py-12 text-center">
          <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-8">
            <p className="text-red-400 text-lg mb-4">{error || "Booking not found"}</p>
            <Link
              href="/movies"
              className="px-6 py-3 bg-[#D98639] hover:bg-[#C77A32] text-white rounded-lg transition-colors inline-block"
            >
              Browse Movies
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#1E1F27]">
      <header className="bg-[#2A2B33] border-b border-[#3A3B44] px-4 py-4">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-xl font-bold text-[#D98639]">🎬 CineBook</h1>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-12">
        {/* Success Icon */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-10 h-10 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Booking Confirmed!</h1>
          <p className="text-[#9A9BA3]">
            Your tickets have been booked successfully.
          </p>
        </div>

        {/* Booking Details Card */}
        <div className="bg-[#2A2B33] rounded-xl p-6 border border-[#3A3B44] mb-6">
          <div className="flex justify-between items-center mb-6 pb-4 border-b border-[#3A3B44]">
            <span className="text-[#9A9BA3]">Booking Code</span>
            <span className="text-2xl font-bold text-[#D98639] font-mono">
              {booking.booking_code}
            </span>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-[#9A9BA3]">Status</span>
              <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-medium">
                {booking.status.toUpperCase()}
              </span>
            </div>

            <div className="flex justify-between">
              <span className="text-[#9A9BA3]">Booking ID</span>
              <span className="text-white font-mono">#{booking.id}</span>
            </div>

            <div className="flex justify-between">
              <span className="text-[#9A9BA3]">Seats</span>
              <span className="text-white">
                {booking.seats.map((s) => s.seat_label).join(", ")}
              </span>
            </div>

            <div className="flex justify-between pt-4 border-t border-[#3A3B44]">
              <span className="text-lg font-semibold text-white">Total Paid</span>
              <span className="text-xl font-bold text-[#D98639]">
                ${Number(booking.total_price).toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <Link
            href="/movies"
            className="flex-1 px-6 py-3 bg-[#2A2B33] border border-[#3A3B44] text-white rounded-lg transition-colors text-center hover:bg-[#3A3B44]"
          >
            Book More
          </Link>
          <button
            onClick={() => {
              // Could implement print ticket functionality here
              window.print();
            }}
            className="flex-1 px-6 py-3 bg-[#D98639] hover:bg-[#C77A32] text-white rounded-lg transition-colors"
          >
            Print Ticket
          </button>
        </div>

        {/* Note */}
        <p className="text-[#9A9BA3] text-sm text-center mt-6">
          Please show this booking code at the cinema entrance.
        </p>
      </main>
    </div>
  );
}
