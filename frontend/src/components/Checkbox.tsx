"use client";

export function Checkbox({ condition }: { condition: boolean }) {
  return (
    <div
      className={`
                w-6 h-6 border-2 rounded mr-3 flex items-center justify-center
                transition-all duration-200
                ${
                  condition
                    ? "bg-cyan-600 border-cyan-600"
                    : "bg-white border-gray-300"
                }
              `}
    >
      {condition && (
        <svg
          className="w-3 h-3 text-white"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={3}
            d="M5 13l4 4L19 7"
          />
        </svg>
      )}
    </div>
  );
}
