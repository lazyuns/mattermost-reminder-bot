# cron-job.org -> GitHub Actions (`repository_dispatch`) Setup

This project no longer relies on GitHub `schedule`.
Use `cron-job.org` to call GitHub's dispatch endpoint at the exact target times.

## Endpoint

- URL: `https://api.github.com/repos/lazyuns/mattermost-reminder-bot/dispatches`
- Method: `POST`

## Headers

- `Accept: application/vnd.github+json`
- `Authorization: Bearer <GITHUB_TOKEN>`
- `X-GitHub-Api-Version: 2022-11-28`
- `Content-Type: application/json`

## Token

- Create a GitHub token that can call repository dispatch.
- Classic PAT: include `repo` scope.

## Request body patterns

You can use either pattern. Pattern A is simpler.

### Pattern A: event type only

```json
{"event_type":"scrum"}
```

```json
{"event_type":"jira"}
```

### Pattern B: generic event + payload

```json
{
  "event_type": "send_reminder",
  "client_payload": {
    "reminder_type": "scrum"
  }
}
```

Optional test override channel:

```json
{
  "event_type": "send_reminder",
  "client_payload": {
    "reminder_type": "jira",
    "channel_override": "@your_username"
  }
}
```

## Recommended cron-job.org jobs (UTC)

- Scrum (KST 09:30): `30 0 * * 1-5`
- Jira (KST 10:00, 12:00, 14:00, 16:00): `0 1,3,5,7 * * 1-5`

Create 2 cron-job.org jobs: one for scrum, one for jira.
