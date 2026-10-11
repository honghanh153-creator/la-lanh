# Google OAuth — iOS, Android, Web setup and acceptance

Date: 2026-10-11. Status: in progress; client registration is not end-to-end login evidence.

## Approved scope

The owner approved creation of three Google OAuth clients in `la-lanh-beta`, in iOS → Android → Web order. Identity scopes only: `openid`, email, profile. No Gmail, Contacts, Calendar, billing activation, store enrollment, or public-audience switch is included. The owner separately approved local Android beta signing/free build tools and accepted the Android SDK agreement shown on the official download page (dated 2026-04-28).

## Platform mappings and receipts

| Platform | App identity | Credential status | Acceptance status |
| --- | --- | --- | --- |
| iOS | Bundle ID `vn.lalanh.app` | Created: `La Lanh Beta iOS`, client ID `555956289550-hsmuonquh192vj5cupi4hbtehlf9q8uk.apps.googleusercontent.com` | Native Google login not implemented/verified |
| Android | Application ID `vn.lalanh.app` | Created: `La Lanh Beta Android`, client ID `555956289550-1hkkbr74d0kt2k4nmtkdf7e9toq2dcq3.apps.googleusercontent.com` | Signed APK and native Google login not verified |
| Web | Origin `https://la-lanh.2-28-136-44.sslip.io` | Created: `La Lanh Beta Web`, client ID `555956289550-i9kaoo214kaf11gs21j6janoup18uetp.apps.googleusercontent.com`; Supabase Google provider saved and enabled | App redirect configuration, deployment and two-account live acceptance pending |

iOS creation was verified by the Google success dialog and the Clients table. App Store ID and Team ID were left empty because they are optional and no verified values are available. Firebase App Check and the AI-agent option were not enabled. Google explicitly reports OAuth access is restricted to configured test users.

Android and Web creation were also verified by success dialogs and the Clients table, in the approved order. Web used the exact origin and Supabase callback below. The original Web creation secret was not read, logged, downloaded, or stored by the agent. The subsequently added secret was accidentally exposed in a tool result by Google's accessible copy-button label; see the incident precaution below. At the owner's later request, external Chrome task tabs were closed; the original creation dialog is no longer available. Use only the built-in browser going forward.

Google Data Access was saved with only `openid`, `userinfo.email`, and `userinfo.profile`. Audience remains External / Testing. After separate approval, `honghanh153@gmail.com` was added and verified as the single test user. No public-audience switch was made.

## Callback and provider configuration

- Google Web authorized JavaScript origin: `https://la-lanh.2-28-136-44.sslip.io`.
- Google Web authorized redirect URI: `https://rlowapjpwsamjftpggen.supabase.co/auth/v1/callback`.
- Required Supabase Site URL: `https://la-lanh.2-28-136-44.sslip.io`.
- Required Supabase app redirect allowlist: `https://la-lanh.2-28-136-44.sslip.io/auth/callback`. These are targets, not saved configuration: the inspected dashboard still has Site URL `http://localhost:3000` and no redirect URLs. Specific approval to save the two exact URLs is pending.
- Supabase accepts the comma-separated client IDs with **Web first**, then mobile IDs, regardless of their creation order. The secret is the **Web** client's secret.
- The owner must directly enter and submit the Web client secret in Supabase. Never put it in chat, screenshots, repository files, frontend environment variables, native binaries, or logs.
- Preserve nonce checks, PKCE, state validation, session ownership, CSRF, and exact redirect allowlists. Do not use wildcard redirects or bypass checks to make a test pass.

## Android beta signing

The inspected project has no release signing configuration, the Mac initially had no Java runtime/Android SDK, and `~/.android/debug.keystore` did not exist. Use an actual persistent local test certificate, not a placeholder SHA-1. Keep the key outside Git with restrictive filesystem permissions. A debug certificate is not a release identity; register the real Play app-signing certificate separately when publishing to Google Play. Do not overwrite an existing keystore.

Download tools only from official Google/Adoptium sources and verify their published SHA-256 checksums before installation. SDK command-line tools inspected: Mac ARM build `15859902`, SHA-256 `835b62a26162b229b441d1f6d4680383815a270809eb33522c0d480fa5002c4e`. Tool installation, successful signing reports, and APK certificate verification must be recorded separately.

Installed and verified on this Mac:

- Android command-line tools under `~/Library/Android/sdk/cmdline-tools/latest`; CLI version `22.0`. `sdkmanager` reports deprecation in favor of `android sdk`; inspect the replacement's help before migrating commands.
- Temurin JDK `21.0.12.1+1-LTS`, official Mac ARM archive SHA-256 `3623232f33a9c3baadf304480b2535f9a3cba8a58d42ecbb438ba267315d9998`, under `~/Library/Java/JavaVirtualMachines/la-lanh-temurin21.jdk`. Verified with `java -version`.
- Persistent local debug keystore `~/.android/debug.keystore`, mode `0600`, alias `androiddebugkey`, standard public debug password. Never use this test-only key/password for production. No existing keystore was overwritten.
- Public certificate SHA-1: `EB:35:6B:DB:FA:91:4C:E4:21:EF:B9:D0:68:0C:8B:D9:43:82:4E:C5` (registered with Google).
- Public certificate SHA-256: `BA:C2:FA:E9:34:24:AD:B1:0F:B7:E7:85:CC:C0:59:17:DA:20:98:23:85:02:EA:02:C7:D6:22:62:B6:45:FB:CD`.

From the repository root, source `infra/mobile/android-beta-env.sh` before building. The home shell profile was not changed. Required packages are `platform-tools`, `platforms;android-36`, and `build-tools;36.0.0`. Their installation currently waits on `android-sdk-license`, dated January 16, 2019; this differs from the approved download-page agreement dated April 28, 2026, so acceptance has not been automated. Other seven SDK licenses were not accepted.

## Native integration gap

The app is Capacitor 8, not Expo. The existing Google UI redirects using `window.location.assign`; it has no native sign-in plugin, registered iOS Google URL callback, Android Credential Manager integration, or secure native-to-backend login bridge. The Capacitor iOS `scheme` setting is an Xcode scheme, not evidence of an OAuth URL scheme.

Client creation alone cannot close this gap. Use platform Google sign-in/identity APIs and a server-validated identity flow, or a reviewed system-browser flow with a single-use, device-bound handoff. A native app and system browser do not automatically share the guest cookie. Preserve guest-to-account ownership checks; never transfer bearer tokens through unprotected deep links or authenticate by email supplied by the client. Do not launch Google's consent page in an embedded WebView.

## Acceptance checklist

- [x] Verify actual iOS bundle ID and Android application ID from source.
- [x] Obtain specific approval for persistent OAuth client creation.
- [x] Create and verify the iOS client.
- [x] Obtain approval for local beta signing/free tools and SDK license acceptance.
- [x] Install and verify Java/Android command-line tools.
- [ ] Accept required package agreement and install Android platform/build packages.
- [x] Generate/reuse a protected persistent beta certificate; record public fingerprints only.
- [ ] Verify Gradle signing report and the built APK use the registered certificate.
- [x] Create and verify Android client using that certificate.
- [x] Create Web client with exact origin/Supabase callback.
- [x] User enters Web secret directly in Supabase; verify redacted provider configuration.
- [ ] Save approved exact Supabase Site URL and app callback; verify callback state survives the real PKCE redirect without widening the allowlist.
- [ ] Replace the test secret exposed in tool output before production activation; use direct user credential entry and verify exchange before retiring old credentials.
- [x] Verify Google audience/test users and minimal identity scopes.
- [ ] Implement/verify native identity bridge and callbacks on iOS/Android.
- [ ] Test login, cancel, logout/relogin, app restart, expired/replayed callback, and wrong-device/wrong-owner rejection.
- [ ] Test two Google accounts on isolated devices/browser contexts; no cross-profile reading/history/session data.
- [ ] Verify guest data survives linking to the intended account, and account deletion/provider cleanup follows policy.
- [ ] Complete release runbook requirements and deploy verified code/configuration before declaring production ready.

No application deployment or paid AI requests have been performed by this OAuth setup so far. Existing staged/uncommitted changes are preserved.

## Resume at the current blockers

1. Supabase dashboard sign-in is now verified in the Codex in-app browser, project `rlowapjpwsamjftpggen`. Chrome remains signed out of Supabase; use the signed-in in-app browser tab, not the stale Chrome sign-in page.
2. The owner reported DONE after directly entering the Web secret and saving Supabase. Verified in the built-in browser: Google Enabled; Client IDs ordered Web, iOS, Android exactly as recorded above; Skip nonce checks disabled; Allow users without an email disabled. No secret was read from Supabase. This verifies saved configuration, not a successful Google token exchange. One additional Web secret was created with explicit approval; the old secret was not disabled/deleted.

3. Supabase URL Configuration still has Site URL `http://localhost:3000` and no redirect URLs. A specific approval request to save the exact production Site URL and `/auth/callback` is pending. Do not save wildcard redirects. The backend appends a login-specific state query: verify real redirect matching and state preservation rather than assuming dashboard save is sufficient.

4. Read-only live checks on 2026-10-11: `/v1/ready` returns `{"status":"ready"}`; `/v1/account` returns HTTP 404. SSH confirms `/opt/la-lanh/current` resolves to `/opt/la-lanh/releases/a7fadf7e4511/source`, the app image is `la-lanh:a7fadf7e4511` and healthy, and both cleanup timers are active. This is the older release, not the consolidated IAM candidate. Do not enable app login or deploy the candidate until backup/restore, migrations through 0036, least-privileged-role and provider-erasure gates in the release runbook have evidence. No credentials were retrieved by these checks.

Secret-screen inspection precaution: Google embeds the plaintext secret in the copy button's accessible label. Do not enumerate button names/ARIA labels or dump full DOM/AX snapshots on a newly generated secret screen. Verify only static headings, terms, and status; screenshots must exclude the value column. An initial control-label inspection exposed the value in tool output; it was not persisted in repository files or repeated in user-facing prose. The owner was informed. Treat it as an exposed test credential and replace it before production activation; never repeat the value in an incident report.

5. Obtain acceptance for the separately displayed January 16, 2019 SDK package license; then install only the three required packages and verify Gradle/APK signing.
6. Complete native integration and live acceptance gates; these are still open. Do not mark this task end-to-end complete or production ready on the strength of client registration alone.

## Official references checked

- [Supabase Google sign-in](https://supabase.com/docs/guides/auth/social-login/auth-google): multi-client ordering, Web secret, PKCE and redirect allowlist.
- [Supabase redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls): production Site URL and exact redirect allowlist.
- [Google native OAuth](https://developers.google.com/identity/protocols/oauth2/native-app): iOS bundle identifiers, optional Team/Store IDs, system-browser/SDK guidance and PKCE.
- [Google OAuth client management](https://support.google.com/cloud/answer/6158849): client registration and Android signing certificate requirements.
- [Capacitor environment setup](https://capacitorjs.com/docs/getting-started/environment-setup): native build tooling requirements.
- [Android official downloads](https://developer.android.com/studio): SDK agreement and Mac ARM tool checksum.
- [Adoptium archive installation](https://adoptium.net/installation/archives): verify archive checksums and user-local JDK setup.

Follow `account-iam-and-retention.md`, `hetzner-supabase-release-runbook.md`, and `chart-synthesis-release-runbook.md` for production/native gates. Pending gates above must not be reported as passed.
