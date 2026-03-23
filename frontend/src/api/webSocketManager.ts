import { chatPayloadSchema } from "@/src/schemas";
import { API_CFG, CONSTANTS as CNST } from "@/src/config";
import { selectedUserStore, contactsStore } from "@/src/stores";
import * as typ from "@/src/types";

export type WebSocketManager = {
  config: typ.WSManagerConfig;
  connect: () => void;
  disconnect: () => void;
  isConnected: () => boolean;
  sendPayload: (payload: typ.ChatPayload) => void;
};

export const createWebSocketManager = (): WebSocketManager => {
  let ws: WebSocket | null = null;
  let reconnectAttempts = 0;
  const messageQueue: string[] = [];
  let isConnecting = false;
  let heartbeatInterval: NodeJS.Timeout | null = null;
  let lastReceived = Date.now();

  const config: typ.WSManagerConfig = {
    token: "",
    reconnectDelay: 3000,
    maxReconnectAttempts: 5,
    autoReconnect: true,
    onConnect: () => {},
    onDisconnect: () => {},
    onPayload: () => {},
    onError: () => {},
  };

  const clearHeartbeat = (): void => {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      heartbeatInterval = null;
    }
  };

  const startHeartbeat = (): void => {
    clearHeartbeat();
    lastReceived = Date.now();
    heartbeatInterval = setInterval(() => {
      const timeSinceLastReceived = Date.now() - lastReceived;

      if (timeSinceLastReceived > CNST.HEARTBEAT_INTERVAL_SECONDS * 1000) {
        const timestamp = new Date().toISOString();

        sendPayload({
          payload_type: typ.ChatPayloadType.PING,
          related_content: { origin: "FRONT" },
          timestamp: timestamp,
        });
      }

      if (timeSinceLastReceived > CNST.RECONNECT_AFTER_SECONDS * 1000) {
        console.warn("Silence to long. Reconnecting...");
        disconnect();
        handleReconnect();
      }
    }, CNST.HEARTBEAT_INTERVAL_SECONDS * 1000);
  };

  const flushMessageQueue = (): void => {
    while (messageQueue.length > 0 && ws?.readyState === WebSocket.OPEN) {
      const message = messageQueue.shift();
      if (message) {
        ws.send(message);
      }
    }
  };

  const handleReconnect = (): void => {
    if (reconnectAttempts >= config.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }

    reconnectAttempts++;
    const delay = config.reconnectDelay * Math.pow(1.5, reconnectAttempts - 1);

    setTimeout(() => {
      if (ws?.readyState !== WebSocket.OPEN) {
        connect();
      }
    }, delay);
  };

  const setupEventListeners = (): void => {
    if (!ws) return;

    ws.onopen = () => {
      isConnecting = false;
      reconnectAttempts = 0;
      lastReceived = Date.now();
      startHeartbeat();
      flushMessageQueue();
      config.onConnect();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const result = chatPayloadSchema.safeParse(data);
        const { selectedUser } = selectedUserStore.getState();
        const { storedRecommendations } = contactsStore.getState();
        if (result.success) {
          config.onPayload(result.data, selectedUser, storedRecommendations);
        } else {
          console.error("Invalid payload received:", result.error);
          config.onError("Invalid payload format");
        }
      } catch (error) {
        console.error("Error parsing message:", error);
        config.onError("Message parse error");
      } finally {
        lastReceived = Date.now();
      }
    };

    ws.onclose = (event) => {
      console.log("WebSocket closed"); // TODO remove
      console.log("Code:", event.code); // Close code (e.g., 1000, 1001, 1006)
      console.log("Reason:", event.reason); // Close reason string
      console.log("Was clean:", event.wasClean); // true if proper close
      clearHeartbeat();
      isConnecting = false;

      config.onDisconnect?.(event);
      if (![1000, 1006].includes(event.code) && config.autoReconnect) {
        handleReconnect();
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      config.onError?.("Connection error");
    };
  };

  const connect = (): void => {
    if (ws?.readyState === WebSocket.OPEN || isConnecting || !config.token) {
      return;
    }
    isConnecting = true;
    const url = `${API_CFG.WS_URL}?token=${encodeURIComponent(config.token)}`;

    try {
      ws = new WebSocket(url);
      setupEventListeners();
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      isConnecting = false;
      handleReconnect();
    }
  };

  const disconnect = (): void => {
    clearHeartbeat();

    if (ws) {
      ws.close(1000, "User initiated disconnect");
      ws = null;
    }

    isConnecting = false;
    reconnectAttempts = 0;
  };

  const isConnected = (): boolean => {
    return ws?.readyState === WebSocket.OPEN;
  };

  const sendPayload = (payload: typ.ChatPayload): void => {
    const jsonString = JSON.stringify(payload);

    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(jsonString);
    } else {
      if (
        payload.payload_type in
        [typ.ChatPayloadType.PING, typ.ChatPayloadType.PONG]
      )
        return;
      messageQueue.push(jsonString);
    }
  };

  return {
    config,
    connect,
    disconnect,
    isConnected,
    sendPayload,
  };
};
