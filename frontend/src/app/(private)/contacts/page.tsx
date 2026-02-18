"use client";

import { useState, useEffect } from "react";
import { PanelLeft } from "lucide-react";

import * as contactsService from "@/src/api/contacts";
import * as str from "@/src/stores";
import { ContentBox, ContactsBar } from "./components";
import { handleErrorInComponent } from "@/src/utils";

export default function ContactsPage() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
  const { stopLoading } = str.useLoadingStore();
  const { setContacts, setRequests, setRecommendations } =
    str.useContactsStore();
  const [error, setError] = useState<string>("");
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await contactsService.getContsNReqstsNRecoms();
        setContacts(response.data.active_contacts);
        setRequests(response.data.contact_requests);
        setRecommendations(response.data.recommendations);
      } catch (err) {
        handleErrorInComponent(err, setError);
      } finally {
        stopLoading();
      }
    };
    fetchData();
  }, [setContacts, setRecommendations, setRequests, stopLoading]);

  if (error) {
    return <div className="text-red-500 text-sm mt-1">{error}</div>;
  }
  return (
    <div className="flex flex-col h-full">
      {/* Mobile-only top-left button */}
      <button
        className={`
          fixed top-4 left-4 z-10
          md:hidden
          p-1
          cursor-pointer text-gray-500 hover:text-cyan-600
        `}
        onClick={toggleSidebar}
        aria-label="Open menu"
      >
        <PanelLeft className="w-6 h-6" />
      </button>

      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <aside
          className={
            (isSidebarOpen ? "z-10" : "hidden md:block") + " w-64 flex-shrink-0"
          }
        >
          <ContactsBar />
        </aside>

        {/* Content */}
        <div className="flex-1 min-h-0 overflow-hidden">
          <ContentBox />
        </div>
      </div>
    </div>
  );
}
