"use client";

import { Checkbox } from "@/src/components";
import { useMoralProfileStore } from "@/src/stores";

export function DefinitionsStep() {
  const {
    values,
    isInitial,
    setValues,
    valueIndex,
    setValueIndex,
    setValuesStep,
    setHaveUnsavedChanges,
  } = useMoralProfileStore();
  const currentValue = values[valueIndex];
  if (!currentValue) {
    console.error("currentValue undefined");
  }

  const handleAspectToggle = (aspectId: number) => {
    const updatedPersonalValues = values.map((value, index) => {
      if (index === valueIndex) {
        return {
          ...value,
          aspects: value.aspects.map((aspect) =>
            aspect.aspect_id === aspectId
              ? { ...aspect, included: !aspect.included }
              : aspect,
          ),
        };
      }
      return value;
    });
    setValues(updatedPersonalValues);
    setHaveUnsavedChanges(true);
  };

  return (
    <div className="rounded-lg shadow-sm border p-8">
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold">
          {isInitial ? "Choose Your Values" : "Your Values"}
        </h1>
        <p className="mt-2">
          Value {valueIndex + 1} of {values.length}
        </p>
      </div>

      {/* Value Card */}
      <div className="max-w-md mx-auto">
        <div className="text-center mb-6">
          <h2 className="text-xl font-semibold">
            {!!currentValue && currentValue.value_name}
          </h2>
        </div>

        {/* Aspects */}
        <div className="space-y-3 mb-8">
          {!!currentValue &&
            currentValue.aspects.map((aspect) => (
              <label
                key={aspect.aspect_id}
                className="flex items-start space-x-3 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={aspect.included}
                  onChange={() => handleAspectToggle(aspect.aspect_id)}
                  className="hidden"
                />

                <Checkbox condition={aspect.included} />

                <span className="flex-1">{aspect.aspect_statement}</span>
              </label>
            ))}
        </div>

        {/* Navigation */}
        <div className="flex justify-between items-center">
          {valueIndex === 0 ? (
            <div />
          ) : (
            <button
              onClick={() => setValueIndex(Math.max(0, valueIndex - 1))}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-700 cursor-pointer"
            >
              <span>Previous</span>
            </button>
          )}

          {valueIndex === values.length - 1 ? (
            <button
              onClick={() => {
                setValuesStep("attitudes");
              }}
              className="bg-cyan-600 text-white px-6 py-2 rounded-lg hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              Continue to Attitude
            </button>
          ) : (
            <button
              onClick={() => setValueIndex(valueIndex + 1)}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-700 cursor-pointer"
            >
              <span>Next</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
