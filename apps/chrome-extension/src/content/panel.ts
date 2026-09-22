import { humanizeReviewReasons } from "../constants/review-reasons.js";
import { estimateTokensLocally } from "../services/local-token-estimate.js";
import { button, closeButton, el } from "./dom.js";
import type { WidgetState } from "./optimization-widget-state.js";
import { PANEL_STYLES } from "./panel-styles.js";

export interface PanelHandlers {
  onOptimize: () => void;
  onApply: () => void;
  onReject: () => void;
  onUndo: () => void;
  onDismiss: () => void;
}

/**
 * Renders the widget into an isolated shadow root (never `innerHTML` with text
 * derived from the user's prompt or the API — always `textContent`/DOM
 * construction via content/dom.ts, so nothing there can execute as markup).
 */
export class OptimizationPanel {
  private readonly host: HTMLElement;
  private readonly shadow: ShadowRoot;
  private readonly root: HTMLElement;

  constructor(
    container: HTMLElement,
    private readonly handlers: PanelHandlers,
  ) {
    this.host = document.createElement("div");
    this.host.setAttribute("data-ai-token-optimizer-root", "");
    this.shadow = this.host.attachShadow({ mode: "closed" });

    const style = document.createElement("style");
    style.textContent = PANEL_STYLES;
    this.shadow.appendChild(style);

    this.root = document.createElement("div");
    this.shadow.appendChild(this.root);

    container.appendChild(this.host);
  }

  destroy(): void {
    this.host.remove();
  }

  render(state: WidgetState): void {
    this.root.replaceChildren();
    const card = this.buildCard(state);
    if (card) this.root.appendChild(card);
  }

  private buildCard(state: WidgetState): HTMLElement | null {
    switch (state.phase) {
      case "hidden":
        return null;
      case "idle":
        return this.renderIdle(state.text);
      case "loading":
        return this.renderLoading();
      case "result":
        return this.renderResult(state);
      case "applied":
        return this.renderApplied(state);
      case "error":
        return this.renderError(state.message);
      default: {
        const exhaustive: never = state;
        return exhaustive;
      }
    }
  }

  private renderIdle(text: string): HTMLElement {
    return el(
      "div",
      "card",
      el(
        "div",
        "pill",
        el("span", "pill-text", `~${estimateTokensLocally(text)} tokens`),
        button("btn-primary", "Optimize", this.handlers.onOptimize),
      ),
    );
  }

  private renderLoading(): HTMLElement {
    return el(
      "div",
      "card",
      el("div", "pill", el("div", "spinner"), el("span", "pill-text", "Optimizing…")),
    );
  }

  private renderResult(state: Extract<WidgetState, { phase: "result" }>): HTMLElement {
    const { result } = state;
    const reduction = Math.round(result.reductionPercentage);

    const header = el(
      "div",
      "header",
      el("span", "title", "Optimization ready"),
      closeButton(this.handlers.onReject),
    );

    const stats = el(
      "div",
      "stats",
      `${result.originalTokens} → ${result.optimizedTokens} tokens `,
      el("strong", undefined, reduction > 0 ? `(${reduction}% smaller)` : "(no size change)"),
    );

    const warning = result.requiresReview
      ? el(
          "div",
          "warning",
          humanizeReviewReasons(result.reviewReasons).length > 0
            ? `Review recommended: ${humanizeReviewReasons(result.reviewReasons).join(", ")}.`
            : "Review recommended before applying.",
        )
      : undefined;

    const changes =
      result.changes.length > 0
        ? el(
            "ul",
            "changes",
            ...result.changes.slice(0, 5).map((change) => el("li", undefined, change.description)),
          )
        : undefined;

    const preview = el("div", "preview", result.optimizedText);

    const actions = el(
      "div",
      "actions",
      button("btn-primary", "Apply", this.handlers.onApply),
      button("btn-secondary", "Keep original", this.handlers.onReject),
    );

    const body = el("div", "body", header, stats, warning, changes, preview, actions);
    return el("div", "card", body);
  }

  private renderApplied(state: Extract<WidgetState, { phase: "applied" }>): HTMLElement {
    return el(
      "div",
      "card",
      el(
        "div",
        "pill",
        el("span", "pill-text", `✓ Applied — ${state.result.tokensSaved} tokens saved`),
        button("btn-link", "Undo", this.handlers.onUndo),
        closeButton(this.handlers.onDismiss),
      ),
    );
  }

  private renderError(message: string): HTMLElement {
    return el(
      "div",
      "card",
      el(
        "div",
        "pill",
        el("span", "pill-text", `Optimization unavailable: ${message}`),
        closeButton(this.handlers.onDismiss),
      ),
    );
  }
}
