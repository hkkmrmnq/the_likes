"use client";

import { useEffect, useState } from "react";

import * as valuesService from "@/src/api/values";

import { LoadingScreen } from "@/src/components";
import { useLoadingStore, useMoralProfileStore } from "@/src/stores";
import { ValuesStep } from "@/src/types";
import { handleErrorInComponent } from "@/src/utils";
import {
  AttitudeStep,
  DefinitionsStep,
  HierarchyStep,
  ResetChangesMPButton,
} from "./components";

export default function MyValuesPage() {
  const { isLoading, stopLoading } = useLoadingStore();
  const {
    valuesStep,
    setValues,
    setIsInitial,
    setAttitudes,
    haveUnsavedChanges,
  } = useMoralProfileStore();
  const [error, setError] = useState("");

  useEffect(() => {
    if (!haveUnsavedChanges) {
      const fetchValuesData = async () => {
        try {
          const response = await valuesService.getValues();
          setValues(response.data.value_links);
          setAttitudes(response.data.attitudes);
          setIsInitial(response.data.initial);
        } catch (err) {
          handleErrorInComponent(err, setError);
        }
      };
      fetchValuesData();
    }
    stopLoading();
  }, [
    setValues,
    setAttitudes,
    setIsInitial,
    isLoading,
    stopLoading,
    haveUnsavedChanges,
  ]);
  if (isLoading) {
    return <LoadingScreen />;
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-red-600">{error}</div>
      </div>
    );
  }

  const mappedSteps = {
    definitions: <DefinitionsStep />,
    attitudes: <AttitudeStep />,
    hierarchy: <HierarchyStep />,
  };

  return (
    <div className="max-w-4xl mx-auto px-4">
      {/* Header container */}
      <div className="flex items-center justify-between pt-8 pb-4 h-24">
        {/* Reset button */}
        <div className="w-auto flex-1">
          {haveUnsavedChanges && <ResetChangesMPButton />}
        </div>

        {/* Progress Indicator */}
        <div className="flex-1 flex justify-center">
          <div className="flex space-x-4">
            {(["definitions", "attitudes", "hierarchy"] as ValuesStep[]).map(
              (step, index) => (
                <div key={step} className="flex items-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      valuesStep === step
                        ? "bg-cyan-600 text-white"
                        : step === "definitions" ||
                            (step === "attitudes" &&
                              valuesStep !== "definitions") ||
                            (step === "hierarchy" && valuesStep === "hierarchy")
                          ? "bg-cyan-200 text-cyan-800"
                          : "bg-gray-200 text-gray-500"
                    }`}
                  >
                    {index + 1}
                  </div>
                  {index < 2 && (
                    <div
                      className={`w-12 h-1 mx-2 ${
                        (step === "definitions" &&
                          valuesStep !== "definitions") ||
                        (step === "attitudes" && valuesStep === "hierarchy")
                          ? "bg-cyan-200"
                          : "bg-gray-200"
                      }`}
                    />
                  )}
                </div>
              ),
            )}
          </div>
        </div>

        {/* Right - flex-1 for balance */}
        <div className="flex-1"></div>
      </div>

      {mappedSteps[valuesStep as ValuesStep]}
    </div>
  );
}
