# GitHub Actions Workflows (Agent Catalog)

Authoritative, agent-facing catalog of workflows in this repository. Use this when loading or modifying
workflows and keep it in sync with the files in this directory.

For a human-readable overview, see [README.md](README.md).

## Workflow catalog

| Workflow | Purpose | Key triggers / notes |
| -------- | ------- | -------------------- |
| [check.yml](check.yml) | Linting and quality gates via actionlint and pre-commit | push, pull_request, schedule; reusable via `workflow_call` |
| [cogni-ai-agent.yml](cogni-ai-agent.yml) | AI-assisted development via Cogni AI Agent | issue_comment, issues, pull_request, pull_request_review_comment; `workflow_call`; `workflow_dispatch` |
| [devcontainer-ci.yml](devcontainer-ci.yml) | Build/test devcontainer and required tools/packages | push/pull_request touching .devcontainer or workflow; schedule; `workflow_call` |
| [molecule.yml](molecule.yml) | Molecule tests for Ansible roles | push, pull_request; reusable via `workflow_call` |
| [test.yml](test.yml) | Run tests for the repository | push, pull_request |

## Details

### check.yml

- Purpose: run actionlint and pre-commit to enforce workflow and repo standards.
- Jobs: `actionlint`, `pre-commit`.

### cogni-ai-agent.yml

- Purpose: AI-assisted development automation triggered by issues, comments, and PRs.
- Reusable: `uses: Cogni-AI-OU/ansible-role-vastai_host/.github/workflows/cogni-ai-agent.yml@main`.
- Inputs: `model`, `prompt`.
- Requires `OPENCODE_API_KEY` secret.

### devcontainer-ci.yml

## Notes

- Keep this catalog updated when workflows are added, removed, or renamed.
