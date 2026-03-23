"use client";
import { v4 as uuidv4 } from "uuid";
import { useCallback, useEffect, useContext } from "react";
import { toast } from "sonner";

import { createWebSocketManager } from "@/src/api";
import { WSClientContext } from "@/src/components";
import * as exc from "@/src/errors";

import * as str from "@/src/stores";
import * as typ from "@/src/types";

const wsManager = createWebSocketManager();

// Gives access to wsManager instance, adds chat-specific behavior.
export const useWSClient: () => typ.WSClient = () => {
  const { token } = str.useAuthStore();
  const { user_id, name } = str.useProfileStore();
  const { incrementUnreadCount, setRecommendations } = str.useContactsStore();
  const { addMessage, markMessageAsSent } = str.useMessagesStore();

  const handleIncomingPayload = useCallback(
    (
      payload: typ.ChatPayload,
      selectedUser: typ.SelectedUser | null,
      storedRecommendations: typ.Recommendation[],
    ) => {
      // console.log("Received payload:");
      // console.log(payload);
      switch (payload.payload_type) {
        case typ.ChatPayloadType.NEW_MSG:
          const msgDisplay = {
            ...payload.related_content,
            pending: false,
            isIncoming: true,
            client_id: uuidv4(),
          };
          addMessage(msgDisplay.sender_id, msgDisplay);
          if (
            selectedUser === null ||
            msgDisplay.sender_id !== selectedUser.user_id
          ) {
            incrementUnreadCount(msgDisplay.sender_id);
          }
          break;

        case typ.ChatPayloadType.MSG_SENT:
          const sentMessage = payload.related_content as typ.MessageSent;
          markMessageAsSent(sentMessage);
          break;

        case typ.ChatPayloadType.PING:
          wsManager.sendPayload({
            payload_type: typ.ChatPayloadType.PONG,
            related_content: { origin: "FRONT" },
            timestamp: new Date().toISOString(),
          });
          break;

        case typ.ChatPayloadType.PONG:
          break;

        case typ.ChatPayloadType.MSG_ERROR:
          const errorContent = payload.related_content as { error: string };
          console.error("Server error:", errorContent.error);
          break;

        case typ.ChatPayloadType.NEW_RECOMM:
          const newRecommendation = payload.related_content;
          const recommendedIds = storedRecommendations.map((r) => r.user_id);
          if (!recommendedIds.includes(newRecommendation.user_id)) {
            console.log("adding...");
            setRecommendations([newRecommendation, ...storedRecommendations]);
            toast.info("You have new recommendation!");
          }
          break;

        case typ.ChatPayloadType.NEW_REQUEST:
        case typ.ChatPayloadType.NEW_CHAT:
        case typ.ChatPayloadType.BLOCKED_BY:
          break;

        default:
          const error = `Received unexpected payload: ${payload}`;
          console.error(error);
          toast.error(error);
      }
    },
    [addMessage, markMessageAsSent, incrementUnreadCount, setRecommendations],
  );

  const sendChatMessage = useCallback(
    (text: string, selectedUser: typ.SelectedUser) => {
      if (selectedUser === null) {
        throw new exc.ComponentError({ message: "selectedUser === null" });
      }
      if (!text) return;

      const messagePaylod = {
        receiver_id: selectedUser.user_id,
        text,
        client_id: uuidv4(),
      };
      wsManager.sendPayload({
        payload_type: typ.ChatPayloadType.CREATE_MSG,
        related_content: messagePaylod,
        timestamp: new Date().toISOString(),
      });
      const messageDisplay = {
        ...messagePaylod,
        created_at: "...",
        time: "...",
        receiver_name: selectedUser.name,
        sender_id: user_id,
        sender_name: name,
        isIncoming: false,
        pending: true,
      };
      addMessage(selectedUser.user_id, messageDisplay);
    },
    [addMessage, user_id, name],
  );

  useEffect(() => {
    if (token) {
      wsManager.config.onPayload = handleIncomingPayload;
      wsManager.config.token = token;
      wsManager.connect();
    }
    return () => {
      // TODO ????????
      wsManager.disconnect();
    };
  }, [token, handleIncomingPayload]);

  return {
    sendChatMessage,
    isConnected: wsManager.isConnected,
    disconnect: wsManager.disconnect,
  };
};

export function useWSClientContext() {
  const wsClient = useContext(WSClientContext);
  if (!wsClient) {
    throw new Error(
      "useWSClientContext must be used within WebSocketClientProvider",
    );
  }
  return wsClient;
}
