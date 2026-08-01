# Universal Agent (Antigravity CLI) — Installation & First-Run Tutorial

Welcome to **Universal Agent** (`uag`)! This guide walks you through the 1-minute installation and setup process on **Ubuntu** or **Termux (Android)**.

---

## ⚡ 1-Line Copy-Paste Installer

Run this single command in your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/Max000110/universal-agent/main/install.sh | bash
```

---

## 📸 Step-by-Step Split Tutorial

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: OPEN TERMINAL & PASTE INSTALLER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ $ curl -fsSL https://raw.githubusercontent.com/Max000110/universal-agent/main/install.sh | bash │
│                                                                             │
│ • Detected Environment: Termux (Android POSIX)                              │
│ • Upgrading pip, setuptools, and wheel...                                   │
│ • Cloning latest release from GitHub (Max000110/universal-agent)...         │
│ • Installing Universal Agent python dependencies...                         │
│ • Symlinking global CLI launchers...                                        │
│ ✓ Installation Successful!                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```
> **Caption**: Step 1 — Paste the 1-line installer. The script sets up the local Python venv, inherits pre-compiled Android packages, and symlinks `universal-agent` and `uag`.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: LAUNCH & IMPORT SESSION COOKIES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ $ uag                                                                       │
│                                                                             │
│ Universal Agent CLI v1.0.0 — Termux / Ubuntu                                │
│ uag > /session import chatgpt                                               │
│                                                                             │
│ === Import Session Cookies for CHATGPT ===                                  │
│ Paste Cookie Header string OR JSON cookie export blob:                      │
│ Cookie Data > session_token=YOUR_TOKEN; __Secure-next-auth...               │
│ ✓ Session successfully imported and encrypted for CHATGPT!                 │
└─────────────────────────────────────────────────────────────────────────────┘
```
> **Caption**: Step 2 — Launch `uag` globally from anywhere and paste your ChatGPT Web or Gemini Web session cookies (Header String or JSON format).

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: VERIFY STATUS BAR & MODEL CONTROL                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Provider: CHATGPT] [Model: gpt-4o] [Think: ON] [Context: 1.5k/128k] [VALID]│
│                                                                             │
│ uag > /model o3-mini                                                        │
│ Command: model — Switched active model to 'o3-mini'.                        │
│                                                                             │
│ uag > /deepthink on                                                         │
│ Command: deepthink — Deep Think reasoning policy is now ENABLED.            │
└─────────────────────────────────────────────────────────────────────────────┘
```
> **Caption**: Step 3 — The status bar confirms your session is active (`VALID`). You can toggle `/deepthink on` or switch models with `/model <name>`.

---

## 📲 Termux Android Installation Resolutions (5-Point Audit)

The installer automatically handles and resolves all 5 Termux mobile obstacles:

1. **Non-Interactive Package Management**: Exports `DEBIAN_FRONTEND=noninteractive` to prevent prompt freezes during `pkg install`.
2. **Pre-Compiled Binary Packages**: Pre-installs Termux's native `python-cryptography` and `python-pydantic` packages via `pkg` and builds the venv with `--system-site-packages` to eliminate heavy C/Rust compilation.
3. **Android NDK API Target Level**: Automatically exports `ANDROID_API_LEVEL=24` required by Rust target toolchains on Android.
4. **Build Isolation Bypassing**: Uses `--no-build-isolation` fallback so `pip` uses native Android pre-compiled `maturin` wheels instead of crashing with SIGSEGV.
5. **Disabled Heavy Fat LTO**: Exports `CARGO_PROFILE_RELEASE_LTO=false` and `RUSTFLAGS="-C lto=off"` to prevent CPU compilation stalls during Rust crate builds.

---

## 🛠️ Troubleshooting & Re-running
If validation fails:
1. Re-copy your cookie string from Browser DevTools (Application -> Cookies).
2. Re-run `uag import-session chatgpt` or `uag import-session gemini`.
3. To update the app safely at any time, run `uag update`.
