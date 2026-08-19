"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import AuthForm from "@/components/AuthForm";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { api } from "@/lib/api";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState("");
  const [registeredMessage, setRegisteredMessage] = useState("");

  useEffect(() => {
    if (searchParams.get("registered") === "true") {
      setRegisteredMessage("Account created successfully! Please sign in.");
    }
  }, [searchParams]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError("");

    if (!validateForm()) return;

    setIsLoading(true);

    try {
      // Login and get token
      await api.login({
        email: formData.email,
        password: formData.password,
      });

      // Fetch user data
      const user = await api.getCurrentUser();
      if (user) {
        // Store user for session
        if (typeof window !== "undefined") {
          localStorage.setItem("user", JSON.stringify(user));
        }
      }

      // Redirect to movies page after successful login
      router.push("/movies");
    } catch (error) {
      setApiError(
        error instanceof Error ? error.message : "Login failed. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {registeredMessage && (
        <div className="p-3 bg-success/10 border border-success/20 rounded-[10px] text-success text-sm">
          {registeredMessage}
        </div>
      )}

      {apiError && (
        <div className="p-3 bg-error/10 border border-error/20 rounded-[10px] text-error text-sm">
          {apiError}
        </div>
      )}

      <Input
        label="Email"
        name="email"
        type="email"
        placeholder="your@email.com"
        value={formData.email}
        onChange={handleChange}
        error={errors.email}
        autoComplete="email"
      />

      <Input
        label="Password"
        name="password"
        type="password"
        placeholder="Enter your password"
        value={formData.password}
        onChange={handleChange}
        error={errors.password}
        showPasswordToggle
        autoComplete="current-password"
      />

      <div className="pt-2">
        <Button type="submit" className="w-full" isLoading={isLoading}>
          Sign In
        </Button>
      </div>
    </form>
  );
}

function LoginFormFallback() {
  return (
    <div className="space-y-4">
      <div className="h-[76px] bg-surface/50 rounded-[10px] animate-pulse" />
      <div className="h-[76px] bg-surface/50 rounded-[10px] animate-pulse" />
      <div className="h-[57px] bg-primary/50 rounded-[10px] animate-pulse" />
    </div>
  );
}

export default function LoginPage() {
  return (
    <AuthForm
      title="Welcome Back"
      subtitle="Sign in to continue booking movies"
      linkText="Don't have an account?"
      linkHref="/signup"
      linkLabel="Sign up"
    >
      <Suspense fallback={<LoginFormFallback />}>
        <LoginForm />
      </Suspense>

      <div className="mt-4 text-center">
        <a
          href="#"
          className="text-sm text-text-muted hover:text-primary transition-colors"
        >
          Forgot your password?
        </a>
      </div>
    </AuthForm>
  );
}
