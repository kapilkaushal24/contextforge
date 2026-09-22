/** Tiny DOM-builder helpers used only by content/panel.ts. Always `textContent`, never
 * `innerHTML`, for anything derived from the user's prompt or an API response. */

type Child = string | HTMLElement | undefined | false;

export function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  for (const child of children) {
    if (!child) continue;
    node.append(child instanceof HTMLElement ? child : document.createTextNode(child));
  }
  return node;
}

export function button(className: string, label: string, onClick: () => void): HTMLButtonElement {
  const node = el("button", className, label);
  node.type = "button";
  node.addEventListener("click", onClick);
  return node;
}

export function closeButton(onClick: () => void): HTMLButtonElement {
  const node = button("close", "×", onClick);
  node.setAttribute("aria-label", "Dismiss");
  return node;
}
