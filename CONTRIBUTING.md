# Contributing to ai-dnd-campaign-forge

Forge is a plugin-host desktop tool. The core host stays thin; every generator,
ruleset, and renderer is a plugin loaded at runtime through the extension
registry. If you're adding a feature, you're almost certainly adding a plugin,
not editing the host.

## Repo shape

```
forge_host/        entry + bootstrap + host loop
forge_core/        campaign engine, session state, dice, NPC synthesis
forge_handlers/    request handlers wired into the host event bus
forge_services/    LLM bridge, persistence, asset pipeline, telemetry
forge_models/      dataclasses + pydantic schemas for campaigns/NPCs/quests
forge_plugins/     bundled plugins + loader + registry + contracts
forge_utils/       logging, rng, text, fs helpers
forge_config/      default config + schema
tests/             pytest suites
```

## Adding a plugin

1. Drop a folder under `forge_plugins/community/<your_plugin>/`.
2. Implement `plugin.py` exposing a class that subclasses
   `forge_plugins.contracts.CampaignPlugin`.
3. Declare `plugin.toml` with `id`, `version`, `entrypoint`, `capabilities`.
4. Run `python -m forge_host --plugin-dir forge_plugins/community --list` to
   confirm the registry picks it up.

Plugins must not import from `forge_host` internals. Use the contracts module.

## Style

- Python 3.12+, `ruff` + `black`, line length 100.
- Type hints on every public function. `mypy --strict` on `forge_core` and
  `forge_plugins/contracts`.
- No printing to stdout from library code — use `forge_utils.logging`.

## Tests

```
pytest -q
```

Every plugin gets a smoke test that instantiates it and runs `generate_encounter`
against a fixed seed. Determinism is a hard requirement — seeded runs must
produce byte-identical campaign JSON.

## PRs

One plugin or one host change per PR. Include a `campaigns/<name>.session`
fixture if you touched the engine. Do not bump the plugin ABI without a
migration note in `forge_plugins/registry.py`.