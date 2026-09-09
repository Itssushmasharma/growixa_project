import type { Metadata } from "next";
import { Suspense } from "react";

import { AuthSplitLayout } from "@/components/auth/auth-split-layout";
import { RegisterForm } from "@/components/auth/register-form";

export const metadata: Metadata = {
  title: "Create your Growixa workspace",
  description:
    "Start your Growixa workspace and turn marketing goals into approved, measurable campaigns.",
  robots: { index: false, follow: false },
};

export default function RegisterPage() {
  return (
    <Suspense fallback={null}>
      <AuthSplitLayout mode="register">
        <RegisterForm />
      </AuthSplitLayout>
    </Suspense>
  );
}
