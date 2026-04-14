# GitHub Actions Workflows (Agent Catalog)

Authoritative, agent-facing catalog of workflows in this repository. Use this when loading or modifying
workflows and keep it in sync with the files in this directory.

For a human-readable overview, see [README.md](README.md).

## Workflow catalog

| Workflow | Purpose | Key triggers / notes |
| -------- | ------- | -------------------- |
| [check.yml](check.yml) | Linting and quality gates via actionlint and pre-commit | push, pull_request, schedule; reusable via `workflow_call` |
| [devcontainer-ci.yml](devcontainer-ci.yml) | Build/test devcontainer and required tools/packages | push/pull_request touching .devcontainer or workflow; schedule; `workflow_call` |
| [opencode.yml](opencode.yml) | AI-assisted development via OpenCode | issue_comment, issues, pull_request_review, pull_request_review_comment; `workflow_call`; `workflow_dispatch` |
| [opencode-review.yml](opencode-review.yml) | Automated PR review using OpenCode | issue_comment, pull_request, pull_request_target, pull_request_review_comment; `workflow_call`; `workflow_dispatch` |

## Details

### check.yml

- Purpose: run actionlint and pre-commit to enforce workflow and repo standards.
- Reusable: `uses: Cogni-AI-OU/.github/.github/workflows/check.yml@main`.
- Jobs: `actionlint`, `pre-commit`.

### devcontainer-ci.yml

- Purpose: build and validate the dev container; ensure required tools and Python packages exist.
- Inputs: `required_commands` (defaults to common CLI tools), `required_python_packages`
  (defaults to ansible, ansible-lint, docker, molecule, pre-commit, uv).
- Triggers: pull_request/push affecting `.devcontainer/` or this workflow; weekly schedule;
  `workflow_call`.
- Permissions: callers must grant `packages: write` when pushing images to GHCR.
- Reusable: `uses: Cogni-AI-OU/.github/.github/workflows/devcontainer-ci.yml@main`.

### opencode.yml

- Purpose: AI-assisted development automation triggered by issues, comments, and PR reviews.
- Reusable: `uses: Cogni-AI-OU/.github/.github/workflows/opencode.yml@main`.
- Inputs: `agent`, `model`, `issue_number`, `prompt` (all optional).
- Requires `OPENCODE_API_KEY` secret.

### opencode-review.yml

- Purpose: Automated PR review using OpenCode, including fork PRs via `pull_request_target`.
- Reusable: `uses: Cogni-AI-OU/.github/.github/workflows/opencode-review.yml@main`.
- Inputs: `pr_number` (required for `workflow_call`/`workflow_dispatch`).
- Requires `OPENCODE_API_KEY` secret.

## Notes

- Follow [.github/instructions/github-workflows.instruction.md](../instructions/github-workflows.instruction.md)
  when editing workflow files (ordering, formatting, validation).
- Keep this catalog updated when workflows are added, removed, or renamed.
