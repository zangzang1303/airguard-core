import React from "react";

export type ButtonVariant = "primary" | "outline" | "ghost" | "destructive" | "success";
export type ButtonSize = "default" | "sm" | "icon";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "outline", size = "default", type = "button", ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={`button button--${variant} button--${size} ${className}`.trim()}
      {...props}
    />
  ),
);

Button.displayName = "Button";

