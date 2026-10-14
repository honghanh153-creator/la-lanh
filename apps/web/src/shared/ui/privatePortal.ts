import { createContext, useContext } from "react";

/**
 * Where sheets and dialogs portal to. SessionBoundary provides a node *inside* its private
 * region, so a dialog is hidden together with the route whenever the session is suspended,
 * re-verified or changes owner. Outside the boundary (tests, public pages) it is document.body.
 */
export const PrivatePortalContext = createContext<HTMLElement | null>(null);

export function usePrivatePortalTarget(): HTMLElement {
  return useContext(PrivatePortalContext) ?? document.body;
}
