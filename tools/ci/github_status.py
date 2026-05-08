#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT_DIR = Path(__file__).resolve().parents[2]
GITHUB_API_ROOT = "https://api.github.com"
FINAL_FAILURE_CONCLUSIONS = {"action_required", "cancelled", "failure", "startup_failure", "timed_out"}
FINAL_PASSING_CONCLUSIONS = {"success", "neutral", "skipped"}


@dataclass(frozen=True)
class GitHubStatusRequest:
    repo: str
    sha: str
    token: str = ""


def run_git(args: Sequence[str], cwd: Path = ROOT_DIR) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).strip())
    return completed.stdout.strip()


def parse_github_repo_from_remote(remote_url: str) -> str:
    value = str(remote_url or "").strip()
    value = value.removesuffix(".git")

    patterns = [
        r"^git@github\.com:(?P<repo>[^/]+/[^/]+)$",
        r"^git@ssh\.github\.com:(?P<repo>[^/]+/[^/]+)$",
        r"^ssh://git@github\.com/(?P<repo>[^/]+/[^/]+)$",
        r"^ssh://git@ssh\.github\.com(?::\d+)?/(?P<repo>[^/]+/[^/]+)$",
        r"^https://github\.com/(?P<repo>[^/]+/[^/]+)$",
        r"^http://github\.com/(?P<repo>[^/]+/[^/]+)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, value)
        if match:
            return match.group("repo")

    raise ValueError(f"无法从远程地址识别 GitHub 仓库：{remote_url}")


def detect_repo(remote: str = "origin") -> str:
    return parse_github_repo_from_remote(run_git(["remote", "get-url", remote]))


def detect_sha(revision: str = "HEAD") -> str:
    return run_git(["rev-parse", revision])


def parse_porcelain_status(status_text: str) -> dict[str, int]:
    counts = {"staged": 0, "unstaged": 0, "untracked": 0, "total": 0}
    for line in str(status_text or "").splitlines():
        if not line:
            continue
        if line.startswith("??"):
            counts["untracked"] += 1
            counts["total"] += 1
            continue
        index_status = line[0] if len(line) > 0 else " "
        worktree_status = line[1] if len(line) > 1 else " "
        if index_status != " ":
            counts["staged"] += 1
        if worktree_status != " ":
            counts["unstaged"] += 1
        if index_status != " " or worktree_status != " ":
            counts["total"] += 1
    return counts


def classify_git_sync(git_snapshot: dict[str, Any]) -> str:
    if not git_snapshot.get("hasRemoteBranch"):
        return "no_remote"
    dirty = git_snapshot.get("dirty") or {}
    if dirty.get("total", 0) > 0:
        return "dirty"
    ahead = int(git_snapshot.get("ahead") or 0)
    behind = int(git_snapshot.get("behind") or 0)
    if ahead > 0 and behind > 0:
        return "diverged"
    if ahead > 0:
        return "ahead"
    if behind > 0:
        return "behind"
    return "synced"


def get_git_sync_label(status: str) -> str:
    return {
        "synced": "已同步",
        "dirty": "有未提交改动",
        "ahead": "有未推送提交",
        "behind": "落后远端",
        "diverged": "本地和远端已分叉",
        "no_remote": "未找到远端分支",
    }.get(status, status)


def refresh_remote_tracking_branch(remote_branch: str = "origin/main") -> bool:
    remote, separator, branch = str(remote_branch or "").partition("/")
    if not remote or not separator or not branch:
        return False
    try:
        run_git(["fetch", "--quiet", remote, f"+{branch}:refs/remotes/{remote}/{branch}"])
    except RuntimeError:
        return False
    return True


def get_git_snapshot(remote_branch: str = "origin/main", fetch_remote: bool = False) -> dict[str, Any]:
    remote_refreshed = refresh_remote_tracking_branch(remote_branch) if fetch_remote else False
    status_text = run_git(["status", "--porcelain"])
    dirty = parse_porcelain_status(status_text)
    branch = run_git(["branch", "--show-current"]) or "(detached)"
    local_sha = detect_sha()
    has_remote_branch = True
    remote_sha = ""
    ahead = 0
    behind = 0

    try:
        remote_sha = detect_sha(remote_branch)
        ahead_behind = run_git(["rev-list", "--left-right", "--count", f"HEAD...{remote_branch}"])
        ahead_text, behind_text = ahead_behind.split()
        ahead = int(ahead_text)
        behind = int(behind_text)
    except (RuntimeError, ValueError):
        has_remote_branch = False

    snapshot: dict[str, Any] = {
        "branch": branch,
        "remoteBranch": remote_branch,
        "remoteRefreshRequested": bool(fetch_remote),
        "remoteRefreshed": remote_refreshed,
        "localSha": local_sha,
        "localShortSha": local_sha[:7],
        "remoteSha": remote_sha,
        "remoteShortSha": remote_sha[:7] if remote_sha else "",
        "hasRemoteBranch": has_remote_branch,
        "ahead": ahead,
        "behind": behind,
        "dirty": dirty,
    }
    sync_status = classify_git_sync(snapshot)
    snapshot["syncStatus"] = sync_status
    snapshot["syncLabel"] = get_git_sync_label(sync_status)
    return snapshot


def build_headers(token: str = "") -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "tony-na-engine-local-ci-status",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def load_json_url(url: str, token: str = "") -> Any:
    request = Request(url, headers=build_headers(token))
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API 请求失败：HTTP {error.code}\n{details}") from error
    except URLError as error:
        raise RuntimeError(f"无法连接 GitHub API：{error}") from error


def fetch_check_runs(request: GitHubStatusRequest) -> list[dict[str, Any]]:
    url = f"{GITHUB_API_ROOT}/repos/{request.repo}/commits/{request.sha}/check-runs"
    payload = load_json_url(url, request.token)
    return list(payload.get("check_runs") or [])


def fetch_annotations(annotations_url: str, token: str = "") -> list[dict[str, Any]]:
    if not annotations_url:
        return []
    payload = load_json_url(annotations_url, token)
    return list(payload or [])


def classify_check_runs(check_runs: Sequence[dict[str, Any]]) -> str:
    if not check_runs:
        return "missing"
    if any(run.get("status") != "completed" for run in check_runs):
        return "in_progress"
    conclusions = {str(run.get("conclusion") or "").lower() for run in check_runs}
    if conclusions & FINAL_FAILURE_CONCLUSIONS:
        return "failure"
    if conclusions and conclusions <= FINAL_PASSING_CONCLUSIONS:
        return "success"
    return "unknown"


def get_status_label(status: str) -> str:
    return {
        "success": "通过",
        "failure": "失败",
        "in_progress": "运行中",
        "missing": "暂未找到检查",
        "unknown": "未知",
    }.get(status, status)


def normalize_check_run(run: dict[str, Any]) -> dict[str, Any]:
    output = run.get("output") or {}
    return {
        "id": run.get("id"),
        "name": run.get("name") or "",
        "status": run.get("status") or "",
        "conclusion": run.get("conclusion") or "",
        "startedAt": run.get("started_at") or "",
        "completedAt": run.get("completed_at") or "",
        "detailsUrl": run.get("details_url") or run.get("html_url") or "",
        "annotationsCount": output.get("annotations_count") or 0,
        "annotationsUrl": output.get("annotations_url") or "",
    }


def build_status_payload(
    repo: str,
    sha: str,
    check_runs: Sequence[dict[str, Any]],
    annotations_by_run: dict[str, list[dict[str, Any]]] | None = None,
    git_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_runs = [normalize_check_run(run) for run in check_runs]
    status = classify_check_runs(check_runs)
    return {
        "repo": repo,
        "sha": sha,
        "shortSha": sha[:7],
        "status": status,
        "statusLabel": get_status_label(status),
        "totalCount": len(normalized_runs),
        "runs": normalized_runs,
        "annotations": annotations_by_run or {},
        "git": git_snapshot or {},
    }


def collect_annotations_for_failures(
    check_runs: Sequence[dict[str, Any]],
    token: str = "",
) -> dict[str, list[dict[str, Any]]]:
    annotations_by_run: dict[str, list[dict[str, Any]]] = {}
    for run in check_runs:
        normalized = normalize_check_run(run)
        if normalized["conclusion"] not in FINAL_FAILURE_CONCLUSIONS:
            continue
        if not normalized["annotationsCount"]:
            continue
        annotations = fetch_annotations(normalized["annotationsUrl"], token)
        annotations_by_run[str(normalized["id"])] = annotations
    return annotations_by_run


def format_status_text(payload: dict[str, Any]) -> str:
    lines = [
        f"GitHub CI 状态：{payload['statusLabel']}",
        f"仓库：{payload['repo']}",
        f"提交：{payload['shortSha']}",
        f"检查数量：{payload['totalCount']}",
    ]
    git = payload.get("git") or {}
    if git:
        dirty = git.get("dirty") or {}
        dirty_total = int(dirty.get("total") or 0)
        lines.extend(
            [
                f"本地同步：{git.get('syncLabel', '')}",
                f"本地分支：{git.get('branch', '')} @ {git.get('localShortSha', '')}",
                f"远端分支：{git.get('remoteBranch', '')}"
                + (f" @ {git.get('remoteShortSha', '')}" if git.get("remoteShortSha") else ""),
                *(
                    [
                        "远端刷新："
                        + ("已刷新" if git.get("remoteRefreshed") else "刷新失败，使用本地缓存")
                    ]
                    if git.get("remoteRefreshRequested")
                    else []
                ),
                f"未提交文件：{dirty_total}",
                f"未推送提交：{git.get('ahead', 0)}",
                f"落后远端提交：{git.get('behind', 0)}",
            ]
        )
    if not payload["runs"]:
        lines.append("还没有查到 GitHub Actions 检查。可能是刚推送，或者这个提交没有触发 workflow。")
    for run in payload["runs"]:
        conclusion = run["conclusion"] or "pending"
        lines.append(f"- {run['name']}: {run['status']} / {conclusion}")
        if run["detailsUrl"]:
            lines.append(f"  {run['detailsUrl']}")
    annotations = payload.get("annotations") or {}
    if annotations:
        lines.append("失败提示：")
        for run_id, items in annotations.items():
            for item in items[:5]:
                message = str(item.get("message") or "").strip()
                path = item.get("path") or ""
                line = item.get("start_line") or ""
                location = f"{path}:{line}" if path and line else path
                lines.append(f"- {location} {message}".strip())
    return "\n".join(lines)


def write_json_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n", encoding="utf-8")


def write_markdown_report(path: Path, payload: dict[str, Any]) -> None:
    git = payload.get("git") or {}
    lines = [
        "# Tony Na Engine GitHub CI Status",
        "",
        f"- Repository: `{payload['repo']}`",
        f"- Commit: `{payload['shortSha']}`",
        f"- Status: `{payload['status']}`",
    ]
    if git:
        dirty = git.get("dirty") or {}
        lines.extend(
            [
                f"- Git sync: `{git.get('syncStatus', '')}`",
                f"- Git branch: `{git.get('branch', '')}` -> `{git.get('remoteBranch', '')}`",
                f"- Remote refresh: `{'updated' if git.get('remoteRefreshed') else 'not requested' if not git.get('remoteRefreshRequested') else 'failed'}`",
                f"- Local changes: `{dirty.get('total', 0)}`",
                f"- Ahead / behind: `{git.get('ahead', 0)} / {git.get('behind', 0)}`",
            ]
        )
    lines.extend(["", "| Check | Status | Conclusion | Link |", "| --- | --- | --- | --- |"])
    for run in payload["runs"]:
        link = f"[open]({run['detailsUrl']})" if run["detailsUrl"] else ""
        lines.append(f"| {run['name']} | {run['status']} | {run['conclusion'] or 'pending'} | {link} |")
    annotations = payload.get("annotations") or {}
    if annotations:
        lines.extend(["", "## Annotations"])
        for run_id, items in annotations.items():
            lines.append(f"### Check Run {run_id}")
            for item in items:
                lines.append(f"- `{item.get('path', '')}:{item.get('start_line', '')}` {item.get('message', '')}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_check_runs_from_file(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    return list(payload.get("check_runs") or payload.get("runs") or [])


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the GitHub Actions status for the current commit.")
    parser.add_argument("--repo", help="GitHub repository in owner/name form. Defaults to git remote origin.")
    parser.add_argument("--remote", default="origin", help="Git remote used to detect the repository.")
    parser.add_argument("--remote-branch", default="origin/main", help="Remote branch used for ahead/behind checks.")
    parser.add_argument("--sha", help="Commit SHA to check. Defaults to HEAD.")
    parser.add_argument("--fetch", action="store_true", help="Fetch the remote branch before local ahead/behind checks.")
    parser.add_argument("--skip-git", action="store_true", help="Only check GitHub Actions, without local Git sync details.")
    parser.add_argument("--watch", action="store_true", help="Wait until GitHub Actions finishes.")
    parser.add_argument("--interval", type=float, default=10.0, help="Polling interval when --watch is used.")
    parser.add_argument("--timeout", type=float, default=900.0, help="Maximum seconds to wait when --watch is used.")
    parser.add_argument("--json-report", type=Path, help="Write a machine-readable JSON report.")
    parser.add_argument("--markdown-report", type=Path, help="Write a human-readable Markdown report.")
    parser.add_argument("--input-json", type=Path, help="Use a saved GitHub check-runs payload instead of the network.")
    return parser.parse_args(argv)


def load_status_payload(args: argparse.Namespace) -> dict[str, Any]:
    repo = args.repo or detect_repo(args.remote)
    sha = args.sha or detect_sha()
    token = os.environ.get("GITHUB_TOKEN", "")
    deadline = time.time() + args.timeout
    git_snapshot = None if args.skip_git else get_git_snapshot(args.remote_branch, args.fetch)

    while True:
        if args.input_json:
            check_runs = read_check_runs_from_file(args.input_json)
        else:
            check_runs = fetch_check_runs(GitHubStatusRequest(repo=repo, sha=sha, token=token))
        status = classify_check_runs(check_runs)
        annotations = collect_annotations_for_failures(check_runs, token) if status == "failure" and not args.input_json else {}
        payload = build_status_payload(repo, sha, check_runs, annotations, git_snapshot)

        if not args.watch or status not in {"in_progress", "missing"}:
            return payload
        if time.time() >= deadline:
            return payload
        print(f"GitHub CI 仍在运行，{args.interval:.0f}s 后再查一次...")
        time.sleep(max(args.interval, 1.0))


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    payload = load_status_payload(args)
    print(format_status_text(payload))
    if args.json_report:
        write_json_report(args.json_report, payload)
    if args.markdown_report:
        write_markdown_report(args.markdown_report, payload)
    if payload["status"] == "success":
        return 0
    if payload["status"] == "failure":
        return 1
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
