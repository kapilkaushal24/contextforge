import type { IPlatformAdapter } from "../types/platform-adapter.js";
import { ChatGptAdapter } from "./chatgpt.adapter.js";
import { ClaudeAdapter } from "./claude.adapter.js";
import { GenericAdapter } from "./generic.adapter.js";

const PLATFORM_ADAPTERS: readonly IPlatformAdapter[] = [new ChatGptAdapter(), new ClaudeAdapter()];

/** Selects the most specific adapter for the current page, falling back to generic. */
export function createPlatformAdapter(url: string = window.location.href): IPlatformAdapter {
  const matched = PLATFORM_ADAPTERS.find((adapter) => adapter.matches(url));
  return matched ?? new GenericAdapter();
}
