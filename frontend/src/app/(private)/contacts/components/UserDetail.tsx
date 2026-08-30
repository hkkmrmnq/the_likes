"use client";

import { useEffect, useState, useRef } from "react";
import { toast } from "sonner";

import {
  useLoadingStore,
  useSelectedUserStore,
  useSelectedSectionStore,
} from "@/src/stores";
import { ComponentError } from "@/src/errors";
import * as contactsService from "@/src/api/contacts";
import { handleErrorInComponent } from "@/src/utils";
import * as actn from "./userActions";

export function UserDetail() {
  const { selectedSection } = useSelectedSectionStore();
  const [alias, setAlias] = useState<string>("");
  const [error, setError] = useState("");
  const { selectedUser, setSelectedUser } = useSelectedUserStore();
  const { stopLoading } = useLoadingStore();

  if (selectedUser === null) {
    throw new ComponentError({
      message: "Chat component error: selectedUser === null.",
    });
  }

  const saveAlias = async () => {
    setError("");
    try {
      const updatedContact = await contactsService.updateContactAlias(
        selectedUser?.user_id,
        alias,
      );
      selectedUser.alias = updatedContact.alias;
      setSelectedUser(selectedUser);
    } catch (err) {
      toast.error("Something went wrong...");
      handleErrorInComponent(err, setError);
    }
  };

  const handleBlur = () => {
    if (selectedUser.alias === alias) return;
    saveAlias();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      (e.currentTarget as HTMLInputElement).blur();
    }
  };

  useEffect(() => {
    setAlias((!!selectedUser.alias && selectedUser.alias) || "");
    stopLoading();
  }, [stopLoading]);

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

  const usernameRow =
    (!!selectedUser.name && `Name: ${selectedUser.name}`) || "";
  const distanceRow =
    (!!selectedUser.distance && `Distance: ${selectedUser.distance}`) || "";

  return (
    <div className="flex flex-col h-full w-full items-center text-center text-lg py-8">
      {params[selectedSection]["message"]}
      <div className="py-4 space-y-4">
        <div>{usernameRow}</div>
        <div>
          Alias:
          <input
            id="alias"
            name="alias"
            type="text"
            value={alias}
            onChange={(e) => setAlias(e.target.value)}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-cyan-500 focus:border-cyan-500 text-center"
            placeholder="Alias if needed..."
          />
        </div>
        <div>Similarity score: {selectedUser.similarity}</div>
        <div>{distanceRow}</div>
        <ActionComponent
          userId={(!!selectedUser && selectedUser.user_id) || ""}
        />
      </div>
    </div>
  );
}
