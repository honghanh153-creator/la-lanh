import { PIXEL_LA_ON_USER_SCREENS } from "./flag";

// Every source file of the web app, read as text, to find who imports the pixel module.
const sources = import.meta.glob<string>("../../../../**/*.{ts,tsx}", { query: "?raw", import: "default", eager: true });

describe("Lá pixel stays behind its flag (#714 AC4, #715 AC3)", () => {
  it("the flag is off", () => {
    expect(PIXEL_LA_ON_USER_SCREENS).toBe(false);
  });

  it("only the internal lab page uses Lá pixel", () => {
    const users = Object.entries(sources)
      .filter(([path]) => !path.includes("/shared/ui/companion/pixel/"))
      .filter(([, source]) => /companion\/pixel\//.test(source))
      .map(([path]) => path.replace(/^(\.\.\/)+/, ""));
    expect(users.length).toBeGreaterThan(0);
    expect(users.every((path) => path.startsWith("features/companion-lab/"))).toBe(true);
  });
});
