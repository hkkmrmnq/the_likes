"use client";

import { useEffect } from "react";
import { useLoadingStore } from "@/src/stores";
import { Header } from "@/src/components";

export default function AboutPage() {
  const { stopLoading } = useLoadingStore();
  useEffect(() => {
    stopLoading();
  }, [stopLoading]);
  return (
    <div>
      <Header />
      <div>Placeholder</div>
    </div>
  );
}
