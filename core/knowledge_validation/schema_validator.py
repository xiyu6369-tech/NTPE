"""
Schema Validation Engine
RM-5.7.3A Schema Validation Engine

Offline JSON Schema Draft validator for knowledge entities.
No runtime dependencies, no provider calls, no API costs.
"""

import json
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft7Validator, Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from jsonschema.exceptions import SchemaError as JsonSchemaError

from core.knowledge_validation.validation_result import (
    ValidationResult,
    ValidationErrorDetail,
)
from core.knowledge_validation.errors import (
    SchemaNotFoundError,
    SchemaVersionMismatchError,
    SchemaLoadError,
    UnsupportedSchemaDraftError,
    ValidationFailedError,
)


class SchemaValidator:
    """Offline JSON Schema validator for knowledge entities."""

    SUPPORTED_DRAFTS = {
        "http://json-schema.org/draft-07/schema#": Draft7Validator,
        "https://json-schema.org/draft/2020-12/schema": Draft202012Validator,
    }

    DEFAULT_SCHEMA_PATHS = [
        "schemas/knowledge",
        "schemas",
    ]

    def __init__(
        self,
        schema_paths: list[str] | None = None,
        base_path: str | Path | None = None,
    ):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.schema_paths = [
            self.base_path / p for p in (schema_paths or self.DEFAULT_SCHEMA_PATHS)
        ]
        self._schema_cache: dict[str, dict] = {}
        self._validator_cache: dict[str, jsonschema.protocols.Validator] = {}

    def _find_schema_file(self, schema_name: str) -> Path | None:
        candidates = [schema_name]
        if not schema_name.endswith(".json"):
            candidates.append(f"{schema_name}.json")
        for schema_path in self.schema_paths:
            for candidate in candidates:
                full_path = schema_path / candidate
                if full_path.exists():
                    return full_path
        return None

    def _load_schema(self, schema_name: str) -> dict:
        if schema_name in self._schema_cache:
            return self._schema_cache[schema_name]

        schema_file = self._find_schema_file(schema_name)
        if not schema_file:
            searched = [str(p / schema_name) for p in self.schema_paths]
            raise SchemaNotFoundError(schema_name, searched)

        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)
            self._schema_cache[schema_name] = schema
            return schema
        except json.JSONDecodeError as e:
            raise SchemaLoadError(str(schema_file), e) from e
        except OSError as e:
            raise SchemaLoadError(str(schema_file), e) from e

    def _get_validator(self, schema: dict) -> jsonschema.protocols.Validator:
        draft_uri = schema.get("$schema", "http://json-schema.org/draft-07/schema#")

        if draft_uri not in self.SUPPORTED_DRAFTS:
            raise UnsupportedSchemaDraftError(
                schema.get("title", "unknown"), draft_uri
            )

        validator_class = self.SUPPORTED_DRAFTS[draft_uri]

        if draft_uri not in self._validator_cache:
            self._validator_cache[draft_uri] = validator_class(schema)
        else:
            self._validator_cache[draft_uri] = validator_class(schema)

        return self._validator_cache[draft_uri]

    def _normalize_errors(
        self,
        errors: list[JsonSchemaValidationError],
        instance: dict,
    ) -> list[ValidationErrorDetail]:
        normalized = []

        for error in errors:
            instance_path = "/".join(str(p) for p in error.path) if error.path else ""
            if instance_path:
                instance_path = f"/{instance_path}"

            schema_path = "/".join(str(p) for p in error.schema_path) if error.schema_path else ""
            if schema_path:
                schema_path = f"/{schema_path}"

            expected = None
            actual = None

            if error.validator == "type":
                expected = error.validator_value
                actual = type(instance).__name__ if instance is not None else "null"
            elif error.validator == "enum":
                expected = error.validator_value
                actual = error.instance
            elif error.validator == "const":
                expected = error.validator_value
                actual = error.instance
            elif error.validator == "format":
                expected = error.validator_value
                actual = error.instance
            elif error.validator == "required":
                expected = error.validator_value
                actual = list(instance.keys()) if isinstance(instance, dict) else None
            elif error.validator in ("minimum", "maximum", "minLength", "maxLength"):
                expected = error.validator_value
                actual = error.instance

            detail = ValidationErrorDetail(
                keyword=error.validator,
                instance_path=instance_path,
                schema_path=schema_path,
                message=error.message,
                expected=expected,
                actual=actual,
            )
            normalized.append(detail)

        return normalized

    def _check_schema_version(self, instance: dict, schema: dict) -> tuple[str | None, str | None]:
        schema_version = schema.get("version") or schema.get("schema_version")
        instance_version = instance.get("schema_version") if isinstance(instance, dict) else None
        return schema_version, instance_version

    def validate(
        self,
        instance: dict,
        schema_name: str,
        strict_version: bool = True,
    ) -> ValidationResult:
        schema = self._load_schema(schema_name)

        schema_version, instance_version = self._check_schema_version(instance, schema)

        if strict_version and schema_version and instance_version:
            if schema_version != instance_version:
                raise SchemaVersionMismatchError(
                    schema_name, schema_version, instance_version
                )

        validator = self._get_validator(schema)
        errors = list(validator.iter_errors(instance))

        if errors:
            normalized_errors = self._normalize_errors(errors, instance)
            return ValidationResult.failure(
                schema=schema_name,
                errors=normalized_errors,
                schema_version=schema_version,
                instance_version=instance_version,
            )

        return ValidationResult.success(
            schema=schema_name,
            schema_version=schema_version,
            instance_version=instance_version,
        )

    def validate_or_raise(
        self,
        instance: dict,
        schema_name: str,
        strict_version: bool = True,
    ) -> ValidationResult:
        result = self.validate(instance, schema_name, strict_version)
        if not result.valid:
            raise ValidationFailedError(schema_name, [e.to_dict() for e in result.errors])
        return result

    def get_schema(self, schema_name: str) -> dict:
        return self._load_schema(schema_name)

    def list_available_schemas(self) -> list[str]:
        schemas = set()
        for schema_path in self.schema_paths:
            if schema_path.exists():
                for file in schema_path.glob("*.json"):
                    schemas.add(file.stem)
        return sorted(schemas)

    def clear_cache(self) -> None:
        self._schema_cache.clear()
        self._validator_cache.clear()
