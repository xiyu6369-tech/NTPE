from __future__ import annotations

from pathlib import Path


class RuntimeManager:
    """
    NTPE v1.2 Foundation-02 Runtime Manager

    統一管理所有執行期產物：
    - runtime/memory
    - runtime/reports
    - runtime/sessions
    - runtime/translated
    - runtime/final_output
    - runtime/logs
    - runtime/prompt_packages
    """

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[2]
        self.runtime_dir = self.root / "runtime"

        self.memory_dir = self.runtime_dir / "memory"
        self.reports_dir = self.runtime_dir / "reports"
        self.sessions_dir = self.runtime_dir / "sessions"
        self.translated_dir = self.runtime_dir / "translated"
        self.final_output_dir = self.runtime_dir / "final_output"
        self.logs_dir = self.runtime_dir / "logs"
        self.prompt_packages_dir = self.runtime_dir / "prompt_packages"

        self.ensure_dirs()

    def ensure_dirs(self) -> None:
        for path in [
            self.runtime_dir,
            self.memory_dir,
            self.reports_dir,
            self.sessions_dir,
            self.translated_dir,
            self.final_output_dir,
            self.logs_dir,
            self.prompt_packages_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def memory_path(self, name: str) -> Path:
        return self.memory_dir / name

    def report_path(self, name: str) -> Path:
        return self.reports_dir / name

    def session_path(self, *parts: str) -> Path:
        path = self.sessions_dir.joinpath(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def translated_path(self, name: str) -> Path:
        return self.translated_dir / name

    def final_output_path(self, name: str) -> Path:
        return self.final_output_dir / name

    def log_path(self, name: str) -> Path:
        return self.logs_dir / name

    def prompt_package_path(self, name: str) -> Path:
        return self.prompt_packages_dir / name