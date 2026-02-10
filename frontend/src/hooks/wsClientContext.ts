import { useContext } from "react";

import { WSClientContext } from "@/src/components";

export function useWSClientContext() {
  const wsClient = useContext(WSClientContext);
  if (!wsClient) {
    throw new Error(
      "useWSClientContext must be used within WebSocketClientProvider",
    );
  }
  return wsClient;
}
