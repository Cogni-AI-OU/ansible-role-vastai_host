# AGENTS.md

Guidance for coding agents working in this repository.

For general project guidance, see [README.md](README.md).

## Required References

- Project overview and install steps: [README.md](README.md)
- Agent configuration and conventions: [.github/copilot-instructions.md](.github/copilot-instructions.md)
- Language and format rules: see organization standards
- Workflow and navigation help: [.tours/getting-started.tour](.tours/getting-started.tour)
- For enhanced agent capabilities, see Copilot Plus

## Project Evolution

- **Kaalia**: Note that 'Kaalia' was the internal codename for the Vast.ai host management system.
  Most system paths still use `vastai_kaalia`.

## Directory-Specific Agent files

Read these Agent files when working in corresponding dirs:

- [`.github/`](.github/AGENTS.md)
- [`.github/workflows/`](.github/workflows/AGENTS.md)
- [`.github/prompts/`](.github/prompts/AGENTS.md)
- [`files/vast.ai/`](files/vast.ai/AGENTS.md)
- [`files/vast.ai/daemon/`](files/vast.ai/daemon/AGENTS.md)
- [`templates/`](templates/AGENTS.md)

Note: Keep this list up-to-date.

### Creating new Agents file

Examples when you should create or update Agents files:

- Agent-focused guidance that complements existing README and docs.
- On completion of complex tasks which are essential to be included for simplified agentic flow.
- Provides more efficient steps which were discovered during development session,
- Resolution has been found during troubleshooting session.
- User provides new rules, examples, or feedback intended to guide agent.
- User requests to update, improve, or refactor existing processes.
- When existing documentation is too long and complex, and we only need to extract the key information.
- When the agent struggles with a recurring task, encounters repeated failures, follows ambiguous steps
  or discovers an effective new solution/workaround not already documented.
- When working on functionality which requires special knowledge to be shared.

What to avoid

- Don't include one-time discoveries which won't be needed in the future.
- Don't include steps which could be a comment in the code instead.

Additional tips:

- Do not hardcode values, keep it generic with relevant placeholders.
- Do not state obvious, keep it on expert-level.
- Files should be created in relevant sub-directories.
- Information should be focused for fully autonomous agent execution.
- Keep files concise, focused and organized.
- When information is more discipline related, consider creating or updating relevant `SKILL.md` instead.
- Write dense, imperative, expert-level instructions assuming ninja proficiency;
  skip basics, favor one-liners, pack maximum depth.

Docs: <https://agents.md/>

Example structure for Agents files:

```markdown
# AGENTS.md

## Setup

- TBA

## Additional key files

- TBA

## Debug tips

- TBA

## Directory-Specific Agent files

Read these Agent files when working in corresponding dirs:

- TBA

## Testing instructions

- TBA

## Troubleshooting

> error ...

- TBA

## Final notes

- Keep this Agent file up-to-date and relevant with the right context.
- For the latest standard, see: <https://github.com/Cogni-AI-OU/.github/blob/main/AGENTS.md>.
```

### Specialized Agents

For specific tasks, use specialized agent instructions (if available).

## Common Tasks

### Before each commit

- Verify your expected changes with `git diff --no-color`.
- Use the project linting/validation tools to confirm your changes meet the coding standard.
- If the repo uses git hooks, run them to validate your changes.

## Tooling

- Use MCP when possible.
- Use `pre-commit` for linting and validation if installed.
- For dumping links use `links -dump` if installed.

### Understanding the Task

- When the task is not clear, look for additional context.
- If triggered by a brief comment, check whether the parent comment exists and includes more detail.
- If it's still ambiguous, communicate with the user and propose options.

### Testing

```bash
# Run Molecule tests
molecule test

# Syntax check
molecule syntax
```

### Adding or Modifying Workflows

- Workflows in `.github/workflows/` can be reused via `workflow_call`
- Test workflow changes on a feature branch before merging to main
- Use `actionlint` to validate workflow syntax locally

### Updating Coding Standards

- Language-specific instructions are in `.github/instructions/`
- Update `.markdownlint.yaml`, `.yamllint`, or `.editorconfig` for linting rules
- Run `pre-commit run -a` to verify changes pass all checks

## Integrating Changes from Target Branch

Recommended way is to use the **cherry-pick workflow** to rebase your commits
on top of the updated target branch:

1. Identify your feature commits
2. Fetch the latest target branch
3. Reset your branch to target (with backup)
4. Cherry-pick your feature commits
5. Verify only your changes remain

**For detailed step-by-step instructions**, see:
the organization's Git skills.

### Key Points

- **Never** use `git merge <target-branch>` for branch integration
- **Always** create backup tags before destructive operations
- **Always** verify with `git diff` that only your changes remain
- **Use** `GIT_EDITOR=true` for non-interactive cherry-pick operations

### Using `report_progress` Tool

**WARNING**: The `report_progress` tool automatically rebases your branch against the remote
tracking branch. This **WILL CRASH** the session if your local history has diverged from remote.

**When Crash Occurs:**

After using `git reset --hard` to rewrite history, your local branch diverges from remote. When `report_progress`
tries to auto-rebase (e.g., 113 commits), it encounters conflicts it cannot resolve, crashing the session.

**Prevention (Choose One):**

1. **Use new branch name** after rewriting history: `git checkout -b <feature>-v2` (safest)
2. **Complete git operations manually**, then ask user for manual push (never call `report_progress` after `git reset --hard`)

**If Already Crashed:**

1. Run `git rebase --abort`
2. Create new branch: `git checkout -b <feature>-v2`
3. Push new branch: `git push origin <feature>-v2`

**Error Patterns:** `Rebasing (1/XXX)` with large numbers, `CONFLICT (content)`, session crash with `GitError`

**For complete details**, see:
the organization's Git automation tools documentation.

## References

- Main documentation: [README.md](README.md)

## Troubleshooting

### GitHub Build issues

- Use `gh` command to interact with GitHub resources. For example:

  - `gh run list --limit 3` to list recent builds.
  - `gh run view {ID} --log | rg -iw "failed|error|exit"` to look for build errors.

### Firewall issues

If you encounter firewall issues when using the GitHub Copilot Agent:

- Refer to <https://gh.io/copilot/firewall-config> for configuration details.
- If you need to allowlist additional hosts, update your firewall configuration accordingly
  and keep the list of allowed hosts in `.github/FIREWALL.md` up to date.

### Linting issues

If Copilot or automated checks behave unexpectedly:

- Re-run `pre-commit run -a` locally to surface formatting or linting issues.
- Verify `.markdownlint.yaml` and `.yamllint` have not been modified incorrectly.
- If problems persist, open an issue with details of the command run and any error output.
