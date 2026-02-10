"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useLoadingStore } from "@/src/stores";
import { LoadingScreen } from "@/src/components";
import { CONSTANTS as CNST } from "@/src/config";

export default function HomePage() {
  const router = useRouter();
  const { startLoading } = useLoadingStore();
  useEffect(() => {
    startLoading();
    router.push(CNST.ROUTES.PRIVATE.CONTACTS);
    // }
  }, [router, startLoading]);

  return <LoadingScreen />;
}
