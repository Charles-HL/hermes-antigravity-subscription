---
name: hermes-catalog-release
description: Protocol for releasing new versions of the Antigravity Subscription DirectSDK plugin and submitting catalog pin-bump PRs to upstream NousResearch/hermes-agent.
---

# Hermes Catalog Release & Upstream PR Protocol

This skill documents the end-to-end workflow for releasing new versions of the `antigravity-subscription-directsdk` plugin and submitting catalog pin-bump PRs to upstream `NousResearch/hermes-agent`.

---

## 1. Upstream Catalog Admission Rules

Per `hermes-agent/plugin-catalog/README.md` (Rules 4 and 5):
- Every catalog entry requires an exact 40-character Git commit SHA pin (`sha:`). Branches and tags are rejected.
- Updating an entry's pin requires a new PR to `NousResearch/hermes-agent` reviewed by maintainers.
- SHA bumps must be submitted by the plugin repository owner or a major contributor.
- Reviewers inspect the commit range being adopted (`vOLD..vNEW`) for security, stability, and capability compliance.

---

## 2. Release Protocol (Plugin Repository)

Execute these steps in `/root/.hermes/plugins/antigravity-subscription-directsdk`:

### Step 1: Bump Version in `plugin.yaml`
Update `version:` in `plugin.yaml`:
```yaml
name: antigravity-subscription-directsdk
manifest_version: 2
version: X.Y.Z
```

### Step 2: Run the Test Suite
Ensure all tests pass before committing:
```bash
PYTHONPATH=/usr/local/lib/hermes-agent:. pytest
```

### Step 3: Commit the Release
Create the release commit on `main`:
```bash
git commit -am "release: vX.Y.Z"
```

### Step 4: Push `main` to `origin/main` FIRST
The GitHub Actions release gate (`.github/workflows/release.yml`) checks:
`git merge-base --is-ancestor "$TAG" origin/main`
The release commit must exist on `origin/main` before the tag is pushed, or CI will fail.
```bash
git push origin main
```

### Step 5: Tag and Push Tag
Tag the commit using strict semver (`vX.Y.Z`):
```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

### Step 6: Monitor Release Workflow
Wait for GitHub Actions to validate tests and publish the GitHub release:
```bash
gh run list --repo soyelmismo/hermes-antigravity-subscription -L 3
gh run watch <run_id> --repo soyelmismo/hermes-antigravity-subscription
```
Verify the published release:
```bash
gh release view vX.Y.Z
```

### Step 7: Record the 40-Hex Commit SHA
```bash
git rev-parse HEAD
# Example: b7ab470b51a2915e19e4df52bb80cd5973c1b0ca
```

---

## 3. Upstream PR Protocol (`NousResearch/hermes-agent`)

Execute these steps in the local `hermes-agent` clone (`/usr/local/lib/hermes-agent`):

### Step 1: Sync `main` with Upstream
```bash
cd /usr/local/lib/hermes-agent
git fetch origin main
git checkout main
git merge --ff-only origin/main
```

### Step 2: Create a Dedicated Branch
```bash
git checkout -b catalog/bump-antigravity-pin-v<version_slug>
# Example: catalog/bump-antigravity-pin-v105
```

### Step 3: Update Catalog Entry
Edit `plugin-catalog/antigravity-subscription-directsdk.yaml`:
- Set `sha:` to the exact 40-character commit SHA recorded in Step 2.7.
- Set `version:` to `"X.Y.Z"`.
- Preserve all existing descriptions, disclosures, and capabilities blocks.

### Step 4: Run Catalog & Plugin Validators
Both validators must pass cleanly:
```bash
python3 scripts/validate_plugin_catalog.py plugin-catalog/antigravity-subscription-directsdk.yaml
# Must output: OK: 1 file(s) valid

hermes plugins validate /root/.hermes/plugins/antigravity-subscription-directsdk
# Must output: Validation passed. (Security scan: safe)
```

### Step 5: Commit and Push to Fork
```bash
git commit -am "catalog: bump antigravity-subscription-directsdk pin to vX.Y.Z"
git push -u fork catalog/bump-antigravity-pin-v<version_slug>
```

### Step 6: Submit Upstream PR
Open the PR against `NousResearch/hermes-agent` `main`:
```bash
gh pr create --repo NousResearch/hermes-agent \
  --base main \
  --head soyelmismo:catalog/bump-antigravity-pin-v<version_slug> \
  --title "catalog: bump antigravity-subscription-directsdk pin to vX.Y.Z" \
  --body "<body_content>"
```

---

## 4. PR Writing Style Guide (Stop-Slop / Technical Standards)

Upstream maintainers review dozens of catalog PRs weekly. Follow these rules strictly:

### Rules:
1. **Language:** English only.
2. **Title Format:** `catalog: bump antigravity-subscription-directsdk pin to vX.Y.Z`.
3. **No AI Clichés or Slop:**
   - Do NOT use puffery words: "Intelligent", "Smart", "Crucial", "Game-changing", "Seamlessly", "Leverages".
   - Replace with plain technical terms: "Tool pruning", "Error classification", "Context bound".
4. **No Filler or Throat-Clearing:**
   - Cut: "Here is what changed", "In order to...", "It is important to understand".
   - Start directly with facts, numbers, and mechanisms.
5. **No Em-Dashes:** Avoid dramatic dashes (`—`). Use colons or standard periods.
6. **Active Voice & Concrete Data:**
   - Name the exact files changed (`prompt.py`, `__init__.py`).
   - Cite exact error signatures, byte counts, and token limits.
   - Mention measured reductions (e.g. "cuts wire payload from 600 KB to 180 KB").

### Canonical PR Body Template:

```markdown
Follow-up to the catalogued plugin (owner-submitted pin bump, catalog rules 4 and 5).

Pin: <OLD_SHA> -> <NEW_SHA>
Version: <OLD_VERSION> -> <NEW_VERSION>
Release: https://github.com/soyelmismo/hermes-antigravity-subscription/releases/tag/v<NEW_VERSION>

Commits adopted in range (`v<OLD_VERSION>..v<NEW_VERSION>`):

• `<NEW_SHA_SHORT>` release: v<NEW_VERSION>
• `<COMMIT_SHA_SHORT>` <commit message>

### Root Cause / Motivation

<Direct description of failure mode or technical reason for the update. Include exact error message if applicable.>

### Changes in v<NEW_VERSION>

1. **<Component / File 1>**
   - <Exact behavior change, measurements, byte/token counts.>
2. **<Component / File 2>**
   - <Exact behavior change, configuration flags.>

### Validation

• Plugin repo CI: <passed count> passed, <skipped count> skipped against `HERMES_REF v2026.9.21`.
• `python3 scripts/validate_plugin_catalog.py plugin-catalog/antigravity-subscription-directsdk.yaml` passed (1 file valid).
• `hermes plugins validate /root/.hermes/plugins/antigravity-subscription-directsdk` passed (safe, declared capabilities match).
• Manifest version <NEW_VERSION> matches git tag `v<NEW_VERSION>` and catalog entry.
```
