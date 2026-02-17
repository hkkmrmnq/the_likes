import { createStore } from "zustand/vanilla";
import { persist } from "zustand/middleware";
import { useStore, create } from "zustand";

import { API_CFG } from "@/src/config";
import * as typ from "@/src/types";

export const authStore = createStore<typ.AuthStore>()(
  persist(
    (set, get) => ({
      token: null,
      expiresAt: 0,
      _hydrated: false,
      _setHydrated: (v: boolean) => set({ _hydrated: v }),
      setCreds: (token: string) => {
        set({
          token: token,
          expiresAt:
            Date.now() +
            (API_CFG.ACCESS_TOKEN_LIFETIME_MINUTES * 60 - 30) * 1000,
        });
        get().manageLifetime();
      },
      _timeoutId: null,
      _clearTimeoutId: () => {
        const currentTimeoutId = get()._timeoutId;
        if (currentTimeoutId) {
          clearTimeout(currentTimeoutId);
        }
      },
      manageLifetime: () => {
        get()._clearTimeoutId();
        const expired = Date.now() > get().expiresAt;
        if (expired) {
          set({ token: null, _timeoutId: null });
        } else {
          const newTimeoutId = setTimeout(
            () => {
              get().manageLifetime();
            },
            API_CFG.ACCESS_TOKEN_LIFETIME_MINUTES * 60 * 1000,
          );
          set({ _timeoutId: newTimeoutId });
        }
      },
      clearCreds: () => {
        get()._clearTimeoutId();
        set({
          token: null,
          expiresAt: 0,
        });
      },
    }),
    {
      name: "token-storage",
      onRehydrateStorage: () => {
        return (state, error) => {
          if (error) {
            console.log("hydration error:", error);
          } else {
            state?._setHydrated(true);
          }
        };
      },
      partialize: (state) => ({
        token: state.token,
        expiresAt: state.expiresAt,
      }),
    },
  ),
);

export const useAuthStore = () => {
  const store = useStore(authStore);
  return {
    token: store.token,
    expiresAt: store.expiresAt,
    setCreds: store.setCreds,
    clearCreds: store.clearCreds,
    tokenHydrated: store._hydrated,
  };
};

export const authStepsStore = create<typ.AuthStepsStore>((set) => ({
  authStep: "creds",
  setAuthStep: (step) => set({ authStep: step }),
}));

export const useAuthSteps = () => useStore(authStepsStore);
