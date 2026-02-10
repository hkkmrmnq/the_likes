"use client";

import { EllipsisVertical, Hourglass } from "lucide-react";

import { ActionButton } from "@/src/components";

export function UserButton({
  onClick,
}: {
  userId: string;
  onClick: () => void;
}) {
  return (
    <ActionButton
      action={onClick}
      className="cursor-pointer"
      label={<EllipsisVertical className="h-4 w-4" />}
      loadingIndication={<Hourglass className="h-4 w-4" />}
    />
  );
}
