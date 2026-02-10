"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import * as authService from "@/src/api/auth";
import { CONSTANTS as CNST } from "@/src/config";
import { useLoadingStore, useAuthSteps } from "@/src/stores";
import { handleErrorInComponent } from "@/src/utils";
import { ClipboardEvent, KeyboardEvent, useRef, RefCallback } from "react";

export default function VerifyStep({ email }: { email: string }) {
  const [code, setCode] = useState<string[]>(Array(6).fill(""));
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);
  const router = useRouter();
  const [error, setError] = useState("");
  const { setAuthStep } = useAuthSteps();
  const { startLoading, stopLoading } = useLoadingStore();

  useEffect(() => {
    stopLoading();
  }, [stopLoading]);

  useEffect(() => {
    inputsRef.current = inputsRef.current.slice(0, 6);
  }, []);

  const setInputRef = (index: number): RefCallback<HTMLInputElement> => {
    return (el: HTMLInputElement | null) => {
      inputsRef.current[index] = el;
    };
  };

  const submit = async (code: string) => {
    startLoading();
    setError("");
    try {
      const response = await authService.verifyEmail(email, code);
      setAuthStep("creds");
      router.push(CNST.ROUTES.PUBLIC.LOGIN);
      toast.info(response.message);
    } catch (err) {
      stopLoading();
      handleErrorInComponent(err, setError);
    }
  };

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;

    const newCode = [...code];

    if (value.length > 1) {
      const digits = value.split("").slice(0, 6);
      digits.forEach((digit, digitIndex) => {
        const targetIndex = Math.min(index + digitIndex, 5);
        if (/^\d$/.test(digit)) {
          newCode[targetIndex] = digit;
        }
      });
      setCode(newCode);

      const lastFilledIndex = Math.min(index + digits.length, 5);
      if (lastFilledIndex < 5) {
        inputsRef.current[lastFilledIndex + 1]?.focus();
      }
    } else {
      newCode[index] = value;
      setCode(newCode);

      if (value && index < 5) {
        inputsRef.current[index + 1]?.focus();
      }
    }

    const currentCode = newCode.join("");
    if (currentCode.length === 6 && submit) {
      submit(currentCode);
    }
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace") {
      if (!code[index] && index > 0) {
        const newCode = [...code];
        newCode[index - 1] = "";
        setCode(newCode);
        inputsRef.current[index - 1]?.focus();
      } else {
        const newCode = [...code];
        newCode[index] = "";
        setCode(newCode);
      }
    } else if (e.key === "ArrowLeft" && index > 0) {
      e.preventDefault();
      inputsRef.current[index - 1]?.focus();
    } else if (e.key === "ArrowRight" && index < 5) {
      e.preventDefault();
      inputsRef.current[index + 1]?.focus();
    } else if (e.key === "Delete") {
      const newCode = [...code];
      newCode[index] = "";
      setCode(newCode);
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text/plain").trim();
    const digits = pastedData.replace(/\D/g, "").slice(0, 6);

    if (digits.length > 0) {
      const newCode = [...code];
      digits.split("").forEach((digit, index) => {
        if (index < 6) {
          newCode[index] = digit;
        }
      });
      setCode(newCode);

      if (digits.length === 6) {
        inputsRef.current[5]?.focus();
        submit(digits);
      } else {
        inputsRef.current[digits.length]?.focus();
      }
    }
  };

  useEffect(() => {
    inputsRef.current[0]?.focus();
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-100">
            Verify your email
          </h2>
          <p className="mt-2 text-center text-sm text-gray-100">
            Check your email and copy and paste the confirmation code we sent
            you
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="code" className="sr-only">
            Confirmation code
          </label>
          <div className="flex flex-col relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-500 rounded-lg focus:outline-none focus:ring-cyan-500 focus:border-cyan-500 resize-none">
            <div className="flex justify-center gap-2 sm:gap-3">
              {code.map((digit, index) => (
                <input
                  key={index}
                  ref={setInputRef(index)}
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={index === 5 ? 1 : 6} // Allow pasting in first input
                  value={digit}
                  onChange={(e) => handleChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  onPaste={index === 0 ? handlePaste : undefined} // Only handle paste on first input
                  className={`
              w-12 h-14 sm:w-14 sm:h-16
              text-center text-2xl sm:text-3xl font-semibold
              border-2 rounded-lg
              focus:outline-none focus:ring-2 focus:ring-offset-1
              transition-all duration-200
              ${
                error
                  ? "border-red-500 focus:border-red-500 focus:ring-red-200 bg-red-50"
                  : "border-gray-300 focus:border-blue-500 focus:ring-blue-200"
              }
            `}
                  aria-label={`Digit ${index + 1} of verification code`}
                />
              ))}
            </div>

            {error && (
              <p className="mt-2 text-sm text-red-600 text-center">
                Invalid verification code. Please try again.
              </p>
            )}

            <div className="mt-4 text-center text-sm text-gray-500">
              <p>You can type each digit or paste the entire code</p>
              <p className="text-xs mt-1">Use Ctrl+V or ⌘+V to paste</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
