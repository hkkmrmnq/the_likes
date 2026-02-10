"use client";

import { useEffect, useState } from "react";

import {
  useLoadingStore,
  useSelectedUserStore,
  useSelectedSectionStore,
} from "@/src/stores";
import { ComponentError } from "@/src/errors";
import * as contactsService from "@/src/api/contacts";
import { handleErrorInComponent } from "@/src/utils";
import { LoadingScreen } from "@/src/components";
import * as actn from "./userActions";
import { OtherProfile } from "@/src/types/api";

export function UserDetail() {
  const { selectedSection } = useSelectedSectionStore();
  const [contactProfile, setContactProfile] = useState<OtherProfile | null>(
    null,
  );
  const [error, setError] = useState("");
  const { selectedUser } = useSelectedUserStore();
  const { stopLoading } = useLoadingStore();

  useEffect(() => {
    const provideContactProfile = async () => {
      try {
        if (selectedUser === null) {
          throw new ComponentError({
            message: "Chat component error: selectedContact === null.",
          });
        }
        try {
          setContactProfile(selectedUser);
        } catch (err) {
          console.log(err);
          handleErrorInComponent(err, setError);
          const response = await contactsService.getContactProfile(
            selectedUser.user_id,
          );
          setContactProfile(response.data);
        }
      } catch (err) {
        handleErrorInComponent(err, setError);
      } finally {
        stopLoading();
      }
    };

    provideContactProfile();
  }, [selectedUser, stopLoading]);

  const params = {
    chat: { message: "error", buttonGroup: actn.ErrorDummy },
    contactProfile: {
      message: "Contact details",
      buttonGroup: actn.ContactProfileActions,
    },
    receivedRequest: {
      message: "Contact request from a user",
      buttonGroup: actn.ReceivedRequestActions,
    },
    sentRequest: {
      message: "Contact request to a user",
      buttonGroup: actn.SentRequestActions,
    },
    recommendation: {
      message: "Contact recommendation",
      buttonGroup: actn.RecommendationActions,
    },
    options: { message: "error", buttonGroup: actn.ErrorDummy },
  };

  const ActionComponent = params[selectedSection]["buttonGroup"];

  if (error) {
    return <div className="text-red-500 text-sm mt-1">{error}</div>;
  }

  if (contactProfile === null) return <LoadingScreen />;

  const usernameRow =
    (contactProfile.name !== null && `Name: ${contactProfile.name}`) || "";
  const distanceRow =
    (contactProfile.distance !== null &&
      `Distance: ${contactProfile.distance}`) ||
    "";

  return (
    <div className="flex flex-col h-full w-full items-center text-center text-lg py-8">
      {params[selectedSection]["message"]}
      <div className="py-4 space-y-4">
        <div>{usernameRow}</div>
        <div>Similarity score: {contactProfile.similarity}</div>
        <div>{distanceRow}</div>
        <ActionComponent
          userId={(!!selectedUser && selectedUser.user_id) || ""}
        />
      </div>
    </div>
  );
}
