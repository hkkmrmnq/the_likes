import { createStore } from "zustand/vanilla";
import { persist } from "zustand/middleware";
import { useStore } from "zustand";

import { ProfileRead, Languages } from "@/src/types/api";
import { CONSTANTS as CNST } from "@/src/config";

interface ProfileStore extends ProfileRead {
  setUserId: (userId: string) => void;
  setName: (newName: string | null) => void;
  setLanguages: (newLanguages: Languages) => void;
  setLongitude: (newLongitude: number | null) => void;
  setLatitude: (newLatitude: number | null) => void;
  setDistanceLimit: (newDistanceLimit: number | null) => void;
  setRecommendMe: (newRecommendMe: boolean) => void;
  setProfile: (newProfile: ProfileRead) => void;
  clearProfile: () => void;
}

export const profileStore = createStore<ProfileStore>()(
  persist(
    (set) => ({
      user_id: "",
      name: null,
      languages: [CNST.DEFAULT_LANGUAGE],
      longitude: null,
      latitude: null,
      distance_limit: null,
      recommend_me: true,

      setUserId: (userId: string) => set({ user_id: userId }),
      setName: (newName: string | null) => set({ name: newName }),
      setLanguages: (newLanguages: Languages) =>
        set({ languages: newLanguages }),
      setLongitude: (newLongitude: number | null) =>
        set({ longitude: newLongitude }),
      setLatitude: (newLatitude: number | null) =>
        set({ latitude: newLatitude }),
      setDistanceLimit: (newDistanceLimit: number | null) =>
        set({ distance_limit: newDistanceLimit }),
      setRecommendMe: (newRecommendMe: boolean) =>
        set({ recommend_me: newRecommendMe }),

      setProfile: (newProfile: ProfileRead) =>
        set({
          user_id: newProfile.user_id,
          name: newProfile.name,
          languages: newProfile.languages,
          longitude: newProfile.longitude,
          latitude: newProfile.latitude,
          distance_limit: newProfile.distance_limit,
          recommend_me: newProfile.recommend_me,
        }),

      clearProfile: () =>
        set({
          name: null,
          languages: [CNST.DEFAULT_LANGUAGE],
          longitude: null,
          latitude: null,
          distance_limit: null,
          recommend_me: true,
        }),
    }),
    {
      name: "profile-storage",
      onRehydrateStorage: () => () => {},
      partialize: (state) => ({
        user_id: state.user_id,
        name: state.name,
        languages: state.languages,
        longitude: state.longitude,
        latitude: state.latitude,
        distance_limit: state.distance_limit,
        recommend_me: state.recommend_me,
      }),
    },
  ),
);

export const useProfileStore = () => useStore(profileStore);
