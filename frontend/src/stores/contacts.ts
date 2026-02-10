import { createStore } from "zustand/vanilla";
import { persist } from "zustand/middleware";
import { useStore } from "zustand";

import { ContactRich, ContactsStore } from "@/src/types";
import * as exc from "@/src/errors";

export const contactsStore = createStore<ContactsStore>()(
  persist(
    (set, get) => ({
      storedContacts: [],
      setContacts: (new_contacts: ContactRich[]) =>
        set({
          storedContacts: new_contacts,
        }),
      storedRequests: [],
      setRequests: (new_requests: ContactRich[]) =>
        set({
          storedRequests: new_requests,
        }),
      storedRecommendations: [],
      setRecommendations: (newRecommendations) =>
        set({ storedRecommendations: newRecommendations }),
      incrementUnreadCount: (contactId, by = 1) => {
        const newContacts = [...get().storedContacts];
        const targetContact = newContacts.find(
          (elem) => elem.user_id === contactId,
        );
        if (!targetContact) {
          throw new exc.AppError({
            message: "incrementUnreadCount error: contact not found",
            code: "STORE_ERROR",
          });
        }
        targetContact.unread_messages += by;
        set({ storedContacts: newContacts });
      },
      resetUnreadCount: (contactId) => {
        const newContacts = [...get().storedContacts];
        const targetContact = newContacts.find(
          (elem) => elem.user_id === contactId,
        );
        if (!targetContact) {
          throw new exc.AppError({
            message: "resetUnreadCount error: contact not found",
            code: "STORE_ERROR",
          });
        }
        targetContact.unread_messages = 0;
        set({ storedContacts: newContacts });
      },
      clearContactsStore: () =>
        set({
          storedRecommendations: [],
          storedRequests: [],
          storedContacts: [],
        }),
    }),

    {
      name: "contacts-storage",
      partialize: (state) => ({
        storedContacts: state.storedContacts,
        storedRequests: state.storedRequests,
        storedRecommendations: state.storedRecommendations,
      }),
    },
  ),
);

export const useContactsStore = () => useStore(contactsStore);
