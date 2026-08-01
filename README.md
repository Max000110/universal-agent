# Antigravity CLI 🚀

**Antigravity CLI** is a local-first, terminal-native agentic framework CLI built for **Ubuntu** and **Termux** (Android). It delivers an Antigravity 2.0-style surface experience with multi-step reasoning, slash command control, provider status bars, and folder-based skills, while using explicit user-owned **Session Cookie Imports** instead of third-party OAuth identity providers.

---

## 🌟 Key Features

- **Dual-Provider Session Support**: Seamlessly switch between **ChatGPT** and **Gemini** sessions at runtime.
- **Flexible Cookie Bootstrap**: Imports both raw **Cookie Header strings** (`session_token=...; __Secure-next-auth...`) and **JSON cookie exports**.
- **Encrypted Local Vault**: AES-256-GCM / Fernet storage for session secrets at rest (`0600` permissions).
- **Strict Log Redaction**: Built-in filter redacts cookies, tokens, JWTs, and authorization headers from all outputs.
- **Deep Think Reasoning Policy**: Framework-level reasoning policy wrap applicable across any model.
- **Antigravity Skills Engine**: Folder-based `SKILL.md` discovery and execution (`/skills`, `/skill <name>`).
- **Ubuntu & Termux First**: Lightweight, zero desktop/systemd dependencies, pure Python execution.

---

## 📥 Quick Installation

```bash
git clone https://github.com/user/antigravity-cli.git
cd antigravity-cli
bash install.sh
```

Or run directly with Python:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
antigravity
```

---

## 🔑 Session Cookie Import

Launch the TUI and import cookies interactively:
```bash
/session import chatgpt
# OR
/session import gemini
```

Both input formats are accepted:
1. **Header String**:
   `session_token=YOUR_SESSION_TOKEN; __Secure-next-auth.session-token=YOUR_AUTH_TOKEN`
2. **JSON Format**:
   `{"session_token": "YOUR_SESSION_TOKEN", "__Secure-next-auth.session-token": "YOUR_AUTH_TOKEN"}`

---

## ⚡ Slash Command Reference

| Command | Action |
| :--- | :--- |
| `/users` | Display active provider sessions, quota, and account health. |
| `/context` | Display active model context window limits and current token budget. |
| `/models [filter]` | List available models for active provider. |
| `/model <name>` | Switch active model or provider at runtime (`/model gpt-4o`, `/model gemini-1.5-pro`). |
| `/deepthink [on\|off]` | Toggle deep thinking reasoning policy. |
| `/skills` | Browse installed built-in and user skills. |
| `/session validate` | Validate stored session cookie health. |
| `/session import <prov>` | Trigger interactive cookie import flow. |
| `/status` | View framework runtime & vault status summary. |
| `/help` | Render slash command palette help. |

---

## 🛡️ Security & Privacy Architecture

- **Encrypted at Rest**: Master session secrets stored encrypted in `~/.antigravitycli/vault.enc`.
- **Zero Plaintext Logs**: Automatic regex redaction filter intercepts all console/file log calls.
- **Local First**: No telemetry, cloud tracking, or remote key reporting.

---

## 🧪 Testing & Verification

Run the test suite:
```bash
pytest -v tests/
```

---

## 📄 License
MIT License
