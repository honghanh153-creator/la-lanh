import { createContext, useContext, useState } from "react";

type OnboardingMotion = {
  paused: boolean;
  toggle: () => void;
};

export const OnboardingMotionContext = createContext<OnboardingMotion | null>(null);

export function useOnboardingMotion(): OnboardingMotion {
  const shared = useContext(OnboardingMotionContext);
  const [paused, setPaused] = useState(false);
  return shared ?? { paused, toggle: () => setPaused((value) => !value) };
}
