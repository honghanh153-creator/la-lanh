import { createContext, useContext, useEffect, useRef, type RefObject } from "react";

/**
 * Where sheets and dialogs portal to. SessionBoundary provides a node *inside* its private
 * region, so a dialog is hidden together with the route whenever the session is suspended,
 * re-verified or changes owner. Outside the boundary (tests, public pages) it is document.body.
 */
export type PrivatePortal = { target: HTMLElement | null; visible: boolean };

export const PrivatePortalContext = createContext<PrivatePortal | null>(null);

export function usePrivatePortalTarget(): HTMLElement {
  return useContext(PrivatePortalContext)?.target ?? document.body;
}

/** False while the private region is hidden (checking, offline, owner change). */
export function usePrivateRegionVisible(): boolean {
  return useContext(PrivatePortalContext)?.visible ?? true;
}

/**
 * Hiding the private region drops focus to <body>. When the same owner is verified again and
 * the dialog is still open, put focus back where it was inside the dialog (or on `initial`)
 * so the focus trap and Escape keep working. Nothing is focused while the region is hidden.
 */
export function useRestoreDialogFocus(
  open: boolean,
  dialogRef: RefObject<HTMLElement | null>,
  initialRef: RefObject<HTMLElement | null>,
): void {
  const visible = usePrivateRegionVisible();
  const lastFocusedRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!open || !dialog) return;
    const remember = (event: FocusEvent) => {
      if (event.target instanceof HTMLElement) lastFocusedRef.current = event.target;
    };
    dialog.addEventListener("focusin", remember);
    return () => dialog.removeEventListener("focusin", remember);
  }, [open, dialogRef]);

  useEffect(() => {
    if (!open) {
      lastFocusedRef.current = null;
      return;
    }
    const dialog = dialogRef.current;
    if (!visible || !dialog || dialog.contains(document.activeElement)) return;
    const last = lastFocusedRef.current;
    const target = last && last.isConnected && dialog.contains(last) && !last.matches(":disabled")
      ? last
      : initialRef.current;
    target?.focus();
  }, [open, visible, dialogRef, initialRef]);
}
