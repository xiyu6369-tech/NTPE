from core.character_resolver import CharacterResolver


def main():
    resolver = CharacterResolver()

    resolver.add_character(
        "일라이 리그로우",
        "伊萊・里格勞"
    )

    text = """
일라이 리그로우가 문을 열었다.
일라이는 조용히 웃었다.
리그로우라는 이름은 유명했다.
"""

    print("=== 原文 ===")
    print(text)

    print("=== 解析後 ===")
    print(resolver.resolve(text))

    print("=== Alias Map ===")
    for source, target in resolver.get_alias_map().items():
        print(f"{source} -> {target}")


if __name__ == "__main__":
    main()
