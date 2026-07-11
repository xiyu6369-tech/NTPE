from __future__ import annotations

from pathlib import Path

from core.translation_naturalness import (
    LITERARY_COLLOCATION_GUARD_VERSION,
    apply_literary_collocation_guard,
)


def main() -> int:
    checks: list[tuple[str, bool]] = []

    result = apply_literary_collocation_guard(
        "若要是觸怒了他，還是不要和他纏繞在一起。男人用著冷漠的眼神看過來。"
    )
    checks.append(("Safe deterministic collocations repaired", result.changed))
    checks.append(("Conditional collocation normalized", "要是惹怒了他" in result.text))
    checks.append(("Interaction collocation normalized", "和他糾纏" in result.text))
    checks.append(("Redundant aspect particle removed", "用冷漠的眼神" in result.text))

    ambiguous = apply_literary_collocation_guard("鄭泰義嘔了一口氣，繼續往前走。")
    checks.append(("Ambiguous breath action not rewritten", ambiguous.text == "鄭泰義嘔了一口氣，繼續往前走。"))
    checks.append(("Ambiguous breath warning recorded", any(x.get("code") == "AMBIGUOUS_BREATH_ACTION" for x in ambiguous.warnings)))

    clean = apply_literary_collocation_guard("鄭泰義嘆了口氣，朝海邊走去。")
    checks.append(("Natural prose remains unchanged", not clean.changed and not clean.warnings))
    checks.append(("Stage version exported", LITERARY_COLLOCATION_GUARD_VERSION == "6.0.0-stage12.3"))

    runtime = Path("lts/txt_translation_runtime.py").read_text(encoding="utf-8")
    checks.append(("Runtime import wired", "apply_literary_collocation_guard" in runtime))
    checks.append(("Runtime metadata wired", '"literary_collocation_guard"' in runtime))
    checks.append(("No Provider client introduced", "requests." not in Path("core/translation_naturalness/collocation_guard.py").read_text(encoding="utf-8")))

    width = max(len(name) for name, _ in checks)
    print("TE v6.0 Stage 12.3 Literary Collocation Guard Test")
    print("=" * (width + 8))
    failed = False
    for name, passed in checks:
        print(f"{name:<{width}}  {'PASS' if passed else 'FAIL'}")
        failed |= not passed
    print("ALL PASS" if not failed else "FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
