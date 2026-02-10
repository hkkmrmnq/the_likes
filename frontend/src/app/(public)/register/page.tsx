"use client";

import { useEffect, useState } from "react";
import CredsStep from "./components/CredsStep";
import VerifyStep from "./components/VerifyStep";
import { useAuthSteps, useLoadingStore } from "@/src/stores";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const { authStep } = useAuthSteps();
  const { stopLoading } = useLoadingStore();
  useEffect(() => {
    stopLoading();
  }, [stopLoading]);
  if (authStep === "creds")
    return <CredsStep email={email} setEmail={setEmail} />;
  return <VerifyStep email={email} />;
}
