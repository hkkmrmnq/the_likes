"use client";

import { createContext, ReactNode } from "react"; // useEffect,

import { useWSClient } from "@/src/hooks";
import { WSClient } from "@/src/types";

export const WSClientContext = createContext<WSClient | null>(null);

export function WSClientProvider({ children }: { children: ReactNode }) {
  const wsClient = useWSClient();

  return (
    <WSClientContext.Provider value={wsClient}>
      {children}
    </WSClientContext.Provider>
  );
}
