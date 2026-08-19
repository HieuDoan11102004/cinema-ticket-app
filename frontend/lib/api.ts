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

    // Store tokens in localStorage on successful login
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", response.access_token);
      localStorage.setItem("refresh_token", response.refresh_token);
    }

    return response;
  }

  async signup(data: SignupRequest): Promise<UserResponse> {
    return this.request<UserResponse>("/api/v1/auth/signup", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async logout(): Promise<void> {
    const token = this.getToken();
    if (token) {
      try {
        await this.request("/api/v1/auth/logout", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
      } catch {
        // Ignore errors on logout
      }
    }

    // Clear stored tokens
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
    }
  }

  getToken(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem("access_token");
    }
    return null;
  }

  async getCurrentUser(): Promise<UserResponse | null> {
    const token = this.getToken();
    if (!token) return null;

    try {
      const user = await this.request<UserResponse>("/api/v1/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      // Store user data
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
    return this.getToken() !== null;
  }
}

export const api = new ApiClient(API_BASE_URL);
