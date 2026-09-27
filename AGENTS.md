# AGENTS.md

Instructions and operating guidelines for AI coding assistants working in this repository (`soyelmismo/hermes-antigravity-subscription`).

---

## 1. Project Overview

This repository contains the `antigravity-subscription-directsdk` provider plugin for [Hermes Agent](https://github.com/NousResearch/hermes-agent). It allows users to run Hermes on their existing Google Antigravity / Gemini subscription by driving the official `agy` CLI as a managed external subprocess in `--input-format stream-json --output-format stream-json` mode.

### Architecture Map
- [`__init__.py`](__init__.py): Registers `AntigravitySubscriptionDirectSDKProfile` with Hermes. Declares model capabilities, context bounds (`get_model_context_length` defaulting to 200,000 tokens), and smart error classification (`classify_api_error`).
- [`client.py`](client.py): Implements `AntigravityClient`, handling persistent worker lifecycle, per-turn delta reuse, thread synchronization (`_lock` / `_worker_lock`), isolated HOME configuration, and cleanup retry budgets.
- [`prompt.py`](prompt.py): Handles prompt assembling from Hermes message lists, historical tool output pruning (retaining recent tools, truncating older outputs to avoid Go channel backpressure), delta prompt formatting, and `<tool_call>` block translation.
- [`process.py`](process.py): Manages `agy` binary detection, OS keyring/token detection across Linux, macOS, and Windows, isolated HOME symlinks, and cross-platform process tree termination.
- [`stream.py`](stream.py): Implements `AntigravityStream`, parsing streaming JSON events from `agy`, synthesizing token chunks, monitoring for native tool abort signals, and calculating per-turn usage deltas.
- [`plugin.yaml`](plugin.yaml): Plugin metadata manifest read by Hermes Agent and the catalog registry.

---

## 2. Development & Testing Requirements

- **Test Suite**: Always run the full test suite before committing:
  ```bash
  PYTHONPATH=/usr/local/lib/hermes-agent:. pytest
  ```
- **Security Boundaries**:
  - Never add `--dangerously-skip-permissions` to default arguments.
  - Preserve isolated HOME directory sandboxing and token symlink safeguards.
- **Async Compatibility**: Ensure facade returns awaitable completions and async-iterable streams (`HERMES_SKIP_ASYNC_WRAP = True`).

---

## 3. Release & Upstream PR Protocol

When preparing a new release or updating the plugin pin in the upstream Hermes Agent catalog (`NousResearch/hermes-agent`), **you MUST read and strictly follow the protocol defined in the skill:**

👉 [`.agents/skills/hermes-catalog-release/SKILL.md`](.agents/skills/hermes-catalog-release/SKILL.md)

### Key Rules to Remember:
1. **Order of Operations**:
   - Bump `version:` in `plugin.yaml`.
   - Run tests (`pytest`).
   - Commit `release: vX.Y.Z`.
   - **Push `main` to `origin/main` BEFORE pushing the tag.** (The release CI workflow requires the tag commit to already exist on `origin/main`).
   - Create and push tag `vX.Y.Z`.
   - Wait for the GitHub Actions `Release` workflow to finish and verify `gh release view vX.Y.Z`.
2. **Upstream Catalog PR**:
   - In `/usr/local/lib/hermes-agent`, create branch `catalog/bump-antigravity-pin-v<slug>`.
   - Update `plugin-catalog/antigravity-subscription-directsdk.yaml` with the exact 40-character commit SHA and version.
   - Run `python3 scripts/validate_plugin_catalog.py plugin-catalog/antigravity-subscription-directsdk.yaml`.
   - Run `hermes plugins validate /root/.hermes/plugins/antigravity-subscription-directsdk`.
   - Push to fork and submit PR to `NousResearch/hermes-agent` `main`.
3. **PR Writing Style (Stop-Slop)**:
   - English only.
   - Short, concise, and direct.
   - No AI buzzwords ("Intelligent", "Smart", "Crucial", "Game-changing", "Seamlessly").
   - No throat-clearing filler ("Here is what changed", "In order to...").
   - No em-dashes (`—`). Use colons or standard periods.
   - Active voice with exact file paths, numbers, byte counts, and error signatures.
