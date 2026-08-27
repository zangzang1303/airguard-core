import React from "react";
import { Button, ButtonVariant } from "./Button";

interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  variant?: ButtonVariant;
}

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ label, title = label, variant = "ghost", ...props }, ref) => (
    <Button
      ref={ref}
      variant={variant}
      size="icon"
      aria-label={label}
      title={title}
      {...props}
    />
  ),
);

IconButton.displayName = "IconButton";

