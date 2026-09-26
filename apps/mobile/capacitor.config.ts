import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "vn.lalanh.app",
  appName: "Lá Lành",
  webDir: "../web/dist",
  bundledWebRuntime: false,
  loggingBehavior: "none",
  server: {
    androidScheme: "https",
    cleartext: false,
    allowNavigation: [],
  },
  ios: {
    scheme: "la-lanh",
    contentInset: "automatic",
    preferredContentMode: "mobile",
    allowsLinkPreview: false,
    webContentsDebuggingEnabled: false,
  },
  android: {
    allowMixedContent: false,
    webContentsDebuggingEnabled: false,
    useLegacyBridge: false,
  },
  plugins: {
    CapacitorCookies: {
      enabled: true,
    },
    CapacitorHttp: {
      enabled: true,
    },
  },
};

export default config;
