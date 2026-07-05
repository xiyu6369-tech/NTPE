# NTPE 1.2 Professional — Stage-12 Plugin Marketplace CLI / Repository Commands

## Goal

Stage-12 adds a formal command layer for the Stage-11 Plugin Marketplace Interface.
The CLI delegates all install, uninstall, validate, inspect, list, and doctor logic to
`PluginMarketplaceManager`, preserving the marketplace API boundary.

## Commands

```bat
python ntpe_plugin_marketplace.py list
python ntpe_plugin_marketplace.py inspect <plugin_package>
python ntpe_plugin_marketplace.py install <plugin_package>
python ntpe_plugin_marketplace.py install <plugin_package> --replace
python ntpe_plugin_marketplace.py uninstall <plugin_id>
python ntpe_plugin_marketplace.py validate
python ntpe_plugin_marketplace.py doctor
python ntpe_plugin_marketplace.py list --json
```

## Compatibility

- Keeps the legacy root entrypoint `ntpe_plugin_marketplace.py`.
- Does not execute plugins directly.
- Does not change Runtime, Session, Pipeline, Foundation v1.0, or NTPE 1.1 LTS contracts.
- CLI parsing is isolated in `core.translation_plugins.marketplace.cli`.

## Gate Review

- Build: PASS
- Unit Test: PASS
- Integration Test: PASS
- Regression Test: PASS
- Architecture Review: PASS
- Backward Compatibility: PASS
