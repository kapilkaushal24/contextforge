import { defineManifest } from "@crxjs/vite-plugin";
import pkg from "./package.json";

/**
 * Manifest V3. Permissions are kept to the minimum necessary (ADR-001):
 * - `storage` for settings/cached stats.
 * - `activeTab` instead of a broad `tabs` permission.
 * - `host_permissions` scoped to the specific AI platforms we support plus the
 *   backend API origin — never `<all_urls>`.
 */
export default defineManifest({
  manifest_version: 3,
  name: "AI Token Optimizer",
  description:
    "Estimates and reduces token usage in prompts sent to AI chat tools, while preserving intent.",
  version: pkg.version,
  icons: {
    16: "src/assets/icon-16.png",
    48: "src/assets/icon-48.png",
    128: "src/assets/icon-128.png",
  },
  action: {
    default_popup: "src/popup/index.html",
    default_icon: {
      16: "src/assets/icon-16.png",
      48: "src/assets/icon-48.png",
      128: "src/assets/icon-128.png",
    },
  },
  options_page: "src/options/index.html",
  background: {
    service_worker: "src/background/service-worker.ts",
    type: "module",
  },
  content_scripts: [
    {
      matches: [
        "https://chat.openai.com/*",
        "https://chatgpt.com/*",
        "https://claude.ai/*",
      ],
      js: ["src/content/index.ts"],
      run_at: "document_idle",
    },
  ],
  host_permissions: [
    "https://chat.openai.com/*",
    "https://chatgpt.com/*",
    "https://claude.ai/*",
    // Dev-only backend origin; replaced with the production API origin at build time
    // via an environment-specific manifest override once the backend (Phase 5) ships.
    "http://localhost:8000/*",
  ],
  permissions: ["storage", "activeTab"],
});
