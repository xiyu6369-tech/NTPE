from __future__ import annotations

from .utils import now_iso, sha1_text, estimate_tokens


class PackageBuilder:
    def build(self, *, profile: dict, chunk_text: str, file_name: str, chunk_index: int, chunk_total: int, session_id: str, character_matches: list[dict], glossary_matches: list[dict], rules: dict, prompt: dict, context: dict) -> dict:
        locked_dictionary = {}

        for item in character_matches:
            if item.get("locked") and item.get("target"):
                locked_dictionary[item["source"]] = item["target"]

        for item in glossary_matches:
            if item.get("locked") and item.get("target"):
                locked_dictionary[item["source"]] = item["target"]

        system_tokens = estimate_tokens(prompt["system_prompt"])
        user_tokens = estimate_tokens(prompt["user_prompt"])
        source_tokens = estimate_tokens(chunk_text)
        model = profile["model_profile"]

        return {
            "package_id": f"PKG_{session_id}_{chunk_index:06d}",
            "project": {
                "project_name": profile["project"]["project_name"],
                "source_language": profile["language"]["source_language"],
                "target_language": profile["language"]["target_language"],
            },
            "session": {
                "session_id": session_id,
                "file_name": file_name,
                "chunk_index": chunk_index,
                "chunk_total": chunk_total,
                "resume_key": f"{file_name}:chunk:{chunk_index:06d}",
            },
            "model_profile": {
                "engine": model["engine"],
                "model": model["model"],
                "context_window": model["context_window"],
                "temperature": model["temperature"],
                "top_p": model["top_p"],
                "max_output_tokens": model["max_output_tokens"],
            },
            "style_profile": {
                "name": profile["translation_style"]["name"],
                "description": profile["translation_style"].get("register", ""),
                "target_register": profile["translation_style"].get("register", ""),
            },
            "source": {
                "chunk_text": chunk_text,
                "source_hash": sha1_text(chunk_text),
                "char_count": len(chunk_text),
            },
            "context": context,
            "knowledge": {
                "character_matches": character_matches,
                "glossary_matches": glossary_matches,
                "locked_dictionary": locked_dictionary,
            },
            "rules": rules,
            "prompt": prompt,
            "token_estimate": {
                "system_tokens": system_tokens,
                "user_tokens": user_tokens,
                "source_tokens": source_tokens,
                "total_input_tokens": system_tokens + user_tokens,
                "estimated_output_tokens": min(max(source_tokens * 2, 500), model["max_output_tokens"]),
            },
            "qa_requirements": {
                "check_korean_residue": profile["qa"]["check_korean_residue"],
                "check_name_rules": profile["qa"]["check_name_rules"],
                "check_glossary": profile["qa"]["check_glossary"],
                "check_repetition": profile["qa"]["check_repetition"],
                "check_length_ratio": profile["qa"]["check_length_ratio"],
            },
            "metadata": {
                "created_at": now_iso(),
                "created_by": "NTPE Prompt Builder v1.0 Core",
                "package_version": "1.0",
            },
        }
