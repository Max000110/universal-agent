# Universal Agent (Antigravity CLI) — Installation & First-Run Tutorial

Welcome to **Universal Agent**! This guide walks you through the 1-minute installation and setup process on **Ubuntu** or **Termux (Android)**.

---

## ⚡ 1-Line Copy-Paste Installer

Run this single command in your terminal:

```bash
git clone https://github.com/user/universal-agent.git && cd universal-agent && bash install.sh
```

---

## 📸 Step-by-Step Split Tutorial

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: OPEN TERMINAL & PASTE INSTALLER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ $ git clone https://github.com/user/universal-agent.git && cd universal-agent│
│ $ bash install.sh                                                           │
│                                                                             │
│ • Creating Python virtual environment in ~/.antigravitycli/venv...           │
│ • Installing dependencies and antigravity package...                         │
│ • Symlinking binary to ~/.local/bin/antigravity...                          │
│ ✓ Installation successful!                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```
> **Caption**: Step 1 — Paste the 1-line installer. The script sets up the local Python venv and symlinks the `antigravity` binary.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: LAUNCH & IMPORT SESSION COOKIES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ $ antigravity                                                               │
│                                                                             │
│ Antigravity CLI v1.0.0 — Ubuntu Linux                                       │
│ antigravity > /session import chatgpt                                       │
│                                                                             │
│ === Import Session Cookies for CHATGPT ===                                  │
│ Paste Cookie Header string OR JSON cookie export blob:                      │
│ Cookie Data > session_token=YOUR_TOKEN; __Secure-next-auth...               │
│ ✓ Session successfully imported and encrypted for CHATGPT!                 │
└─────────────────────────────────────────────────────────────────────────────┘
```
> **Caption**: Step 2 — Launch `antigravity` and paste your ChatGPT Web or Gemini Web session cookies (Header String or JSON format).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: VERIFY STATUS BAR & MODEL CONTROL                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Provider: CHATGPT] [Model: gpt-4o] [Think: ON] [Context: 1.5k/128k] [VALID]│
│                                                                             │
│ antigravity > /model o3-mini                                                │
│ Command: model — Switched active model to 'o3-mini'.                        │
│                                                                             │
│ antigravity > /deepthink on                                                 │
│ Command: deepthink — Deep Think reasoning policy is now ENABLED.            │
└─────────────────────────────────────────────────────────────────────────────┘
```
> **Caption**: Step 3 — The status bar confirms your session is active (`VALID`). You can toggle `/deepthink on` or switch models with `/model <name>`.

---

## 🛠️ Troubleshooting & Re-running
If validation fails:
1. Re-copy your cookie string from Browser DevTools (Application -> Cookies).
2. Re-run `/session import chatgpt` or `/session import gemini`.
3. To update the app safely at any time, run `bash update.sh`.
