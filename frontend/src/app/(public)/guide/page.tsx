"use client";

import { useEffect } from "react";
import { useLoadingStore } from "@/src/stores";
import { Header } from "@/src/components";

export default function GuidePage() {
  const { stopLoading } = useLoadingStore();
  useEffect(() => {
    stopLoading();
  }, [stopLoading]);
  return (
    <div className="flex flex-col h-screen">
      <header className="h-16 flex-shrink-0">
        <Header />
      </header>
      <main className="flex-1 overflow-auto thin-scrollbar">
        <div className="flex justify-center">
          <div className="p-2 max-w-[800px]">
            <p>
              I offer you a set of terms denoting possible abstract values:
              Pleasure, Comfort, Happiness, Love, Beauty, Wealth, Status, Power,
              Violence, Truth, Freedom.
            </p>
            <p>
              In the first step, you must select components — Aspects — for each
              value. If you agree that a statement should be included in the
              value definition, check the box next to it. For example, if you
              agree that Beauty is (partially or completely) an objective
              quality, include this aspect in the definition of beauty.
            </p>

            <p>
              Important: each combination of Aspects is considered as an
              independent Value. That is, if you included the Aspect "objective
              quality" in Beauty, and someone else — not — we do not know how
              close or distant is your view on Beauty from the view of that
              other person.
            </p>
            <p>
              In the second step, distribute your Values among three groups:
              positive, negative, and neutral. Initially, all Values are in the
              neutral group. If you want more Beauty in your life, move it to
              the positive. If less, move it to the negative. Leave the values
              you don't care about in the neutral group.
            </p>
            <p>
              Positive and negative Values should be arranged hierarchically
              according to how you feel about them: the best at the very top,
              the worst at the very bottom. Neutral values don't need to be
              sorted — their order doesn't matter.
            </p>
            <p>
              Though the values can be ordered any way you like — all decisions
              will be taken into account — preference will be given to the first
              two positive and last two negative values. You can change Aspects
              and Values hierarchy later, but frequent changes will reduce
              chances of getting a recommendation.
            </p>
            <p>
              In the third step, you'll choose a statement that characterizes
              your overall attitude toward values.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
