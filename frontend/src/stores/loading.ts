import { create } from "zustand";

import { LoadingStore } from "@/src/types";

export const useLoadingStore = create<LoadingStore>((set) => ({
  isLoading: true,
  waitingForApi: false,
  loadingMessage: "Loading...",
  startLoading: (message = "Loading...") =>
    set({ isLoading: true, loadingMessage: message }),
  stopLoading: () => set({ isLoading: false, loadingMessage: "Loading..." }),
  setWaitingForApi: (v) => set({ waitingForApi: v }),
}));
