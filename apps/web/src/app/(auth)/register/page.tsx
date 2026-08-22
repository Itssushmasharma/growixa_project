"use client";

import { Suspense } from "react";

import { AuthSplitLayout } from "@/components/auth/auth-split-layout";
import { RegisterForm } from "@/components/auth/register-form";

export default function RegisterPage() {
  return (
    <Suspense fallback={null}>
      <AuthSplitLayout mode="register">
        <RegisterForm />
      </AuthSplitLayout>
    </Suspense>
  );
}
