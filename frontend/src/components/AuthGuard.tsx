"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import * as str from "@/src/stores";
import { LoadingScreen } from "@/src/components/LoadingScreen";
import { CONSTANTS as CNST } from "@/src/config";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { token, tokenHydrated, expiresAt, clearCreds } = str.useAuthStore();

  useEffect(() => {
    if (tokenHydrated) {
      if (!token || expiresAt < Date.now()) {
        clearCreds();
        router.push(CNST.ROUTES.PUBLIC.DOORSTEP);
      }
    }
  }, [token, tokenHydrated, expiresAt, clearCreds, router]);

  if (!tokenHydrated) return <LoadingScreen />;
  return <>{children}</>;
}
