import { create } from "zustand";
import * as typ from "@/src/types";

export const useSelectedUserStore = create<typ.SelectedUserStore>((set) => ({
  selectedUser: null,
  setSelectedUser: (user: typ.Recommendation | typ.ContactRich) =>
    set({ selectedUser: user }),
  clearSelectedUser: () => set({ selectedUser: null }),
}));

export const useSelectedSectionStore = create<typ.SelectedSectionStore>(
  (set) => ({
    selectedSection: "chat",
    setSelectedSection: (section: typ.ContactsSectionName) =>
      set({ selectedSection: section }),
  }),
);
