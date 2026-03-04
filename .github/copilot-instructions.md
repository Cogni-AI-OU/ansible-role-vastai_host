# Copilot Instructions

## Project Overview

This is an Ansible role template repository. It provides standardized structure,
GitHub Actions workflows, issue/PR templates, and coding standards for creating
reusable Ansible roles.

Key contents:

- **Ansible role structure**: Standard role directories (tasks, handlers, templates, defaults, vars, meta)
- **CI/CD workflows**: Pre-commit checks, linting, Molecule testing
- **Agent configurations**: `AGENTS.md`, `CLAUDE.md` for AI coding assistants

### Getting started

- Refer to the `README.md` in the project root for setup and installation instructions.
- Check also `.tours/getting-started.tour` which provides a guided walkthrough of key project features and structure.

## Coding Standards

### Python

- Use **Python 3.11+**.
- Use `uv` script headers for dependency management:

  ```python
  #!/usr/bin/env -S uv run --script
  # /// script
  # requires-python = ">=3.11"
  # dependencies = [
  #     "xero-python",
  #     "PyYAML",
  # ]
  # ///
  ```

- Follow **PEP 8** style guidelines.
- Use `argparse` for CLI argument parsing.
- Handle `BrokenPipeError` for CLI tools that might be piped to `head` or `grep`.

## Formatting Guidelines

### JSON

Follow the JSON rules in `.github/instructions/json.instructions.md`, which mirror the repository `.editorconfig` configuration.

To test locally, use `jq` for validation or use the VS Code JSON formatter.

### Markdown

Follow the Markdown rules in `.github/instructions/markdown.instructions.md`, which mirror the repository markdownlint configuration.

To test locally, run via `pre-commit run markdownlint -a` or use the VS Code Markdownlint extension.

### YAML

Follow the YAML rules in `./.github/instructions/yaml.instructions.md`, which mirror the repository `.yamllint` configuration.

Notes:

- Project utilizes Codespaces with config at `.devcontainer/devcontainer.json` and requirements at `.devcontainer/requirements.txt`.
- GitHub Actions run pre-commit checks (`.pre-commit-config.yaml`).
- To verify locally, run `pre-commit run yamllint -a` from the repo root.

## Project Structure

```text
.
├── .github/
│   ├── ISSUE_TEMPLATE/      # Issue templates (bug reports, feature requests)
│   ├── agents/              # AI agent configurations
│   ├── instructions/        # Language-specific coding standards
│   ├── skills/              # Agent skills definitions
│   ├── workflows/           # GitHub Actions workflows
│   ├── copilot-instructions.md
│   └── pull_request_template.md
├── .tours/                  # VS Code guided tours
├── defaults/                # Default role variables
├── handlers/                # Handler tasks
├── meta/                    # Role metadata and dependencies
├── molecule/                # Molecule test scenarios
├── tasks/                   # Main role tasks
├── templates/               # Jinja2 templates
├── vars/                    # Role variables
├── AGENTS.md                # AI agent guidance
├── CLAUDE.md                # Claude-specific configuration
└── README.md                # Repository documentation
```

### Tours

- Keep the `.tours` folder up-to-date (especially `.tours/getting-started.tour`)
  when making significant changes to the codebase.
  Update existing tours or create new ones to reflect changes in project structure,
  workflows, or key files.

## Troubleshooting

### Finding Build Errors

To identify and diagnose the latest build errors:

1. **Reproduce errors locally:**
   - For pre-commit errors: Run `pre-commit run -a` to check all files
   - For specific hooks: Run `pre-commit run <hook-name> -a` (e.g., `markdownlint`, `yamllint`)
   - For actionlint errors: Install actionlint and run it on workflow files

2. **Common error patterns:**
   - **Markdown linting errors:** Check `.markdownlint.yaml` for rules; errors show line numbers
   - **YAML linting errors:** Check `.yamllint` for rules; verify indentation and structure
   - **JSON formatting errors:** Use `jq . <file>` to validate JSON syntax
