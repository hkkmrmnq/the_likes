"use client";

import { CONSTANTS as CNST } from "@/src/config";
import { Checkbox } from "@/src/components";
import { Languages } from "@/src/types/api";

export function LanguageSelector({
  languages,
  setLanguages: setSelectedLanguages,
}: {
  languages: Languages;
  setLanguages: (newLanguages: Languages) => void;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-center mb-3">
        Languages
      </label>
      <div className="flex justify-center space-x-6">
        {CNST.SUPPORTED_LANGUAGES.map((lan) => (
          <label
            key={lan}
            className="flex items-center cursor-pointer rounded-lg border-gray-200 hover:border-cyan-300 transition-colors"
          >
            <input
              type="checkbox"
              checked={languages.includes(lan)}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedLanguages([...languages, lan]);
                } else {
                  setSelectedLanguages(languages.filter((l) => l !== lan));
                }
              }}
              className="hidden"
            />

            {/* Custom checkbox  */}
            <Checkbox condition={languages.includes(lan)} />

            {/* Language label */}
            <span className="font-medium">{lan.toUpperCase()}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
