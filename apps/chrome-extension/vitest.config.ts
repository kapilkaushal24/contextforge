import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // Every *.test.ts file here is deliberately DOM-free (pure state machines, pure
    // formatting helpers) — the DOM-touching wiring (content/optimization-widget.ts,
    // background/service-worker.ts) is thin by design and verified manually via
    // `npm run build:extension` + loading the unpacked extension, not unit-tested.
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
