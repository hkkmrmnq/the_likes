import {
  Contact,
  ValueLinks,
  Attitude,
  MessageSent,
  ChatPayloadType,
} from "./api";
import {
  MessageDisplay,
  ValuesStep,
  AuthStep as AuthStep,
} from "@/src/types/client";

export interface LoadingStore {
  isLoading: boolean;
  waitingForApi: boolean;
  loadingMessage: string;
  startLoading: (message?: string) => void;
  stopLoading: () => void;
  setWaitingForApi: (v: boolean) => void;
}

export interface AuthStore {
  token: string | null;
  expiresAt: number;
  _hydrated: boolean;
  _setHydrated: (value: boolean) => void;
  _timeoutId: NodeJS.Timeout | null;
  _clearTimeoutId: () => void;
  _isRefreshing: boolean;
  manageLifetime: () => void;
  setCreds: (token: string) => void;
  clearCreds: () => void;
}

export interface MoralProfileStore {
  values: ValueLinks;
  setValues: (new_values: ValueLinks) => void;
  valuesStep: ValuesStep;
  setValuesStep: (step: ValuesStep) => void;
  valueIndex: number;
  setValueIndex: (v: number) => void;
  attitudes: Attitude[];
  setAttitudes: (new_attitudes: Attitude[]) => void;
  isInitial: boolean;
  setIsInitial: (v: boolean) => void;
  haveUnsavedChanges: boolean;
  setHaveUnsavedChanges: (v: boolean) => void;
  clearMoralProfile: () => void;
}

export interface ContactsStore {
  storedContacts: Contact[];
  setContacts: (contacts: Contact[]) => void;
  storedRequests: Contact[];
  setRequests: (contacts: Contact[]) => void;
  storedRecommendations: Contact[];
  setRecommendations: (newRecommendations: Contact[]) => void;
  incrementUnreadCount: (contactId: string, by?: number) => void;
  resetUnreadCount: (contactId: string) => void;
  clearContactsStore: () => void;
}

interface Conversation {
  messages: MessageDisplay[];
  unread_count: number;
}

export interface MessagesState {
  conversations: Record<string, Conversation>;
  addMessage: (contactId: string, message: MessageDisplay) => void;
  getConversationMessages: (contactId: string | null) => MessageDisplay[];
  setConversationMessages: (
    contactId: string,
    messages: MessageDisplay[],
  ) => void;
  markMessageAsSent: (confirmedMsg: MessageSent) => void;
  clearMessages: () => void;
}

export interface AuthStepsStore {
  authStep: AuthStep;
  setAuthStep: (step: AuthStep) => void;
}

export interface SelectedUserStore {
  selectedUser: Contact | null;
  setSelectedUser: (user: Contact) => void;
  clearSelectedUser: () => void;
}

export interface StoredNotification {
  type:
    | ChatPayloadType.NEW_RECOMM
    | ChatPayloadType.NEW_REQUEST
    | ChatPayloadType.NEW_CHAT;
  user_id: string;
}

export interface NotificationsStore {
  notifications: StoredNotification[];
  addNotification: (notification: StoredNotification) => void;
  clearNotification: (notification: StoredNotification) => void;
}
