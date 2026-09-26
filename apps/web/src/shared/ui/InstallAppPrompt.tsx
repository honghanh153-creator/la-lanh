import { DownloadSimple } from "@phosphor-icons/react";
import { useEffect, useState } from "react";

type BeforeInstallPromptChoice = {
  outcome: "accepted" | "dismissed";
  platform: string;
};

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<BeforeInstallPromptChoice>;
}

function isStandalone(): boolean {
  const iosNavigator = navigator as Navigator & { standalone?: boolean };
  return window.matchMedia?.("(display-mode: standalone)").matches === true
    || iosNavigator.standalone === true;
}

export function InstallAppPrompt() {
  const [installEvent, setInstallEvent] = useState<BeforeInstallPromptEvent | null>(null);
  const [hidden, setHidden] = useState(() => localStorage.getItem("la-lanh-install-dismissed") === "true");

  useEffect(() => {
    if (isStandalone()) return undefined;
    const handler = (event: Event) => {
      event.preventDefault();
      setInstallEvent(event as BeforeInstallPromptEvent);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  if (hidden || !installEvent) return null;

  const install = async () => {
    await installEvent.prompt();
    const choice = await installEvent.userChoice;
    if (choice.outcome === "accepted") setHidden(true);
    setInstallEvent(null);
  };

  const dismiss = () => {
    localStorage.setItem("la-lanh-install-dismissed", "true");
    setHidden(true);
  };

  return (
    <aside className="install-prompt" aria-label="Cài Lá Lành như app">
      <div>
        <strong>Muốn giữ Lá Lành như app?</strong>
        <p>Cài vào màn hình chính để mở nhanh note hôm nay.</p>
      </div>
      <button onClick={() => void install()} type="button"><DownloadSimple size={16} /> Cài</button>
      <button aria-label="Ẩn gợi ý cài app" onClick={dismiss} type="button">×</button>
    </aside>
  );
}
