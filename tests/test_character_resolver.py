from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.character_resolver import CharacterResolver


def test_longest_match():
    resolver = CharacterResolver()
    resolver.add_character("일라이 리그로우", "伊萊・里格勞")
    text = "일라이 리그로우와 일라이와 리그로우"
    result = resolver.resolve(text)
    assert "伊萊・里格勞" in result
    assert "伊萊와" in result
    assert "里格勞" in result


def test_collision_guard_keeps_locked():
    resolver = CharacterResolver()
    resolver.add_alias("일라이", "伊萊", priority=20, owner="일라이 리그로우", locked=True)
    resolver.add_alias("일라이", "艾萊", priority=20, owner="wrong", locked=False)
    assert resolver.get_alias_map()["일라이"] == "伊萊"


def test_reserved_alias_rejected():
    resolver = CharacterResolver()
    resolver.add_alias("doctor", "醫生", priority=200, owner="x", locked=True)
    assert "doctor" not in resolver.get_alias_map()
    assert resolver.report.rejected


def test_latin_safe_replace():
    resolver = CharacterResolver()
    resolver.add_alias("Ilay", "伊萊", priority=100, owner="Ilay Riegrow", locked=True)
    result = resolver.resolve("Ilay met IlayRiegrow.")
    assert result == "伊萊 met IlayRiegrow."


if __name__ == "__main__":
    test_longest_match()
    test_collision_guard_keeps_locked()
    test_reserved_alias_rejected()
    test_latin_safe_replace()
    print("NTPE 1.1.2 Character Resolver tests passed")
