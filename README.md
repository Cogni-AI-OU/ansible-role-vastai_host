# Ansible Role: Template

[![PR Reviews][pr-reviews-image]][pr-reviews-link]
[![License][license-image]][license-link]

This is a template role.
Use it as starting point to create your own role.

## Getting Started

🗺️ **New to this repository?** Take the [**CodeTour**](.tours/getting-started.tour) to explore the project structure!

To view the tour:

1. Install the [CodeTour extension](https://marketplace.visualstudio.com/items?itemName=vsls-contrib.codetour) in VS Code
2. Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
3. Run "CodeTour: Start Tour"

Or simply open this repository in a devcontainer - the extension is pre-configured!

## Requirements

This role requires:

- Ansible
- Python
- Administrative/root access on target hosts
- One of the following operating systems:
  - Alpine Linux
  - Debian/Ubuntu
  - NixOS or systems with Nix package manager

## Install

To install this role, you can use the following terminal command:

```shell
ansible-galaxy install git+https://github.com/Cogni-AI-OU/ansible-role-template.git
```

## Role Variables

For available variables,
check [`defaults/main.yml`](defaults/main.yml).

## Testing

### Docker

Steps to test role on Docker containers.

1. Install the current role by running the following commands in shell:

    ```shell
    ansible-galaxy install -r requirements.yml
    jinja2 requirements-local.yml.j2 -D "pwd=$PWD" -o requirements-local.yml
    ansible-galaxy install -r requirements-local.yml
    ```

    Alternatively, for development purposes, you can consider using symbolic link, e.g.

    ```shell
    ln -vs "$PWD" ~/.ansible/roles/cogni-ai.template
    ```

2. Ensure Docker service (e.g. Docker Desktop) is running.
3. Run playbook from `tests/`:

    ```shell
    ansible-playbook -i tests/inventory/docker-containers.yml tests/playbooks/docker-containers.yml
    ```

4. Run the verify-tag playbook (stops containers after verification):

  ```shell
  ansible-playbook -i tests/inventory/docker-containers.yml tests/playbooks/tags/verify.yml --tags verify
  ```

### Molecule

To test using Molecule, run:

```shell
molecule test
```

## Development

### Setup

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Install Python dependencies (for devcontainer)
pip install -r .devcontainer/requirements.txt
```

### Testing and Validation

```bash
# Run all pre-commit checks
pre-commit run -a

# Run specific checks
pre-commit run markdownlint -a
pre-commit run yamllint -a
pre-commit run black -a
pre-commit run flake8 -a
```

## AI Agents

This repository provides AI agent configurations for automated development.

### Agent Configuration Files

| File/Directory | Audience | Purpose |
| -------------- | -------- | ------- |
| [AGENTS.md](AGENTS.md) | All agents | Repository-specific guidance and workflows |
| [CLAUDE.md](CLAUDE.md) | Claude | Claude-specific configuration |
| [.github/copilot-instructions.md](.github/copilot-instructions.md) | Copilot | Coding standards and project context |
| [.github/agents/](.github/agents/) | Orchestrators | Specialized agent configs for specific tasks |
| [.github/skills/](.github/skills/) | All agents | Reusable capabilities (git, GitHub Actions, etc.) |
| [.github/prompts/](.github/prompts/) | All | Prompt templates (`.md` for VSCode, `.yaml` for GitHub Models) |
| [.github/instructions/](.github/instructions/) | Linters & agents | Language-specific code standards |

See also:

- [`AGENTS.md` file format specification](https://agents.md/)
- [Best practices for using GitHub Copilot](https://gh.io/copilot-coding-agent-tips).

## GitHub Actions

For documentation on GitHub Actions workflows, problem matchers, and CI/CD
configuration, see [.github/README.md](.github/README.md).

<!-- Named links -->

[pr-reviews-image]: https://img.shields.io/github/issues-pr/Cogni-AI-OU/ansible-role-template?label=PR+Reviews&logo=github
[pr-reviews-link]: https://github.com/Cogni-AI-OU/ansible-role-template/pulls
[license-image]: https://img.shields.io/badge/License-MIT-blue.svg
[license-link]: LICENSE
