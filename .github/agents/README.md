# Custom Agents

This folder contains custom agents designed to enhance your development workflow.
These agents are tailored to specific tasks and integrate seamlessly with GitHub Copilot and MCP servers.

## Available Agents

### [Cogni AI Architect](cogni-ai-architect.agent.md)

Elite autonomous neurosymbolic architect. Features:

- Recursive problem decomposition and zero-defect invariants
- Structural perfection and conceptual integrity
- Strategic deep-module scaling

### [Code Tour Expert](code-tour.agent.md)

Expert agent for creating and maintaining VSCode CodeTour files. Features:

- Creating `.tours/` files with proper CodeTour schema
- Designing step-by-step walkthroughs for complex codebases
- Implementing interactive tours with command links and code snippets
- Setting up primary tours and tour linking sequences

**When to use**: Anytime you need to create or update `.tour` files for repository onboarding.

## How to Use Custom Agents

### Installation

- Download the desired agent configuration file (`*.agent.md`) and add it to your repository.
- Use the Copilot CLI for local testing: [Copilot CLI](https://gh.io/customagents/cli).
- Merge the agent configuration file into the default branch of your repository.
- Access installed agents through the VS Code Chat interface, Copilot CLI,
  or assign them in Copilot Coding Agent (CCA).

For more details, see:

- [About custom agents](https://gh.io/customagents)
- [Custom Agents Documentation](https://gh.io/customagents/config).
- [Create custom agents](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents)
- [Copilot CLI](https://gh.io/customagents/cli)
- [GitHub Awesome Copilot repository](https://github.com/github/awesome-copilot)
- [Supported Models](https://docs.github.com/en/copilot/reference/ai-models/supported-models)

## Customizing development environment

See: [Customizing the development environment for GitHub Copilot coding agent][customize-env].

## Firewall

See: [Customizing or disabling the firewall for GitHub Copilot coding agent][firewall-config].

### Firewall allowlist

See [FIREWALL.md](FIREWALL.md) for recommended hosts to allow and the official guidance link.

<!-- Named links -->

[customize-env]: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-environment
[firewall-config]: https://gh.io/copilot/firewall-config

### MCP Server Setup

Some agents require MCP servers to function. You can add custom MCP servers for additional integrations.

**Important notes:**

- File-based config cannot use GitHub Actions secrets (`${{ secrets.* }}`). Use
  inline config for secrets.
- HTTP-based MCP servers (using `"type": "http"`) may work with inline config
  but can fail with file-based config due to how the process loads
  external files.

Follow the instructions in the agent's documentation to configure the necessary MCP servers.

## Troubleshooting
