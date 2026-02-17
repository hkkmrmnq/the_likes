"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import * as str from "@/src/stores";
import { LoadingScreen } from "@/src/components/LoadingScreen";
import { CONSTANTS as CNST } from "@/src/config";
import { useWSClientContext } from "@/src/hooks";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { token, tokenHydrated, expiresAt, clearCreds } = str.useAuthStore();
  const { disconnect } = useWSClientContext();

  useEffect(() => {
    if (tokenHydrated) {
      if (!token || expiresAt < Date.now()) {
        clearCreds();
        disconnect();
        router.push(CNST.ROUTES.PUBLIC.DOORSTEP);
      }
    }
  }, [token, tokenHydrated, expiresAt, clearCreds, disconnect, router]);

  if (!tokenHydrated) return <LoadingScreen />;
  return <>{children}</>;
}
