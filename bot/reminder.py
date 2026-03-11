import json
import os
import sys
import urllib.request
from urllib.error import HTTPError, URLError

WEBHOOK_URL = os.environ["MATTERMOST_WEBHOOK_URL"]
CHANNEL = os.getenv("MATTERMOST_CHANNEL", "")
STRICT_CHANNEL_OVERRIDE = os.getenv("MATTERMOST_STRICT_CHANNEL_OVERRIDE", "").lower() in ("1", "true", "yes")
SCRUM_DOC_URL = "https://www.notion.so/31f2947a9611803aa292c4890f9a7d0c"
JIRA_DOC_URL = "https://ssafy.atlassian.net/jira/software/c/projects/S14P21C103/boards/12733"

REMINDER_TYPE = sys.argv[1] if len(sys.argv) > 1 else "jira_morning"

MESSAGES = {
    "scrum_prep": (
        "@channel\n"
        "### ✍️🐵 스크럼 회의록 사전 작성 알림\n"
        "오전 9:30 스크럼 전, 노션 회의록에 오늘 공유할 내용을 미리 작성해주세요.\n"
        f"- **문서:** [👉 Scrum 링크]({SCRUM_DOC_URL})"
    ),
    "scrum": (
        "@channel\n"
        "### 🏁🐵 스크럼 알림\n"
        "평일 오전 9:30 스크럼 시작합니다. C103 팀원 전원 참석 부탁드립니다.\n"
        f"- **문서:** [👉 Scrum 링크]({SCRUM_DOC_URL})"
    ),
    "jira_morning": (
        "@channel\n"
        "### ☀️🐵 Jira 업데이트 알림 (오전)\n"
        "오늘 작업 시작 전에 Jira 상태를 업데이트해주세요.\n"
        f"- **보드:** [👉 Jira 링크]({JIRA_DOC_URL})"
    ),
    "jira": (
        "@channel\n"
        "### 🔄🐵 Jira 업데이트 알림\n"
        "작업 진행 중 Jira 진행상태/작업로그를 최신으로 유지해주세요.\n"
        f"- **보드:** [👉 Jira 링크]({JIRA_DOC_URL})"
    ),
    "jira_evening": (
        "@channel\n"
        "### 🌙🐵 Jira 업데이트 알림 (오후)\n"
        "하루 마무리 전에 Jira 진행상태/작업로그를 업데이트해주세요.\n"
        f"- **보드:** [👉 Jira 링크]({JIRA_DOC_URL})"
    ),
}

def build_gitlab_mr_message():
    action = os.getenv("GITLAB_MR_ACTION", "").strip()
    project = os.getenv("GITLAB_PROJECT", "").strip()
    iid = os.getenv("GITLAB_MR_IID", "").strip()
    title = os.getenv("GITLAB_MR_TITLE", "").strip()
    url = os.getenv("GITLAB_MR_URL", "").strip()
    actor = os.getenv("GITLAB_MR_ACTOR", "").strip()
    author = os.getenv("GITLAB_MR_AUTHOR", "").strip()

    # Backward compatibility: old payload used `author` for event actor.
    if not actor and author:
        actor = author

    mr_ref = f"{project}!{iid}" if project and iid else ""

    lines = ["@channel", "### :baseball: :woman-running: GitLab MR 알림"]
    if mr_ref:
        lines.append(f"- **MR:** `{mr_ref}`")
    if title:
        lines.append(f"- **제목:** {title}")
    if actor:
        lines.append(f"- **수행자:** {actor}")
    if author:
        lines.append(f"- **작성자:** {author}")
    if action:
        lines.append(f"- **이벤트:** `{action}`")
    if url:
        lines.append(f"- **링크:** [👉 MR 링크]({url})")

    return "\n".join(lines)


if REMINDER_TYPE == "gitlab_mr":
    text = build_gitlab_mr_message()
elif REMINDER_TYPE in MESSAGES:
    text = MESSAGES[REMINDER_TYPE]
else:
    raise ValueError(f"Unknown reminder type: {REMINDER_TYPE}")

payload = {"text": text}
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
