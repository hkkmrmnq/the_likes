"use client";

import { useCallback } from "react";
import { toast } from "sonner";

import {
  useLoadingStore,
  useSelectedUserStore,
  useContactsStore,
} from "@/src/stores";
import * as typ from "@/src/types/api";
import { handleErrorInComponent } from "@/src/utils";

export function useContactAction() {
  const { startLoading, stopLoading } = useLoadingStore();
  const {
    setContacts,
    setRequests,
    storedRecommendations,
    setRecommendations,
  } = useContactsStore();
  const { clearSelectedUser } = useSelectedUserStore();

  const createContactAction = useCallback(
    (
      serviceMethod: (
        userId: string,
      ) => Promise<typ.ContactsAndRequestsResponse>,
    ) => {
      return async (userId: string, setError?: (error: string) => void) => {
        try {
          startLoading();
          const response = await serviceMethod(userId);
          toast.info(response.message);
          const filteredRecs = storedRecommendations.filter(
            (rec) => rec.user_id !== userId,
          );
          setRecommendations(filteredRecs);
          setContacts(response.data.active_contacts);
          setRequests(response.data.contact_requests);
          clearSelectedUser();
        } catch (err) {
          if (setError) handleErrorInComponent(err, setError);
        } finally {
          stopLoading();
        }
      };
    },
    [
      startLoading,
      stopLoading,
      storedRecommendations,
      setRecommendations,
      setContacts,
      setRequests,
      clearSelectedUser,
    ],
  );

  return { createContactAction };
}
