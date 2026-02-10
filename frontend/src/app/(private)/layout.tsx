"use client";

import { Header, AuthGuard } from "@/src/components";

export default function PrivateLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <div className="flex flex-col h-screen">
        <header className="h-16 flex-shrink-0">
          <Header />
        </header>
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </AuthGuard>
  );
}
