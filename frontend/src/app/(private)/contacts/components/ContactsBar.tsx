import { SquareArrowUpRight, SquareArrowDownLeft } from "lucide-react";

import { truncate } from "@/src/utils";
import { CONSTANTS as CNST } from "@/src/config";
import * as str from "@/src/stores";
import { ContactRich, OtherProfile } from "@/src/types";

function RecommendationsBox({
  recommendations,
}: {
  recommendations: OtherProfile[];
}) {
  const { selectedUser, setSelectedUser } = str.useSelectedUserStore();
  const { setSelectedSection } = str.useSelectedSectionStore();
  if (recommendations.length === 0) return null;
  return (
    <div className="h-full overflow-y-auto thin-scrollbar bg-gray-800">
      {recommendations.map((recommendation) => (
        <button
          key={recommendation.user_id}
          className={
            (selectedUser?.user_id === recommendation.user_id
              ? "bg-gray-600 hover:bg-gray-500 "
              : "hover:bg-gray-600 ") +
            "w-full flex py-4 space-y-1 rounded-lg cursor-pointer transition-colors"
          }
          onClick={() => {
            setSelectedUser(recommendation);
            setSelectedSection("recommendation");
          }}
        >
          <span className="flex-1">
            {truncate(recommendation.name || "User", CNST.SMALL_USERNAME)}
          </span>
        </button>
      ))}
    </div>
  );
}

function RequestsBox({ requests }: { requests: ContactRich[] }) {
  const { selectedUser, setSelectedUser } = str.useSelectedUserStore();
  const { setSelectedSection } = str.useSelectedSectionStore();
  if (requests.length === 0) return null;
  return (
    <div className="h-full overflow-y-auto thin-scrollbar bg-gray-800">
      {requests.map((contactRequest) => (
        <button
          key={contactRequest.user_id}
          className={
            (selectedUser?.user_id === contactRequest.user_id
              ? "bg-gray-600 hover:bg-gray-500 "
              : "hover:bg-gray-600 ") +
            "w-full flex py-4 space-y-1 rounded-lg cursor-pointer transition-colors"
          }
          onClick={() => {
            setSelectedUser(contactRequest);
            setSelectedSection(
              contactRequest.status === "requested by me"
                ? "sentRequest"
                : "receivedRequest",
            );
          }}
        >
          <span className="flex-1">
            {truncate(contactRequest.name || "User", CNST.SMALL_USERNAME)}
          </span>
          <span className="px-2 py-1">
            {contactRequest.status === "requested by me" ? (
              <SquareArrowUpRight className="h-4 w-4" />
            ) : (
              <SquareArrowDownLeft className="h-4 w-4 text-cyan-500" />
            )}
          </span>
        </button>
      ))}
    </div>
  );
}

function ContactsBox({ constacts }: { constacts: ContactRich[] }) {
  const { selectedUser, setSelectedUser } = str.useSelectedUserStore();
  const { setSelectedSection } = str.useSelectedSectionStore();
  return (
    <div className="h-full overflow-y-auto thin-scrollbar bg-gray-800">
      {constacts.map((contact) => (
        <button
          key={contact.user_id}
          className={
            (selectedUser?.user_id === contact.user_id
              ? "bg-gray-600 hover:bg-gray-500 "
              : "hover:bg-gray-600 ") +
            "w-full flex py-4 space-y-1 rounded-lg cursor-pointer transition-colors"
          }
          onClick={() => {
            setSelectedUser(contact);
            setSelectedSection("chat");
          }}
        >
          <span className="flex-1">
            {truncate(contact.name || "User", CNST.SMALL_USERNAME)}
          </span>
          {!!contact.unread_messages && (
            <span className="px-2 p-3 py-1 text-xs font-semibold text-cyan-500 rounded-full">
              {contact.unread_messages}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

export function ContactsBar() {
  const { storedRecommendations, storedRequests, storedContacts } =
    str.useContactsStore();

  const showRecommendations = storedRecommendations.length > 0;
  const showRequests = storedRequests.length > 0;

  return (
    <div className="h-full flex flex-col p-4">
      {/* Recommendations - only if has items */}
      {showRecommendations && (
        <div className="mb-3">
          <div className="max-h-28 overflow-y-auto rounded-[10px] thin-scrollbar">
            <RecommendationsBox recommendations={storedRecommendations} />
          </div>
        </div>
      )}

      {/* Requests - only if has items */}
      {showRequests && (
        <div className="mb-3">
          <div className="max-h-28 overflow-y-auto rounded-[10px] thin-scrollbar">
            <RequestsBox requests={storedRequests} />
          </div>
        </div>
      )}

      {/* Contacts - always visible, takes remaining space */}
      <div
        className={`flex-1 min-h-0 ${!showRecommendations && !showRequests ? "mt-0" : ""}`}
      >
        <div className="h-full rounded-[10px] overflow-hidden">
          <ContactsBox constacts={storedContacts} />
        </div>
      </div>
    </div>
  );
}
