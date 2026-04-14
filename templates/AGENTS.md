# AGENTS.md

Guidance for coding agents working in this directory.

## Setup

- Templates in this directory follow remote standards for Vast.ai services.
- Do not modify or edit templates without important justification.
- Do not perform syntax checks or linting on templates unless absolutely necessary.

## Additional key files

- vast_server.j2 - Main server configuration template
- vastai.service.j2 - Systemd service template
- environment.j2 - Environment variables template

## Debug tips

- If issues arise with templates, verify they match remote Vast.ai standards.
- Consult Vast.ai documentation before making changes.

## Directory-Specific Agent files

Read these Agent files when working in corresponding dirs:

- N/A

## Testing instructions

- N/A - Templates follow remote standards

## Troubleshooting

- Template rendering issues: Check variable definitions and Jinja2 syntax
- Service failures: Verify template matches Vast.ai service requirements

## Final notes

- Keep this Agent file up-to-date and relevant with the right context.
- Templates should only be modified with strong justification and after verifying compatibility with Vast.ai standards.
