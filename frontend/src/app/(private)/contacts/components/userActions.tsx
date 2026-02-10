"use client";

import { ActionButton } from "@/src/components/Buttons";
import { buttonMono, buttonColored } from "@/src/styles";
import * as contactsService from "@/src/api/contacts";
import { useContactAction } from "@/src/hooks";
import { ContactDetailProps } from "@/src/types";

export function ContactProfileActions({ userId }: ContactDetailProps) {
  const { createContactAction } = useContactAction();
  return (
    <ActionButton
      action={() =>
        createContactAction(contactsService.blockContact)(
          // , "Block user"
          userId,
        )
      }
      className={buttonMono}
      label="Block user"
    />
  );
}

export function ReceivedRequestActions({ userId }: ContactDetailProps) {
  const { createContactAction } = useContactAction();
  return (
    <>
      <ActionButton
        action={() => createContactAction(contactsService.agreeToStart)(userId)}
        className={buttonColored}
        label="Accept"
      />
      <ActionButton
        action={() =>
          createContactAction(contactsService.rejectContactRequest)(userId)
        }
        className={buttonMono}
        label="Reject"
      />
    </>
  );
}

export function SentRequestActions({ userId }: ContactDetailProps) {
  const { createContactAction } = useContactAction();
  return (
    <ActionButton
      action={() =>
        createContactAction(contactsService.cancelContactRequest)(userId)
      }
      className={buttonMono}
      label="Cancel request"
    />
  );
}

export function RecommendationActions({ userId }: ContactDetailProps) {
  const { createContactAction } = useContactAction();

  return (
    <ActionButton
      action={() => createContactAction(contactsService.agreeToStart)(userId)}
      className={buttonColored}
      label="Start conversation"
    />
  );
}

export function ErrorDummy() {
  return <></>;
}
