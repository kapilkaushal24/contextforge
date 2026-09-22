import { createPlatformAdapter } from "../adapters/factory.js";
import { OptimizationWidget } from "./optimization-widget.js";

/**
 * Content script entry point: selects the platform adapter and starts the proactive
 * optimization widget (see optimization-widget.ts / docs/architecture/chrome-extension.md
 * §3a). One widget instance per page load; it watches the adapter's input element for
 * the page's lifetime, so it does not need to be recreated on SPA route changes.
 */
const adapter = createPlatformAdapter();
new OptimizationWidget(adapter);

// eslint-disable-next-line no-console
console.debug(`[ai-token-optimizer] adapter "${adapter.id}" active`);
