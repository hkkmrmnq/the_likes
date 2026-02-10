"use client";

import { useState } from "react";
import * as authService from "@/src/api/auth";
import { handleErrorInComponent } from "@/src/utils";
import { useLoadingStore, useAuthSteps } from "@/src/stores";
import { ActionButton, ToLoginButton } from "@/src/components/Buttons";
import { linkColored, buttonColored } from "@/src/styles";

export default function CredsStep({
  email,
  setEmail,
}: {
  email: string;
  setEmail: (newEmail: string) => void;
}) {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const { startLoading, stopLoading } = useLoadingStore();
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const { setAuthStep } = useAuthSteps();

  const submit = async () => {
    startLoading();
    setError("");
    setFieldErrors({});

    try {
      await authService.register(email, password, confirmPassword);
      setAuthStep("verify");
    } catch (err) {
      handleErrorInComponent(err, setError, setFieldErrors);
      stopLoading();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-100">
            Create an account
          </h2>
        </div>

        <div className="space-y-4">
          <div>
            <label htmlFor="email" className="sr-only">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="relative block w-full px-3 py-2 border border-white placeholder-gray-500 rounded-lg focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Email"
            />
            {fieldErrors && fieldErrors.email && (
              <p className="text-red-500 text-sm mt-1">{fieldErrors.email}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="sr-only">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="relative block w-full px-3 py-2 border border-white placeholder-gray-500 rounded-lg focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Password"
            />
            {fieldErrors && fieldErrors.password && (
              <p className="text-red-500 text-sm mt-1">
                {fieldErrors.password}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="sr-only">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="relative block w-full px-3 py-2 border border-white placeholder-gray-500 rounded-lg focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Confirm password"
            />
            {fieldErrors && fieldErrors.confirmPassword && (
              <p className="text-red-500 text-sm mt-1">
                {fieldErrors.confirmPassword}
              </p>
            )}
          </div>
        </div>

        <div>
          <ActionButton
            label="Create account"
            action={submit}
            className={buttonColored}
          />
        </div>

        <div className="text-center">
          <ToLoginButton
            text="Already have an account? Sign in"
            className={linkColored}
          />
        </div>
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
