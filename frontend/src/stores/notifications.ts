import { createStore, useStore } from "zustand";
import { persist } from "zustand/middleware";
import { NotificationsStore } from "@/src/types";

export const notificationsStore = createStore<NotificationsStore>()(
  persist(
    (set, get) => ({
      notifications: [],
      addNotification: (notification) => {
        const currentNotifications = get().notifications;
        const newNotifications = [...currentNotifications, notification];
        set({ notifications: newNotifications });
      },
      clearNotification: (notificaton) => {
        const currentNotifications = get().notifications;
        const newNotifications = currentNotifications.filter(
          (n) =>
            n.type === notificaton.type && n.user_id == notificaton.user_id,
        );
        set({ notifications: newNotifications });
      },
    }),
    {
      name: "notifications-storage",
      partialize: (state) => ({ notifications: state.notifications }),
    },
  ),
);

export const useNotificationsStore = () => useStore(notificationsStore);
