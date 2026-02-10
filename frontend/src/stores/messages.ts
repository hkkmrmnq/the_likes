import { createStore, useStore } from "zustand";
import { persist } from "zustand/middleware";
import { MessagesState, MessageSent } from "@/src/types";

const EMPTY_ARRAY: never[] = [];

export const messagesStore = createStore<MessagesState>()(
  persist(
    (set, get) => ({
      conversations: {},

      addMessage: (contactId, message) =>
        set((state) => {
          const currentConversation = state.conversations[contactId];

          const newMessages = [
            ...(currentConversation?.messages || []),
            message,
          ];
          return {
            conversations: {
              ...state.conversations,
              [contactId]: {
                messages: newMessages,
                unread_count: currentConversation?.unread_count || 0,
              },
            },
          };
        }),

      getConversationMessages: (contactId) => {
        if (contactId === null) return EMPTY_ARRAY;
        const conversation = get().conversations[contactId];
        return conversation?.messages || EMPTY_ARRAY;
      },

      setConversationMessages: (contactId, messages) =>
        set((state) => {
          const currentConversation = state.conversations[contactId];

          return {
            conversations: {
              ...state.conversations,
              [contactId]: {
                messages: messages,
                // Keep existing unread_count or default to 0
                unread_count: currentConversation?.unread_count || 0,
              },
            },
          };
        }),

      markMessageAsSent: (confirmedMsg: MessageSent) =>
        set((state) => {
          const targetConversation =
            state.conversations[confirmedMsg.receiver_id];

          if (!targetConversation) {
            console.warn(
              `No conversation found for receiver_id: ${confirmedMsg.receiver_id}`,
            );
            return state;
          }

          const updatedConversation = {
            ...targetConversation,
            messages: targetConversation.messages.map((msg) => {
              if (confirmedMsg.client_id === msg.client_id) {
                return {
                  ...msg,
                  pending: false,
                  created_at: confirmedMsg.created_at,
                  time: confirmedMsg.time,
                };
              }
              return msg;
            }),
          };

          return {
            conversations: {
              ...state.conversations,
              [confirmedMsg.receiver_id]: updatedConversation,
            },
          };
        }),

      clearMessages: () => set({ conversations: {} }),
    }),
    {
      name: "chat-storage",
      partialize: (state) => ({ all_messages: state.conversations }),
    },
  ),
);

export const useMessagesStore = () => useStore(messagesStore);

export const useMessagesSelector = <T>(selector: (state: MessagesState) => T) =>
  useStore(messagesStore, selector);
