"use client";

import { MessageDisplay } from "@/src/types";

interface MessageProps {
  message: MessageDisplay;
  className?: string;
}

export function Message({ message, className = "" }: MessageProps) {
  return (
    <div
      className={`flex w-full ${
        message.isIncoming ? "justify-start" : "justify-end"
      } ${className}`}
    >
      <div className="flex max-w-[90%] m-1">
        {/* Message bubble */}
        <div
          className={`relative px-4 py-3 rounded-2xl ${
            message.isIncoming
              ? "bg-gray-500 rounded-tl-none"
              : "bg-cyan-700 rounded-br-none"
          }`}
        >
          {/* Message text with padding for timestamp */}
          <p className="whitespace-pre-wrap break-words pr-10 pb-0.5">
            {message.text}
          </p>

          {/* Timestamp - positioned absolutely in bottom right */}
          <div
            className={`
            absolute bottom-2 right-3 
            flex items-end space-x-1 
            ${message.isIncoming ? "text-gray-400" : "text-cyan-500"}
          `}
          >
            <span className="text-xs font-medium leading-none">
              {!!message.time && message.time.slice(0, -3)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
