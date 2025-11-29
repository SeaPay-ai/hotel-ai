import { StartScreenPrompt, ToolOption } from "@openai/chatkit";

export const CHATKIT_API_URL =
  import.meta.env.VITE_CHATKIT_API_URL ?? "/chatkit";

/**
 * ChatKit still expects a domain key at runtime. Use any placeholder locally,
 * but register your production domain at
 * https://platform.openai.com/settings/organization/security/domain-allowlist
 * and deploy the real key.
 */
export const CHATKIT_API_DOMAIN_KEY =
  import.meta.env.VITE_CHATKIT_API_DOMAIN_KEY ?? "domain_pk_localhost_dev";

export const THEME_STORAGE_KEY = "seapay-theme";

export const GREETING = "I'm here to help you find and book hotels";

export const STARTER_PROMPTS: StartScreenPrompt[] = [
  {
    label: "Find hotels",
    prompt: "Find hotels",
    icon: "globe",
  },
  {
    label: "Check availability",
    prompt: "Check hotel availability for my dates",
    icon: "calendar",
  },
  {
    label: "View hotel details",
    prompt: "Show me available hotels with details",
    icon: "sparkle",
  },
  {
    label: "Help with booking",
    prompt: "Help me make a reservation",
    icon: "lightbulb",
  },
];

export const getPlaceholder = (hasThread: boolean) => {
  return hasThread
    ? "Ask about hotels or make a reservation"
    : "Find hotels";
};

// No custom tool toggles for now; the SeaPay agent decides when to call MCP tools.
export const TOOL_CHOICES: ToolOption[] = [];
