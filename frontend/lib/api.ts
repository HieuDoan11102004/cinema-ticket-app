const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  address?: string;
  phone_number?: string;
  birth_date?: string;
}

export interface SignupRequest {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  address?: string;
  phone_number?: string;
  birth_date?: string;
}

export interface FilmResponse {
  id: number;
  title: string;
  original_title: string | null;
  tagline: string | null;
  overview: string | null;
  release_date: string | null;
  poster_url: string | null;
  backdrop_url: string | null;
  trailer_url: string | null;
  genres: string[];
  original_language: string;
  spoken_languages: string[];
  production_countries: string[];
  production_companies: string[];
  runtime: number | null;
  status: string | null;
  adult: boolean;
  tmdb_id: number | null;
  imdb_id: string | null;
  homepage: string | null;
  budget: number;
  revenue: number;
  vote_average: number;
  vote_count: number;
  popularity: number;
}

export interface FilmListResponse {
  films: FilmResponse[];
  total: number;
  page: number;
  per_page: number;
}

export interface ShowtimeResponse {
  id: number;
  film_id: number;
  film_title: string;
  cinema_room: string;
  start_time: string;
  base_price: number;
}

export interface ShowtimeListResponse {
  showtimes: ShowtimeResponse[];
  total: number;
}

export interface SeatResponse {
  id: number;
  showtime_id: number;
  seat_label: string;
  status: "available" | "held" | "booked";
}

export interface SeatListResponse {
  seats: SeatResponse[];
  total: number;
}

export interface HoldSeatsRequest {
  seat_ids: number[];
  showtime_id: number;
}

export interface ReleaseSeatsRequest {
  seat_ids: number[];
  showtime_id: number;
}

export interface SeatActionResponse {
  success: boolean;
  message: string;
  released_seats: SeatResponse[];
}

// Booking types
export type BookingStatus = "pending" | "confirmed" | "cancelled";

export interface BookingResponse {
  id: number;
  user_id: string;
  showtime_id: number;
  booking_code: string;
  total_price: number;
  status: BookingStatus;
  expires_at: string | null;
  cancelled_at: string | null;
  cancellation_reason: string | null;
  created_at: string;
  updated_at: string | null;
  seats: SeatResponse[];
}

export interface BookingListResponse {
  bookings: BookingResponse[];
  total: number;
}

export interface BookingActionResponse {
  success: boolean;
  message: string;
  booking: BookingResponse | null;
}

export interface CreateBookingRequest {
  seat_ids: number[];
  showtime_id: number;
}

// Payment types
export type PaymentProvider = "stripe" | "vnpay" | "momo";
export type PaymentStatus = "pending" | "succeeded" | "failed" | "refunded";

export interface CheckoutResponse {
  checkout_url: string;
  payment_id: number;
  amount: number;
  provider: PaymentProvider;
  expires_at: string;
}

export interface PaymentResponse {
  id: number;
  booking_id: number;
  provider: PaymentProvider;
  status: PaymentStatus;
  amount: number;
  created_at: string;
  updated_at: string | null;
}

export interface CreateCheckoutRequest {
  booking_id: number;
}

export interface ApiError {
  detail: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const config: RequestInit = {
      ...options,
      credentials: "include", // Important: send cookies automatically
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });

    // Tokens are now stored in HttpOnly cookies by the backend
    // No need to store in localStorage

    return response;
  }

  async signup(data: SignupRequest): Promise<UserResponse> {
    return this.request<UserResponse>("/api/v1/auth/signup", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async logout(): Promise<void> {
    try {
      await this.request("/api/v1/auth/logout", {
        method: "POST",
      });
    } catch {
      // Ignore errors on logout
    }

    // Clear user data from localStorage
    if (typeof window !== "undefined") {
      localStorage.removeItem("user");
    }
  }

  async getCurrentUser(): Promise<UserResponse | null> {
    try {
      const user = await this.request<UserResponse>("/api/v1/auth/me", {
        // No Authorization header needed - cookie is sent automatically
      });

      // Store user data for quick access
      if (typeof window !== "undefined") {
        localStorage.setItem("user", JSON.stringify(user));
      }

      return user;
    } catch {
      return null;
    }
  }

  getUser(): UserResponse | null {
    if (typeof window !== "undefined") {
      const userStr = localStorage.getItem("user");
      if (userStr) {
        try {
          return JSON.parse(userStr);
        } catch {
          return null;
        }
      }
    }
    return null;
  }

  isAuthenticated(): boolean {
    // Check if we have a user cached (quick client-side check)
    // The real check is server-side via /me endpoint
    if (typeof window !== "undefined") {
      return localStorage.getItem("user") !== null;
    }
    return false;
  }

  async refreshToken(): Promise<boolean> {
    try {
      await this.request("/api/v1/auth/refresh", {
        method: "POST",
      });
      return true;
    } catch {
      return false;
    }
  }

  async getFilms(page: number = 1, limit: number = 20): Promise<FilmListResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/films?skip=${(page - 1) * limit}&limit=${limit}`,
      {
        credentials: "include", // Send auth cookies
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getFilmById(id: number): Promise<FilmResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/films/${id}`, {
      credentials: "include", // Send auth cookies
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async searchFilms(params: {
    q?: string;
    genres?: string[];
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<FilmListResponse> {
    const searchParams = new URLSearchParams();

    if (params.q) searchParams.set("q", params.q);
    if (params.genres && params.genres.length > 0) {
      searchParams.set("genres", params.genres.join(","));
    }
    if (params.status) searchParams.set("status", params.status);
    if (params.skip) searchParams.set("skip", params.skip.toString());
    if (params.limit) searchParams.set("limit", params.limit.toString());

    const response = await fetch(
      `${this.baseUrl}/api/v1/films?${searchParams.toString()}`,
      {
        credentials: "include",
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getFilmShowtimes(filmId: number): Promise<ShowtimeResponse[]> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/films/${filmId}/showtimes`,
      {
        credentials: "include",
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data: ShowtimeListResponse = await response.json();
    return data.showtimes;
  }

  async getShowtimeById(id: number): Promise<ShowtimeResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/showtimes/${id}`, {
      credentials: "include",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getShowtimeSeats(showtimeId: number): Promise<SeatListResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/showtimes/${showtimeId}/seats`,
      {
        credentials: "include",
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async holdSeats(seatIds: number[], showtimeId: number): Promise<SeatActionResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/seats/hold`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        seat_ids: seatIds,
        showtime_id: showtimeId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async releaseSeats(seatIds: number[], showtimeId: number): Promise<SeatActionResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/seats/release`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        seat_ids: seatIds,
        showtime_id: showtimeId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // ============ Booking Methods ============

  async createBooking(seatIds: number[], showtimeId: number): Promise<BookingActionResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/bookings`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        seat_ids: seatIds,
        showtime_id: showtimeId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getBookings(skip: number = 0, limit: number = 100): Promise<BookingListResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/bookings?skip=${skip}&limit=${limit}`,
      {
        credentials: "include",
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getBookingById(bookingId: number): Promise<BookingResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/bookings/${bookingId}`, {
      credentials: "include",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async cancelBooking(bookingId: number, reason?: string): Promise<BookingActionResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/bookings/${bookingId}/cancel`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        reason: reason || null,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // ============ Payment Methods ============

  async createCheckout(bookingId: number): Promise<CheckoutResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/payments/create-checkout`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        booking_id: bookingId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getPayment(paymentId: number): Promise<PaymentResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/payments/${paymentId}`, {
      credentials: "include",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Mock payment completion for testing (remove in production)
  async mockPaymentComplete(paymentId: number): Promise<PaymentResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/payments/mock-checkout/${paymentId}/complete`,
      {
        method: "POST",
        credentials: "include",
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Mock payment failure for testing (remove in production)
  async mockPaymentFail(paymentId: number): Promise<PaymentResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/payments/mock-checkout/${paymentId}/fail`,
      {
        method: "POST",
        credentials: "include",
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }
}

export const api = new ApiClient(API_BASE_URL);
