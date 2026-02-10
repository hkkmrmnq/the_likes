"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import * as authService from "@/src/api/auth";
import { ActionButton } from "@/src/components/Buttons";
import * as str from "@/src/stores";
import { buttonThinColored } from "@/src/styles";
import { handleErrorInComponent } from "@/src/utils";
import { SetNewPassword } from "./SetNewPassword";

export default function LoginPage() {
  const { startLoading, stopLoading } = str.useLoadingStore();
  const { authStep, setAuthStep } = str.useAuthSteps();
  useEffect(() => {
    stopLoading();
  }, [stopLoading]);
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");

  const sendEmailToVerify = async () => {
    setError("");
    try {
      startLoading();
      const message = await authService.forgotPassword({ email });
      toast.info(message);
      setAuthStep("verify");
    } catch (err) {
      handleErrorInComponent(err, setError);
      stopLoading();
    }
  };

  if (authStep === "creds") {
    return (
      <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div>
            <div className="mt-6 text-center text-xl font-extrabold text-gray-100">
              Forgot password? Enter your email and we will send you a
              confirmation code.
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <label htmlFor="email" className="sr-only">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="relative block w-full px-3 py-2 border border-white placeholder-gray-500 rounded-lg focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Email address"
            />
          </div>

          <div>
            <ActionButton
              label="Send code"
              loadingIndication="Sending..."
              action={sendEmailToVerify}
              className={buttonThinColored}
            />
          </div>
        </div>
      </div>
    );
  }

  return <SetNewPassword email={email} />;
}
