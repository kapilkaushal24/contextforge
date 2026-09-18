/**
 * Centralized, versioned DOM selectors — one block per platform. Nothing outside this
 * file (and its owning adapter) should ever hardcode a selector string, so a site's
 * DOM change is a one-file fix (docs/architecture/chrome-extension.md §3).
 */
export const CHATGPT_SELECTORS = {
  /** Version tag bumped whenever ChatGPT's DOM forces a selector change. */
  version: 1,
  promptInput: "#prompt-textarea",
  submitButton: '[data-testid="send-button"]',
} as const;

export const CLAUDE_SELECTORS = {
  version: 1,
  promptInput: 'div[contenteditable="true"][data-testid="chat-input"]',
  submitButton: 'button[aria-label="Send Message"]',
} as const;
