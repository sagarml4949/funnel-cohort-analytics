#!/usr/bin/env python
"""
deploy_github.py — publish this project to GitHub WITHOUT installing Git.

It talks to the GitHub REST API directly (Git Data API:
blobs -> tree -> commit -> ref update), so it works on machines where `git`
is not available. When it finishes you can point Streamlit Community Cloud
or Render at the new repo (see DEPLOYMENT.md, Options A and C).

Create a token first:
  * classic token with the `repo` scope, or
  * fine-grained token with "Contents: Read and write" plus
    "Administration: Read and write"
  -> https://github.com/settings/tokens

Usage
-----
  # 1. Dry run: lists every file that would be uploaded (no network calls at all)
  python deploy/deploy_github.py --repo funnel-cohort-analytics --dry-run

  # 2. Real deploy (token via --token or the GITHUB_TOKEN env var)
  python deploy/deploy_github.py --repo funnel-cohort-analytics --token ghp_xxx
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com"

# repo root = parent of this deploy/ folder
REPO_ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "env", ".idea", ".vscode", ".pytest_cache"}
SKIP_SUFFIXES = (".pyc", ".log", ".bak")
SKIP_FILES = {".streamlit/secrets.toml"}


def collect_files(root: Path = REPO_ROOT):
    """Return [(posix_relative_path, absolute_path)] for every file to publish."""
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith(SKIP_SUFFIXES):
                continue
            abs_path = Path(dirpath) / name
            rel = abs_path.relative_to(root).as_posix()
            if rel in SKIP_FILES:
                continue
            files.append((rel, abs_path))
    return files


def api(method: str, url: str, token: str, payload=None):
    """Call the GitHub API. Returns (status_code, parsed_json_body)."""
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "funnel-cohort-analytics-deploy")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"message": body}
        return exc.code, parsed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Publish this project to GitHub without git.")
    ap.add_argument("--repo", required=True, help="repository name to create or update")
    ap.add_argument("--owner", help="GitHub user/org (defaults to the token's own user)")
    ap.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"),
                    help="GitHub token (or set the GITHUB_TOKEN environment variable)")
    ap.add_argument("--branch", default="main", help="branch to publish (default: main)")
    ap.add_argument("--private", action="store_true", help="create the repo as private")
    ap.add_argument("--message", default="Add funnel & cohort analytics dashboard")
    ap.add_argument("--dry-run", action="store_true", help="list files only, no network calls")
    args = ap.parse_args(argv)

    files = collect_files()
    total = sum(p.stat().st_size for _, p in files)

    print(f"Repo root : {REPO_ROOT}")
    print(f"Branch    : {args.branch}")
    print(f"Files     : {len(files)} ({total / 1e6:.2f} MB)")
    for rel, abs_path in files:
        print(f"  {abs_path.stat().st_size:>10,} B  {rel}")

    if args.dry_run:
        print("\n[dry-run] No network calls made. Re-run without --dry-run to publish.")
        return 0

    if not args.token:
        print("\nERROR: a GitHub token is required. Pass --token or set GITHUB_TOKEN.",
              file=sys.stderr)
        return 2

    status, me = api("GET", f"{API}/user", args.token)
    if status != 200:
        print(f"\nERROR: token rejected ({status}): {me.get('message')}", file=sys.stderr)
        return 3
    owner = args.owner or me["login"]
    print(f"\nAuthenticated as {me['login']} -> publishing to {owner}/{args.repo}")

    status, repo = api("POST", f"{API}/user/repos", args.token,
                       {"name": args.repo, "private": args.private, "auto_init": True,
                        "description": "E-commerce funnel & cohort analytics dashboard (Streamlit)"})
    if status == 201:
        print(f"Created repository: {repo['html_url']}")
    elif status == 422:  # already exists -> update it instead
        status, repo = api("GET", f"{API}/repos/{owner}/{args.repo}", args.token)
        if status != 200:
            print(f"ERROR: cannot access {owner}/{args.repo} ({status}): {repo.get('message')}",
                  file=sys.stderr)
            return 4
        print(f"Repository already exists, updating: {repo['html_url']}")
    else:
        print(f"ERROR: could not create repo ({status}): {repo.get('message')}",
              file=sys.stderr)
        return 4

    # GitHub's Git Data API refuses to create blobs in a repo that has no commits
    # at all (409 "Git Repository is empty."), so seed one initial commit first.
    branch = args.branch
    status, ref = api("GET", f"{API}/repos/{owner}/{args.repo}/git/ref/heads/{branch}", args.token)
    if status != 200:
        seed = api("PUT", f"{API}/repos/{owner}/{args.repo}/contents/.gitkeep", args.token,
                   {"message": "Initialize repository",
                    "content": base64.b64encode(b"\n").decode()})
        if seed[0] not in (200, 201):
            print(f"ERROR: could not initialize the empty repo ({seed[0]}): "
                  f"{seed[1].get('message')}", file=sys.stderr)
            return 4
        branch = repo.get("default_branch") or branch
        print(f"Initialized empty repository on branch '{branch}'")

    # 1. upload every file as a blob
    tree = []
    for rel, abs_path in files:
        content = base64.b64encode(abs_path.read_bytes()).decode()
        status, blob = api("POST", f"{API}/repos/{owner}/{args.repo}/git/blobs", args.token,
                           {"content": content, "encoding": "base64"})
        if status not in (200, 201):
            print(f"ERROR: blob upload failed for {rel} ({status}): {blob.get('message')}",
                  file=sys.stderr)
            return 5
        tree.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    print(f"Uploaded {len(tree)} file blobs")

    # 2. assemble them into one tree
    status, new_tree = api("POST", f"{API}/repos/{owner}/{args.repo}/git/trees", args.token,
                           {"tree": tree})
    if status not in (200, 201):
        print(f"ERROR: tree creation failed ({status}): {new_tree.get('message')}",
              file=sys.stderr)
        return 6

    # 3. commit (with a parent if the branch already has history)
    parents = []
    status, ref = api("GET", f"{API}/repos/{owner}/{args.repo}/git/ref/heads/{branch}",
                      args.token)
    if status == 200:
        parents = [ref["object"]["sha"]]

    status, commit = api("POST", f"{API}/repos/{owner}/{args.repo}/git/commits", args.token,
                         {"message": args.message, "tree": new_tree["sha"], "parents": parents})
    if status not in (200, 201):
        print(f"ERROR: commit failed ({status}): {commit.get('message')}", file=sys.stderr)
        return 7

    # 4. create or fast-forward the branch
    if parents:
        status, ref = api("PATCH", f"{API}/repos/{owner}/{args.repo}/git/refs/heads/{branch}",
                          args.token, {"sha": commit["sha"]})
    else:
        status, ref = api("POST", f"{API}/repos/{owner}/{args.repo}/git/refs", args.token,
                          {"ref": f"refs/heads/{branch}", "sha": commit["sha"]})
    if status not in (200, 201):
        print(f"ERROR: could not update branch '{branch}' ({status}): {ref.get('message')}",
              file=sys.stderr)
        return 8

    print(f"\nDone. {owner}/{args.repo}@{branch} now has {len(tree)} files.")
    print(f"  Commit : {commit['sha'][:10]}")
    print(f"  Repo   : {repo['html_url']}")
    print("\nNext step (Streamlit Community Cloud):")
    print("  1. https://share.streamlit.io -> New app")
    print(f"  2. Repository: {owner}/{args.repo}   Main file path: dashboard/app.py")
    print("  3. Deploy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
