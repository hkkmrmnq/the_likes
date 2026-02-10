"use client";

import { useEffect } from "react";

import { useSelectedUserStore, useSelectedSectionStore } from "@/src/stores";
import { Chat } from "./Chat";
import { UserDetail } from "./UserDetail";
import { ActionButton } from "@/src/components";
import { Options } from "./Options";

export function ContentBox() {
  const { selectedUser, clearSelectedUser } = useSelectedUserStore();
  const { selectedSection, setSelectedSection } = useSelectedSectionStore();
  useEffect(() => {
    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        clearSelectedUser();
        setSelectedSection("chat");
      }
    };

    window.addEventListener("keydown", handleEsc);

    return () => {
      window.removeEventListener("keydown", handleEsc);
    };
  }, [clearSelectedUser, setSelectedSection]);

  if (!selectedUser) {
    if (selectedSection === "options") {
      return (
        <div className="h-full w-full">
          <Options />
        </div>
      );
    }
    return (
      <div className="h-full w-full flex items-center justify-center text-gray-500">
        <div>
          Select a conversation to start mesaging.
          <ActionButton
            action={() => {
              setSelectedSection("options");
            }}
            className="text-gray-400 py-3 px-4 rounded-lg font-medium hover:bg-gray-800 transition-colors cursor-pointer"
            label="More options"
          />
        </div>
      </div>
    );
  }

  if (selectedSection === "chat") {
    return (
      <div className="h-full w-full">
        <Chat />
      </div>
    );
  }

  return (
    <div className="h-full w-full">
      <UserDetail />
    </div>
  );
}
