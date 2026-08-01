---
name: provider-status
description: Audits live health, model availability, and adapter state for ChatGPT and Gemini
command: provider-status
version: 1.0.0
---
# Provider Status Skill

This skill performs a diagnostic check across both provider adapters:
- Verifies session token presence in local encrypted vault.
- Probes model listing endpoints.
- Reports authentication status and connection health.

Trigger via `/users` or `/status`.
