#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BUNDLED_PNPM="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm"

if [[ -x "$BUNDLED_PNPM" ]]; then
  PNPM="$BUNDLED_PNPM"
  export PATH="$(dirname "$BUNDLED_PNPM"):$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH"
elif command -v pnpm >/dev/null 2>&1; then
  PNPM="$(command -v pnpm)"
else
  echo "Không tìm thấy pnpm. Hãy mở project bằng Codex và chạy lại."
  read -r "?Nhấn Enter để đóng…"
  exit 1
fi

cd "$ROOT"

WEB_PORT="${LA_LANH_QA_WEB_PORT:-5180}"
API_PORT="${LA_LANH_QA_API_PORT:-8010}"
REVIEW_URL="http://127.0.0.1:${WEB_PORT}/welcome"
READY_URL="http://127.0.0.1:${WEB_PORT}/__qa/ready"

open_review() {
  if command -v open >/dev/null 2>&1; then
    open "$REVIEW_URL"
  fi
}

if curl --fail --silent --show-error "$READY_URL" >/dev/null 2>&1; then
  echo "Lá Lành QA đang chạy. Đang mở bản review…"
  open_review
  echo "$REVIEW_URL"
  exit 0
fi

echo "Đang chuẩn bị bản review mới nhất…"
"$PNPM" qa:build

export LA_LANH_QA_WEB_PORT="$WEB_PORT"
export LA_LANH_QA_API_PORT="$API_PORT"
"$PNPM" qa:start &
SERVER_PID=$!

cleanup() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

for _ in {1..120}; do
  if curl --fail --silent --show-error "$READY_URL" >/dev/null 2>&1; then
    echo ""
    echo "Lá Lành QA đã sẵn sàng. Đang mở bản review…"
    echo "$REVIEW_URL"
    open_review
    wait "$SERVER_PID"
    exit $?
  fi
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    wait "$SERVER_PID"
    exit $?
  fi
  sleep 0.5
done

echo "Bản review khởi động quá lâu. Hãy đóng cửa sổ này rồi thử lại."
exit 1
