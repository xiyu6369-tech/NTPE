# NTPE 1.2 Professional Stage-13

Stage-13 adds a local plugin packaging and publishing layer.

Commands:

```bat
python ntpe_plugin_marketplace.py build <plugin_source> --output plugins/packages
python ntpe_plugin_marketplace.py publish <metadata_json> --repository plugins/published
python ntpe_plugin_marketplace.py published
```

This stage does not execute plugins and does not perform network publishing.
