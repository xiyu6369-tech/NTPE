from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable

LOGICAL_ID = "canary-001"
CANONICAL_ID = "canary-001-character-honorific"
SCHEMA_VERSION = "te-v7.2-stage12.5.6a-corpus-identity-v1"

class CorpusIdentityError(ValueError): pass
class UnknownCorpusIdentityError(CorpusIdentityError): pass
class DuplicateCorpusAliasError(CorpusIdentityError): pass
class AmbiguousCorpusIdentityError(CorpusIdentityError): pass

@dataclass(frozen=True)
class CorpusIdentityContract:
    logical_id: str
    canonical_id: str
    aliases: tuple[str, ...]
    schema_version: str
    source_hash: str
    fixture_hash: str
    immutable: bool = True

    def to_dict(self) -> dict[str, object]:
        return {"logical_id": self.logical_id, "canonical_id": self.canonical_id,
                "aliases": list(self.aliases), "schema_version": self.schema_version,
                "source_hash": self.source_hash, "fixture_hash": self.fixture_hash,
                "immutable": self.immutable}

@dataclass(frozen=True)
class CorpusResolutionResult:
    requested_id: str
    logical_id: str
    canonical_id: str
    source_hash: str
    fixture_hash: str

def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def build_corpus_identity_contract(fixture_path: str | Path) -> CorpusIdentityContract:
    path = Path(fixture_path); raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    exact = [case for case in payload.get("cases", []) if case.get("case_id") == CANONICAL_ID]
    if len(exact) != 1: raise CorpusIdentityError("canonical-corpus-id-must-resolve-exactly-once")
    source = exact[0].get("source_text")
    if not isinstance(source, str) or not source: raise CorpusIdentityError("canonical-corpus-source-invalid")
    return CorpusIdentityContract(LOGICAL_ID, CANONICAL_ID, (LOGICAL_ID,), SCHEMA_VERSION,
                                  _sha(source.encode("utf-8")), _sha(raw))

def resolve_canary_corpus_id(requested_id: str, contracts: Iterable[CorpusIdentityContract]) -> CorpusResolutionResult:
    aliases: dict[str, list[CorpusIdentityContract]] = {}; canonicals: dict[str, list[CorpusIdentityContract]] = {}
    for contract in tuple(contracts):
        if not contract.immutable: raise CorpusIdentityError("mutable-corpus-contract-forbidden")
        if len(set(contract.aliases)) != len(contract.aliases): raise DuplicateCorpusAliasError("duplicate-alias-within-contract")
        canonicals.setdefault(contract.canonical_id, []).append(contract)
        for alias in contract.aliases: aliases.setdefault(alias, []).append(contract)
    if any(len(items) > 1 for items in aliases.values()): raise DuplicateCorpusAliasError("duplicate-alias-across-contracts")
    if any(len(items) > 1 for items in canonicals.values()): raise AmbiguousCorpusIdentityError("duplicate-canonical-id")
    unique = {item.canonical_id: item for item in canonicals.get(requested_id, []) + aliases.get(requested_id, [])}
    if not unique: raise UnknownCorpusIdentityError(f"unknown-corpus-id:{requested_id}")
    if len(unique) != 1: raise AmbiguousCorpusIdentityError(f"ambiguous-corpus-id:{requested_id}")
    contract = next(iter(unique.values()))
    return CorpusResolutionResult(requested_id, contract.logical_id, contract.canonical_id,
                                  contract.source_hash, contract.fixture_hash)
