"use client";
import { v4 as uuidv4 } from "uuid";

import { useState, useEffect, useCallback, useRef } from "react";

import * as str from "@/src/stores";
import { LoadingScreen } from "@/src/components";
import { UserButton } from "./Buttons";
import { Message } from "./Message";
import * as messagesService from "@/src/api/messages";
import { handleErrorInComponent } from "@/src/utils";
import * as exc from "@/src/errors";
import { useWSClientContext } from "@/src/hooks";

export function Chat() {
  const [waitingForApi, setWaitingForApi] = useState(true);
  const { setSelectedSection } = str.useSelectedSectionStore();
  const { selectedUser } = str.useSelectedUserStore();
  const { resetUnreadCount } = str.useContactsStore();
  const { sendChatMessage, isConnected } = useWSClientContext();
  if (selectedUser === null) {
    throw new exc.ComponentError({
      message: "selectedUser === null.",
    });
  }
  const { setConversationMessages } = str.useMessagesStore();
  const conversationMessages = str.useMessagesSelector((state) =>
    state.getConversationMessages(selectedUser.user_id),
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showInput, setShowInput] = useState(true);
  const [messageTextInput, setMessageTextInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState("");

  const submit = useCallback(() => {
    const directInput = inputRef.current?.value || "";
    sendChatMessage(directInput);
    setMessageTextInput("");
  }, [sendChatMessage]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversationMessages]);

  useEffect(() => {
    if (!waitingForApi && conversationMessages.length > 0) {
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "auto" });
      }, 100);
    }
  }, [waitingForApi, conversationMessages.length]);

  useEffect(() => {
    const getMessages = async () => {
      try {
        const contactId = selectedUser.user_id;
        if (conversationMessages.length === 0) {
          const response = await messagesService.getMessages(contactId);
          const display_messages = response.data.map((msg) => ({
            ...msg,
            pending: false,
            isIncoming: selectedUser.user_id === msg.sender_id,
            client_id: uuidv4(),
          }));
          setConversationMessages(contactId, display_messages);
        }
        resetUnreadCount(contactId);
        setWaitingForApi(false);
      } catch (err) {
        setWaitingForApi(false);
        handleErrorInComponent(err, setError);
      }
    };

    getMessages();
  }, [
    selectedUser,
    conversationMessages,
    setConversationMessages,
    resetUnreadCount,
    isConnected,
  ]);

  useEffect(() => {
    const handleEnter = (event: KeyboardEvent) => {
      if (event.key === "Enter") {
        submit();
      }
    };

    window.addEventListener("keydown", handleEnter);

    return () => {
      window.removeEventListener("keydown", handleEnter);
    };
  }, [submit]);

  if (waitingForApi) {
    return <LoadingScreen />;
  }
  if (error) {
    return <div className="text-red-500 text-sm mt-1">{error}</div>;
  }
  return (
    <div className="flex flex-col h-full w-full items-center">
      <div className="w-full max-w-[800px] flex flex-col h-full px-2">
        {/* Chat header */}
        <div className="flex items-center justify-center w-full h-10 flex-shrink-0 rounded-xl border border-gray-500 relative">
          {/* Name */}
          <div className="text-center text-lg">
            {selectedUser.name || "User"}
          </div>

          {/* User icon */}
          <div className="absolute right-3 top-2">
            <UserButton
              userId={selectedUser.user_id}
              onClick={() => {
                setSelectedSection("contactProfile");
              }}
            />
          </div>
        </div>

        {/* Messages area */}
        <div className="flex-1 min-h-0 overflow-hidden">
          <div className="h-full overflow-y-auto p-4 thin-scrollbar">
            <div className="space-y-4">
              {conversationMessages.length === 0 ? (
                <div className="h-full flex items-center justify-center text-gray-500 text-center">
                  <div>
                    <p className="text-lg mb-2">No messages yet</p>
                    <p className="text-sm">Start the conversation!</p>
                  </div>
                </div>
              ) : (
                <>
                  {conversationMessages.map((msg) => (
                    <Message message={msg} key={msg.client_id} />
                  ))}
                  <div ref={messagesEndRef} />
                </>
              )}
            </div>
          </div>
        </div>

        {/* Meesage input */}
        <div className="flex-shrink-0 pb-4">
          <button
            onClick={() => setShowInput(!showInput)}
            className="flex text-gray-600 hover:text-gray-400 text-sm cursor-pointer"
          >
            <svg
              className={`w-4 h-4 transition-transform ${
                showInput ? "" : "rotate-180"
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
          {showInput && (
            <div className="flex items-center gap-2">
              {/* Text input */}
              <div className="flex-1 relative">
                <input
                  type="text"
                  placeholder="Type a message..."
                  value={messageTextInput}
                  ref={inputRef}
                  className="w-full p-3 pr-12 rounded-xl border border-gray-400 outline-none"
                  onChange={(e) => setMessageTextInput(e.target.value)}
                />

                {/* Send button */}
                <button
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 p-2 text-cyan-800 hover:text-cyan-600 cursor-pointer"
                  onClick={() => submit()}
                >
                  <svg
                    className="w-6 h-6 transform rotate-90"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                  </svg>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
