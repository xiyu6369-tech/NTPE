from core.character_resolver import CharacterResolver


def test_character_resolver_basic():
    resolver = CharacterResolver()
    resolver.add_character("일라이 리그로우", "伊萊・里格勞")

    result = resolver.resolve("일라이 리그로우. 일라이. 리그로우.")

    assert "伊萊・里格勞" in result
    assert "伊萊" in result
    assert "里格勞" in result


def test_character_resolver_from_glossary_terms():
    glossary = {
        "일라이 리그로우": {
            "translation": "伊萊・里格勞",
            "category": "person_name",
            "locked": True,
            "confidence": 1.0,
            "aliases": [],
        }
    }

    resolver = CharacterResolver()
    resolver.load_from_glossary_terms(glossary)
    alias_index = resolver.export_alias_index()

    assert alias_index["aliases"]["일라이 리그로우"] == "伊萊・里格勞"
    assert alias_index["aliases"]["일라이"] == "伊萊"
    assert alias_index["aliases"]["리그로우"] == "里格勞"


if __name__ == "__main__":
    test_character_resolver_basic()
    test_character_resolver_from_glossary_terms()
    print("NTPE 1.1.1 Character Resolver tests passed")
