from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional

from ..context import CLIContext
from .translate_options import TranslateOptions
from .translate_progress import TranslateProgress
from .translate_report import TranslateReport

TranslatorHook = Callable[[str, TranslateOptions], str]


@dataclass
class TranslateRunSummary:
    input_path: Path
    output_path: Path
    progress: TranslateProgress
    report: TranslateReport
    report_path: Optional[Path] = None

    def to_dict(self) -> dict:
        return {
            "input": str(self.input_path),
            "output": str(self.output_path),
            "progress": self.progress.to_dict(),
            "report": self.report.to_dict(),
            "report_path": str(self.report_path) if self.report_path else None,
        }


class TranslateRunner:
    """CLI-facing translation runner.

    The runner is intentionally thin: it discovers text files, delegates actual
    translation to an optional hook/engine, writes outputs, and returns a
    structured report. This keeps the CLI layer stable while Stage-02/03/04
    internals continue to evolve behind the product runtime boundary.
    """

    def __init__(self, context: CLIContext, translator: Optional[TranslatorHook] = None) -> None:
        self.context = context
        self.translator = translator or self._resolve_translator(context)

    def _resolve_translator(self, context: CLIContext) -> TranslatorHook:
        hook = context.metadata.get("translation_hook")
        if callable(hook):
            return hook  # type: ignore[return-value]
        return self._default_translator

    @staticmethod
    def _default_translator(text: str, options: TranslateOptions) -> str:
        # Deterministic local fallback for CLI acceptance tests and offline runs.
        # Real provider execution is injected through context.metadata["translation_hook"].
        return (
            "[NTPE Translation Output]\n"
            f"provider={options.provider}\n"
            f"quality={options.quality}\n\n"
            f"{text}"
        )

    def discover_sources(self, options: TranslateOptions) -> List[Path]:
        source = self._absolute(options.input_path)
        if source.is_file():
            return [source]
        if source.is_dir():
            return sorted(p for p in source.rglob(options.pattern) if p.is_file())
        raise FileNotFoundError(f"translate input not found: {source}")

    def output_root(self, options: TranslateOptions) -> Path:
        if options.output_path:
            return self._absolute(options.output_path)
        return self.context.path("output")

    def output_for(self, source: Path, options: TranslateOptions, base_input: Optional[Path] = None) -> Path:
        root = self.output_root(options)
        if base_input and base_input.is_dir():
            rel = source.relative_to(base_input)
            return root.joinpath(rel.parent, f"{source.stem}{options.suffix}{source.suffix}")
        return root.joinpath(f"{source.stem}{options.suffix}{source.suffix}")

    def run(self, options: TranslateOptions) -> TranslateRunSummary:
        input_path = self._absolute(options.input_path)
        sources = self.discover_sources(options)
        output_root = self.output_root(options)
        progress = TranslateProgress(total=len(sources))
        report = TranslateReport(provider=options.provider, quality=options.quality, dry_run=options.dry_run)

        for source in sources:
            try:
                output = self.output_for(source, options, base_input=input_path if input_path.is_dir() else None)
                if output.exists() and (options.resume or not options.overwrite):
                    progress.add_skipped(str(source), str(output), reason="exists")
                    report.add(status="skipped", source=str(source), output=str(output), reason="exists")
                    continue

                text = source.read_text(encoding="utf-8", errors="ignore")
                translated = self.translator(text, options)
                if not options.dry_run:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_text(translated, encoding="utf-8")
                progress.add_completed(str(source), str(output))
                report.add(status="completed", source=str(source), output=str(output), chars=len(text))
            except Exception as exc:
                progress.add_failed(str(source), str(exc))
                report.add(status="failed", source=str(source), error=str(exc))

        report_path = None
        if not options.dry_run:
            report_path = output_root / "translation_report.json"
            report.write_json(report_path)

        return TranslateRunSummary(input_path=input_path, output_path=output_root, progress=progress, report=report, report_path=report_path)

    def _absolute(self, path: Path) -> Path:
        return path if path.is_absolute() else self.context.path(str(path))
