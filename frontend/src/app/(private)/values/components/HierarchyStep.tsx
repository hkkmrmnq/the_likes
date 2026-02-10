"use client";

import { Board } from "./Board";

import { SubmitValuesButton } from "./Buttons";
import { useLoadingStore, useMoralProfileStore } from "@/src/stores";
import { buttonMono } from "@/src/styles";

export function HierarchyStep() {
  const { setValuesStep } = useMoralProfileStore();
  const { isLoading } = useLoadingStore();

  return (
    <div className="rounded-lg shadow-sm border p-6 md:p-8">
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold text-gray-100">
          Arrange Your Values
        </h1>
        <p className="text-gray-300 mt-2">
          Drag values between areas to categorize them
        </p>
        <Board />
      </div>

      <div className="flex flex-col sm:flex-row justify-between gap-4 mt-8">
        <button
          onClick={() => setValuesStep("attitudes")}
          disabled={isLoading}
          className={buttonMono}
        >
          Back To Attitudes
        </button>
        <div className="min-w-80"></div>
        <SubmitValuesButton />
      </div>
    </div>
  );
}
