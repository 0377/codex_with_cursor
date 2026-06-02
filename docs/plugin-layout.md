# Codex Plugin Layout

This repository ships as a Codex plugin with Git marketplace installation and upgrade (`codex plugin marketplace` + `codex plugin add`).

## Structure

- `.codex-plugin/plugin.json`: Codex plugin manifest and UI metadata.
- `.agents/plugins/marketplace.json`: Marketplace catalog so Codex can discover and install this plugin from the repository.
- `plugins/codex-with-cursor`: Symlink to the repository root (`..`) so the marketplace entry can use the standard `./plugins/<name>` layout without duplicating the plugin tree.
- `skills/`: Shared plugin content root for the Codex plugin.
- `skills/codex-with-cursor/`: The real workflow implementation, runtime scripts, `contract.json`, and contract docs.

## Why the runtime stays under `skills/codex-with-cursor/`

The delegated runtime, hook gate, and contract tests assume that `skills/codex-with-cursor/` is the canonical workflow root. Keeping that directory stable avoids breaking:

- platform-specific packaging of `windows_scripts/` and `macos_scripts/`
- verification scripts and path-sensitive tests
- the shared `contract.json` read by both Python runtime code and the platform hook

## Installation and update

1. Register the marketplace source:

   ```bash
   codex plugin marketplace add 0377/codex_with_cursor
   # or from a local clone:
   codex plugin marketplace add /path/to/codex_with_cursor
   ```

2. Install the plugin (confirm `<MARKETPLACE>` from `codex plugin marketplace list`):

   ```bash
   codex plugin add codex-with-cursor@<MARKETPLACE>
   ```

3. Update after pulling or publishing new commits:

   ```bash
   codex plugin marketplace upgrade <MARKETPLACE>
   ```

   Restart Codex or reload plugins if the new version does not appear. Re-run `codex plugin add` after `remove` if needed.

Installed workflow root:

`~/.codex/plugins/cache/<marketplace>/codex-with-cursor/<version>/skills/codex-with-cursor`

No script-based cross-project installer is provided by this repository anymore.
