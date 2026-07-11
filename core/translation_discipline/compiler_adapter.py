from __future__ import annotations

from core.prompt_compiler import CompiledPrompt, PromptCompiler, PromptSections


class PromptCompilerAdapter:
    """Compatibility boundary; compilation remains owned by the legacy compiler."""

    def __init__(self, compiler: PromptCompiler | None = None) -> None:
        self.compiler = compiler or PromptCompiler()

    def compile(self, sections: PromptSections) -> CompiledPrompt:
        return self.compiler.compile(sections)
