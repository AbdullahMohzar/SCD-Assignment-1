#!/usr/bin/env python3
"""CivicPulse - Submission Pre-Flight Lint & Sanity Checker (§5.8)

Validates compliance against assignment specifications and automatic deduction traps:
- Required files and directories presence (§5.7)
- Sensitive secret and .env leakage checks (§5.3)
- Dockerfile base image pinning and non-root USER enforcement (§3.1)
- Compose production network segmentation and port protection (§3.2)
- Kubernetes manifest validation (StatefulSet, ClusterIP, Probes, placeholders) (§3.3)
- CI/CD workflow gating rules (needs:, immutable references, least privilege) (§3.4)
- Documentation and ADR verification (§4, §5.2)
"""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

errors = 0
warnings = 0


def log_pass(msg: str) -> None:
    print(f"[{GREEN}PASS{RESET}] {msg}")


def log_fail(msg: str) -> None:
    global errors
    errors += 1
    print(f"[{RED}FAIL{RESET}] {msg}")


def log_warn(msg: str) -> None:
    global warnings
    warnings += 1
    print(f"[{YELLOW}WARN{RESET}] {msg}")


def check_file_exists(rel_path: str, critical: bool = True) -> bool:
    target = ROOT / rel_path
    if target.exists():
        log_pass(f"Found {rel_path}")
        return True
    if critical:
        log_fail(f"Missing required file: {rel_path}")
    else:
        log_warn(f"Recommended file missing: {rel_path}")
    return False


def check_secrets_and_env() -> None:
    print(f"\n{BOLD}{BLUE}--- Checking Secrets & Leaks (§5.3) ---{RESET}")
    # 1. Check for real .env committed
    if (ROOT / ".env").exists():
        log_fail(".env file found in repository root! Must be gitignored.")
    else:
        log_pass("No committed .env file found in root.")

    # 2. Check gitignore contains .env
    gitignore = ROOT / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8", errors="ignore")
        if ".env" in content:
            log_pass(".gitignore explicitly excludes .env")
        else:
            log_fail(".gitignore does NOT exclude .env")
    else:
        log_fail(".gitignore file does not exist")

    # 3. Check for obvious API key leaks in repository files (excluding git, tests, docs)
    suspicious_patterns = [
        re.compile(r"gsk_[a-zA-Z0-9]{20,}", re.IGNORECASE),
        re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}", re.IGNORECASE),
        re.compile(r"ghp_[a-zA-Z0-9]{36}", re.IGNORECASE),
    ]

    for root, dirs, files in os.walk(ROOT):
        # Ignore git, node_modules, and venv
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache"}]
        for f in files:
            p = Path(root) / f
            if p.suffix in {".py", ".yaml", ".yml", ".json", ".ts", ".tsx", ".md"}:
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    for pattern in suspicious_patterns:
                        match = pattern.search(text)
                        if match and "placeholder" not in match.group(0).lower() and "example" not in str(p).lower():
                            log_fail(f"Potential real API key matched in {p.relative_to(ROOT)}: {match.group(0)[:8]}...")
                except Exception:
                    pass


def check_docker_compose() -> None:
    print(f"\n{BOLD}{BLUE}--- Checking Docker Compose Files (§3.2, §5.3) ---{RESET}")
    compose_dev = ROOT / "compose.yaml"
    compose_prod = ROOT / "compose.prod.yaml"

    if compose_dev.exists():
        content = compose_dev.read_text(encoding="utf-8", errors="ignore")
        if "internal: true" in content or "internal:true" in content:
            log_pass("compose.yaml configures internal: true network")
        else:
            log_fail("compose.yaml lacks internal: true network isolation")

        if "volumes:" in content and "pgdata:" in content and "redisdata:" in content:
            log_pass("compose.yaml configures named volumes (pgdata, redisdata)")
        else:
            log_fail("compose.yaml missing required named volumes")

    if compose_prod.exists():
        content = compose_prod.read_text(encoding="utf-8", errors="ignore")
        if "build:" in content:
            log_fail("compose.prod.yaml must not contain 'build:' keys (must use image: ${IMAGE_TAG})")
        else:
            log_pass("compose.prod.yaml contains no 'build:' directives")

        # Check published ports for database and redis in prod
        # Database ports 5432:5432 or "5432" under database
        db_block = re.search(r"database:\s*(.*?)(?=\n\s*[a-zA-Z0-9_-]+:|$)", content, re.DOTALL)
        if db_block and "ports:" in db_block.group(1):
            log_fail("compose.prod.yaml exposes ports on database container! (-8 marks)")
        else:
            log_pass("compose.prod.yaml does not expose database ports to host")

        redis_block = re.search(r"cache:\s*(.*?)(?=\n\s*[a-zA-Z0-9_-]+:|$)", content, re.DOTALL)
        if redis_block and "ports:" in redis_block.group(1):
            log_fail("compose.prod.yaml exposes ports on redis cache container! (-8 marks)")
        else:
            log_pass("compose.prod.yaml does not expose redis ports to host")


def check_dockerfiles() -> None:
    print(f"\n{BOLD}{BLUE}--- Checking Dockerfiles & Multi-Stage Builds (§3.1, §5.3) ---{RESET}")
    backend_df = ROOT / "backend" / "Dockerfile"
    frontend_df = ROOT / "frontend" / "Dockerfile"

    if backend_df.exists():
        text = backend_df.read_text(encoding="utf-8", errors="ignore")
        if "FROM python:3" in text and ":latest" not in text:
            log_pass("backend/Dockerfile uses pinned Python base image")
        else:
            log_fail("backend/Dockerfile does not use pinned Python base image")

        if "USER " in text:
            log_pass("backend/Dockerfile specifies non-root USER")
        else:
            log_fail("backend/Dockerfile does not declare non-root USER")

        if "HEALTHCHECK " in text:
            log_pass("backend/Dockerfile declares HEALTHCHECK")
        else:
            log_fail("backend/Dockerfile missing HEALTHCHECK")

    if frontend_df.exists():
        text = frontend_df.read_text(encoding="utf-8", errors="ignore")
        if "FROM node:" in text and "FROM nginx:" in text:
            log_pass("frontend/Dockerfile uses multi-stage Node build -> Nginx serve")
        else:
            log_fail("frontend/Dockerfile missing multi-stage pattern (node -> nginx)")


def check_k8s_manifests() -> None:
    print(f"\n{BOLD}{BLUE}--- Checking Kubernetes Manifests (§3.3, §5.3) ---{RESET}")
    k8s_base = ROOT / "k8s" / "base"
    postgres_yaml = k8s_base / "postgres.yaml"
    secret_yaml = k8s_base / "secret.yaml"
    hpa_yaml = k8s_base / "hpa.yaml"

    if postgres_yaml.exists():
        content = postgres_yaml.read_text(encoding="utf-8", errors="ignore")
        if "kind: StatefulSet" in content:
            log_pass("PostgreSQL uses StatefulSet")
        else:
            log_fail("PostgreSQL must be a StatefulSet, not a Deployment (-8 marks)")
        if "volumeClaimTemplates:" in content:
            log_pass("PostgreSQL StatefulSet defines volumeClaimTemplates")
        else:
            log_fail("PostgreSQL StatefulSet missing volumeClaimTemplates")

    if secret_yaml.exists():
        content = secret_yaml.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"gsk_[a-zA-Z0-9]+", content) or "AIzaSy" in content:
            log_fail("k8s/base/secret.yaml contains live API credentials! Must contain placeholders.")
        else:
            log_pass("k8s/base/secret.yaml contains placeholders only")

    if hpa_yaml.exists():
        content = hpa_yaml.read_text(encoding="utf-8", errors="ignore")
        if "apiVersion: autoscaling/v2" in content and "HorizontalPodAutoscaler" in content:
            log_pass("HPA manifest correctly declared autoscaling/v2")
        else:
            log_fail("HPA manifest incorrect or not autoscaling/v2")


def check_cicd_workflows() -> None:
    print(f"\n{BOLD}{BLUE}--- Checking CI/CD Workflows (§3.4, §5.3) ---{RESET}")
    ci_yml = ROOT / ".github" / "workflows" / "ci.yml"
    cd_yml = ROOT / ".github" / "workflows" / "cd.yml"

    if ci_yml.exists():
        content = ci_yml.read_text(encoding="utf-8", errors="ignore")
        for expected in ["lint-and-type", "test-backend", "test-frontend", "scan", "manifests", "integration"]:
            if expected in content:
                log_pass(f"ci.yml contains required job: {expected}")
            else:
                log_fail(f"ci.yml missing required job: {expected}")

    if cd_yml.exists():
        content = cd_yml.read_text(encoding="utf-8", errors="ignore")
        if "needs: test" in content or "needs: [test]" in content:
            log_pass("cd.yml publishing/deploying job is gated by 'needs:'")
        else:
            log_fail("cd.yml publishing job must be gated by 'needs:' (-8 marks)")

        if ":latest" in content and "${{ github.sha }}" not in content:
            log_fail("cd.yml deploys :latest tag (-8 marks). Must deploy immutable commit SHA.")
        else:
            log_pass("cd.yml deploys by immutable reference (commit SHA)")


def check_docs() -> None:
    print(f"\n{BOLD}{BLUE}--- Checking Documentation & ADRs (§4, §5.2) ---{RESET}")
    adrs = [
        "docs/adr/0001-provider-interface.md",
        "docs/adr/0002-frontend-runtime-config.md",
        "docs/adr/0003-deploy-by-sha.md",
        "docs/adr/0004-pii-and-data-governance.md",
    ]
    for adr in adrs:
        check_file_exists(adr)

    check_file_exists("docs/ENGINEERING-NOTES.md")
    check_file_exists("docs/RUNBOOK.md")
    check_file_exists("docs/AI-USAGE.md")
    check_file_exists("docs/TRIAGE.md")
    check_file_exists("README.md")


def main() -> int:
    print(f"{BOLD}=== CivicPulse Pre-Submission Verification Lint ==={RESET}")
    check_secrets_and_env()
    check_docker_compose()
    check_dockerfiles()
    check_k8s_manifests()
    check_cicd_workflows()
    check_docs()

    print(f"\n{BOLD}=== Summary ==={RESET}")
    print(f"Total Errors:   {RED if errors else GREEN}{errors}{RESET}")
    print(f"Total Warnings: {YELLOW if warnings else GREEN}{warnings}{RESET}")

    if errors > 0:
        print(f"\n{RED}{BOLD}Pre-flight check failed! Address errors above before submitting.{RESET}")
        return 1
    print(f"\n{GREEN}{BOLD}Pre-flight check passed! All structural and safety checks clean.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
