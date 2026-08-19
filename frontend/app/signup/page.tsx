"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import AuthForm from "@/components/AuthForm";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { api } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone_number: "",
    birth_date: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState("");

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.first_name.trim()) {
      newErrors.first_name = "First name is required";
    } else if (formData.first_name.trim().length < 2) {
      newErrors.first_name = "First name must be at least 2 characters";
    }

    if (!formData.last_name.trim()) {
      newErrors.last_name = "Last name is required";
    } else if (formData.last_name.trim().length < 2) {
      newErrors.last_name = "Last name must be at least 2 characters";
    }

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email";
    }

    if (!formData.phone_number) {
      newErrors.phone_number = "Phone number is required";
    } else if (!/^[0-9]{10,15}$/.test(formData.phone_number.replace(/[\s-]/g, ""))) {
      newErrors.phone_number = "Please enter a valid phone number";
    }

    if (!formData.birth_date) {
      newErrors.birth_date = "Birth date is required";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
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
      await api.signup({
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        email: formData.email,
        phone_number: formData.phone_number.replace(/[\s-]/g, ""),
        birth_date: formData.birth_date,
        password: formData.password,
      });

      // Redirect to login page after successful signup
      router.push("/login?registered=true");
    } catch (error) {
      setApiError(
        error instanceof Error ? error.message : "Signup failed. Please try again."
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

  // Password strength indicator
  const getPasswordStrength = (password: string) => {
    if (!password) return { strength: 0, label: "", color: "" };

    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;

    const levels = [
      { label: "Very Weak", color: "bg-error" },
      { label: "Weak", color: "bg-orange-500" },
      { label: "Fair", color: "bg-yellow-500" },
      { label: "Good", color: "bg-primary" },
      { label: "Strong", color: "bg-success" },
    ];

    return {
      strength: Math.min(strength, 4),
      ...levels[Math.min(strength, 4)],
    };
  };

  const passwordStrength = getPasswordStrength(formData.password);

  return (
    <AuthForm
      title="Create Account"
      subtitle="Join CineBook and start booking"
      linkText="Already have an account?"
      linkHref="/login"
      linkLabel="Sign in"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {apiError && (
          <div className="p-3 bg-error/10 border border-error/20 rounded-[10px] text-error text-sm">
            {apiError}
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <Input
            label="First Name"
            name="first_name"
            type="text"
            placeholder="John"
            value={formData.first_name}
            onChange={handleChange}
            error={errors.first_name}
            autoComplete="given-name"
          />

          <Input
            label="Last Name"
            name="last_name"
            type="text"
            placeholder="Doe"
            value={formData.last_name}
            onChange={handleChange}
            error={errors.last_name}
            autoComplete="family-name"
          />
        </div>

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
          label="Phone Number"
          name="phone_number"
          type="tel"
          placeholder="0912345678"
          value={formData.phone_number}
          onChange={handleChange}
          error={errors.phone_number}
          autoComplete="tel"
        />

        <Input
          label="Birth Date"
          name="birth_date"
          type="date"
          placeholder="YYYY-MM-DD"
          value={formData.birth_date}
          onChange={handleChange}
          error={errors.birth_date}
          autoComplete="bday"
        />

        <div>
          <Input
            label="Password"
            name="password"
            type="password"
            placeholder="Create a password"
            value={formData.password}
            onChange={handleChange}
            error={errors.password}
            showPasswordToggle
            autoComplete="new-password"
          />
          {formData.password && (
            <div className="mt-2">
              <div className="flex gap-1 mb-1">
                {[0, 1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className={`h-1 flex-1 rounded-full transition-colors ${
                      i <= passwordStrength.strength
                        ? passwordStrength.color
                        : "bg-border"
                    }`}
                  />
                ))}
              </div>
              <p className="text-xs text-text-muted">
                Password strength: {passwordStrength.label}
              </p>
            </div>
          )}
        </div>

        <Input
          label="Confirm Password"
          name="confirmPassword"
          type="password"
          placeholder="Confirm your password"
          value={formData.confirmPassword}
          onChange={handleChange}
          error={errors.confirmPassword}
          showPasswordToggle
          autoComplete="new-password"
        />

        <div className="pt-2">
          <Button type="submit" className="w-full" isLoading={isLoading}>
            Create Account
          </Button>
        </div>
      </form>

      <p className="mt-4 text-xs text-text-muted text-center">
        By signing up, you agree to our{" "}
        <a href="#" className="text-primary hover:underline">
          Terms of Service
        </a>{" "}
        and{" "}
        <a href="#" className="text-primary hover:underline">
          Privacy Policy
        </a>
      </p>
    </AuthForm>
  );
}
