import { X } from "@phosphor-icons/react";
import {
  useEffect,
  useId,
  useRef,
  type KeyboardEvent as ReactKeyboardEvent,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

type AppSheetProps = {
  children: ReactNode;
  closeDisabled?: boolean;
  eyebrow?: string;
  onClose: () => void;
  open: boolean;
  title: string;
};

const focusableSelector = [
  "button:not(:disabled)",
  "a[href]",
  "input:not(:disabled)",
  "select:not(:disabled)",
  "textarea:not(:disabled)",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

export function AppSheet({
  children,
  closeDisabled = false,
  eyebrow,
  onClose,
  open,
  title,
}: AppSheetProps) {
  const titleId = useId();
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const wasOpenRef = useRef(false);

  useEffect(() => {
    if (!open) {
      if (wasOpenRef.current) {
        wasOpenRef.current = false;
        returnFocusRef.current?.focus();
        returnFocusRef.current = null;
      }
      return;
    }

    wasOpenRef.current = true;
    returnFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  useEffect(() => () => {
    if (wasOpenRef.current) returnFocusRef.current?.focus();
  }, []);

  if (!open) return null;

  const handleKeyDown = (event: ReactKeyboardEvent<HTMLDialogElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      if (!closeDisabled) onClose();
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = Array.from(event.currentTarget.querySelectorAll<HTMLElement>(focusableSelector));
    const first = focusable[0];
    const last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first?.focus();
    }
  };

  return createPortal(
    <div
      className="app-sheet-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !closeDisabled) onClose();
      }}
      role="presentation"
    >
      <dialog
        aria-labelledby={titleId}
        aria-modal="true"
        className="app-sheet"
        onKeyDown={handleKeyDown}
        open
      >
        <div aria-hidden="true" className="app-sheet__handle" />
        <button
          aria-label="Đóng"
          className="app-sheet__close"
          disabled={closeDisabled}
          onClick={onClose}
          ref={closeButtonRef}
          type="button"
        >
          <X aria-hidden="true" />
        </button>
        <header className="app-sheet__header">
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h2 id={titleId}>{title}</h2>
        </header>
        <div className="app-sheet__body">{children}</div>
      </dialog>
    </div>,
    document.body,
  );
}
