from __future__ import annotations

import tkinter as tk
from dataclasses import replace
from tkinter import filedialog, messagebox, ttk

from core.launcher_product.config import load_launcher_config
from core.launcher_product.models import LauncherConfig
from core.launcher_product.model_catalog import model_catalog
from core.launcher_product.provider_catalog import provider_catalog

from .controller import LauncherController
from .state import build_window_model
from .widgets import add_labeled_combobox, add_labeled_entry


class TranslationLauncherApp:
    def __init__(self, root: tk.Tk, controller: LauncherController | None = None) -> None:
        self.root = root
        self.controller = controller or LauncherController()
        self.window_model = build_window_model()
        self.root.title(self.window_model.title)
        self.root.minsize(760, 620)
        self.variables = self._create_variables()
        self.status = tk.Text(root, height=12, wrap="word", state="disabled")
        self.start_button: ttk.Button
        self._build()

    def _create_variables(self) -> dict[str, tk.Variable]:
        return {
            "input_path": tk.StringVar(value=self.window_model.input_path),
            "output_directory": tk.StringVar(value=self.window_model.output_directory),
            "source_language": tk.StringVar(value=self.window_model.source_language),
            "target_language": tk.StringVar(value=self.window_model.target_language),
            "provider_id": tk.StringVar(value=self.window_model.provider_id),
            "model_id": tk.StringVar(value=self.window_model.model_id),
            "translation_profile": tk.StringVar(value=self.window_model.translation_profile),
            "chunk_size": tk.StringVar(value=str(self.window_model.chunk_size)),
            "api_timeout": tk.StringVar(value=str(self.window_model.api_timeout)),
            "resume_enabled": tk.BooleanVar(value=self.window_model.resume_enabled),
            "overwrite": tk.BooleanVar(value=self.window_model.overwrite),
        }

    def _build(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        input_entry = add_labeled_entry(frame, 0, "Input file", self.variables["input_path"])
        ttk.Button(frame, text="Browse", command=self._choose_input).grid(row=0, column=2, padx=6)
        output_entry = add_labeled_entry(frame, 1, "Output folder", self.variables["output_directory"])
        ttk.Button(frame, text="Browse", command=self._choose_output).grid(row=1, column=2, padx=6)
        add_labeled_combobox(frame, 2, "Source language", self.variables["source_language"], ("auto", "ko", "ja", "en"))
        add_labeled_combobox(frame, 3, "Target language", self.variables["target_language"], ("zh-Hant",))
        add_labeled_combobox(
            frame, 4, "Provider", self.variables["provider_id"], tuple(item.provider_id for item in provider_catalog())
        )
        add_labeled_combobox(
            frame, 5, "Model", self.variables["model_id"], tuple(item.model_id for item in model_catalog())
        )
        add_labeled_combobox(frame, 6, "Profile", self.variables["translation_profile"], ("literary", "balanced", "faithful"))
        add_labeled_entry(frame, 7, "Chunk size", self.variables["chunk_size"])
        add_labeled_entry(frame, 8, "Timeout", self.variables["api_timeout"])
        ttk.Checkbutton(frame, text="Resume", variable=self.variables["resume_enabled"]).grid(row=9, column=0, sticky="w", padx=6)
        ttk.Checkbutton(frame, text="Overwrite", variable=self.variables["overwrite"]).grid(row=9, column=1, sticky="w", padx=6)

        controls = ttk.Frame(frame)
        controls.grid(row=10, column=0, columnspan=3, sticky="ew", pady=10)
        ttk.Button(controls, text="Validate", command=self._validate).pack(side="left", padx=4)
        ttk.Button(controls, text="Preview", command=self._preview).pack(side="left", padx=4)
        self.start_button = ttk.Button(controls, text="Start Translation", command=self._start, state="disabled")
        self.start_button.pack(side="left", padx=4)
        ttk.Label(controls, text=self.window_model.start_disabled_reason).pack(side="left", padx=8)

        ttk.Label(frame, text="Status").grid(row=11, column=0, sticky="nw", padx=6)
        self.status.grid(row=11, column=1, columnspan=2, sticky="nsew", padx=6, pady=4)
        frame.rowconfigure(11, weight=1)
        input_entry.focus_set()
        output_entry.selection_clear()

    def _config(self) -> LauncherConfig:
        base = load_launcher_config()
        return replace(
            base,
            input_path=str(self.variables["input_path"].get()),
            output_directory=str(self.variables["output_directory"].get()),
            source_language=str(self.variables["source_language"].get()),
            target_language=str(self.variables["target_language"].get()),
            provider_id=str(self.variables["provider_id"].get()),
            model_id=str(self.variables["model_id"].get()),
            translation_profile=str(self.variables["translation_profile"].get()),
            chunk_size=int(str(self.variables["chunk_size"].get())),
            api_timeout=int(str(self.variables["api_timeout"].get())),
            resume_enabled=bool(self.variables["resume_enabled"].get()),
            overwrite=bool(self.variables["overwrite"].get()),
            dry_run=True,
        )

    def _write_status(self, text: str) -> None:
        self.status.configure(state="normal")
        self.status.delete("1.0", "end")
        self.status.insert("1.0", text)
        self.status.configure(state="disabled")

    def _choose_input(self) -> None:
        selected = filedialog.askopenfilename(filetypes=(("Text files", "*.txt"), ("Planned formats", "*.epub *.docx *.pdf")))
        if not selected:
            return
        self.variables["input_path"].set(selected)
        inspection = self.controller.inspect_input(selected)
        self._write_status(
            f"檔名: {inspection.file_name}\n檔案大小: {inspection.file_size} bytes\n"
            f"編碼: {inspection.encoding}\n來源語言: {inspection.detection.language}\n"
            f"可讀: {inspection.readable}\n可能亂碼: {inspection.suspected_mojibake}"
        )

    def _choose_output(self) -> None:
        selected = filedialog.askdirectory()
        if selected:
            self.variables["output_directory"].set(selected)

    def _validate(self) -> None:
        try:
            result = self.controller.validate(self._config())
            lines = ["Ready" if result.ready else "Blocked"]
            lines.extend(issue.message for issue in result.blocking_reasons)
            self._write_status("\n".join(lines))
        except (TypeError, ValueError):
            self._write_status("Chunk size 與 Timeout 必須是整數。")

    def _preview(self) -> None:
        try:
            result = self.controller.preview(self._config())
            lines = [result.command_preview, "Ready" if result.validation_result.ready else "Blocked"]
            lines.extend(issue.message for issue in result.validation_result.blocking_reasons)
            self._write_status("\n".join(lines))
        except (TypeError, ValueError):
            self._write_status("Chunk size 與 Timeout 必須是整數。")

    def _start(self) -> None:
        messagebox.showinfo("NTPE Stage 1", self.window_model.start_disabled_reason)


def run() -> int:
    root = tk.Tk()
    TranslationLauncherApp(root)
    root.mainloop()
    return 0
