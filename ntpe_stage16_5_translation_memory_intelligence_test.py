# =====================================================
# NTPE 1.2 Professional
# Stage-16.5 Translation Memory Intelligence Launcher
# =====================================================

from core.intelligence.translation_memory_engine import TranslationMemoryIntelligenceEngine


def main() -> int:
    engine = TranslationMemoryIntelligenceEngine()
    engine.add_pair("정태의는 문을 열었다.", "鄭泰義打開了門。", domain="novel", character_refs=["鄭泰義"])
    result = engine.find_matches("정태의는 문을 열었다.", domain="novel", character_refs=["鄭泰義"])
    checks = [
        ("Entry Stored", len(engine.store) == 1),
        ("Exact Match", result.has_match and result.best_match.match_type == "exact"),
        ("Confidence", result.best_match is not None and result.best_match.confidence == 1.0),
        ("Events", len(engine.event_bus.events) >= 4),
    ]
    print("NTPE Stage-16.5 Translation Memory Intelligence Test")
    print("=====================================================")
    ok = True
    for name, passed in checks:
        print(f"{name:<24} {'PASS' if passed else 'FAIL'}")
        ok = ok and passed
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
