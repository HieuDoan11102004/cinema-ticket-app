"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "default" | "small";
  isLoading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className = "",
      variant = "primary",
      size = "default",
      isLoading = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "font-medium rounded-[10px] transition-all duration-200 flex items-center justify-center gap-2";

    const variants = {
      primary:
        "bg-primary text-white hover:bg-primary-hover active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed",
      secondary:
        "bg-surface text-white border border-border hover:bg-border active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed",
      ghost:
        "bg-transparent text-white hover:bg-surface/50 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed",
    };

    const sizes = {
      default: "h-[57px] px-6 text-[15px]",
      small: "h-10 px-4 text-sm",
    };

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <svg
              className="animate-spin h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span>Loading...</span>
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

export default Button;
