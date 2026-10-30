import {
  ApiProblem,
  createTarotGuest,
  currentSessionEpoch,
  getSession,
} from "../../shared/api/client";
import { SESSION_RESTART_REQUIRED_KEY } from "../../shared/session/sessionIdentity";

/** A guest session exists only once the person sends something (self-draw or human reader). */
export async function ensureTarotGuest(): Promise<void> {
  const expectedEpoch = currentSessionEpoch();
  try {
    const session = await getSession();
    if (expectedEpoch && expectedEpoch !== session.session_epoch) {
      sessionStorage.setItem(SESSION_RESTART_REQUIRED_KEY, "1");
      throw new ApiProblem(401, "SESSION_CHANGED", "Phiên trên trình duyệt đã đổi.");
    }
  } catch (error) {
    if (error instanceof ApiProblem && error.code === "SESSION_CHANGED") throw error;
    if (!(error instanceof ApiProblem) || error.status !== 401) throw error;
    const key = sessionStorage.getItem("la-lanh-tarot-guest-key") ?? crypto.randomUUID();
    sessionStorage.setItem("la-lanh-tarot-guest-key", key);
    await createTarotGuest(key);
    sessionStorage.removeItem("la-lanh-tarot-guest-key");
  }
}
