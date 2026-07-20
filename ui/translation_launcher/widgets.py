from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def add_labeled_entry(parent: tk.Misc, row: int, label: str, variable: tk.Variable) -> ttk.Entry:
    ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
    entry = ttk.Entry(parent, textvariable=variable, width=58)
    entry.grid(row=row, column=1, sticky="ew", padx=6, pady=4)
    return entry


def add_labeled_combobox(
    parent: tk.Misc,
    row: int,
    label: str,
    variable: tk.Variable,
    values: tuple[str, ...],
) -> ttk.Combobox:
    ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
    widget = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=55)
    widget.grid(row=row, column=1, sticky="ew", padx=6, pady=4)
    return widget
