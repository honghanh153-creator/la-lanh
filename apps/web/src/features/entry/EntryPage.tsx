import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { ApiProblem, getBirthProfile, getSession } from "../../shared/api/client";
import { clearPersonalDataOnDevice } from "../../shared/storage/clearPersonalData";
import { SignalStationFrame } from "../../shared/ui/SignalStationFrame";

export function EntryPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        const session = await getSession(controller.signal);
        try {
          await getBirthProfile(controller.signal);
          void navigate(session.onboarding_status === "completed" ? "/home" : "/reveal", { replace: true });
        } catch (error) {
          if (error instanceof ApiProblem && error.status === 404) {
            void navigate("/birth", { replace: true });
          } else throw error;
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          if (error instanceof ApiProblem && error.code === "GUEST_EXPIRED") {
            await clearPersonalDataOnDevice();
            queryClient.clear();
          }
          void navigate("/welcome", {
            replace: true,
            state: {
              offline: !(error instanceof ApiProblem),
              expired: error instanceof ApiProblem && error.code === "GUEST_EXPIRED",
            },
          });
        }
      }
    })();
    return () => controller.abort();
  }, [navigate, queryClient]);

  return (
    <SignalStationFrame act={0} className="signal-station--loading" loading titleId="entry-loading-title">
      <span className="signal-station__pulse" aria-hidden="true" />
      <h1 id="entry-loading-title">Đang tìm tín hiệu của bạn…</h1>
      <p className="signal-station__lead" aria-live="polite">Kiểm tra phiên khách để đưa bạn về đúng trạm.</p>
    </SignalStationFrame>
  );
}
