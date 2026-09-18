import { createPlatformAdapter } from "../adapters/factory.js";

/**
 * Content script entry point. For this scaffold it only proves out the adapter
 * pattern end-to-end (selection + input detection); wiring `onSubmitIntercept` to
 * the optimize-preview UI (Apply/Reject/Undo) lands with the preview component,
 * once the backend (Phase 5) has a real /optimize endpoint to call.
 */
const adapter = createPlatformAdapter();

function logActivation(): void {
  const input = adapter.getInputElement();
  // eslint-disable-next-line no-console
  console.debug(
    `[ai-token-optimizer] adapter "${adapter.id}" active; prompt input ${input ? "found" : "not found"}`,
  );
}

logActivation();

// Re-check periodically: AI chat UIs are SPAs where the input element can be
// unmounted/remounted (new conversation, route change) without a full page load.
const observer = new MutationObserver(() => {
  if (adapter.getInputElement()) {
    observer.disconnect();
    logActivation();
  }
});
observer.observe(document.body, { childList: true, subtree: true });
