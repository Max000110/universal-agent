---
name: deep-think
description: Enables multi-step deep thinking reasoning policy wrap for AI models
command: deepthink
version: 1.0.0
---
# Deep Think Reasoning Skill

When enabled, the Deep Think skill injects a structured reasoning policy into every outgoing request.
It forces the active model to:
1. Break complex prompts into logical sub-components.
2. Evaluate potential edge cases and failure modes.
3. Validate output syntax and logic before outputting the final response.

Use `/deepthink on` to activate, or `/deepthink off` to disable.
