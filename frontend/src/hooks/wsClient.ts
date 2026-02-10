"use client";
import { v4 as uuidv4 } from "uuid";

import { useEffect, useCallback } from "react";
import { toast } from "sonner";

import { createWebSocketManager } from "@/src/api";
import * as str from "@/src/stores";
import * as typ from "@/src/types";
import * as exc from "@/src/errors";

const wsManager = createWebSocketManager();

// Gives access to wsManager singleton, adds chat-specific behavior.
export const useWSClient: () => typ.WSClient = () => {
  const { token } = str.useAuthStore();
  const { user_id, name } = str.useProfileStore();
  const { incrementUnreadCount } = str.useContactsStore();
  const { addMessage, markMessageAsSent } = str.useMessagesStore();
  const { selectedUser } = str.useSelectedUserStore();

  const handleIncomingPayload = useCallback(
    (payload: typ.ChatPayload) => {
      console.log("handleIncomingPayload");
      switch (payload.payload_type) {
        case typ.ChatPayloadType.NEW:
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

        case typ.ChatPayloadType.SENT:
          const sentMessage = payload.related_content as typ.MessageSent;
          markMessageAsSent(sentMessage);
          break;

        case typ.ChatPayloadType.PING:
          const { ping_timestamp } = payload.related_content as {
            ping_timestamp: string;
          };
          wsManager.sendPayload({
            payload_type: typ.ChatPayloadType.PONG,
            related_content: { ping_timestamp },
            timestamp: new Date().toISOString(),
          });
          break;

        case typ.ChatPayloadType.PONG:
          break;

        case typ.ChatPayloadType.ERROR:
          const errorContent = payload.related_content as { error: string };
          console.error("Server error:", errorContent.error);
          break;

        default:
          const error = `Received unexpected payload: ${payload}`;
          console.error(error);
          toast.error(error);
      }
    },
    [selectedUser, addMessage, markMessageAsSent, incrementUnreadCount],
  );

  const sendChatMessage = useCallback(
    (text: string) => {
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
        payload_type: typ.ChatPayloadType.CREATE,
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
    [addMessage, selectedUser, user_id, name],
  );

  useEffect(() => {
    if (token) {
      console.log("useWSClient hook: mounting");
      wsManager.config.onPayload = handleIncomingPayload;
      wsManager.config.token = token;
      wsManager.connect();
    }
    return () => {
      console.log("useWSClient hook: unmounting");
      wsManager.disconnect();
    };
  }, [token, handleIncomingPayload]);

  return {
    sendChatMessage,
    isConnected: wsManager.isConnected,
    disconnect: wsManager.disconnect,
  };
};
