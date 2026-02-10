"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { Menu, X } from "lucide-react";
import { useAuthStore } from "@/src/stores/auth";
import {
  ToDoorstepButton,
  ToProfileButton,
  ToAboutButton,
  ToGuideButton,
  ToContactsButton,
  ToValuesButton,
  LogOutButton,
} from "@/src/components/Buttons";
import { navbarClickable, mobileMenuClickable } from "@/src/styles";
import { CONSTANTS as CNST } from "@/src/config";

function Navbar() {
  const { token } = useAuthStore();
  return (
    <nav className="fixed top-0 w-screen z-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Image
              src="/logo.png"
              alt="The Likes"
              width={120}
              height={40}
              className="h-7 w-auto"
              priority
            />
          </div>
          <div className="md:flex items-center space-x-6">
            <ToAboutButton className={navbarClickable} />
            <ToGuideButton className={navbarClickable} />
            {token && <ToContactsButton className={navbarClickable} />}
            {token && <ToValuesButton className={navbarClickable} />}
            {token && <ToProfileButton className={navbarClickable} />}
            <div>{token ? <LogOutButton /> : <ToDoorstepButton />}</div>
          </div>
        </div>
      </div>
    </nav>
  );
}

function MobileMenu() {
  const { token } = useAuthStore();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  return (
    <>
      {/* Backdrop */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-20"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
      <div className="fixed top-4 right-4 z-30">
        <div className="rounded-lg p-1 flex flex-col items-center gap-2">
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="cursor-pointer text-gray-500 hover:text-cyan-600"
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
          {isMobileMenuOpen && (
            <div>
              {token ? (
                <LogOutButton className={mobileMenuClickable} />
              ) : (
                <ToDoorstepButton className={mobileMenuClickable} />
              )}
              {token && <ToProfileButton className={mobileMenuClickable} />}
              {token && <ToContactsButton className={mobileMenuClickable} />}
              {token && <ToValuesButton className={mobileMenuClickable} />}
              <ToAboutButton className={mobileMenuClickable} />
              <ToGuideButton className={mobileMenuClickable} />
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export function Header() {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < CNST.MOBILE_SCREEN_MAX_WIDTH);
    };

    checkScreenSize();
    window.addEventListener("resize", checkScreenSize);
    return () => window.removeEventListener("resize", checkScreenSize);
  }, []);
  return (
    <header className="h-16">{isMobile ? <MobileMenu /> : <Navbar />}</header>
  );
}
