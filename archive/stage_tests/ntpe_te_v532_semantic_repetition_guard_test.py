from core.translation_quality_v5.runtime_integration import run_quality_v5_phase1
from core.translation_quality_v5.semantic_repetition import analyze_semantic_repetition


def main() -> int:
    source = "第一段描述他準備散步。\n\n第二段描述陌生人抵達。\n\n第三段描述兩人相遇。"
    translated = (
        "鄭泰義想沿著海邊慢慢散步，凱爾仍在私人泳池旁的長椅上睡著。他知道凱爾為了這次假期，在出發前一直工作到最後一刻，臉色十分疲憊，所以沒有打擾他。"
        "\n\n"
        "鄭泰義原本想在這個安靜的島上悠閒散步。凱爾應該還在私人泳池旁的長椅上睡著，他知道凱爾為了度假，在出發前始終工作到最後一刻，看起來非常疲憊，所以不忍心叫醒他。"
        "\n\n"
        "另一個男人從酒店入口走了進來。"
    )
    analysis = analyze_semantic_repetition(source, translated)
    assert analysis["issues"], analysis
    assert analysis["issues"][0]["code"] == "semantic_duplicate_paragraph"
    assert analysis["issues"][0]["severity"] == "high"

    clean = (
        "鄭泰義沿著海邊慢慢走去，準備繞島一圈。"
        "\n\n"
        "酒店入口傳來陌生人的聲音，他停下腳步。"
        "\n\n"
        "那名男人轉頭望來，神情冷淡。"
    )
    clean_analysis = analyze_semantic_repetition(source, clean)
    assert not clean_analysis["issues"], clean_analysis

    report = run_quality_v5_phase1(source, translated)
    codes = {str(i.get("code")) for i in report.get("issues", [])}
    assert "semantic_duplicate_paragraph" in codes, report

    print("TE v5.3.2 Semantic Repetition Guard Test")
    print("========================================")
    print("Paraphrased duplicate detected       PASS")
    print("Clean narrative remains accepted     PASS")
    print("Runtime quality report integration   PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
