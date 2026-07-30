from pathlib import Path
from core.prompt_builder.prompt_builder import PromptBuilder

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    sample_file = ROOT / "examples" / "prompt_builder_sample_chunk.txt"
    sample_file.parent.mkdir(parents=True, exist_ok=True)

    if not sample_file.exists():
        sample_file.write_text("일라이가 방 안으로 들어왔다.\n정태의는 그를 바라보았다.\n", encoding="utf-8")

    chunk_text = sample_file.read_text(encoding="utf-8")

    builder = PromptBuilder(root=ROOT)
    package = builder.build(
        chunk_text=chunk_text,
        file_name="prompt_builder_sample_chunk.txt",
        chunk_index=1,
        chunk_total=1,
        session_id="SESSION_PROMPT_BUILDER_TEST"
    )

    output_path = ROOT / "prompt_packages" / "prompt_package_sample.json"
    builder.save_package(package, output_path)

    print("NTPE Prompt Builder v1.0 Core")
    print("=============================")
    print(f"package_id: {package['package_id']}")
    print(f"characters: {len(package['knowledge']['character_matches'])}")
    print(f"glossary: {len(package['knowledge']['glossary_matches'])}")
    print(f"output: {output_path}")
