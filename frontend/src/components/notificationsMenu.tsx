"use client";

import { useState, useEffect, useRef } from "react";
import { Bell } from "lucide-react";

import { useNotificationsStore } from "@/src/stores/notifications";
import { StoredNotification } from "@/src/types";

export const NotificationsDropdown = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { notifications, clearNotification } = useNotificationsStore();
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const toggleDropdown = (event: MouseEvent) => {
      // Check if click is on the button (icon)
      if (
        buttonRef.current &&
        buttonRef.current.contains(event.target as Node)
      ) {
        return; // Don't close if clicking the button
      }

      setIsOpen(false);
    };

    // Use mousedown for immediate response
    document.addEventListener("mousedown", toggleDropdown);
    return () => document.removeEventListener("mousedown", toggleDropdown);
  }, []);

  const handleNotificationClick = (notification: StoredNotification) => {
    // Placeholder that accepts notification.type and notification.user_id
    console.log("Notification clicked:", {
      type: notification.type,
      user_id: notification.user_id,
    });

    // You can add your custom logic here
    // For example: navigate to different pages based on type
    // switch(notification.type) {
    // case 'message':
    // router.push(`/messages/${notification.user_id}`);
    // break;
    // case 'friend_request':
    // router.push('/friends');
    // break;
    // default:
    // router.push(`/profile/${notification.user_id}`);
    // }

    // Clear notification after click (optional)
    // clearNotification(notification);
    setIsOpen(false);
  };

  return (
    // className="relative"
    <div ref={dropdownRef}>
      {/* Bell Icon with notification badge */}
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 rounded-full hover:bg-gray-600 transition-colors cursor-pointer"
        aria-label="Notifications"
      >
        <Bell className="w-6 h-6 text-cyan-400" />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500">
                <Bell className="w-6 h-6 mx-auto mb-3 text-gray-400" />
                <p>No notifications yet</p>
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {notifications.map((notification, index) => (
                  <li
                    key={index} // Consider using a proper id from your notification object
                    onClick={() => handleNotificationClick(notification)}
                    className="px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <div className="flex items-start">
                      <div className="flex-1">
                        {/* Customize this based on your notification structure */}
                        <p className="text-sm text-gray-900">
                          <span className="font-medium capitalize">
                            {notification.type}
                          </span>{" "}
                          from user {notification.user_id}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Click to view details
                        </p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
