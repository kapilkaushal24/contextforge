/**
 * Scoped to the widget's shadow root, so it can never leak into (or be broken by) the
 * host AI site's CSS — the whole reason this widget lives in a shadow DOM
 * (docs/architecture/chrome-extension.md §4).
 */
export const PANEL_STYLES = `
  :host { all: initial; }
  * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }

  .card {
    position: fixed;
    right: 20px;
    bottom: 20px;
    z-index: 2147483647;
    max-width: 340px;
    background: #ffffff;
    color: #111827;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    font-size: 13px;
    line-height: 1.4;
  }

  .pill {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
  }

  .pill-text { color: #4b5563; }

  button {
    font: inherit;
    cursor: pointer;
    border-radius: 6px;
    border: 1px solid transparent;
    padding: 6px 10px;
  }

  .btn-primary { background: #2563eb; color: #fff; border-color: #2563eb; }
  .btn-primary:hover { background: #1d4ed8; }
  .btn-secondary { background: #f3f4f6; color: #374151; border-color: #e5e7eb; }
  .btn-secondary:hover { background: #e5e7eb; }
  .btn-link { background: transparent; color: #2563eb; padding: 4px 6px; }

  .close {
    background: transparent;
    border: none;
    color: #9ca3af;
    padding: 2px 6px;
    margin-left: auto;
  }

  .body { padding: 12px; }
  .header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
  .title { font-weight: 600; }

  .stats { color: #4b5563; margin-bottom: 8px; }
  .stats strong { color: #111827; }

  .warning {
    background: #fffbeb;
    border: 1px solid #fde68a;
    color: #92400e;
    border-radius: 6px;
    padding: 8px;
    margin-bottom: 8px;
  }

  .notice {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1e40af;
    border-radius: 6px;
    padding: 8px;
    margin-bottom: 8px;
  }

  .changes { margin: 0 0 8px 0; padding-left: 18px; color: #4b5563; }
  .changes li { margin-bottom: 2px; }

  .preview {
    max-height: 120px;
    overflow-y: auto;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 8px;
    margin-bottom: 10px;
    white-space: pre-wrap;
    word-break: break-word;
    color: #1f2937;
  }

  .actions { display: flex; gap: 8px; }
  .spinner {
    width: 12px;
    height: 12px;
    border: 2px solid #d1d5db;
    border-top-color: #2563eb;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
`;
