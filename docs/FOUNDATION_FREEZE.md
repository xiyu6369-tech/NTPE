# NTPE Foundation v1.0 Freeze

Status: Frozen  
Compatibility: Stable  
API Level: 1

Foundation v1.0 freezes the completed NTPE Foundation architecture after Foundation-08.9.
This freeze does not add product features. It records the stable baseline used by NTPE 1.0 Beta and later SDK stages.

## Frozen Scope

The following Foundation contracts are stable:

- Runtime Contract
- Context Pipeline Contract
- Prompt Pipeline Contract
- Plugin Contract
- Production Pipeline Contract
- Translation Runtime Contract
- Intelligence Contract
- Knowledge Contract
- Snapshot Contract

## Allowed Changes

- Bug fixes
- Security fixes
- Documentation updates
- Test improvements
- Non-breaking refactors
- Backward compatibility fixes

## Not Allowed

- Breaking API changes
- Removing completed Foundation behavior
- Replacing existing contracts without migration
- Changing public manifest semantics
- Introducing new Foundation modules that force upstream API changes

## Release Tag

Recommended tag:

```bash
git tag foundation-v1.0
git push origin foundation-v1.0
```
