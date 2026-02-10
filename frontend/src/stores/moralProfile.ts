import { createStore, useStore } from "zustand";
import { persist } from "zustand/middleware";

import { MoralProfileStore } from "@/src/types";

export const moralProfileStore = createStore<MoralProfileStore>()(
  persist(
    (set) => ({
      values: [],
      setValues: (new_values) => set({ values: new_values }),
      valuesStep: "definitions",
      setValuesStep: (step) => set({ valuesStep: step }),
      valueIndex: 0,
      setValueIndex: (v) => set({ valueIndex: v }),
      attitudes: [],
      setAttitudes: (new_attitudes) => set({ attitudes: new_attitudes }),
      isInitial: true,
      haveUnsavedChanges: false,
      setIsInitial: (v) => set({ isInitial: v }),
      setHaveUnsavedChanges: (v) => {
        set({ haveUnsavedChanges: v });
      },
      clearMoralProfile: () =>
        set({
          values: [],
          valuesStep: "definitions",
          valueIndex: 0,
          attitudes: [],
          isInitial: true,
          haveUnsavedChanges: false,
        }),
    }),
    {
      name: "moral-profile-storage",
      partialize: (state) => ({
        values: state.values,
        currentStep: state.valuesStep,
        currentValueIndex: state.valueIndex,
        attitudes: state.attitudes,
        isInitial: state.isInitial,
        haveUnsavedChanges: state.haveUnsavedChanges,
      }),
    },
  ),
);

export const useMoralProfileStore = () => useStore(moralProfileStore);
