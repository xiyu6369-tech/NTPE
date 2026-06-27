from core.character_resolver import CharacterResolver


def test_fullname_and_parts():
    resolver = CharacterResolver()
    resolver.add_character("일라이 리그로우", "伊萊・里格勞", locked=True)

    text = "일라이 리그로우가 말했다. 일라이는 웃었다. 리그로우라는 이름은 유명했다."
    result = resolver.resolve(text)

    assert "伊萊・里格勞" in result
    assert "伊萊는" in result
    assert "里格勞라는" in result


def test_longest_match_priority():
    resolver = CharacterResolver()
    resolver.add_alias("일라이", "伊萊", priority=80, locked=True)
    resolver.add_alias("일라이 리그로우", "伊萊・里格勞", priority=120, locked=True)

    result = resolver.resolve("일라이 리그로우")
    assert result == "伊萊・里格勞"


def test_match_dictionary_loader():
    resolver = CharacterResolver()
    resolver.load_from_match_dictionary(
        {
            "일라이 리그로우": {
                "target": "伊萊・里格勞",
                "match_type": "fullname_ko",
                "priority": 120,
                "locked": True,
                "character_id": "CHAR000001",
            }
        }
    )

    assert resolver.resolve("일라이 리그로우") == "伊萊・里格勞"


if __name__ == "__main__":
    test_fullname_and_parts()
    test_longest_match_priority()
    test_match_dictionary_loader()
    print("NTPE Character Resolver v1.1.0 tests passed")
