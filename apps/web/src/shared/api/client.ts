import type { components, paths } from "@la-lanh/contracts";

import { runtimeConfig } from "../config/runtime";
import { readCachedDailyNote } from "../storage/noteCache";
import {
  clearSavedNoteMutationQueue,
  enqueueSavedNoteMutation,
  flushSavedNoteMutations,
  type SavedNoteMutationIntent,
} from "../storage/savedNoteMutationQueue";

export type HealthResponse =
  paths["/v1/health"]["get"]["responses"][200]["content"]["application/json"];
export type GuestSession = components["schemas"]["GuestSessionResponse"];
export type BirthReveal = components["schemas"]["BirthRevealResponse"];
export type ZodiacSign = components["schemas"]["ZodiacSign"];
export type DailyNote = components["schemas"]["DailyNoteResponse"];
export type BackgroundLens = "work" | "relationships" | "communication" | "energy" | "self_care";
export type SignalContext = "auto" | BackgroundLens;
export type ResonanceChoice = "hit" | "miss";
export type ResonanceResponse = {
  choice: ResonanceChoice;
  background_lens: BackgroundLens | null;
  created_at: string;
};
export type ResonanceStatus = {
  consented: boolean;
  feedback_count: number;
  last_choice: ResonanceChoice | null;
};
export type MoodValue = components["schemas"]["MoodValue"];
export type MoodCheckIn = components["schemas"]["MoodResponse"];
export type SavedNote = components["schemas"]["SavedNoteResponse"] & {
  revision_id?: string | null;
  reading_snapshot?: ReadingContent | null;
};
export type ShareArtifact = components["schemas"]["ShareArtifactResponse"] & {
  revision_id?: string | null;
};
export type ShareFormat = components["schemas"]["ShareFormat"];
export type PlaceResult = components["schemas"]["PlaceResultResponse"];
export type BirthTimeMode = components["schemas"]["BirthTimeMode"];
export type ApproxWindow = components["schemas"]["ApproxWindow"];
export type BirthSupplement = components["schemas"]["BirthSupplementResponse"];
export type BirthSupplementState = components["schemas"]["BirthSupplementStateResponse"];
export type PublicShareArtifact = components["schemas"]["PublicShareArtifactResponse"];
export type OnboardingStatus = components["schemas"]["OnboardingStatus"];
export type InsightOverview = components["schemas"]["InsightOverviewResponse"];
export type ReadingContent = components["schemas"]["ReadingContentProjection"];
export type ReadingProjection = components["schemas"]["ReadingProjection"];
export type DailyExperiment = components["schemas"]["ExperimentResponse"];
export type ExperimentOutcome = components["schemas"]["ExperimentOutcome"];
export type ExperimentLens = components["schemas"]["BackgroundLens"];
export type ChooseDailyExperimentInput = components["schemas"]["ExperimentChooseRequest"];
export type ReadingPurpose = components["schemas"]["ReadingPurpose"];
export type Tradition = components["schemas"]["Tradition"];
export type Ayanamsa = components["schemas"]["Ayanamsa"];
export type HouseSystem = components["schemas"]["HouseSystem"];
export type NodeMode = components["schemas"]["NodeMode"];
export type OwnerClaim = components["schemas"]["OwnerClaimResponse"];
export type LaChungInvite = components["schemas"]["InviteResponse"];
export type PublicLaChungInvite = components["schemas"]["PublicInviteResponse"];
export type LaChungSubmitResult = components["schemas"]["SubmitResponseResult"];
export type LaChungOwnerResult = components["schemas"]["OwnerResultResponse"];
export type MatchingIntent = components["schemas"]["MatchingIntent"];
export type MatchingGender = components["schemas"]["MatchingGender"];
export type GenderPreference = components["schemas"]["GenderPreference"];
export type WeeklyIntent = components["schemas"]["WeeklyIntent"];
export type VerificationStatus = components["schemas"]["VerificationStatus"];
export type MatchingProfile = components["schemas"]["MatchingProfileResponse"];
export type MatchingReadiness = components["schemas"]["MatchingReadinessResponse"];
export type RadarInvite = {
  id: string;
  recipient_label: string;
  context: "crush" | "friend" | "partner" | "someone";
  voice: RadarVoice;
  mode: "private_check" | "consented_invite";
  status: "pending" | "completed" | "revoked" | "withdrawn" | "expired";
  created_at: string;
  expires_at: string;
  share_url?: string | null;
};
export type RadarVoice = "straight_warm" | "gentle_specific" | "playful_grounded" | "deep_dive";
export type RadarPrivateCheckInput = {
  recipient_label: string;
  context: RadarInvite["context"];
  voice: RadarVoice;
  birth_date: string;
  birth_time_mode: "exact" | "unknown";
  birth_time_local: string | null;
  place_id: string;
  authorization_attested: boolean;
};
export type PublicRadarInvite = {
  request_id: string;
  recipient_label: string;
  context: string;
  voice: RadarVoice;
  expires_at: string;
  consent_version: string;
  requires_exact_birth_profile: boolean;
  privacy_note: string;
};
export type RadarResult = {
  request_id?: string | null;
  recipient_label?: string | null;
  mode?: RadarInvite["mode"] | null;
  version: string;
  headline: string;
  summary: string;
  pair_signature?: {
    kicker: string;
    headline: string;
    summary: string;
    themes?: Array<{
      key: string;
      label: string;
    }>;
  } | null;
  compatibility_map?: Array<{
    key: "resonance" | "coordination" | "friction";
    label: string;
    value: number;
    meaning: string;
    evidence?: Array<{
      evidence_id: string;
      source: "synastry" | "house_overlay" | "composite_midpoint";
      plain: string;
      technical: Record<string, string | number>;
    }>;
  }>;
  sections?: Array<{
    key: "fit" | "friction" | "perspective" | "check";
    label: string;
    title: string;
    body: string;
    topics?: string[];
    depth?: "focused" | "layered";
    highlights?: Array<{
      key: string;
      label: string;
      title: string;
      body: string;
      evidence_ids: string[];
    }>;
    scene?: {
      label: string;
      title: string;
      body: string;
    } | null;
    perspectives?: Array<{
      key: "you" | "them" | "shared";
      label: string;
      title: string;
      body: string;
    }>;
    observation?: {
      label: string;
      title: string;
      body: string;
    } | null;
    evidence: Array<{
      evidence_id: string;
      source: "synastry" | "house_overlay" | "composite_midpoint";
      plain: string;
      technical: Record<string, string | number>;
    }>;
  }>;
  dimensions: Array<{
    key: string;
    label: string;
    body: string;
    signal: string;
    evidence_ids: string[];
  }>;
  strongest_contacts: Array<{
    body_a: string;
    body_b: string;
    kind: string;
    tone: string;
    orb: number;
  }>;
  metadata?: {
    knowledge_version: string;
    renderer_version: string;
    gate_version: string;
    chart_config_version: string;
    evidence_ids: string[];
    concept_ids: string[];
    voice: RadarVoice;
    voice_label: string;
    time_precision?: "exact" | "unknown";
    precision_note?: string;
  } | null;
  disclaimer: string;
};

export type TarotContext = "general" | "relationships" | "work" | "communication" | "energy" | "self_care";
export type TarotSpread = "one_card" | "three_card" | "five_card";
export type TarotSpreadMap =
  | "one_focus"
  | "three_unblock"
  | "five_clarity"
  | "five_loop"
  | "five_choice"
  | "five_conversation";
export type TarotCard = {
  id: string;
  title_vi: string;
  title_en: string;
  arcana: "major" | "minor";
  suit?: string | null;
  rank?: string | null;
  core: string;
  tension: string;
  resource: string;
  source_concept_ids: string[];
};
export type TarotReadingPosition = {
  key: string;
  label: string;
  card: TarotCard;
  meaning_here: string;
  everyday_scene: string;
  reflection_question: string;
  small_action: string;
};
export type TarotReading = {
  headline: string;
  summary: string;
  question: string;
  question_intent: "clarity" | "boundary" | "next_step" | "communication" | "self_check";
  context: TarotContext;
  spread: TarotSpread;
  spread_map: TarotSpreadMap;
  voice: "straight_warm" | "gentle_specific" | "playful_grounded";
  positions: TarotReadingPosition[];
  closing_prompt: string;
  disclaimer: string;
  provenance: {
    schema_version: string;
    knowledge_version: string;
    renderer_version: string;
    gate_version: string;
    deck_version: string;
    spread_version: string;
    question_rules_version: string;
    methodology_version: string;
    source_ids: string[];
    draw_actor: "self";
    draw_purpose: "first_reading";
  };
};
export type TarotSession = {
  id: string;
  version: number;
  state: "choosing" | "complete";
  context: TarotContext;
  spread: TarotSpread;
  spread_map: TarotSpreadMap;
  voice: TarotReading["voice"];
  origin: "direct" | "daily" | "radar";
  prompt_id?: string | null;
  question: string;
  fan_size: number;
  required_cards: number;
  selected_cards: Array<{
    fan_index: number;
    position_key: string;
    position_label: string;
    card: TarotCard;
  }>;
  reading?: TarotReading | null;
  created_at: string;
  updated_at: string;
  expires_at: string;
};

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return request<HealthResponse>("/health", { signal });
}

export class ApiProblem extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details: Record<string, unknown> = {},
  ) {
    super(message);
  }
}

export function isGuestSessionUnavailable(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const problem = error as { status?: unknown; code?: unknown };
  return problem.status === 401
    && (problem.code === "GUEST_SESSION_MISSING" || problem.code === "GUEST_EXPIRED");
}

export const SESSION_EPOCH_KEY = "la-lanh-session-epoch";
export const OWNER_SESSION_EPOCH_KEY = "la-lanh-owner-session-epoch";
const NATIVE_CSRF_KEY = "la-lanh-native-csrf-v1";
const REQUEST_TIMEOUT_MS = 15_000;
const DELETE_GUEST_TIMEOUT_MS = 75_000;
let activeDailyReading: { scopeKey: string; revisionId: string } | null = null;
let ownerClaimInFlight: { sessionEpoch: string | null; promise: Promise<OwnerClaim> } | null = null;

type RequestOptions = RequestInit & { timeoutMs?: number };

class ApiTimeoutError extends Error {
  readonly name = "TimeoutError";

  constructor(public readonly timeoutMs: number) {
    super(`Request timed out after ${timeoutMs}ms`);
  }
}

function isNativeApp(): boolean {
  if (typeof window === "undefined") return false;
  const capacitor = (window as Window & {
    Capacitor?: { isNativePlatform?: () => boolean; getPlatform?: () => string };
  }).Capacitor;
  return capacitor?.isNativePlatform?.()
    ?? (capacitor?.getPlatform?.() === "ios" || capacitor?.getPlatform?.() === "android");
}

function nativeClientHeader(): Record<string, string> {
  return isNativeApp() ? { "X-La-Lanh-Client": "capacitor-v1" } : {};
}

function readCookie(name: string): string | null {
  const prefix = `${encodeURIComponent(name)}=`;
  const value = document.cookie.split("; ").find((item) => item.startsWith(prefix));
  return value ? decodeURIComponent(value.slice(prefix.length)) : null;
}

export function currentSessionEpoch(): string | null {
  return sessionStorage.getItem(SESSION_EPOCH_KEY);
}

function currentDailyRevisionId(): string | null {
  const cachedProjection = readCachedDailyNote()?.note.reading_projection;
  if (cachedProjection) {
    return activeDailyReading?.scopeKey === cachedProjection.scope_key
      ? activeDailyReading.revisionId
      : cachedProjection.active.revision_id;
  }
  return activeDailyReading?.revisionId ?? null;
}

export function clearActiveDailyReading(): void {
  activeDailyReading = null;
}

function isConnectivityFailure(error: unknown): boolean {
  return error instanceof TypeError
    || error instanceof ApiTimeoutError
    || (typeof navigator !== "undefined" && !navigator.onLine);
}

function csrfHeader(): Record<string, string> {
  const csrfToken = readCookie("la_lanh_csrf")
    ?? (isNativeApp() ? localStorage.getItem(NATIVE_CSRF_KEY) : null);
  return csrfToken ? { "X-CSRF-Token": csrfToken } : {};
}

async function request<T>(path: string, init?: RequestOptions): Promise<T> {
  const { timeoutMs = REQUEST_TIMEOUT_MS, ...fetchInit } = init ?? {};
  const controller = new AbortController();
  let didTimeout = false;
  const abortFromCaller = () => controller.abort(fetchInit.signal?.reason);
  if (fetchInit.signal?.aborted) abortFromCaller();
  else fetchInit.signal?.addEventListener("abort", abortFromCaller, { once: true });
  const timeoutId = window.setTimeout(() => {
    didTimeout = true;
    controller.abort(new ApiTimeoutError(timeoutMs));
  }, timeoutMs);

  try {
    const response = await fetch(`${runtimeConfig.VITE_API_BASE_URL}${path}`, {
      ...fetchInit,
      signal: controller.signal,
      credentials: "include",
      headers: {
        Accept: "application/json",
        ...nativeClientHeader(),
        ...fetchInit.headers,
      },
    });
    if (!response.ok) {
      const problem = (await response.json().catch(() => null)) as {
        code?: string;
        title?: string;
        [key: string]: unknown;
      } | null;
      throw new ApiProblem(
        response.status,
        problem?.code ?? "REQUEST_FAILED",
        problem?.title ?? `Request failed with status ${response.status}`,
        problem ?? {},
      );
    }
    if (response.status === 204 || response.headers.get("content-length") === "0") {
      return undefined as T;
    }
    return await response.json() as T;
  } catch (error) {
    if (didTimeout) throw new ApiTimeoutError(timeoutMs);
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
    fetchInit.signal?.removeEventListener("abort", abortFromCaller);
  }
}

async function applySavedIntent(intent: SavedNoteMutationIntent): Promise<void> {
  if (intent.intent === "save") {
    await request<SavedNote>(`/daily-note/${intent.daily_note_id}/saved`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...csrfHeader() },
      body: JSON.stringify({ revision_id: intent.revision_id }),
    });
    return;
  }
  await request<void>(`/daily-note/${intent.daily_note_id}/saved`, {
    method: "DELETE",
    headers: csrfHeader(),
  });
}

async function acceptSessionEpoch(session: GuestSession): Promise<void> {
  const epoch = "session_epoch" in session && typeof session.session_epoch === "string"
    ? session.session_epoch
    : null;
  if (!epoch) return;
  if (isNativeApp() && typeof session.csrf_token === "string") {
    localStorage.setItem(NATIVE_CSRF_KEY, session.csrf_token);
  }
  sessionStorage.setItem(SESSION_EPOCH_KEY, epoch);
  await flushSavedNoteMutations(epoch, applySavedIntent);
}

export async function getSession(signal?: AbortSignal): Promise<GuestSession> {
  const session = await request<GuestSession>("/session", { signal });
  await acceptSessionEpoch(session);
  return session;
}

export function updateOnboardingStatus(
  status: OnboardingStatus,
): Promise<GuestSession> {
  return request<GuestSession>("/session/onboarding-status", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify({ status }),
  });
}

export async function createGuest(idempotencyKey: string): Promise<GuestSession> {
  const session = await request<GuestSession>("/guest-sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      consent_version: "birth-profile-v1",
      purpose: "birth_profile_basic",
      idempotency_key: idempotencyKey,
    }),
  });
  await acceptSessionEpoch(session);
  return session;
}

export async function createTarotGuest(idempotencyKey: string): Promise<GuestSession> {
  const session = await request<GuestSession>("/guest-sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      consent_version: "tarot-reflection-v1",
      purpose: "tarot_reflection",
      idempotency_key: idempotencyKey,
    }),
  });
  await acceptSessionEpoch(session);
  return session;
}

export function startTarotSession(input: {
  context: TarotContext;
  question: string;
  spread: TarotSpread;
  origin: "direct" | "daily" | "radar";
  prompt_id?: string | null;
  idempotency_key: string;
}): Promise<TarotSession> {
  return request<TarotSession>("/tarot/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...csrfHeader() },
    body: JSON.stringify(input),
  });
}

export function getTarotSession(sessionId: string, signal?: AbortSignal): Promise<TarotSession> {
  return request<TarotSession>(`/tarot/sessions/${encodeURIComponent(sessionId)}`, { signal });
}

export function selectTarotCard(
  sessionId: string,
  fanIndex: number,
  expectedVersion: number,
): Promise<TarotSession> {
  return request<TarotSession>(
    `/tarot/sessions/${encodeURIComponent(sessionId)}/selections`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...csrfHeader() },
      body: JSON.stringify({ fan_index: fanIndex, expected_version: expectedVersion }),
    },
  );
}

export function deleteTarotSession(sessionId: string): Promise<void> {
  return request<void>(`/tarot/sessions/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
    headers: csrfHeader(),
  });
}

export function getBirthProfile(signal?: AbortSignal): Promise<BirthReveal> {
  return request<BirthReveal>("/birth-profile", { signal });
}

export function createBirthProfile(birthDate: string): Promise<BirthReveal> {
  return request<BirthReveal>("/birth-profile", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify({ birth_date: birthDate }),
  });
}

export async function getDailyNote(signal?: AbortSignal): Promise<DailyNote> {
  const note = await request<DailyNote>("/daily-note", { signal });
  activeDailyReading = note.reading_projection
    ? {
        scopeKey: note.reading_projection.scope_key,
        revisionId: note.reading_projection.active.revision_id,
      }
    : null;
  return note;
}

export async function getContextualReading(
  backgroundLens: Exclude<SignalContext, "auto">,
  signal?: AbortSignal,
): Promise<ReadingProjection> {
  const projection = await request<ReadingProjection>("/daily-note/context", {
    method: "POST",
    signal,
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify({ background_lens: backgroundLens }),
  });
  activeDailyReading = {
    scopeKey: projection.scope_key,
    revisionId: projection.active.revision_id,
  };
  return projection;
}

export function checkInMood(dailyNoteId: string, mood: MoodValue): Promise<MoodCheckIn> {
  return request<MoodCheckIn>(`/daily-note/${dailyNoteId}/mood`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify({ mood }),
  });
}

export function getCurrentMood(
  dailyNoteId: string,
  signal?: AbortSignal,
): Promise<MoodCheckIn | null> {
  return request<MoodCheckIn | null>(`/daily-note/${dailyNoteId}/mood`, { signal });
}

export function getResonanceStatus(signal?: AbortSignal): Promise<ResonanceStatus> {
  return request<ResonanceStatus>("/daily-note/resonance", { signal });
}

export function recordResonance(
  dailyNoteId: string,
  input: {
    choice: ResonanceChoice;
    revision_id: string | null;
    background_lens: BackgroundLens | null;
  },
): Promise<ResonanceResponse> {
  return request<ResonanceResponse>(`/daily-note/${encodeURIComponent(dailyNoteId)}/resonance`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify({ ...input, consent_version: "reading-resonance-v1" }),
  });
}

export function clearResonance(revokeConsent: boolean): Promise<void> {
  return request<void>("/daily-note/resonance", {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify({ revoke_consent: revokeConsent }),
  });
}

export function getCurrentDailyExperiment(signal?: AbortSignal): Promise<DailyExperiment | null> {
  return request<DailyExperiment | null>("/daily-note/experiment", { signal });
}

export function chooseDailyExperiment(
  dailyNoteId: string,
  input: ChooseDailyExperimentInput,
): Promise<DailyExperiment> {
  return request<DailyExperiment>(
    `/daily-note/${encodeURIComponent(dailyNoteId)}/experiment`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...csrfHeader(),
      },
      body: JSON.stringify(input),
    },
  );
}

export function undoDailyExperiment(input: {
  experiment_id: string;
  expected_version: number;
}): Promise<void> {
  return request<void>("/daily-note/experiment", {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify(input),
  });
}

export function reflectDailyExperiment(input: {
  experiment_id: string;
  expected_version: number;
  outcome: ExperimentOutcome;
}): Promise<DailyExperiment> {
  return request<DailyExperiment>("/daily-note/experiment/outcome", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify(input),
  });
}

export async function listSavedNotes(signal?: AbortSignal): Promise<SavedNote[]> {
  const epoch = currentSessionEpoch();
  if (epoch) await flushSavedNoteMutations(epoch, applySavedIntent);
  return request<SavedNote[]>("/saved-notes", { signal });
}

export async function saveDailyNote(
  dailyNoteId: string,
  revisionId: string | null = currentDailyRevisionId(),
): Promise<SavedNote> {
  try {
    return await request<SavedNote>(`/daily-note/${dailyNoteId}/saved`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...csrfHeader() },
      body: JSON.stringify({ revision_id: revisionId }),
    });
  } catch (error) {
    const epoch = currentSessionEpoch();
    if (epoch && isConnectivityFailure(error)) {
      enqueueSavedNoteMutation({
        sessionEpoch: epoch,
        dailyNoteId,
        revisionId,
        intent: "save",
      });
    }
    throw error;
  }
}

export async function unsaveDailyNote(
  dailyNoteId: string,
  revisionId: string | null = currentDailyRevisionId(),
): Promise<void> {
  try {
    await request<void>(`/daily-note/${dailyNoteId}/saved`, {
      method: "DELETE",
      headers: csrfHeader(),
    });
  } catch (error) {
    const epoch = currentSessionEpoch();
    if (!epoch || !isConnectivityFailure(error)) throw error;
    enqueueSavedNoteMutation({
      sessionEpoch: epoch,
      dailyNoteId,
      revisionId,
      intent: "unsave",
    });
  }
}

export function createShareArtifact(
  dailyNoteId: string,
  format: ShareFormat = "story_9_16",
  revisionId: string | null = currentDailyRevisionId(),
): Promise<ShareArtifact> {
  return request<ShareArtifact>(`/daily-note/${dailyNoteId}/share-artifacts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify({ format, revision_id: revisionId }),
  });
}

export function revokeShareArtifact(artifactId: string): Promise<void> {
  return request<void>(`/share-artifacts/${encodeURIComponent(artifactId)}`, {
    method: "DELETE",
    headers: csrfHeader(),
  });
}

export function getShareArtifact(
  shareToken: string,
  signal?: AbortSignal,
): Promise<PublicShareArtifact> {
  return request<PublicShareArtifact>(`/share-artifacts/${encodeURIComponent(shareToken)}`, { signal });
}

export function searchBirthPlaces(query: string, signal?: AbortSignal): Promise<PlaceResult[]> {
  return request<PlaceResult[]>("/birth-places/search", {
    method: "POST",
    signal,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
}

export function addBirthSupplement(input: {
  birth_time_mode: BirthTimeMode;
  birth_time_local?: string | null;
  approx_window?: ApproxWindow | null;
  place_id?: string | null;
}): Promise<BirthSupplement> {
  return request<BirthSupplement>("/birth-profile/supplement", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify({ ...input, consent_version: "birth-profile-deep-v1" }),
  });
}

export function getBirthSupplement(signal?: AbortSignal): Promise<BirthSupplementState> {
  return request<BirthSupplementState>("/birth-profile/supplement", { signal });
}

export function removeBirthSupplement(input: {
  remove_time?: boolean;
  remove_place?: boolean;
}): Promise<BirthSupplementState> {
  return request<BirthSupplementState>("/birth-profile/supplement", {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify(input),
  });
}

export async function deleteGuest(): Promise<void> {
  await request<void>("/guest-session", {
    method: "DELETE",
    headers: csrfHeader(),
    timeoutMs: DELETE_GUEST_TIMEOUT_MS,
  });
  sessionStorage.removeItem(SESSION_EPOCH_KEY);
  sessionStorage.removeItem(OWNER_SESSION_EPOCH_KEY);
  localStorage.removeItem(NATIVE_CSRF_KEY);
  clearSavedNoteMutationQueue();
  clearActiveDailyReading();
}

export function getInsightOverview(
  input: {
    tradition: Tradition;
    ayanamsa?: Ayanamsa;
    nodeMode?: NodeMode;
    houseSystem?: HouseSystem;
  },
  signal?: AbortSignal,
): Promise<InsightOverview> {
  return request<InsightOverview>(`/insights/overview?${readingConfigQuery(input)}`, { signal });
}

export type CurrentSky = {
  observed_at: string;
  tradition: Tradition;
  config_hash: string;
  bodies: Array<{
    body: string;
    sign: string;
    degree_in_sign: number;
    retrograde: boolean;
  }>;
  note: string;
};

export function getCurrentSky(
  tradition: Tradition,
  signal?: AbortSignal,
): Promise<CurrentSky> {
  return request<CurrentSky>(`/insights/current-sky?tradition=${tradition}`, { signal });
}

export type ReadingConfig = {
  tradition: Tradition;
  ayanamsa?: Ayanamsa;
  nodeMode?: NodeMode;
  houseSystem?: HouseSystem;
};

function readingConfigQuery(input: ReadingConfig): string {
  const query = new URLSearchParams({ tradition: input.tradition });
  if (input.ayanamsa) query.set("ayanamsa", input.ayanamsa);
  if (input.nodeMode) query.set("node_mode", input.nodeMode);
  if (input.houseSystem) query.set("house_system", input.houseSystem);
  return query.toString();
}

export function getPrivateReading(
  purpose: Exclude<ReadingPurpose, "daily_note">,
  input: ReadingConfig,
  signal?: AbortSignal,
): Promise<ReadingProjection> {
  return request<ReadingProjection>(
    `/insights/readings/${purpose}?${readingConfigQuery(input)}`,
    { signal },
  );
}

export async function activateReadingProjection(
  scopeKey: string,
  expectedRevisionId: string,
): Promise<ReadingProjection> {
  const projection = await request<ReadingProjection>(
    `/reading-projections/${encodeURIComponent(scopeKey)}/activate`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...csrfHeader(),
      },
      body: JSON.stringify({ expected_revision_id: expectedRevisionId }),
    },
  );
  activeDailyReading = {
    scopeKey: projection.scope_key,
    revisionId: projection.active.revision_id,
  };
  return projection;
}

export function acknowledgeAuraTransition(
  scopeKey: string,
  transitionId: string,
): Promise<ReadingProjection> {
  return request<ReadingProjection>(
    `/reading-projections/${encodeURIComponent(scopeKey)}/aura-transition/acknowledge`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...csrfHeader(),
      },
      body: JSON.stringify({ transition_id: transitionId }),
    },
  );
}

export function ownerClaimNeedsRefresh(): boolean {
  const sessionEpoch = currentSessionEpoch();
  return sessionEpoch !== null && sessionStorage.getItem(OWNER_SESSION_EPOCH_KEY) !== sessionEpoch;
}

export async function claimOwner(): Promise<OwnerClaim> {
  const sessionEpoch = currentSessionEpoch();
  if (ownerClaimInFlight?.sessionEpoch === sessionEpoch) {
    return ownerClaimInFlight.promise;
  }
  const promise = request<OwnerClaim>("/identity/claim", {
    method: "POST",
    headers: csrfHeader(),
  }).then((owner) => {
    if (sessionEpoch && currentSessionEpoch() === sessionEpoch) {
      sessionStorage.setItem(OWNER_SESSION_EPOCH_KEY, sessionEpoch);
    }
    return owner;
  }).finally(() => {
    if (ownerClaimInFlight?.promise === promise) ownerClaimInFlight = null;
  });
  ownerClaimInFlight = { sessionEpoch, promise };
  return promise;
}

export function getMatchingReadiness(signal?: AbortSignal): Promise<MatchingReadiness> {
  return request<MatchingReadiness>("/matching/readiness", { signal });
}

export function saveMatchingProfile(input: {
  display_name: string;
  gender_identity: MatchingGender;
  intent: MatchingIntent;
  gender_preference: GenderPreference;
  min_age: number;
  max_age: number;
  region_code: string;
  weekly_intent: WeeklyIntent;
}): Promise<MatchingProfile> {
  return request<MatchingProfile>("/matching/profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...csrfHeader() },
    body: JSON.stringify(input),
  });
}

export function grantMatchingConsent(): Promise<void> {
  return request<void>("/matching/consent", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...csrfHeader() },
    body: JSON.stringify({ version: "matching-v1" }),
  });
}

export function withdrawMatchingConsent(): Promise<void> {
  return request<void>("/matching/consent", {
    method: "DELETE",
    headers: csrfHeader(),
  });
}

export function setMatchingPoolMembership(active: boolean): Promise<MatchingProfile> {
  return request<MatchingProfile>("/matching/pool-membership", {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...csrfHeader() },
    body: JSON.stringify({ active }),
  });
}

export function createRadarInvite(input: {
  recipient_label: string;
  context: RadarInvite["context"];
  voice: RadarVoice;
}): Promise<RadarInvite> {
  return request<RadarInvite>("/radar/requests", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...csrfHeader() },
    body: JSON.stringify(input),
  });
}

export function createPrivateRadarCheck(input: RadarPrivateCheckInput): Promise<RadarResult> {
  return request<RadarResult>("/radar/private-checks", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...csrfHeader() },
    body: JSON.stringify({ ...input, consent_version: "radar-authorized-input-v1" }),
  });
}

export function listRadarInvites(signal?: AbortSignal): Promise<RadarInvite[]> {
  return request<RadarInvite[]>("/radar/requests", { signal });
}

export function getRadarShareLink(requestId: string): Promise<RadarInvite> {
  return request<RadarInvite>(`/radar/requests/${encodeURIComponent(requestId)}/share`, {
    method: "POST",
    headers: csrfHeader(),
  });
}

export function revokeRadarInvite(requestId: string): Promise<void> {
  return request<void>(`/radar/requests/${encodeURIComponent(requestId)}/revoke`, {
    method: "POST",
    headers: csrfHeader(),
  });
}

export function getPublicRadarInvite(
  token: string,
  signal?: AbortSignal,
): Promise<PublicRadarInvite> {
  return request<PublicRadarInvite>(`/public/radar/${encodeURIComponent(token)}`, { signal });
}

export function getCurrentRadarInvite(signal?: AbortSignal): Promise<PublicRadarInvite> {
  return request<PublicRadarInvite>("/public/radar/current", { signal });
}

export function acceptRadarInvite(requestId: string): Promise<RadarResult> {
  return request<RadarResult>("/public/radar/current/accept", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...csrfHeader() },
    body: JSON.stringify({ request_id: requestId, consent_version: "radar-pair-v1" }),
  });
}

export function declineRadarInvite(requestId: string): Promise<void> {
  return request<void>("/public/radar/current/decline", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...csrfHeader() },
    body: JSON.stringify({ request_id: requestId }),
  });
}

export function getRadarResult(requestId: string, signal?: AbortSignal): Promise<RadarResult> {
  return request<RadarResult>(`/radar/results/${encodeURIComponent(requestId)}`, { signal });
}

export function getRadarReceipt(signal?: AbortSignal): Promise<RadarResult> {
  return request<RadarResult>("/public/radar/receipt", { signal });
}

export function deleteRadarResult(requestId: string): Promise<void> {
  return request<void>(`/radar/results/${encodeURIComponent(requestId)}`, {
    method: "DELETE",
    headers: csrfHeader(),
  });
}

export function withdrawRadarResult(requestId: string): Promise<void> {
  return request<void>("/public/radar/receipt/withdraw", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...csrfHeader() },
    body: JSON.stringify({ request_id: requestId }),
  });
}

export function createLaChungInvite(input: {
  recipient_label: string;
  context: "bff" | "crush" | "couple" | "friend" | "workmate";
  idempotency_key: string;
}): Promise<LaChungInvite> {
  return request<LaChungInvite>("/la-chung/requests", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify(input),
  });
}

export function listLaChungInvites(signal?: AbortSignal): Promise<LaChungInvite[]> {
  return request<LaChungInvite[]>("/la-chung/requests", { signal });
}

export function resendLaChungInvite(requestId: string): Promise<LaChungInvite> {
  return request<LaChungInvite>(`/la-chung/requests/${encodeURIComponent(requestId)}/resend`, {
    method: "POST",
    headers: csrfHeader(),
  });
}

export function revokeLaChungInvite(requestId: string): Promise<void> {
  return request<void>(`/la-chung/requests/${encodeURIComponent(requestId)}/revoke`, {
    method: "POST",
    headers: csrfHeader(),
  });
}

export function replaceLaChungInvite(requestId: string): Promise<LaChungInvite> {
  return request<LaChungInvite>(`/la-chung/requests/${encodeURIComponent(requestId)}/replacement`, {
    method: "POST",
    headers: csrfHeader(),
  });
}

export function getPublicLaChungInvite(
  token: string,
  signal?: AbortSignal,
): Promise<PublicLaChungInvite> {
  return request<PublicLaChungInvite>(`/public/la-chung/${encodeURIComponent(token)}`, { signal });
}

export function submitLaChungResponse(
  token: string,
  input: {
    statement_ids: string[];
    identity_mode: "anonymous" | "alias";
    display_alias?: string | null;
    idempotency_key: string;
  },
): Promise<LaChungSubmitResult> {
  return request<LaChungSubmitResult>(`/public/la-chung/${encodeURIComponent(token)}/responses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function withdrawLaChungResponse(): Promise<void> {
  return request<void>("/public/la-chung/receipt/withdraw", { method: "POST" });
}

export function reportLaChungInvite(
  token: string,
  reason: "not_for_me" | "unsafe" | "spam" | "other",
): Promise<void> {
  return request<void>(`/public/la-chung/${encodeURIComponent(token)}/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
}

export function getLaChungResult(
  requestId: string,
  signal?: AbortSignal,
): Promise<LaChungOwnerResult> {
  return request<LaChungOwnerResult>(
    `/la-chung/results/${encodeURIComponent(requestId)}`,
    { signal },
  );
}

export function hideLaChungResult(requestId: string): Promise<void> {
  return request<void>(`/la-chung/results/${encodeURIComponent(requestId)}/hide`, {
    method: "POST",
    headers: csrfHeader(),
  });
}

export function deleteLaChungResult(requestId: string): Promise<void> {
  return request<void>(`/la-chung/results/${encodeURIComponent(requestId)}`, {
    method: "DELETE",
    headers: csrfHeader(),
  });
}
