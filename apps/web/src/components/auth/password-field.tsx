"use client";

import { type InputHTMLAttributes, useState } from "react";

import { EyeIcon, EyeOffIcon, LockIcon } from "./auth-icons";
import styles from "./auth.module.css";

interface PasswordFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
  id?: string;
}

export function PasswordField({
  label = "Password",
  id = "password",
  className,
  ...props
}: PasswordFieldProps) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className={styles.fieldGroup}>
      {label && (
        <label htmlFor={id} className={styles.label}>
          {label}
        </label>
      )}
      <div className={styles.inputWrapper}>
        <span className={styles.inputIcon} aria-hidden="true">
          <LockIcon />
        </span>
        <input
          {...props}
          id={id}
          type={showPassword ? "text" : "password"}
          className={`${styles.inputWithIcons} ${className || ""}`}
          placeholder={props.placeholder || "••••••••"}
        />
        <button
          type="button"
          className={styles.passwordToggle}
          onClick={() => setShowPassword((prev) => !prev)}
          aria-label={showPassword ? "Hide characters" : "Show characters"}
          tabIndex={-1}
        >
          {showPassword ? <EyeOffIcon /> : <EyeIcon />}
        </button>
      </div>
    </div>
  );
}
