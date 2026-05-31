# Codex Plugin Layout

This repository ships as a Codex plugin with repository-direct installation (`codex plugin install`).

## Structure

- `.codex-plugin/plugin.json`: Codex plugin manifest and UI metadata.
- `skills/`: Shared plugin content root for the Codex plugin.
- `skills/codex-with-cursor/`: The real workflow implementation, runtime scripts, `contract.json`, and contract docs.

## Why the runtime stays under `skills/codex-with-cursor/`

The delegated runtime, hook gate, and contract tests assume that `skills/codex-with-cursor/` is the canonical workflow root. Keeping that directory stable avoids breaking:

- platform-specific packaging of `windows_scripts/` and `macos_scripts/`
- verification scripts and path-sensitive tests
- the shared `contract.json` read by both Python runtime code and the platform hook

## Installation paths

- Source layout: this repository exposes `.codex-plugin/plugin.json` so it can be recognized as a Codex plugin source.
- Distribution path: `codex plugin install https://github.com/xdd666t/codex_with_cc --scope user`, or install from a local clone path.
- No script-based cross-project installer is provided by this repository anymore.
