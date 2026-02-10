"use client";

import * as str from "@/src/stores";

export function useClearStores() {
  const { clearCreds } = str.useAuthStore();
  const { clearSelectedUser } = str.useSelectedUserStore();
  const { setSelectedSection } = str.useSelectedSectionStore();
  const { clearProfile } = str.useProfileStore();
  const { clearMoralProfile } = str.useMoralProfileStore();
  const { clearContactsStore } = str.useContactsStore();
  const clearStores = () => {
    setSelectedSection("chat");
    clearContactsStore();
    clearMoralProfile();
    clearSelectedUser();
    clearProfile();
    clearCreds();
  };
  return { clearStores };
}
