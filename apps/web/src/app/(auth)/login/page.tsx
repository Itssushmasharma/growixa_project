import type { Metadata } from "next";
import { Suspense } from "react";

import { AuthSplitLayout } from "@/components/auth/auth-split-layout";
import { LoginForm } from "@/components/auth/login-form";

export const metadata: Metadata = {
  title: "Log in to Growixa",
  description: "Sign in to your Growixa marketing workspace.",
  robots: { index: false, follow: false },
};

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <AuthSplitLayout mode="login">
        <LoginForm />
      </AuthSplitLayout>
    </Suspense>
  );
}
