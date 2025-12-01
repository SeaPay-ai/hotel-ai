import clsx from "clsx";
import { useRef } from "react";
import { Route, Routes } from "react-router-dom";

import { ChatKitPanel } from "./components/ChatKitPanel";
import type { ChatKit } from "./components/ChatKitPanel";
import { ThemeToggle } from "./components/ThemeToggle";
import { useAppStore } from "./store/useAppStore";

function AppShell() {
  const chatkitRef = useRef<ChatKit | null>(null);
  const scheme = useAppStore((state) => state.scheme);

  const containerClass = clsx(
    "h-full flex min-h-screen flex-col transition-colors duration-300 relative",
    "bg-cover bg-center bg-no-repeat"
  );
  const headerBarClass = clsx(
    "sticky top-0 z-30 w-full border-b shadow-sm backdrop-blur-sm bg-white/80 dark:bg-[#1c1c1c]/80",
    scheme === "dark"
      ? "border-slate-200 text-slate-100"
      : "border-slate-800 text-slate-900"
  );

  return (
    <div className={containerClass}>
      <div
        className='absolute inset-0 bg-cover bg-center bg-no-repeat blur-sm'
        style={{
          backgroundImage: "url('/R0002623.JPG')",
        }}
      />
      <div className='relative z-10 flex min-h-screen flex-col'>
        <div className={headerBarClass}>
          <div className='relative flex w-full flex-col gap-4 px-6 py-6 pr-24 sm:flex-row sm:items-center sm:gap-8'>
            <span className='text-xl font-semibold uppercase tracking-[0.45em] text-slate-900 dark:text-slate-100'>
              Sea Pay
            </span>
            <p className='mt-1 text-sm font-normal tracking-wide text-slate-800 dark:text-slate-200'>
              Find and reserve hotels with crypto payments.
            </p>
            <div className='absolute right-6 top-5'>
              <ThemeToggle />
            </div>
          </div>
        </div>
        <div className='flex flex-1 min-h-0 items-center justify-center p-4 md:p-8'>
          <div className='w-full max-w-4xl h-full max-h-[calc(100vh-120px)] flex flex-col bg-white/95 dark:bg-[#1c1c1c]/95 rounded-lg shadow-2xl backdrop-blur-sm border border-slate-200 dark:border-slate-700'>
            <ChatKitPanel
              className='flex-1'
              onChatKitReady={(chatkit) => (chatkitRef.current = chatkit)}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path='/' element={<AppShell />} />
      <Route path='*' element={<AppShell />} />
    </Routes>
  );
}
