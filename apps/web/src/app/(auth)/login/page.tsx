"use client";

import { Suspense } from "react";

import { AuthSplitLayout } from "@/components/auth/auth-split-layout";
import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <AuthSplitLayout mode="login">
        <LoginForm />
      </AuthSplitLayout>
    </Suspense>
  );
}
