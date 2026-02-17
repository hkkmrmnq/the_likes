import { create, useStore } from "zustand";
import { createStore } from "zustand/vanilla";
import * as typ from "@/src/types";

export const selectedUserStore = createStore<typ.SelectedUserStore>()(
  (set) => ({
    selectedUser: null,
    setSelectedUser: (user: typ.Recommendation | typ.ContactRich) =>
      set({ selectedUser: user }),
    clearSelectedUser: () => set({ selectedUser: null }),
  }),
);

export const useSelectedUserStore = () => {
  return useStore(selectedUserStore);
};

export const useSelectedSectionStore = create<typ.SelectedSectionStore>(
  (set) => ({
    selectedSection: "chat",
    setSelectedSection: (section: typ.ContactsSectionName) =>
      set({ selectedSection: section }),
  }),
);
