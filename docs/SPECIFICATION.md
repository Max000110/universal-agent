# Antigravity CLI — Engineering Specification & Architecture Plan (Phase 0)

## 1. Overview & Product Goals
**Antigravity CLI** is a local-first, terminal-native agentic framework CLI designed to run cleanly on both **Ubuntu** and **Termux** (Android). It mimics the surface experience, multi-step reasoning, slash command structure, and skills system of Antigravity 2.0 while replacing standard OAuth flows with explicit user-owned **Session Cookie Bootstrap** (supporting both Cookie Header String and JSON formats).

### Key Objectives:
- **Local-First & Private**: Encryption at rest for session vault secrets; zero cloud telemetry or third-party credential reporting.
- **Dual-Provider Architecture**: First-class, isolated adapters for **ChatGPT** and **Gemini**.
- **Flexible Cookie Bootstrap**: Support both Cookie Header strings (`session_token=...`) and JSON blobs.
- **Deep Think as a Policy Mode**: Deep thinking wrapped as a request/reasoning policy applicable across any supported model.
- **Termux First, Ubuntu Second**: Zero dependency on desktop GUI, systemd, or root privileges.
- **Antigravity Skills Compatibility**: Folder-based `SKILL.md` discovery and execution.

---

## 2. User Flow & Onboarding Lifecycle
1. **Installation**: Single bash execution (`install.sh`) setting up a virtual environment and `antigravity` executable.
2. **First Launch**: Automatically detects existing configuration or prompts for session import.
3. **Session Import (`/session import`)**:
   - User selects target provider (`ChatGPT` or `Gemini`).
   - System prompts for session cookie data (accepts raw Cookie Header string OR JSON format).
   - Strict validation checks input shape, required tokens, non-empty values, and provider match.
   - Encrypts and writes secret payload to local vault (`~/.antigravitycli/vault.enc`).
4. **Session Bootstrap & Health Check**:
   - Decrypts local vault in memory.
   - Executes lightweight health probe against provider endpoint.
   - Initializes active model and populates `ModelRegistry`.
5. **Interactive TUI Session**:
   - Displays live status bar (Provider, Model, Deep-Think state, Context usage, Quota, Session Health).
   - Processes prompt inputs or slash commands seamlessly.

---

## 3. Command System & Map

| Slash Command | Input Parameters | Description / Display Output | Failure Handling |
| :--- | :--- | :--- | :--- |
| `/users` | None | Displays active provider sessions, account label, validation status, and remaining quota. | Reports unauthenticated providers clearly. |
| `/context` | None | Shows current model context window limit, token usage, and remaining context budget. | Fallback to estimated character metrics if token counts are unavailable. |
| `/models` | `[filter]` | Lists available models for active provider with deep-think & context capability tags. | Shows cached model list if network probe fails. |
| `/model` | `<model_name>` | Switches active model dynamically without restarting app or clearing chat state. | Reverts to previous model if target is invalid/unsupported. |
| `/deepthink` | `on\|off\|toggle` | Toggles reasoning policy wrap on outgoing prompts. | Validates state parameter; defaults to toggle if omitted. |
| `/skills` | `[search]` | Scans and lists installed built-in and user skills with metadata. | Ignores malformed skill files with warning log. |
| `/skill` | `<name>` | Views detailed metadata, usage guide, and options for specified skill. | Shows "Skill not found" message. |
| `/session validate` | `[provider]` | Runs live health probe on stored cookies and reports status. | Prompts re-import if session expired/invalid. |
| `/session import` | `[provider]` | Triggers interactive cookie import flow (Header string or JSON). | Rejects invalid cookies before persisting. |
| `/status` | None | Shows overall system health, vault state, active provider, model, and platform runtime. | Displays degraded state indicators. |
| `/help` | `[command]` | Renders command palette and detailed documentation. | Displays full command list if specific command is unknown. |

---

## 4. Provider Abstraction Layer

```
                     ┌───────────────────────────┐
                     │   BaseProviderAdapter     │
                     └─────────────┬─────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
   ┌────────────────────┐                    ┌────────────────────┐
   │  ChatGPTAdapter    │                    │   GeminiAdapter    │
   └────────────────────┘                    └────────────────────┘
```

### Shared Adapter Interface:
```python
class BaseProviderAdapter(ABC):
    @abstractmethod
    async def validate_session(self, session_data: dict) -> SessionHealth: ...
    
    @abstractmethod
    async def list_models(self) -> List[ModelInfo]: ...
    
    @abstractmethod
    async def get_quota(self) -> QuotaInfo: ...
    
    @abstractmethod
    async def get_context_window(self, model_name: str) -> ContextInfo: ...
    
    @abstractmethod
    async def stream_chat(self, messages: List[ChatMessage], model: str, deep_think: bool) -> AsyncGenerator[str, None]: ...
    
    @abstractmethod
    async def health_check(self) -> bool: ...
```

---

## 5. Session Vault & Security Architecture

### Vault File Structure (`~/.antigravitycli/`)
- `config.json`: Non-sensitive settings (active provider, active model, deepthink toggle, theme).
- `vault.enc`: AES-256-GCM / Fernet encrypted master payload containing provider session cookies.
- `vault.key`: Local key file protected with `0600` filesystem permissions (or derived via device machine-id/salt).
- `skills/`: Directory for user-installed custom skills.

### Redaction Policy Engine
A custom logging filter (`RedactingFilter`) redacts all patterns matching:
- Cookie headers (`Cookie: ...`, `Set-Cookie: ...`, `session_token=...`)
- Bearer tokens (`Bearer ...`)
- JSON secret keys (`"session_token"`, `"cookie"`, `"access_token"`, `"api_key"`)
- Raw HTTP header dumps containing authorization fields.

---

## 6. Skills Framework

Folder structure for skills:
```
skills/
└── deep-think/
    ├── SKILL.md
    └── resources/
```

### `SKILL.md` Schema:
```markdown
---
name: deep-think
description: Enables enhanced multi-step chain-of-thought reasoning policy
command: deep-think
version: 1.0.0
---
# Deep Think Skill
Instructions and systemic prompt modifiers for deep thinking...
```

---

## 7. Terminal User Interface (TUI) Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Antigravity CLI v1.0.0 [ChatGPT / gpt-4o]                      [DeepThink: ON]│
├─────────────────────────────────────────────────────────────────────────────┤
│ > /models                                                                   │
│ Available Models for ChatGPT:                                               │
│   - gpt-4o (Active, 128k context, Reasoning supported)                      │
│   - gpt-4o-mini (128k context)                                              │
│   - o3-mini (200k context, DeepReasoning)                                  │
│                                                                             │
│ > Hello! Analyze this code architecture for Termux compatibility.          │
│ Assistant: Certainly! Here is a structured analysis...                      │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Provider: ChatGPT] [Model: gpt-4o] [Think: ON] [Context: 1.2k/128k] [Quota: OK]│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Platform Support & Constraints Matrix

| Feature / Subsystem | Ubuntu (Workstation/Server) | Termux (Android POSIX) |
| :--- | :--- | :--- |
| TUI Rendering | Rich full panel & status bar | Rich layout with auto-fallback to basic text mode if width < 60 |
| Vault Path | `~/.antigravitycli/vault.enc` | `~/.antigravitycli/vault.enc` (Internal app space) |
| Dependencies | Pure Python (`typer`, `rich`, `httpx`, `cryptography`, `pydantic`) | Pure Python (Same, standard `pip install` without compilation dependencies) |
| Process Mgmt | Direct CLI / Background daemon optional | Direct CLI process (Zero systemd dependency) |

---

## 9. Acceptance Criteria (Phase 0 Exit Gate)
1. Complete, non-ambiguous spec document saved in `docs/SPECIFICATION.md`.
2. Architecture covers both Header String and JSON session cookie import flows.
3. Provider isolation guaranteed via clean abstract adapter interfaces.
4. Security model guarantees zero plaintext secrets at rest or in log outputs.
5. Termux and Ubuntu compatibility constraints explicitly addressed.
