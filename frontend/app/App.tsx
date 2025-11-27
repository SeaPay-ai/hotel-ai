"use client";

import { useCallback } from "react";
import { motion } from "framer-motion";
import { Plane, Sparkles } from "lucide-react";
import { ChatKitPanel, type FactAction } from "@/components/ChatKitPanel";
import { useColorScheme } from "@/hooks/useColorScheme";

export default function App() {
  const { scheme, setScheme } = useColorScheme();

  const handleWidgetAction = useCallback(async (action: FactAction) => {
    if (process.env.NODE_ENV !== "production") {
      console.info("[ChatKitPanel] widget action", action);
    }
  }, []);

  const handleResponseEnd = useCallback(() => {
    if (process.env.NODE_ENV !== "production") {
      console.debug("[ChatKitPanel] response end");
    }
  }, []);

  return (
    <div
      className="flex min-h-screen flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 bg-cover bg-center bg-no-repeat"
      style={{ backgroundImage: "url(/bg.jpg)" }}
    >
      <motion.header
        initial={{ y: -80, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="border-b border-white/60 bg-white/80 backdrop-blur-xl shadow-sm"
      >
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg shadow-purple-500/30 ring-2 ring-white/40">
              <Plane className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800">AI Travel Agent</h1>
              <p className="text-sm text-slate-600">
                Your personal trip planner and itinerary expert
              </p>
            </div>
          </div>
        </div>
      </motion.header>

      <main className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto flex max-w-5xl flex-col gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.5, ease: "easeOut" }}
            className="rounded-3xl border border-white/60 bg-white/70 px-5 py-4 text-slate-700 shadow-lg shadow-black/5 backdrop-blur-lg ring-1 ring-white/40"
          >
            <div className="flex items-center gap-2 text-sm sm:text-base">
              <Sparkles className="h-5 w-5 text-purple-500" />
              <span className="font-semibold text-slate-800">
                Tell me about your dream destination and travel style. I will craft routes, stays,
                and must-see stops for you.
              </span>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6, ease: "easeOut" }}
          >
            <ChatKitPanel
              theme={scheme}
              onWidgetAction={handleWidgetAction}
              onResponseEnd={handleResponseEnd}
              onThemeRequest={setScheme}
            />
          </motion.div>
        </div>
      </main>
    </div>
  );
}
