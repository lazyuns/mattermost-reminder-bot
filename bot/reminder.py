import json
import os
import sys
import urllib.request

WEBHOOK_URL = os.environ["MATTERMOST_WEBHOOK_URL"]
CHANNEL = os.getenv("MATTERMOST_CHANNEL", "")
JIRA_URL = os.getenv("JIRA_URL", "https://your-domain.atlassian.net/jira/software/projects/XXX/boards/1")

REMINDER_TYPE = sys.argv[1] if len(sys.argv) > 1 else "jira_morning"

MESSAGES = {
    "scrum": (
        "@channel 🏁🐵 [스크럼 알림]\n"
        "오늘도 화이팅! 평일 자동 알림 테스트 중입니다(5분 간격). C103 팀원 전원 참석 부탁드립니다. 😊"
    ),
    "jira_morning": (
        "@channel ☀️🐵 [Jira 업데이트 알림 - 오전]\n"
        f"좋은 아침이에요! 오늘 작업 시작 전에 Jira 상태 업데이트 부탁드립니다.\n{JIRA_URL}"
    ),
    "jira_evening": (
        "@channel 🌙🐵 [Jira 업데이트 알림 - 오후]\n"
        f"하루 마무리 전에 Jira 진행상태/작업로그 업데이트 부탁드립니다. 고생 많았어요! 🙌\n{JIRA_URL}"
    ),
}

if REMINDER_TYPE not in MESSAGES:
    raise ValueError(f"Unknown reminder type: {REMINDER_TYPE}")

payload = {"text": MESSAGES[REMINDER_TYPE]}
if CHANNEL:
    payload["channel"] = CHANNEL

req = urllib.request.Request(
    WEBHOOK_URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req) as res:
    body = res.read().decode("utf-8")
    if res.status != 200:
        raise RuntimeError(f"Failed: {res.status}, body={body}")
    print("Mattermost sent:", body)
