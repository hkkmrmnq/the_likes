import * as contactsService from "@/src/api";
import { ChatPayload, Polarity } from "@/src/types/api";

export type ValueNamesColumns = Record<Polarity, string[]>;

export type ColumnToDropToProps = {
  id: Polarity;
  items: string[];
  borderColor: string;
};

export interface ContentBoxProps {
  sendChatMessage: (input: string) => void;
  isConnected: () => boolean;
}

export type AuthStep = "creds" | "verify";

export interface SelectedSectionStore {
  selectedSection: ContactsSectionName;
  setSelectedSection: (section: ContactsSectionName) => void;
}

export type ValuesStep = "definitions" | "attitudes" | "hierarchy";

export type ContactsSectionName =
  | "chat"
  | "receivedRequest"
  | "sentRequest"
  | "contactProfile"
  | "recommendation"
  | "options";

export interface ContactDetailProps {
  userId: string;
}

export type ContactsServiceMethods = keyof typeof contactsService;

export interface WSManagerConfig {
  token: string;
  autoReconnect: boolean;
  reconnectDelay: number;
  maxReconnectAttempts: number;
  onConnect: () => void;
  onDisconnect: (event: CloseEvent) => void;
  onPayload: (payload: ChatPayload) => void;
  onError: (error: string, payload?: ChatPayload) => void;
}

export interface WSClient {
  sendChatMessage: (text: string) => void;
  isConnected: () => boolean;
  disconnect: () => void;
}

export interface MessageDisplay {
  created_at: string | null;
  time: string | null;
  text: string;
  client_id: string;
  pending: boolean;
  isIncoming: boolean;
  sender_id: string;
  receiver_id: string;
  sender_name: string | null;
  receiver_name: string | null;
}
