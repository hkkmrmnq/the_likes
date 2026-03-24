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
  const {
    incrementUnreadCount,
    setRecommendations,
    storedRequests,
    setRequests,
    storedContacts,
    setContacts,
  } = str.useContactsStore();
  const { addMessage, markMessageAsSent } = str.useMessagesStore();

  const handleIncomingPayload = useCallback(
    (
      payload: typ.ChatPayload,
      selectedUser: typ.SelectedUser | null,
      storedRecommendations: typ.Recommendation[],
    ) => {
      const currentRecommsIds = storedRecommendations.map((r) => r.user_id);
      const currentRequestsIds = storedRequests.map((req) => req.user_id);
      const currentChatsIds = storedContacts.map((cnt) => cnt.user_id);
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
          if (!currentRecommsIds.includes(newRecommendation.user_id)) {
            setRecommendations([newRecommendation, ...storedRecommendations]);
            toast.info("New recommendation!");
          }
          break;

        case typ.ChatPayloadType.NEW_REQUEST:
          const newRequest = payload.related_content;
          if (currentRecommsIds.includes(newRequest.user_id)) {
            const filteredRecomms = storedRecommendations.filter(
              (rec) => rec.user_id !== newRequest.user_id,
            );
            setRecommendations(filteredRecomms);
          }
          if (!currentRequestsIds.includes(newRequest.user_id)) {
            setRequests([...storedRequests, newRequest]);
            toast.info("New chat request!");
          }
          break;

        case typ.ChatPayloadType.REQUEST_CLOSED:
          const closedRequest = payload.related_content;
          if (currentRequestsIds.includes(closedRequest.user_id)) {
            const filteredRequests = storedRequests.filter(
              (rqst) => rqst.user_id !== closedRequest.user_id,
            );
            setRequests(filteredRequests);
          }
          break;

        case typ.ChatPayloadType.NEW_CHAT:
          const newActiveContact = payload.related_content;
          if (currentRequestsIds.includes(newActiveContact.user_id)) {
            const filteredRequests = storedRequests.filter(
              (rec) => rec.user_id !== newActiveContact.user_id,
            );
            setRequests(filteredRequests);
          }
          if (!currentChatsIds.includes(newActiveContact.user_id)) {
            setContacts([...storedContacts, newActiveContact]);
            toast.info("New chat started!");
          }
          break;

        case typ.ChatPayloadType.BLOCKED_BY:
          const contactWhoBlocks = payload.related_content;
          if (currentChatsIds.includes(contactWhoBlocks.user_id)) {
            const filteredContacts = storedContacts.filter(
              (contact) => contact.user_id !== contactWhoBlocks.user_id,
            );
            setContacts(filteredContacts);
          }
          break;

        case typ.ChatPayloadType.UNBLOCKED_BY:
          const contactWhoUnblocks = payload.related_content;
          console.log("UNBLOCKED_BY");
          console.log(contactWhoUnblocks);
          console.log("activeChatsIds:");
          console.log(currentChatsIds);
          if (!currentChatsIds.includes(contactWhoUnblocks.user_id)) {
            setContacts([...storedContacts, contactWhoUnblocks]);
          }
          break;

        default:
          const errMsg = "Received unexpected payload:";
          console.error(errMsg);
          console.error(payload);
          toast.error(errMsg);
      }
    },
    [
      addMessage,
      markMessageAsSent,
      incrementUnreadCount,
      setRecommendations,
      storedRequests,
      setRequests,
      storedContacts,
      setContacts,
    ],
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
