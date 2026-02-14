"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Image from "next/image";
import { useAuthStore } from "@/src/stores";
import {
  ToLoginButton,
  ToRegisterButton,
  ToAbout,
} from "@/src/components/Buttons";
import { useLoadingStore } from "@/src/stores";
import { CONSTANTS as CNST } from "@/src/config";

export default function DoorstepPage() {
  const router = useRouter();
  const { token } = useAuthStore();
  const { stopLoading, startLoading } = useLoadingStore();

  useEffect(() => {
    if (token) {
      startLoading();
      router.push(CNST.ROUTES.PRIVATE.CONTACTS);
    }
    stopLoading();
  }, [token, startLoading, stopLoading, router]);

  return (
    <div className="flex min-h-screen items-center justify-center font-sans">
      <main className="max-w-md w-full mx-4">
        <div className="text-center">
          <Image
            src="/logo.png"
            alt="The Likes"
            width={240}
            height={40}
            className="h-8 w-auto mx-auto inline-block"
            priority
          />

          <p className="mt-2">Find people with similar values</p>
        </div>

        <div className="space-y-4 mt-8">
          <ToLoginButton />
          <ToRegisterButton />
          <ToAbout className="flex justify-self-center py-2" />
        </div>
      </main>
    </div>
  );
}
