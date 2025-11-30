import { ChatKit, useChatKit, Widgets } from "@openai/chatkit-react";
import clsx from "clsx";
import { useCallback, useRef } from "react";

import {
  CHATKIT_API_DOMAIN_KEY,
  CHATKIT_API_URL,
  GREETING,
  STARTER_PROMPTS,
  TOOL_CHOICES,
  getPlaceholder,
} from "../lib/config";
import { LORA_SOURCES } from "../lib/fonts";
import { useAppStore } from "../store/useAppStore";

export type ChatKit = ReturnType<typeof useChatKit>;

type ChatKitPanelProps = {
  onChatKitReady: (chatkit: ChatKit) => void;
  className?: string;
};

export function ChatKitPanel({ onChatKitReady, className }: ChatKitPanelProps) {
  const chatkitRef = useRef<ReturnType<typeof useChatKit> | null>(null);

  const theme = useAppStore((state) => state.scheme);
  const activeThread = useAppStore((state) => state.threadId);
  const setThreadId = useAppStore((state) => state.setThreadId);

  const handleWidgetAction = useCallback(
    async (
      action: { type: string; payload?: Record<string, unknown> },
      widgetItem: { id: string; widget: Widgets.Card | Widgets.ListView }
    ) => {
      const chatkit = chatkitRef.current;
      if (!chatkit) {
        return;
      }

      switch (action.type) {
        case "select_hotel":
        case "hotels.select_hotel": {
          // Support both old and new action format
          const hotelId = action.payload?.id as string | undefined;
          const hotelName = action.payload?.hotelName as string | undefined;
          const options = action.payload?.options as
            | Array<{ id: string; hotelName: string }>
            | undefined;

          let selectedHotelName: string | undefined;

          if (hotelName) {
            // Old format with hotelName directly
            selectedHotelName = hotelName;
          } else if (hotelId && options) {
            // New format: find hotel by id in options
            const selectedHotel = options.find((h) => h.id === hotelId);
            selectedHotelName = selectedHotel?.hotelName;
          }

          if (selectedHotelName) {
            // Send the custom action - the backend will handle it
            // The action payload contains the hotel info for the agent to process
            await chatkit.sendCustomAction(action, widgetItem.id);
          }
          break;
        }
        case "hotels.more_hotels": {
          // Send the custom action - the backend will handle it
          await chatkit.sendCustomAction(action, widgetItem.id);
          break;
        }
      }
    },
    []
  );

  const chatkit = useChatKit({
    api: { url: CHATKIT_API_URL, domainKey: CHATKIT_API_DOMAIN_KEY },
    theme: {
      density: "spacious",
      colorScheme: theme,
      color: {
        grayscale: {
          hue: 0,
          tint: 0,
          shade: theme === "dark" ? -1 : 0,
        },
        accent: {
          primary: "#ff5f42",
          level: 1,
        },
      },
      typography: {
        fontFamily: "Lora, serif",
        fontSources: LORA_SOURCES,
      },
      radius: "round",
    },
    startScreen: {
      greeting: GREETING,
      prompts: STARTER_PROMPTS,
    },
    composer: {
      placeholder: getPlaceholder(Boolean(activeThread)),
      tools: TOOL_CHOICES,
    },
    threadItemActions: {
      feedback: false,
    },
    widgets: {
      onAction: handleWidgetAction,
    },
    onThreadChange: ({ threadId }) => setThreadId(threadId),
    onError: ({ error }) => {
      console.error("ChatKit error", error);
    },
    onReady: () => {
      onChatKitReady?.(chatkit);
    },
  });
  chatkitRef.current = chatkit;

  return (
    <div className={clsx("relative h-full w-full overflow-hidden", className)}>
      <ChatKit control={chatkit.control} className='block h-full w-full' />
    </div>
  );
}
