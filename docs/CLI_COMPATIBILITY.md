# NTPE CLI Compatibility

NTPE 1.0 Beta Stage-06.9 freezes the CLI v1 public interface.

Stable commands:

- `ntpe version`
- `ntpe doctor`
- `ntpe translate`
- `ntpe project`
- `ntpe benchmark`
- `ntpe quality`
- `ntpe session`
- `ntpe config`
- `ntpe plugin`

Frozen contracts:

- command names
- primary subcommands
- JSON result shape: `ok`, `exit_code`, `message`, `data`, `errors`
- text output compatibility
- exit-code compatibility
- manifest compatibility

Allowed changes after freeze: bug fixes, documentation, tests, and backward-compatible additions.
Breaking changes require a new CLI major baseline.
