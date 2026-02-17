import { chatPayloadSchema } from "@/src/schemas";
import { API_CFG } from "@/src/config";
import { selectedUserStore } from "@/src/stores";
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
  let lastReceived = 0;

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
    heartbeatInterval = setInterval(() => {
      const timeSinceLastReceived = Date.now() - lastReceived;

      if (timeSinceLastReceived > 20000) {
        const timestamp = new Date().toISOString();

        sendPayload({
          payload_type: typ.ChatPayloadType.PING,
          related_content: { ping_timestamp: timestamp },
          timestamp: timestamp,
        });
        console.debug("ping sent");
      }

      if (timeSinceLastReceived > 60000) {
        console.warn("Heartbeat timeout, reconnecting...");
        disconnect();
        handleReconnect();
      }
    }, 10000);
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

    console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`);

    setTimeout(() => {
      if (ws?.readyState !== WebSocket.OPEN) {
        connect();
      }
    }, delay);
  };

  const setupEventListeners = (): void => {
    if (!ws) return;

    ws.onopen = () => {
      console.log("WebSocket connected");
      isConnecting = false;
      reconnectAttempts = 0;
      lastReceived = Date.now();
      // startHeartbeat();
      flushMessageQueue();
      config.onConnect();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const result = chatPayloadSchema.safeParse(data);
        const { selectedUser } = selectedUserStore.getState();
        if (result.success) {
          config.onPayload(result.data, selectedUser);
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
      //
      console.log({
        code: event.code,
        reason: event.reason || "No reason provided",
        timestamp: new Date().toISOString(),
        wasClean: event.wasClean,
        pageVisibility: document.visibilityState,
      });

      clearHeartbeat();
      isConnecting = false;

      config.onDisconnect?.(event);
      console.debug(`event.code=${event.code}`);
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
      console.log(
        `ws connect() aborted: ws?.readyState: ${ws?.readyState}, 
        isConnecting: ${isConnecting}, !!token: ${!!config.token}`,
      );
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
      console.log("Message queued, connection not ready");
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
