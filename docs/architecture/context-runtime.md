# Translation Context Runtime

A context bundle contains:

- current segment context
- previous segment context
- next segment context
- glossary context
- character context
- narrative context
- scene context
- runtime metadata
- user metadata
- pipeline context

The runtime adapter exposes `build_context`, `attach_context`, `validate`, and `manifest`.
