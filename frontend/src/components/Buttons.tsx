"use client";

import { useRouter, usePathname } from "next/navigation";
import * as str from "@/src/stores";
import { useClearStores, useWSClientContext } from "@/src/hooks";
import { CONSTANTS as CNST } from "@/src/config";
import { buttonMono, buttonColored, linkColored } from "@/src/styles";

interface ActionButtonProps {
  action: () => Promise<void> | void;
  className: string;
  label: string | React.ReactNode;
  loadingIndication?: string | React.ReactNode;
}

export function ActionButton({
  action,
  className,
  label,
  loadingIndication: loadingText = "Loading...",
}: ActionButtonProps) {
  const { isLoading, startLoading } = str.useLoadingStore();
  const handleClick = async () => {
    if (isLoading) return;
    startLoading();
    action();
  };

  return (
    <button onClick={handleClick} disabled={isLoading} className={className}>
      {isLoading ? loadingText : label}
    </button>
  );
}

interface NavigationButtonProps {
  destination: string;
  className: string;
  text: string;
  loadingText?: string;
}

function NavigationButton({
  destination,
  className,
  text,
  loadingText = "Loading...",
}: NavigationButtonProps) {
  const router = useRouter();
  const { isLoading, startLoading } = str.useLoadingStore();
  const pathname = usePathname();
  const handleClick = async () => {
    if (isLoading) return;
    if (pathname !== destination) {
      startLoading();
      router.push(destination);
    }
  };
  return (
    <button onClick={handleClick} disabled={isLoading} className={className}>
      {isLoading ? loadingText : text}
    </button>
  );
}

export function ToDoorstepButton({ className = buttonMono }) {
  return (
    <NavigationButton
      destination={CNST.ROUTES.PUBLIC.DOORSTEP}
      text="Sign In / Sign Up"
      className={className}
    />
  );
}

export function LogOutButton({ className = buttonMono }) {
  const { clearStores } = useClearStores();
  const { disconnect } = useWSClientContext();
  const logout = () => {
    disconnect();
    clearStores();
  };
  return (
    <button onClick={logout} className={className}>
      Sign Out
    </button>
  );
}

export function ToLoginButton({ text = "Sign In", className = buttonColored }) {
  return (
    <NavigationButton
      destination={CNST.ROUTES.PUBLIC.LOGIN}
      text={text}
      className={className}
    />
  );
}

export function ToRegisterButton({ text = "Sign Up", className = buttonMono }) {
  return (
    <NavigationButton
      destination={CNST.ROUTES.PUBLIC.REGISTER}
      text={text}
      className={className}
    />
  );
}

export function ToAboutButton({ text = "About", className = buttonMono }) {
  return (
    <NavigationButton
      destination={CNST.ROUTES.PUBLIC.ABOUT}
      text={text}
      className={className}
    />
  );
}

export function ToProfileButton({ text = "Profile", className = buttonMono }) {
  return (
    <NavigationButton
      destination={CNST.ROUTES.PRIVATE.PROFILE}
      text={text}
      className={className}
    />
  );
}

export function ToGuideButton({ text = "Guide", className = buttonMono }) {
  return (
    <NavigationButton
      destination={CNST.ROUTES.PUBLIC.GUIDE}
      text={text}
      className={className}
    />
  );
}

export function ToContactsButton({
  text = "Contacts",
  className = buttonMono,
}) {
  return (
    <NavigationButton
      destination={CNST.ROUTES.PRIVATE.CONTACTS}
      text={text}
      className={className}
    />
  );
}

export function ToValuesButton({ text = "Values", className = buttonMono }) {
  return (
    <NavigationButton
      destination={CNST.ROUTES.PRIVATE.VALUES}
      text={text}
      className={className}
    />
  );
}

export function ToChangePasswordButton() {
  const router = useRouter();
  const { isLoading, startLoading } = str.useLoadingStore();
  const { setAuthStep } = str.authStepsStore();
  const pathname = usePathname();
  const handleClick = async () => {
    setAuthStep("creds");
    if (isLoading) return;
    if (pathname !== CNST.ROUTES.PUBLIC.FORGOT_PASSWORD) {
      startLoading();
      router.push(CNST.ROUTES.PUBLIC.FORGOT_PASSWORD);
    }
  };
  return (
    <button onClick={handleClick} disabled={isLoading} className={linkColored}>
      Forgot password?
    </button>
  );
}
