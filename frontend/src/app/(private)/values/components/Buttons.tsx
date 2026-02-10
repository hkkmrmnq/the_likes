"use client";
import { toast } from "sonner";
import { useState } from "react";
import { Hourglass, RotateCcw } from "lucide-react";

import * as valuesService from "@/src/api";
import * as str from "@/src/stores";
import { buttonColored } from "@/src/styles";
import { Attitude } from "@/src/types";
import { handleErrorInComponent } from "@/src/utils";
import { ActionButton } from "@/src/components";

export function ResetChangesMPButton() {
  const { setHaveUnsavedChanges } = str.useMoralProfileStore();
  return (
    <ActionButton
      action={() => {
        setHaveUnsavedChanges(false);
      }}
      className={`w-26 border border-gray-400 py-3 px-4 rounded-lg font-medium hover:bg-gray-500 transition-colors cursor-pointer flex items-center gap-2`}
      label={
        <>
          <span>Reset</span>
          <RotateCcw className="h-4 w-4" />
        </>
      }
      loadingIndication={<Hourglass className="h-4 w-4" />}
    />
  );
}

function getAttitudeID(attitudes: Attitude[]): number {
  const attitude = (attitudes as Attitude[]).find((a) => a.chosen);
  if (!!attitude) {
    return attitude.attitude_id;
  } else {
    throw new Error("getAttitudeID error - no chosen attitude");
  }
}

export function SubmitValuesButton() {
  const [, setError] = useState("");
  const {
    values,
    setValues,
    setAttitudes,
    isInitial,
    attitudes,
    setHaveUnsavedChanges,
  } = str.useMoralProfileStore();
  const handleSubmit = async () => {
    try {
      const newData = {
        attitude_id: getAttitudeID(attitudes),
        value_links: values.map((personalValue) => ({
          value_id: personalValue.value_id,
          polarity: personalValue.polarity,
          user_order: personalValue.user_order,
          aspects: personalValue.aspects.map((aspect) => ({
            aspect_id: aspect.aspect_id,
            included: aspect.included,
          })),
        })),
      };
      const response = await valuesService.submitValues(isInitial, newData);
      setValues(response.data.value_links);
      setAttitudes(response.data.attitudes);
      setHaveUnsavedChanges(false);
      toast.info(response.message);
    } catch (err) {
      handleErrorInComponent(err, setError);
    }
  };
  return (
    <ActionButton
      action={() => handleSubmit()}
      label={isInitial ? "Save My Values" : "Update Values"}
      loadingIndication="Saving..."
      className={buttonColored}
    />
  );
}
