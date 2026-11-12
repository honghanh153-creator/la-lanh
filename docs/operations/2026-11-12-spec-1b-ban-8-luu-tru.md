# Spec 1b — cổng nghiệm thu PR không sửa được, và cách ly mã agent khỏi dữ liệu của owner

Mức: L, vì đổi ranh giới quyền. Trạng thái: **bản 8**. Codex đã phản biện 7 vòng; P1 cuối (vòng 7) đã sửa ở bản này. Theo quy tắc vòng ≥ 3, Claude chốt thiết kế; cổng thật là phép thử §6, và PR dựng sẽ được Codex review như mọi PR. Chưa dựng gì.
Nguồn: hai P1 trong phản biện lần 3 của Codex về báo cáo DevCon. Bản 1 (5 P1), bản 2 (3 P1) và bản 3 (2 P1), bản 4 (2 P1), bản 5 (1 P1), bản 6 (1 P1), bản 7 (1 P1) bị Codex không duyệt, xem §9.
Hai đợt A/B chỉ bắt đầu khi mọi phép thử ở §6 đạt.

## 1. Hiện trạng (đã kiểm ngày 12.11.2026)

| Sự kiện | Bằng chứng |
|---|---|
| `pr-check.yml` chạy bằng `pull_request`, đọc workflow từ merge ref. PR sửa được workflow nên sửa được kết quả. | `.github/workflows/pr-check.yml` |
| `collab/integration` chỉ có luật chặn force-push và xoá nhánh (thêm 12.11). | ruleset 27085048 |
| `mergeGate` dựa vào comment "Author check" và verdict. Không đọc CI, không kiểm file bảo vệ. | `scripts/collab-merge.mjs:7` |
| launchd chạy `collab-cron.sh`. Script này tải integration rồi chạy `collab-tick`, trong đó có `pnpm install`/`make`/`pnpm check` của PR, bằng tài khoản macOS của owner, ngoài sandbox. | `scripts/collab-cron.sh:18`, `scripts/collab-check.mjs` |
| Agent và owner dùng chung token `gh` có quyền `repo` + `workflow`, tương đương admin. | `gh auth status` |
| Thư mục home của owner có quyền `750`, nhóm `staff`. `~/.codex` và `~/.config` có quyền `755`. Mọi tài khoản macOS khác trên máy đều đọc được. | `ls -ld` |
| CI đã chạy đúng `pnpm check` cho mức `full`. 60 lượt gần nhất: 37 thành công, 5 thất bại, 18 bị huỷ do có commit mới hơn. | `gh run list -w pr-check` |
| Repo có `Dockerfile` và `infra/compose`. | cây thư mục |

**Gốc vấn đề:** mọi agent chạy bằng tài khoản macOS của owner và token của owner. Vì vậy mọi cổng chỉ là quy ước, và mọi mã agent chạy đều đọc được dữ liệu của owner.

## 2. Ba vùng quyền

| Vùng | Ở đâu | Có gì | Không có gì |
|---|---|---|---|
| **Q — quản trị** | **Điện thoại của owner** (trình duyệt hoặc app GitHub) | Phiên GitHub đầy đủ: ruleset, biến repo, thu hồi token, sửa workflow | Không agent nào chạy trên điện thoại |
| **O — owner trên Mac** | Tài khoản macOS hiện tại | Dữ liệu riêng của owner, phiên Claude tương tác **bắt buộc có sandbox chỉ thấy repo** (§4), token hẹp T | **Không có phiên GitHub web nào**: đăng xuất github.com khỏi mọi trình duyệt trên Mac |
| **R — người duyệt** | **Tài khoản macOS `lalanh-review`** (standard) | Codex read-only đọc PR qua API công khai, ghi verdict dạng JSON vào thư mục trao đổi `/Users/Shared/lalanh-verdicts`. Chỉ R ghi được vào thư mục này, và chỉ S đọc được | **Không có token, không có khoá App**, không đọc được vùng O, A, S |
| **S — người ký** | **Tài khoản macOS `lalanh-sign`** (standard) | **Khoá riêng của GitHub App `la-lanh-verdict`** (file `600`). Một script nhỏ, ghim cố định: đọc JSON verdict, tự tính diện owner duyệt từ dữ liệu GitHub, rồi đăng check-run | **Không chạy Codex hay bất kỳ mô hình nào. Không chạy mã của PR.** Không đọc được vùng O, A, R |
| **A — agent tự động** | **Tài khoản macOS mới `lalanh-agent`** (standard, không phải admin) | launchd tick, Codex review, heal, ops clone, token hẹp T | Không đọc được home của owner: home owner chuyển sang `700`. Không có trình duyệt đăng nhập |

**Token T** là fine-grained PAT chỉ dùng cho repo `la-lanh`, quyền như sau:

| Quyền | Mức |
|---|---|
| Contents | Read and write |
| Pull requests | Read and write |
| Issues | Read and write |
| Actions, Commit statuses, Metadata | Read |
| **Workflows, Administration, Variables, Secrets** | **Không cấp** |

Owner thu hồi token cũ qua điện thoại: Settings → Applications → huỷ quyền GitHub CLI, và xoá các PAT cũ.

**GitHub App `la-lanh-verdict`**: owner tạo một lần, chỉ cài vào repo `la-lanh`. Quyền:
- Checks: read and write;
- Contents: read and write;
- Pull requests: read and write;
- Variables: read.

App là **danh tính duy nhất được merge vào `collab/**`** (xem A4c). App không nằm trong danh sách được miễn luật của `main`/`release/**`.

**Hệ quả.** Mã vận hành trong `collab/integration` có thể bị một PR sửa. Nhưng khi chạy, nó chỉ có quyền của T trong vùng A: không sửa được ruleset, biến hay workflow, không đọc được dữ liệu owner. Vì vậy mã vận hành **không cần** owner duyệt từng thay đổi. Phép thử P9–P11 chứng minh điều này.

## 3. Thiết kế A — cổng nghiệm thu

### A1. Ruleset `collab/**`

Bổ sung vào ruleset hiện có:
- **Require a pull request before merging**, 0 lượt duyệt.
- **Require status checks**:
  - `check` và **`acceptance-v<N>`**, nguồn bắt buộc là app **GitHub Actions**;
  - **`codex-verdict`**, nguồn bắt buộc là app **`la-lanh-verdict`**.
- Token T không tạo được check của app khác, nên **verdict của Codex và luật `needs-owner` được GitHub cưỡng chế, không còn chỉ do script kiểm**. Merge bằng API mà thiếu verdict cũng bị chặn. `N` là phiên bản chính sách nghiệm thu, lưu ở biến `ACCEPTANCE_VERSION` (chỉ Q sửa). Tên job tổng hợp là `acceptance-v${{ vars.ACCEPTANCE_VERSION }}`.
- **Đổi chính sách theo đúng thứ tự, khoá cổng trước:**
  1. Q đổi tên check bắt buộc trong ruleset sang `acceptance-v<N+1>`. Chưa run nào mang tên này, nên **mọi merge bị chặn** ngay từ bước này.
  2. Q đổi `ACCEPTANCE_SHA` và/hoặc `ACCEPTANCE_ACCEPTED`.
  3. Q đặt `ACCEPTANCE_VERSION = N+1`. Chỉ sau bước này mới có run mang tên mới.
- **Mỗi run dùng một bản chính sách duy nhất.** Job `run` ghi vào output ba giá trị nó đã dùng: `VERSION`, `SHA`, `ACCEPTED`. Job tổng hợp so ba giá trị đó với giá trị biến lúc nó chạy; lệch một giá trị là trượt. Một run bắt đầu giữa chừng (sau bước 2, trước bước 3, hay cắt ngang bước 3) sẽ mang tên cũ, hoặc trượt vì lệch. P16 kiểm điều này.
- **Require branches to be up to date** (strict).

**Khoá `main` và nhánh phát hành.** Thêm ruleset cho `~DEFAULT_BRANCH` và `release/**`:
- **Require a pull request**;
- **Require status check `owner-release`**, nguồn là app `la-lanh-verdict`. S chỉ đăng `success` khi head SHA nằm trong biến `OWNER_RELEASE_SHAS`, biến chỉ Q sửa được;
- giữ luật chặn force-push và xoá nhánh hiện có.

Như vậy T không đẩy thẳng và không merge được vào `main`. P23 kiểm điều này.
- Không ai được miễn luật.

Claude làm bước này **trước khi** đổi token. Sau đó chỉ vùng Q sửa được ruleset.

Vì T không có quyền Workflows, agent không thêm được workflow mới, nên không tạo được check trùng tên. Phép thử P5 kiểm điều này.

### A2. Workflow `acceptance.yml`, gồm 3 job

1. **`build`**: checkout PR, build image app từ `Dockerfile`, xuất image thành file. Ghi digest image vào output của job. Tải lên artifact tên `app-image`. Không chạy test.
2. **`run`**: chạy trên runner mới.
   - **Không checkout cả repo.** Lấy riêng cây `tests/acceptance` của head SHA bằng `git archive` (từ một bản fetch không có working tree), giải nén vào **thư mục sạch `$RUNNER_TEMP/acc`, nằm ngoài mọi checkout**. Trong và trên thư mục đó không có `.npmrc`, `pnpm-workspace.yaml`, `.pnpmfile.cjs` hay `package.json` nào của PR.
   - **Từ chối** nếu bộ test có symlink, có file ngoài danh sách cho phép (`*.ts`, `*.json`, `pnpm-lock.yaml`), có `.npmrc`/`.pnpmfile.cjs`, hoặc lockfile có phụ thuộc `link:`/`file:`/`git:`/workspace.
   - Tính hash tổng (SHA-256 của danh sách hash từng file, đã sắp xếp) **trên chính thư mục đã giải nén**, so với biến `ACCEPTANCE_SHA` (chỉ Q sửa).
   - Bộ chạy test là **manifest nằm trong chính bộ test đã ghim hash**: `tests/acceptance/package.json` (chỉ `@playwright/test` phiên bản cố định, không có `scripts`), `pnpm-lock.yaml`, `playwright.config.ts`. Trình duyệt tải bằng `playwright install chromium` của đúng phiên bản trong lockfile, từ CDN chính thức của Playwright, có kiểm checksum sẵn trong Playwright.
   - Cài bằng pnpm phiên bản ghim (corepack với hash), `--frozen-lockfile --ignore-scripts --ignore-workspace --config.registry=https://registry.npmjs.org/`, với `HOME` và `XDG_CONFIG_HOME` trỏ vào thư mục trống, `NPM_CONFIG_USERCONFIG=/dev/null`. Lockfile có integrity hash cho mọi gói.
   - Tải artifact **trong cùng run** (artifact gắn với run, PR khác không ghi đè được), kiểm digest khớp output của `build`.
   - Chạy app bằng `docker run --read-only --cap-drop=ALL --security-opt no-new-privileges`, **không mount thư mục nào**, chỉ mở cổng HTTP. App không chạm được file hay tiến trình của runner test.
   - Test Playwright hộp đen chỉ đi qua HTTP. Kết quả từng mã việc (`tests/acceptance/<issue>/`) ghi vào job summary, kèm hash tổng và SHA đã chạy.
3. **`acceptance`** (đây là check bắt buộc): `if: always()`. Chỉ đạt khi:
   - `build` và `run` đều đạt (`success`). Skip, neutral, cancel hay thiếu đều bị coi là trượt.
   - Hash tổng khớp `ACCEPTANCE_SHA`.
   - Mọi mã việc trong biến **`ACCEPTANCE_ACCEPTED`** (các việc owner đã nghiệm thu) đều **có thư mục test, có ít nhất 1 test thực sự chạy (không skip) và đạt**. Mã việc không có test, không tìm thấy test hay mọi test bị skip đều tính là trượt. Mục đích là chặn hồi quy.

Quyền: `contents: read`. Không dùng secret, không `pull_request_target`, action ghim theo SHA.

### A3. Nghiệm thu việc đang làm, không để "nghiệm thu rỗng"

- Việc N của đợt B đang làm thì **không** chặn merge bằng test của N. Nếu chặn, mọi PR khác đang mở sẽ trượt theo.
- Khi nghiệm thu, owner hoặc phiên Codex kiểm mù **chỉ tin job summary** của workflow `acceptance`: đúng SHA preview, đúng hash tổng, mã việc N đạt. Workflow này agent không sửa được.
- Thiếu test cho N, hoặc N trượt, thì việc **không đạt nghiệm thu** và tính là lỗi của đợt B. Merge sớm không làm đẹp được số liệu.
- Sau khi nghiệm thu, owner thêm N vào `ACCEPTANCE_ACCEPTED` qua điện thoại (khoảng 1 phút). Từ đó mọi PR phải giữ test của N đạt.

### A4. Cập nhật bộ test

Codex viết test trong PR riêng (`tests/acceptance/<issue>/`). Claude gửi owner hash tổng mới, kèm danh sách file và hash từng file. Owner dán **một chuỗi 64 ký tự** vào biến `ACCEPTANCE_SHA` bằng điện thoại, mỗi đợt một lần.

### A4b. Tiến trình duyệt (vùng R)

- **R** chạy theo lịch. Lấy các PR mở vào `collab/integration` qua API công khai, rồi chạy Codex read-only trên diff tại head SHA. Bước này giữ nguyên prompt và chính sách P2 như hiện nay.
- **S** kiểm JSON theo schema chặt (PR, head SHA, verdict, số P0/P1, review đầy đủ hay không). JSON sai schema thì coi là không có verdict. Sau đó S đăng check-run `codex-verdict` **gắn với head SHA**:
  - `success` chỉ khi verdict là APPROVE **và** PR không thuộc diện owner duyệt;
  - ngược lại là `failure`, kèm lý do.
- **Diện owner duyệt do S tự tính**, từ diff lấy qua API và sổ trạng thái riêng của S. S **không đọc nhãn hay comment** (T tạo và sửa được cả hai). Các trường hợp cần owner:
  - (a) diff đụng `.github/**`, `tests/acceptance/**`, `.claude/**`, câu chữ privacy hoặc khủng hoảng, và các mục khác theo quy tắc hiện hành;
  - (b) sổ của S ghi PR này đã có **≥ 2 verdict REQUEST_CHANGES**;
  - (c) verdict mới nhất ghi "review chưa đầy đủ".
  - (d) JSON verdict là APPROVE nhưng có P0, P1, hoặc P2 thuộc loại bảo mật hay privacy. S coi đây là verdict sai, chặn và ghi vào sổ.
- **Trạng thái chờ owner là bền vững.** Một khi PR hay SHA rơi vào (a)–(d), trạng thái đó giữ nguyên qua mọi verdict sau, kể cả APPROVE đầy đủ. Chỉ một cách giải phóng: owner thêm **head SHA hiện tại** vào `OWNER_APPROVED_SHAS`.
- **Quyết định gắn với SHA, gộp qua mọi PR.** Mỗi head SHA có đúng một quyết định. SHA bị chặn ở bất kỳ PR nào thì bị chặn ở **mọi** PR có cùng head SHA. Một PR bị chặn ở mức PR (b, c) thì mọi head SHA mới của PR đó cũng bị chặn. S đăng `failure` cho tất cả các PR liên quan.
- **Chỉ S đọc `OWNER_APPROVED_SHAS`** (qua quyền Variables: read của App) và chỉ S đăng check. R chỉ xuất JSON verdict, không có credential GitHub nào.
- Sổ trạng thái của S nằm trong vùng S, chỉ thêm dòng, không xoá. **Nhãn `needs-owner` chỉ để hiển thị.**
- **Owner duyệt bằng biến `OWNER_APPROVED_SHAS`** (chỉ Q sửa, qua điện thoại): thêm head SHA đã duyệt vào biến. **S** đọc biến rồi đăng lại `success` cho đúng SHA đó. Đổi head thì phải duyệt lại.
- Mã của vùng R và S là **bản ghim**: thư mục chỉ đọc với tài khoản R, cập nhật bằng tay qua phiên của owner. Không tự tải từ integration.

### A4c. Chỉ S được merge — cưỡng chế ngay lúc merge

- **Hai ruleset tách riêng cho `collab/**`:**
  - **`collab-restrict`**: chỉ có luật **Restrict updates**. Danh sách được miễn luật **chỉ gồm App `la-lanh-verdict`**. Token T vì vậy **không push và không merge** được, kể cả bằng API.
  - **`collab-checks`** (ruleset 27085048 mở rộng): luật bắt buộc PR, các check bắt buộc, strict (nhánh phải cập nhật theo base), chặn force-push và xoá nhánh. **Không ai được miễn, kể cả App.** Vì vậy lần merge của S cũng bị GitHub cưỡng chế strict và check.
- **S là bên duy nhất merge.** Với mỗi PR, S làm theo thứ tự trong một lượt:
  1. Đọc PR. Lấy head SHA `H` và base.
  2. Kiểm sổ ở **mức PR** (b, c), rồi ở **mức SHA trên mọi PR** có head `H` (a–d). Kiểm `OWNER_APPROVED_SHAS` nếu PR thuộc diện cần owner.
  3. Kiểm `check` và `acceptance-v<N>` đạt (`success`) tại `H`, phiên bản chính sách khớp biến hiện tại, và PR **không đi sau base mới nhất** (`mergeable_state` không phải `behind`). GitHub cũng cưỡng chế điều này qua `collab-checks`.
  4. Kiểm verdict JSON APPROVE tại `H` cho **đúng PR này**.
  5. Gọi API merge với tham số **`sha=H`**. Nếu head đổi sau bước 1, GitHub từ chối và S bắt đầu lại từ bước 1 ở lượt sau.
- Vì chỉ S merge, và S kiểm sổ của chính PR đang merge ngay trước khi gọi merge gắn với `sha=H`, nên **không còn khoảng đua** giữa lúc T đổi head và lúc S cập nhật sổ.
- App chỉ được miễn `collab-restrict`, không được miễn `collab-checks`. Sau khi thêm A4c, `collab-merge.mjs` của vùng A **không còn đường merge**. Bước 2 ở §5 gỡ quyền merge khỏi nó.

### A5. Lớp phụ trong `collab-merge`

Đọc kết quả `check` và `acceptance` tại đúng head. Kết quả `cancelled` hay `skipped` là chưa đạt. Ranh giới chính vẫn là A1 + T; lớp này chỉ để báo sớm.

## 4. Thiết kế B — chạy mã ở đâu

| Việc | Trước | Sau |
|---|---|---|
| `pnpm install`/`make`/`pnpm check` của PR | Mac, vùng O | **Chỉ trên CI** (`check`). Gỡ khỏi đường tự động |
| Scheduler chờ "Author check" trước review | comment local | Chờ kết quả `check` CI tại head |
| Heal: merge integration vào nhánh cũ | nằm trong `runCheckInClone` | Tách thành bước riêng chỉ chạy `git merge` + `push`, không cài, không build, chạy ở vùng A |
| Codex review | Mac, vùng O, sandbox read-only | **Vùng A**, sandbox read-only, prompt cấm chạy mã PR. Nếu Codex vẫn chạy mã thì nó chỉ thấy dữ liệu của vùng A (ops clone, token T), không thấy dữ liệu owner |
| Claude tương tác (khi chạy mã: test, build, script) | Vùng O, chưa có sandbox | Vùng O, **bắt buộc sandbox chỉ thấy repo**: `failIfUnavailable`, `allowUnsandboxedCommands: false`, `filesystem.denyRead: ["~/"]` rồi `allowRead` chỉ thư mục repo của agent và cache công cụ (node, pnpm store, uv). `~/Documents` ngoài repo, credential và trình duyệt đều không đọc được. Read/Edit tool có luật `deny` tương ứng ngoài thư mục repo. Phép thử sandbox tuần 1a phải đạt trước, gồm canary trong `~/Documents` (P12). Nếu P12 trượt thì Claude chỉ chạy mã trong vùng A |

Lợi ích phụ: Mac không còn chạy check 10–60 phút mỗi PR, giảm nóng máy.

## 5. Thứ tự làm và phút của owner

| Bước | Ai | Phút owner |
|---|---|---|
| 1. Thử sandbox (1a): đạt mới đi tiếp | Claude, bằng 1 phiên | 0 |
| 2. PR: `acceptance.yml`, scheduler đọc CI, tách heal, gỡ check local, script cài vùng A | Claude viết, Codex review; owner duyệt vì đụng `.github/**` | 10 |
| 3. Claude bổ sung luật vào ruleset (token cũ vẫn còn quyền) | Claude | 0 |
| 4. Tạo tài khoản `lalanh-agent`, `lalanh-review`, `lalanh-sign`; `chmod 700 ~` cho cả bốn tài khoản | **Owner**. Claude không đổi cài đặt hệ thống | 15 |
| 4b. Tạo GitHub App `la-lanh-verdict`, cài vào repo, lưu khoá riêng vào vùng S | **Owner** (Claude soạn hướng dẫn từng bước) | 15 |
| 5. Tạo token T, đăng nhập `gh` bằng T ở cả vùng O và A | **Owner**. Claude không nhập token | 10 |
| 6. Thu hồi token cũ; đăng xuất GitHub khỏi trình duyệt trên Mac | Owner, dùng điện thoại | 5 |
| 7. Chuyển launchd tick sang vùng A | Claude soạn lệnh, owner chạy | 5 |
| 8. Chạy phép thử §6, ghi kết quả vào PR | Claude | 0 |

Tổng một lần: khoảng 60 phút owner, chia vào 2 phiên. Mỗi lần đổi chính sách nghiệm thu, Q đổi 3 biến và tên check trong ruleset: khoảng 4 phút, chia vào 1–2 phiên, tính vào trần 180 phút/tuần. Mỗi đợt B thêm khoảng 3 phút, mỗi việc được nghiệm thu thêm 1 phút.

## 6. Phép thử bắt buộc (AC của spec)

Mọi phép thử dùng nhánh `agent/probe-*` và nội dung giả. Mỗi phép thử có điều kiện đạt rõ.

| # | Given / When | Đạt khi |
|---|---|---|
| P1 | Dùng token T, đẩy commit sửa `.github/workflows/pr-check.yml` | GitHub từ chối push |
| P2 | Dùng token T, merge (API) một PR có thay đổi workflow do owner tạo | GitHub từ chối. **Nếu T merge được thì dừng triển khai**, sửa thiết kế rồi thử lại. Ghi lại hành vi không được tính là đạt |
| P3 | Dùng token T, `git push` thẳng vào `collab/integration` | Bị từ chối |
| P4 | Dùng token T, sửa ruleset, biến repo, hay tạo workflow | Đều HTTP 403/404 |
| P5 | PR có job tên `acceptance` trong file workflow mới | Không push được (P1). Check bắt buộc vẫn chỉ nhận kết quả từ GitHub Actions |
| P6 | PR sửa `tests/acceptance/**` mà không đổi `ACCEPTANCE_SHA` | `acceptance` trượt; `gh pr merge` bị từ chối |
| P7 | PR làm `build` lỗi | `acceptance` trượt (không bị skip); merge bị từ chối |
| P8 | App độc: khi chạy thì cố ghi đè file test, sửa `node_modules` của runner, kill tiến trình Playwright, và đọc `$GITHUB_WORKSPACE` | Mọi thao tác đều thất bại; kết quả test không đổi |
| P9 | Năm PR, mỗi PR một kiểu tác động: `.npmrc` gốc đổi registry; `pnpm-workspace.yaml` gốc; `.pnpmfile.cjs` gốc; symlink trong `tests/acceptance` trỏ ra ngoài; lockfile test có `file:` | 3 PR đầu: runner test không bị ảnh hưởng (log cài đặt cho thấy registry chuẩn, không có hook). 2 PR sau: `acceptance` trượt ngay ở bước kiểm |
| P10 | Từ vùng A, đọc `~/.codex`, `~/.config/gh`, `~/.ssh`, `~/Documents/canary-*.txt` của owner | Mỗi lệnh đọc đều trả lỗi quyền (chứng minh bằng lỗi, không chỉ bằng việc vắng canary) |
| P11 | Canary: đặt file giả `~/canary-<ngẫu nhiên>.txt` trong vùng O; chạy tick, Codex review và heal ở vùng A, có PR cố in nội dung file này | Chuỗi canary **không** xuất hiện trong log, comment, output Codex hay CI |
| P12 | Phiên Claude có sandbox ở vùng O: dùng **Bash** và **Read tool** đọc `~/Documents/canary-*.txt` (ngoài repo), `~/.codex`, cookie trình duyệt | Cả hai đường đều bị từ chối, có thông báo lỗi; trong repo vẫn đọc được |
| P13 | Đột biến: một việc có test, 3 nhánh mỗi nhánh cài 1 lỗi | `acceptance` bắt được 3/3 |
| P14 | Hai PR liên tiếp: PR 1 merge, PR 2 bị heal cập nhật | CI chạy lại trên head mới, review gắn SHA mới, merge đúng SHA đó; không có `pnpm` nào chạy trên Mac (log launchd của tài khoản A, không chỉ dựa vào `pgrep`) |
| P15 | Thử **bằng chính S (App)**: (a) `check` của head bị huỷ vì có commit mới; (b) hai PR A và B cùng xanh trên base B0, S merge A, rồi S thử merge B bằng `sha=H_B` khi B chưa cập nhật theo base mới | (a), (b): GitHub từ chối lần merge của S (strict và check không miễn App) |
| P16 | PR có `acceptance-v1` xanh; Q thêm một mã việc đang trượt vào `ACCEPTANCE_ACCEPTED`, tăng lên v2 và đổi tên check trong ruleset; T merge thẳng bằng API trên cùng SHA | GitHub chặn merge |
| P17 | `ACCEPTANCE_ACCEPTED` có mã việc không tồn tại; mã việc có thư mục nhưng không có test; mọi test bị `skip`; job `run` bị huỷ; artifact có digest sai | Mỗi trường hợp: `acceptance-v<N>` trượt, merge bị chặn |
| P19 | Dùng T merge thẳng bằng API ba PR có CI xanh: một PR thiếu verdict, một PR có REQUEST_CHANGES, một PR thuộc diện owner duyệt mà chưa có SHA trong `OWNER_APPROVED_SHAS` | Cả ba bị GitHub chặn |
| P20 | Dùng T tạo check-run hay commit status tên `codex-verdict` | Không thoả luật, vì nguồn sai app hoặc bị 403 |
| P21 | Quanh từng bước 1–3 của §A1: (a) một run đang chạy, (b) một run đang chờ, (c) chạy lại (re-run) một run cũ sau khi đã đổi phiên bản. Cắt ngang ở mỗi bước. Thử merge bằng API ở mỗi thời điểm | Không lúc nào merge được theo chính sách cũ. Run chạy lại mà lệch chính sách thì trượt |
| P22 | Runner sạch theo A2: cài và chạy 1 test Playwright mẫu | Chạy được; log cho thấy không đọc file nào của PR ngoài bộ test đã ghim |
| P23 | Dùng T `git push` thẳng vào `main`, và merge bằng API một PR vào `main` có CI xanh | Cả hai bị GitHub chặn |
| P24 | Một PR có 2 verdict REQUEST_CHANGES, rồi T xoá nhãn `needs-owner` và sửa comment; verdict thứ 3 là APPROVE; T merge bằng API | Bị chặn, vì S vẫn tính là cần owner |
| P25 | Đặt khoá App giả trong vùng S. Từ R (cả Codex lẫn shell) và từ A thử đọc khoá, đọc biến môi trường và `ps` của tiến trình ký | Mọi lệnh đọc đều báo lỗi quyền; khoá giả không xuất hiện trong output Codex |
| P26 | Hai PR khác nhánh, cùng head SHA: PR 1 đã bị chặn (2 REQUEST_CHANGES), PR 2 nhận APPROVE. (a) Dùng T merge bằng API cả hai; (b) T đổi head của PR 1 sang SHA đã xanh rồi merge **ngay**, trước lượt S kế tiếp; (c) đổi base nhưng giữ head | (a), (b): GitHub từ chối vì T không có quyền cập nhật `collab/**`. Ở lượt sau, S không merge PR 1. (c): bị chặn |
| P30 | Dùng T `git push` thẳng vào `collab/integration`, và merge bằng API một PR đã đủ mọi điều kiện | Cả hai bị từ chối; chỉ S merge được |
| P31 | S gọi merge với `sha=H` trong khi T vừa đẩy head mới | GitHub từ chối lần merge này; S không merge head chưa được kiểm |
| P27 | Verdict "chưa đầy đủ", rồi verdict đầy đủ + APPROVE, owner chưa duyệt | Vẫn chặn. Owner thêm SHA vào biến thì mới mở |
| P28 | JSON APPROVE kèm 1 P1; JSON APPROVE kèm 1 P2 loại privacy; JSON sai schema | S từ chối cả ba |
| P29 | Chạy trọn luồng owner duyệt, trong khi R không có credential GitHub nào (kiểm keychain, biến môi trường, file). Ép mã PR chạy ở A và ở R để đọc canary | Owner duyệt vẫn chạy được; mọi lệnh đọc canary đều báo lỗi quyền |
| P18 | Thử tên job có `${{ vars.ACCEPTANCE_VERSION }}` | Check hiện đúng tên `acceptance-v<N>`. Nếu GitHub không cho dùng `vars` trong tên job thì dùng workflow riêng cho từng phiên bản, do Q đổi |

Ghi chú về P1, P2: tài liệu chính thức chưa mô tả đủ cách GitHub xử lý push và merge với token thiếu quyền Workflows, nên phải thử thật.

## 7. Rủi ro còn lại

- **App trong PR có thể được viết để nhận ra đang bị test.** Phần bù là kiểm mù bằng phiên Codex mới và nghiệm thu của owner.
- **Vùng A vẫn đẩy được nhánh `agent/*`**, nhưng không merge được. Việc merge vào integration do S làm.
- **S giữ khoá App có quyền ghi.** Lộ khoá thì vượt được cổng ở `collab/**` (không gồm `main`). Cách giảm: S không chạy mô hình hay mã PR, mã của S ghim cố định, khoá có quyền `600` trong một tài khoản riêng; P25 kiểm. Lên `main` và deploy vẫn chỉ owner làm.
- **Phiên Claude tương tác ở vùng O.** Bash bị Seatbelt chặn ở mức hệ điều hành và chỉ thấy repo. Read/Edit tool bị chặn bằng luật `deny` của Claude Code, chưa phải ranh giới tài khoản hệ điều hành. P12 thử cả hai đường. Nếu muốn chặt hơn nữa, chuyển Claude sang vùng A.
- **Chi phí của owner:** khoảng 40 phút một lần, thêm 3–4 phút mỗi đợt. Nếu vượt trần phút của tuần thì lùi lịch A/B.

## 8. Quay lui và dữ liệu cá nhân

**Quay lui:**
- Tắt luật PR và check bắt buộc qua điện thoại.
- **Dừng hẳn vòng tự động** (gỡ launchd). **Không** chạy vòng tự động trong vùng O dưới bất kỳ dạng nào. Owner tự merge bằng tay cho tới khi vùng A chạy lại.
- Không khôi phục token admin cho agent. Không chạy lại check local.

**Khi có lỗi bảo mật hay privacy:** chặn merge, sửa hoặc revert bằng PR, Codex kiểm lại, báo owner.

**Dữ liệu cá nhân:**
- Test chỉ dùng dữ liệu giả, không có ngày, giờ, nơi sinh thật.
- Log CI không in token hay nội dung người dùng.
- Vùng A không có dữ liệu của owner.

## 9. Bản 1 → bản 2

| P1 Codex nêu ở bản 1 | Bản 2 xử lý |
|---|---|
| App chạy chung runner với test | Container `--read-only`, không mount, chỉ qua HTTP; P8 |
| Skip được coi là đạt; nghiệm thu rỗng | Job `acceptance` dùng `always()` và chỉ nhận `success`; A3 chỉ tin summary; P7 |
| Agent dùng được phiên quản trị web; token cũ chưa thu hồi | Vùng Q trên điện thoại; đăng xuất GitHub trên Mac; thu hồi token; P4 |
| Codex chạy mã PR trên Mac thấy dữ liệu owner | Codex chuyển sang vùng A; canary P11; sandbox 1a là điều kiện trước |
| Mã vận hành từ integration chạy với quyền đủ | Chạy ở vùng A với token T, nên quyền có hạn; P10, P11 |
| (P2) Scheduler và heal mắc kẹt | Scheduler đọc CI; heal tách riêng; P14 |

| P1 Codex nêu ở bản 2 | Bản 3 xử lý |
|---|---|
| Đổi chính sách không làm check xanh cũ hết hiệu lực | Tên check bắt buộc gắn phiên bản; Q đổi biến và luật cùng lúc; P16, P18 |
| Runner test chịu cấu hình gốc của PR | Bộ test giải nén ra thư mục sạch ngoài checkout; chặn symlink, `file:`, `.pnpmfile`; ghim pnpm và registry; P9 |
| Claude ở O đọc được `~/Documents`; quay lui đưa vòng về O | Sandbox chỉ thấy repo (Bash + Read); quay lui là dừng hẳn vòng; P10, P12 có canary và lỗi quyền |
| (P2) "Ghi lại hành vi" bị coi là đạt | P2 có điều kiện dừng cứng |

| P1 Codex nêu ở bản 3 | Bản 4 xử lý |
|---|---|
| Đổi chính sách không nguyên tử | Khoá cổng trước bằng tên check mới; đổi biến; cuối cùng mới tăng phiên bản; mỗi run dùng một bản chính sách; P16, P21 |
| T merge được khi bỏ qua verdict và `needs-owner` | Check `codex-verdict` từ GitHub App riêng ở vùng R; diện owner duyệt tính trong R; owner duyệt bằng biến chỉ Q sửa; P19, P20 |
| (P2) Chưa rõ nguồn của bộ chạy test | Manifest và config nằm trong bộ test đã ghim hash; trình duyệt theo đúng phiên bản; P22 |

| P1 Codex nêu ở bản 4 | Bản 5 xử lý |
|---|---|
| Codex và khoá App cùng một tài khoản | Tách vùng S giữ khoá: không mô hình, không mã PR; R chỉ ghi JSON; P25 |
| `main` chưa khoá riêng | Ruleset `main`/`release/**`: bắt buộc PR, check `owner-release` từ app, chỉ Q cấp; P23 |
| (P2) Trạng thái cần owner tin vào nhãn | S tự giữ sổ (≥ 2 REQUEST_CHANGES, review chưa đầy đủ), không đọc nhãn hay comment; P24 |

| Phát hiện Codex nêu ở bản 5 | Bản 6 xử lý |
|---|---|
| P1: verdict được dùng lại giữa các PR có cùng SHA | Mỗi SHA một quyết định, gộp qua mọi PR; chặn ở mức PR áp cho mọi head; P26 |
| P2: trạng thái chờ owner tự mất | Trạng thái bền vững; chỉ giải phóng bằng SHA trong biến của Q; P27; thêm (d) APPROVE kèm lỗi nặng; P28 |
| P2: R vừa không có token vừa đọc biến | Chỉ S đọc biến và đăng check; R không có credential; P29 |

| P1 Codex nêu ở bản 7 | Bản 8 xử lý |
|---|---|
| App được miễn luật thì cũng thoát luôn strict và check | Tách 2 ruleset: chỉ `collab-restrict` miễn App; `collab-checks` không miễn ai; S kiểm thêm nhánh không đi sau base; P15 thử bằng S |

| P1 Codex nêu ở bản 6 | Bản 7 xử lý |
|---|---|
| Khoảng đua: T đổi head sang SHA đã xanh rồi merge trước khi S cập nhật | Restrict updates: chỉ App merge; S kiểm sổ PR + SHA rồi merge với `sha=H`; P26(b), P30, P31 |
