"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { CONSTANTS } from "@/src/config";
import * as authService from "@/src/api/auth";
import { handleErrorInComponent } from "@/src/utils";
import * as str from "@/src/stores";
import { ActionButton, ToChangePasswordButton } from "@/src/components";
import { buttonThinColored } from "@/src/styles";

export default function LoginPage() {
  const { startLoading, stopLoading } = str.useLoadingStore();
  useEffect(() => {
    stopLoading();
  }, [stopLoading]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const router = useRouter();
  const { setCreds } = str.useAuthStore();

  const login = async () => {
    setError("");
    setFieldErrors({});

    try {
      startLoading();
      const token = await authService.login({
        email,
        password,
      });
      setCreds(token);
      router.push(CONSTANTS.ROUTES.PRIVATE.CONTACTS);
    } catch (err) {
      stopLoading();
      handleErrorInComponent(err, setError, setFieldErrors);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-100">
            Sign in to your account
          </h2>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
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
        </div>

        <div className="flex items-center justify-between">
          <ToChangePasswordButton />
        </div>

        <div>
          <ActionButton
            label="Sign in"
            loadingIndication="Signing in..."
            action={login}
            className={buttonThinColored}
          />
        </div>
      </div>
    </div>
  );
}
