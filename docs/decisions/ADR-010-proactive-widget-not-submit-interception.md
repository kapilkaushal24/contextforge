# ADR-010: Proactive Optimization Widget, Not Submit Interception

## Context
The Phase 4 extension scaffold gave `IPlatformAdapter` an `onSubmitIntercept(callback)`
hook: click the platform's Send button, prevent the default action, silently swap in
optimized text, then re-click Send. It was never wired to anything — Phase 10 is where
the preview UI (Apply/Reject/Undo) was due to land, so this needed a real decision.

That design has three problems:
1. It silently replaces and resubmits the user's prompt with no explicit Apply click,
   directly contradicting the UX contract ("optimization is never auto-applied by
   default" — docs/architecture/chrome-extension.md §6).
2. It is fragile against React-controlled inputs: programmatically setting `textContent`
   and re-dispatching a click on the same button, inside the same capturing listener,
   depends on the second pass being a no-op (text already equal) rather than recursing.
3. It only ever triggers at the moment of submission, so the user never sees a
   before/after preview, confidence score, or reasons before their prompt leaves the
   browser — the whole point of `docs/product/requirements.md`'s core user stories.

## Decision
Replace it with a proactive widget (`content/optimization-widget.ts` +
`content/optimization-widget-state.ts` + `content/panel.ts`):
- The content script watches the adapter's input element (debounced, 400ms) and shows a
  small shadow-DOM pill once the prompt reaches `MIN_WORDS_TO_SHOW` (8) words, with a
  local, zero-latency `~N tokens` estimate.
- Clicking **Optimize** is the only thing that calls the backend. The result — token
  counts, reduction %, confidence, a review warning with human-readable reasons when
  `requiresReview` is true, and the changes made — is shown before anything happens to
  the input.
- **Apply** calls `adapter.setText()` (the only place that happens) and remembers the
  pre-optimization text; **Undo** restores it. **Keep original** / dismiss just closes
  the widget — the input is never touched.
- `IPlatformAdapter` loses `onSubmitIntercept` entirely; nothing hooks the Send button.
- The pure state machine (`reduceWidgetState`) is unit-tested in isolation (21 test
  cases) precisely because it is the thing responsible for the "no `setText` without an
  explicit Apply/Undo click" invariant — see the comment at the top of that file.

## Alternatives considered
- **Keep submit interception, but show a confirm dialog synchronously** — rejected:
  `window.confirm` is jarring, blocks the page, and a network call (to optimize) can't
  happen synchronously inside a click handler before `preventDefault` without racing
  the site's own submit logic.
- **Auto-apply optimizations above the confidence threshold** — rejected: contradicts
  the product's core trust proposition (docs/product/requirements.md §7); the user must
  stay in control even when the score is high.

## Consequences
- The user takes one extra click (Optimize) compared to silent auto-optimization; this
  is intentional, not an oversight.
- The widget is unverified against the real ChatGPT/Claude DOM in this environment (no
  logged-in browser session available) — load-unpacked-and-test is still needed before
  shipping, same caveat as the adapters' selectors since Phase 4.
- A future "one-click always optimize" power-user setting is possible as an opt-in
  preference, but would need its own confirmation UX design, not a resurrection of
  submit interception.
