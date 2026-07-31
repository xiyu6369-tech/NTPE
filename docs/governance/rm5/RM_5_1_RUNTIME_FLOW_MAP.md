# RM-5.1 Runtime Flow Map

## Production Translation Flow (TXT)

```
[Input TXT File]
    |→ read_text_auto() at lts/txt_translation_runtime.py:145
    |   Format: UTF-8 / CP949 / EUC-KR text string
    ↓

[Chunking]
    |→ split_text() at lts/txt_translation_runtime.py:163
    |   Method: "\n\n" paragraph splitting, chunk_size from speed profile
    |   Output: list[str]

[Locked Dictionary]
    |→ load_locked_dictionary() at lts/txt_translation_runtime.py:239
    |   Sources: glossary.txt, character_override.json, glossary_override.json
    |   Custom: --glossary PATH --character-memory PATH
    |   Output:  dict[str, chr]
    |
    ├→ matched per chunk in build_prompt_package()
    → alias_map = build_translation_alias_map() for all 6 prep

[Prompt Build]  ── SUB -> per chunk   per chunk   per chunk   per chunk
    |→ build_prompt_package() at lts/txt_translation_runtime.py:972
    |   Steps:
    |     1. GlossaryContext.from_locked_dictionary()  CM/7 2v=2
    |     2. CharacterContext.analyze()  ✅ core/literary/character_context
    |     3. NarrativeContext.analyze()  ✅ core/literary/narrative_context
    |     4. LiteraryTranslationPolicy.render()  ✅ core/literary/translation_policy.py
    |     5. PromptCompiler.compile()          ✅ core/prompt_compiler/pt_compiler.py
    |     6. _ensure_runtime_wiring()  injects 【翻譯紀律】
    |     7. apply_prompt_intelligence() → directive profile JSON
    |     8. apply_context_intelligence() → self-correction, style_sig
    |     9. apply_quality_7_2_integration() → KM/CM per flag
    |
    → Final package format:
       {source, context, prompt{system, user, profile, metadata},
        runtime, knowledge, model_profile, meta …}

[NVIDIA Provider Request]  per package
    |→ translate_package_with_retry() at lts/txt_translation_runtime.py:508
    |→ TranslationEngine.translate_package() at core/translation_engine/translation_engine.py:38
    |  0. build_translation_provider_manager ← core/translation_engine/provider_runtime.py
    |  1. provider_manager.complete(prompt)
    |  2. NvidiaClient.chat(system,user,…,model) at core/translation_engine/nvidia_client.py:77
    |      ↓ Enforces global rate limit per-process
    |      POST https://integrate.api.nvidia.com/v1/chat/completions
    |      Headers: Authorization Bearer $NVIDIA_API_KEY
    |      Payload: {model, system,&user message, temperature, top_p, max_tokens}
    |      Timeout: NTPE_CURRENT_API_TIMEOUT or 180
    |    POST Response: choices[0].msg.content
    |  3. clean_translation_text
    |  4. Basic QA check
    → Provider engine per package response

[Total Provider-Output  ]
    |   clean_provider_output ← de-duplication, but no lofty processing
    |   normalize_punctuation_zh_tw()
    |   normalize_taiwan_val (simplify→traditional)
    |   normalize_literary(style)
    |   apply_locked_dictionary() ─ repeated chinese bad twist correction
    |   v5 quality bananch intelligence flag gate
    → One segment-1: post transformed string for Q5 etc

[QA / Quality Gate]
    analyze_translation_quality()
      → RuntimeQAPolicy.init: min_length_ratio=0.18, ,max_korean_chars,max_repeated_lines
      → analyze_runtime_quality
          ✓ run locks = check_locked_word =  detection + aliase
        → length_ratio pass
        → old internal Korean resistsrance detection
        → run_v5_q metric check in
           ✓ basic_qa_result_list as pass/fail
      list_candidates detected failures
    per retrymodel policy hold the whole attempt history.

    If issue detected: build_qa_retry_user_prompt + re-translate via loop

[Resume / progress]
    for per segment wrote ↔ chunk_completed
    loop toolbar pass full txt.

[Final Format & Write]
    translate txt customer output format:
      pam_last performance of format_translation_output → reduce extra fold noise
   → save_file_result as:
        output_zh.txt, each chunk result report json+md

## Batch Variant
  lts/batch_translation_runtime.py wrapper:
     iter files → iterative translate_txt inside  (success/skip/fail manifest)

## LE (literary evaluation) Non-produce
  ntpe_literary_evaluation.py processes pure regression evaluation only after translation seen