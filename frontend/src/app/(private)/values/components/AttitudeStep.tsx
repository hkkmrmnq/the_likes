"use client";

import { useMoralProfileStore } from "@/src/stores";

export function AttitudeStep() {
  const { attitudes, setAttitudes, setValuesStep, setHaveUnsavedChanges } =
    useMoralProfileStore();
  const handleAttitudeToggle = (attitudeId: number) => {
    const updatedAttitudes = attitudes.map((attitude) => ({
      ...attitude,
      chosen: attitude.attitude_id === attitudeId,
    }));
    setAttitudes(updatedAttitudes);
    setHaveUnsavedChanges(true);
  };

  const selectedCount = attitudes.filter((a) => a.chosen).length;

  return (
    <div className="rounded-lg shadow-sm border p-8">
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold">Choose Your Attitude</h1>
        <p className="mt-2">Select one statement that resonates with you</p>
      </div>

      <div className="max-w-md mx-auto space-y-4 mb-8">
        {attitudes.map((attitude) => (
          <label
            key={attitude.attitude_id}
            className="flex items-start space-x-3 cursor-pointer p-4 border border-gray-200 rounded-lg hover:bg-gray-700"
          >
            <input
              type="radio"
              name="attitude"
              checked={attitude.chosen}
              onChange={() => handleAttitudeToggle(attitude.attitude_id)}
              className="mt-1 h-4 w-4 text-cyan-600 focus:ring-cyan-500 border-gray-300"
            />
            <span className="flex-1">{attitude.statement}</span>
          </label>
        ))}
      </div>

      <div className="flex justify-between">
        <button
          onClick={() => {
            setValuesStep("definitions");
          }}
          className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-700 cursor-pointer"
        >
          Back to Values
        </button>
        <button
          disabled={selectedCount !== 1}
          onClick={() => {
            setValuesStep("hierarchy");
          }}
          className="bg-cyan-600 text-white px-6 py-2 rounded-lg hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          Continue to Board
        </button>
      </div>
    </div>
  );
}
