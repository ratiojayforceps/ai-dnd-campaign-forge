# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.6.x   | yes       |
| 0.5.x   | security-only |
| < 0.5   | no        |

## Threat model

Forge loads third-party plugins from disk and executes them in-process. This
is the primary attack surface. We treat plugin loading the way a browser
treats extension installs:

- Plugins run with full user privileges. There is no sandbox in 0.6.x.
- The loader validates `plugin.toml` against a schema and refuses plugins
  whose `entrypoint` escapes the plugin directory (`..`, absolute paths,
  symlink traversal).
- LLM bridge calls are made with user-supplied endpoints. SSRF is the user's
  problem, but we do reject `file://` and `gopher://` schemes by default.

## Reporting

Open a private security advisory on GitHub, or email `forge-sec@` (see repo
profile). Do not file public issues for loader bypasses.

## Known non-issues

- A plugin reading your `campaigns/` directory: by design.
- A plugin making network calls: by design, plugins are trusted once loaded.
- Prompt injection from campaign text reaching the LLM bridge: mitigated by
  `forge_services.llm_bridge.sanitize_prompt`, but not eliminated. Do not feed
  untrusted web text into a DM-context prompt without review.

## Hardening roadmap

0.7.0 targets subprocess-isolated plugins with a capability manifest. Until
then, do not load community plugins you have not read.