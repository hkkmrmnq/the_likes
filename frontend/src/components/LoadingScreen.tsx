"use client";

import { useEffect } from "react";
import { useLoadingStore } from "@/src/stores/loading";
import { Spinner } from "@/src/components/Spinner";

interface BlockerProps {
  message?: string;
}

export function LoadingScreen({ message = "Loading..." }: BlockerProps) {
  useEffect(() => {
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = "auto";
    };
  }, []);

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="flex items-center justify-center gap-3">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        <p className="text-gray-700 dark:text-gray-300 font-medium">
          {message || <Spinner />}
        </p>
      </div>
    </div>
  );
}

export function BlockerManager() {
  const { isLoading, loadingMessage } = useLoadingStore();

  if (!isLoading) return null;

  return <LoadingScreen message={loadingMessage} />;
}
