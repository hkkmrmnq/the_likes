"use client";

import { useEffect, useState } from "react";

import * as contactsService from "@/src/api/contacts";
import { ActionButton } from "@/src/components";
import * as typ from "@/src/types";
import { useLoadingStore } from "@/src/stores";
import { useContactAction } from "@/src/hooks";
import { buttonColored } from "@/src/styles";
import { handleErrorInComponent } from "@/src/utils";

export function Options() {
  const [error, setError] = useState<string>("");
  const { stopLoading } = useLoadingStore();
  const { createContactAction } = useContactAction();
  const [contactsOptions, setContactsOptions] = useState<typ.ContactsOptions>({
    cancelled_requests: [],
    rejected_requests: [],
    blocked_contacts: [],
  });
  useEffect(() => {
    const fetchData = async () => {
      const response = await contactsService.getContactsOptions();
      setContactsOptions(response.data);
    };
    try {
      fetchData();
    } catch (err) {
      handleErrorInComponent(err, setError);
    } finally {
      stopLoading();
    }
  }, [stopLoading, setError]);

  if (error) {
    return <div className="text-red-500 text-sm mt-1">{error}</div>;
  }

  const { cancelled_requests, rejected_requests, blocked_contacts } =
    contactsOptions;

  const totalLength =
    cancelled_requests.length +
    rejected_requests.length +
    blocked_contacts.length;

  if (totalLength === 0) {
    return (
      <div className="h-full w-full flex items-center justify-center text-center text-gray-500 py-8">
        No other options now.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-full items-center text-center py-8 overflow-y-auto">
      {cancelled_requests.length > 0 && (
        <div className="text-lg text-gray-400 py-4">Cancelled requests</div>
      )}
      {cancelled_requests.map((item) => (
        <div key={item.user_id} className="w-[300px] py-4">
          <span>{item.name || "Name not set."}</span>
          <ActionButton
            action={() => {
              createContactAction(contactsService.agreeToStart)(item.user_id);
              setContactsOptions({
                cancelled_requests: cancelled_requests.filter(
                  (cr) => cr.user_id !== item.user_id,
                ),
                rejected_requests,
                blocked_contacts,
              });
            }}
            className={buttonColored}
            label="Request again"
          />
        </div>
      ))}
      {rejected_requests.length > 0 && (
        <div className="text-lg text-gray-400 py-4">Rejected requests</div>
      )}
      {rejected_requests.map((item) => (
        <div key={item.user_id} className="w-[300px] py-4">
          <span>{item.name || "Name not set."}</span>
          <ActionButton
            action={() => {
              createContactAction(contactsService.agreeToStart)(item.user_id);
              setContactsOptions({
                cancelled_requests,
                rejected_requests: rejected_requests.filter(
                  (rr) => rr.user_id !== item.user_id,
                ),
                blocked_contacts,
              });
            }}
            className={buttonColored}
            label="Request back"
          />
        </div>
      ))}
      {blocked_contacts.length > 0 && (
        <div className="text-lg text-gray-400 py-4">Blocked contacts</div>
      )}
      {blocked_contacts.map((item) => (
        <div key={item.user_id} className="w-[300px]  py-4">
          <span>
            {item.name || "Name not set."} - {item.status}
          </span>
          <ActionButton
            action={() => {
              createContactAction(contactsService.unblockContact)(item.user_id);
              setContactsOptions({
                cancelled_requests,
                rejected_requests,
                blocked_contacts: blocked_contacts.filter(
                  (bc) => bc.user_id !== item.user_id,
                ),
              });
            }}
            className={buttonColored}
            label="Unblock user"
          />
        </div>
      ))}
    </div>
  );
}
