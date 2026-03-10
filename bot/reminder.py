import json
import os
import sys
import urllib.request
from urllib.error import HTTPError, URLError

WEBHOOK_URL = os.environ["MATTERMOST_WEBHOOK_URL"]
CHANNEL = os.getenv("MATTERMOST_CHANNEL", "")
STRICT_CHANNEL_OVERRIDE = os.getenv("MATTERMOST_STRICT_CHANNEL_OVERRIDE", "").lower() in ("1", "true", "yes")
JIRA_URL = os.getenv("JIRA_URL", "https://your-domain.atlassian.net/jira/software/projects/XXX/boards/1")

REMINDER_TYPE = sys.argv[1] if len(sys.argv) > 1 else "jira"

MESSAGES = {
    "scrum": (
        "@channel 🏁🐵 [스크럼 알림]\n"
        "오늘도 화이팅! 평일 오전 9:30 스크럼 시작합니다. C103 팀원 전원 참석 부탁드립니다. 😊"
    ),
    "jira": (
        "@channel 🔄🐵 [Jira 업데이트 알림]\n"
        f"작업 중간중간 Jira 진행상태/작업로그를 최신으로 업데이트해주세요.\n{JIRA_URL}"
    ),
}

# Backward compatibility for legacy event names.
MESSAGES["jira_morning"] = MESSAGES["jira"]
MESSAGES["jira_evening"] = MESSAGES["jira"]

if REMINDER_TYPE not in MESSAGES:
    raise ValueError(f"Unknown reminder type: {REMINDER_TYPE}")

payload = {"text": MESSAGES[REMINDER_TYPE]}
if CHANNEL:
    payload["channel"] = CHANNEL

def send(webhook_payload):
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(webhook_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req) as res:
        body = res.read().decode("utf-8")
        if res.status != 200:
            raise RuntimeError(f"Failed: {res.status}, body={body}")
        print("Mattermost sent:", body)


try:
    send(payload)
except HTTPError as e:
    error_body = e.read().decode("utf-8", errors="replace")
    if CHANNEL and e.code in (400, 404):
        if STRICT_CHANNEL_OVERRIDE:
            raise RuntimeError(
                f"Channel override failed in strict mode ({e.code}), body={error_body}"
            ) from e
        # Some servers reject channel override even when webhook itself is valid.
        print(
            f"Channel override failed ({e.code}). Retrying without MATTERMOST_CHANNEL. "
            f"body={error_body}"
        )
        payload.pop("channel", None)
        send(payload)
    else:
        raise RuntimeError(f"Failed: {e.code}, body={error_body}") from e
except URLError as e:
    raise RuntimeError(f"Network error while sending Mattermost webhook: {e}") from e
