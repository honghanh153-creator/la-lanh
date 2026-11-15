// In-page layout check for the verification run. Runs inside the browser via page.evaluate, so it
// must stay self-contained (no imports, no closures over Node values).
//
// - overlap: a visible control (button, link, input, ...) whose box overlaps a line of text that
//   is not its own label. This is the class of bug where Home's close (X) button sat on the text.
// - clipped: an element with its own text that overflows a hidden/clipped box (and is not an
//   intended ellipsis or line clamp).
// - offscreen: text that runs past the left/right edge of the viewport.
// - horizontalOverflow: the page itself scrolls sideways.
//
// Candidate overlaps are confirmed by hit-testing (see below), so content covered by an open sheet
// or text under a transparent tap area is not reported.
//
// mode "top" checks pairs in the same layer (both in normal flow, or both fixed). Mode "bottom"
// runs after scrolling to the end and checks pairs where one side is fixed/sticky (a bottom bar may
// cover text mid-scroll, but must not cover it once the user reaches the end of the page).

export type LayoutFinding = { kind: "overlap" | "clipped" | "offscreen"; control?: string; text: string; detail: string };
export type LayoutResult = { findings: LayoutFinding[]; horizontalOverflow: number };

export function layoutCheck(mode: "top" | "bottom"): LayoutResult {
  const viewportWidth = window.innerWidth;
  const findings: LayoutFinding[] = [];
  const seen = new Set<string>();
  const push = (finding: LayoutFinding) => {
    const key = `${finding.kind}|${finding.control ?? ""}|${finding.text}`;
    if (seen.has(key)) return;
    seen.add(key);
    findings.push(finding);
  };

  const isShown = (el: Element) => {
    const html = el as HTMLElement;
    if (typeof html.checkVisibility === "function" && !html.checkVisibility({ opacityProperty: true, visibilityProperty: true })) return false;
    return !el.closest("[aria-hidden='true'], [hidden], [inert]");
  };
  const layerOf = (el: Element) => {
    for (let node: Element | null = el; node; node = node.parentElement) {
      const position = getComputedStyle(node).position;
      if (position === "fixed" || position === "sticky") return position;
    }
    return "flow";
  };
  const describe = (el: Element) => {
    const label = el.getAttribute("aria-label") || (el as HTMLElement).innerText || el.getAttribute("title") || "";
    const cls = (el.getAttribute("class") ?? "").split(/\s+/).filter(Boolean)[0];
    return `${el.tagName.toLowerCase()}${cls ? `.${cls}` : ""} "${label.replace(/\s+/g, " ").trim().slice(0, 40)}"`;
  };
  const short = (text: string) => text.replace(/\s+/g, " ").trim().slice(0, 60);

  const controls = Array.from(document.querySelectorAll(
    "button, a[href], input:not([type=hidden]), select, textarea, [role=button], [role=link], [role=switch], [role=checkbox], [role=radio], [role=tab]",
  )).filter((el) => {
    if (!isShown(el)) return false;
    const box = el.getBoundingClientRect();
    return box.width >= 4 && box.height >= 4;
  });

  // Visually-hidden text (sr-only: a 1px clipped box) still reports full-size line boxes.
  const visuallyHidden = (el: Element) => {
    for (let node: Element | null = el; node && node !== document.body; node = node.parentElement) {
      const style = getComputedStyle(node);
      const box = node.getBoundingClientRect();
      if (style.clip !== "auto" && style.clip !== "") return true;
      if ((box.width <= 2 || box.height <= 2) && style.overflow !== "visible") return true;
    }
    return false;
  };

  type TextLine = { node: Text; parent: Element; rects: DOMRect[] };
  const textRects = (node: Text) => {
    const range = document.createRange();
    range.selectNodeContents(node);
    return Array.from(range.getClientRects()).filter((rect) => rect.width > 1 && rect.height > 1);
  };
  const lines: TextLine[] = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode() as Text | null; node; node = walker.nextNode() as Text | null) {
    const parent = node.parentElement;
    if (!parent || !node.data.trim() || !isShown(parent) || visuallyHidden(parent)) continue;
    if (["SCRIPT", "STYLE", "NOSCRIPT", "OPTION"].includes(parent.tagName)) continue;
    const rects = textRects(node);
    if (rects.length) lines.push({ node, parent, rects });
  }

  // A control with no background, border or shadow is drawn only by its text and icons; its box
  // may carry extra padding just to make a 44px tap area (e.g. an inline "Xem chi tiết" link with
  // negative margins). For those, judge what is drawn: the text and icon boxes inside it. A
  // transparent hit area with nothing drawn is not a visual overlap.
  const controlBoxes = (control: Element) => {
    const style = getComputedStyle(control);
    const painted = !/rgba\(0, 0, 0, 0\)|transparent/.test(style.backgroundColor)
      || style.backgroundImage !== "none"
      || parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth) + parseFloat(style.borderLeftWidth) + parseFloat(style.borderRightWidth) > 0
      || style.boxShadow !== "none";
    if (painted || ["INPUT", "SELECT", "TEXTAREA"].includes(control.tagName)) return [control.getBoundingClientRect()];
    const range = document.createRange();
    range.selectNodeContents(control);
    const rects = Array.from(range.getClientRects());
    control.querySelectorAll("svg, img").forEach((icon) => rects.push(icon.getBoundingClientRect()));
    return rects.filter((rect) => rect.width > 1 && rect.height > 1);
  };

  // Text that belongs to the control (its <label>, aria-labelledby or aria-describedby, e.g. a
  // floating label or a 0/280 counter drawn inside a field) is part of the control's design.
  const ownText = (control: Element, parent: Element) => {
    const labels = (control as HTMLInputElement).labels;
    if (labels && Array.from(labels).some((label) => label.contains(parent))) return true;
    const ids = `${control.getAttribute("aria-labelledby") ?? ""} ${control.getAttribute("aria-describedby") ?? ""}`.split(/\s+/).filter(Boolean);
    return ids.some((id) => document.getElementById(id)?.contains(parent));
  };

  const overlapOf = (box: DOMRect, rect: DOMRect) => {
    // Line boxes include leading above and below the glyphs; only the middle half counts, so
    // a padded touch target that grazes the gap between lines is not reported.
    const top = rect.top + rect.height / 4;
    const bottom = rect.bottom - rect.height / 4;
    const left = Math.max(box.left, rect.left);
    const right = Math.min(box.right, rect.right);
    const upper = Math.max(box.top, top);
    const lower = Math.min(box.bottom, bottom);
    return right - left >= 3 && lower - upper >= 3 ? { left, right, top: upper, bottom: lower } : null;
  };

  // Hit-testing: both sides must be drawn on top somewhere (not hidden under a sheet or backdrop),
  // and at the overlap the topmost element must be one of the two. Elements with
  // pointer-events: none are invisible to this test (known limit).
  const topAt = (x: number, y: number) =>
    x >= 0 && y >= 0 && x < window.innerWidth && y < window.innerHeight ? document.elementFromPoint(x, y) : null;
  const ownsPoint = (owner: Element, x: number, y: number) => {
    const top = topAt(x, y);
    return Boolean(top && (owner.contains(top) || top.contains(owner)));
  };
  const visibleIn = (owner: Element, rects: DOMRect[]) => rects.some((rect) => {
    const x = Math.min(Math.max(rect.left + rect.width / 2, 0), window.innerWidth - 1);
    const y = Math.min(Math.max(rect.top + rect.height / 2, 0), window.innerHeight - 1);
    return ownsPoint(owner, x, y);
  });

  for (const control of controls) {
    const controlLayer = layerOf(control);
    for (const line of lines) {
      if (control.contains(line.node) || ownText(control, line.parent)) continue;
      const mixed = controlLayer !== layerOf(line.parent);
      if ((mode === "top" && mixed) || (mode === "bottom" && !mixed)) continue;
      const hit = controlBoxes(control).some((box) => line.rects.some((rect) => overlapOf(box, rect)));
      if (!hit) continue;
      // Bring the overlap into view (same-layer pairs keep their relative position), then confirm.
      const scrollY = window.scrollY;
      let confirmed: { left: number; right: number; top: number; bottom: number } | null = null;
      for (const box of controlBoxes(control)) {
        for (const rect of line.rects) {
          const area = overlapOf(box, rect);
          if (!area) continue;
          if (mode === "top" && controlLayer === "flow") {
            window.scrollTo(0, window.scrollY + (area.top + area.bottom) / 2 - window.innerHeight / 2);
          }
          const boxes = controlBoxes(control);
          const lineRects = textRects(line.node);
          const fresh = boxes.flatMap((b) => lineRects.map((r) => overlapOf(b, r))).find(Boolean) ?? null;
          if (!fresh) continue;
          const cx = (fresh.left + fresh.right) / 2;
          const cy = (fresh.top + fresh.bottom) / 2;
          const topOwned = ownsPoint(control, cx, cy) || ownsPoint(line.parent, cx, cy);
          if (topOwned && visibleIn(control, boxes) && visibleIn(line.parent, lineRects)) {
            confirmed = { ...fresh, top: fresh.top + window.scrollY, bottom: fresh.bottom + window.scrollY };
          }
          break;
        }
        if (confirmed) break;
      }
      if (mode === "top") window.scrollTo(0, scrollY);
      if (!confirmed) continue;
      push({
        kind: "overlap",
        control: describe(control),
        text: short(line.node.data),
        detail: `${Math.round(confirmed.right - confirmed.left)}x${Math.round(confirmed.bottom - confirmed.top)}px at (${Math.round(confirmed.left)}, ${Math.round(confirmed.top)})`,
      });
    }
  }

  if (mode === "top") {
    const clipsX = (el: Element) => {
      for (let node = el.parentElement; node && node !== document.body; node = node.parentElement) {
        const overflowX = getComputedStyle(node).overflowX;
        if (overflowX !== "visible") return true;
      }
      return false;
    };
    for (const line of lines) {
      const el = line.parent as HTMLElement;
      const style = getComputedStyle(el);
      const hidesX = style.overflowX === "hidden" || style.overflowX === "clip";
      const hidesY = style.overflowY === "hidden" || style.overflowY === "clip";
      // Visually-hidden (sr-only) text is meant to be clipped to a 1px box.
      if (el.clientWidth <= 2 || el.clientHeight <= 2) continue;
      const clamped = style.textOverflow === "ellipsis" || (style.getPropertyValue("-webkit-line-clamp") || "none") !== "none";
      if (!clamped && ((hidesX && el.scrollWidth > el.clientWidth + 1) || (hidesY && el.scrollHeight > el.clientHeight + 1)) && el.clientWidth > 0 && el.clientHeight > 0) {
        push({ kind: "clipped", text: short(line.node.data), detail: `${describe(el)} content ${el.scrollWidth}x${el.scrollHeight} > box ${el.clientWidth}x${el.clientHeight}` });
      }
      if (!clipsX(el) && line.rects.some((rect) => rect.right > viewportWidth + 1 || rect.left < -1)) {
        const rect = line.rects.find((r) => r.right > viewportWidth + 1 || r.left < -1)!;
        push({ kind: "offscreen", text: short(line.node.data), detail: `${describe(el)} spans ${Math.round(rect.left)}..${Math.round(rect.right)} in a ${viewportWidth}px viewport` });
      }
    }
  }

  const root = document.documentElement;
  return { findings, horizontalOverflow: Math.max(0, root.scrollWidth - root.clientWidth) };
}
