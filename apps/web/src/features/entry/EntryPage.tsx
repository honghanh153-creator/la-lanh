import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { ApiProblem, getBirthProfile, getSession } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";

export function EntryPage() {
  const navigate = useNavigate();

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        await getSession(controller.signal);
        try {
          await getBirthProfile(controller.signal);
          void navigate("/home", { replace: true });
        } catch (error) {
          if (error instanceof ApiProblem && error.status === 404) {
            void navigate("/birth", { replace: true });
          } else throw error;
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          void navigate("/welcome", {
            replace: true,
            state: { offline: !(error instanceof ApiProblem) },
          });
        }
      }
    })();
    return () => controller.abort();
  }, [navigate]);

  return (
    <main className="entry-loading" aria-live="polite">
      <BrandMark />
      <span className="entry-loading__orbit" aria-hidden="true" />
      <p>Đang tìm chiếc Lá của bạn…</p>
    </main>
  );
}
