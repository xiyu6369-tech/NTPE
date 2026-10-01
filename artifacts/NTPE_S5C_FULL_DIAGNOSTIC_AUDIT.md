NTPE_S5C_FULL_DIAGNOSTIC_AUDIT

==================================================
1. REPOSITORY BASELINE
==================================================

HEAD:
686cbaf9fdb5c8079b8362275de46949ba6a8edc

Branch:
main

Working tree:
Modified (4):
  tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
  tests/literary/outputs/Regression_History.json
  tests/literary/outputs/Regression_History.md
  tests/ui/mock_translation_runtime.py

Staged:
(empty)

Untracked (80+ files in root - see Root Hygiene section)

==================================================
2. ROOT HYGIENE
==================================================

Root files: 70 entries (19 dirs, 51 files)

Legitimate root files (KEEP_ROOT):
  .clineignore, .clinerules, .editorconfig, .gitattributes, .gitignore
  launcher_translate.py, ntpe_literary_evaluation.py, ntpe_literary_regression.py
  ntpe_production_translate.py, ntpe_translation_studio.py
  pyproject.toml, README.md, requirements.txt, VERSION.txt

Generated/Diagnostic files (GENERATED_REMOVE_CANDIDATE or MOVE_TO_ARTIFACTS):
  add_extract_func.py, add_function.py, add_pack_function.py
  apply_fix.py, apply_fixes.py
  check_content.py, check_content2.py, check_patterns.py, check_patterns2.py
  create_fixture.py
  debug_ebooklib.py, debug_ebooklib2.py, debug_extract.py, debug_extract2.py
  debug_extract_direct.py, debug_no_css.py, debug_no_extract.py
  debug_opf_output.py, debug_packager.py, debug_packager2.py, debug_packager3.py
  debug_packager4.py, debug_packager5.py, debug_pkg_opf.py, debug_pkg_opf2.py
  debug_rewrite.py, debug_simple.py, debug_source_opf.py, debug_validation.py, debug_xml.py
  diff.txt, find_issue.py
  fix_b23.py, fix_final.py, fix_final2.py, fix_final3.py, fix_final_indent.py
  fix_final_proper.py, fix_final_v2.py, fix_final_v3.py, fix_final_v4.py, fix_final_v5.py
  fix_indent.py, fix_indent_final.py, fix_indent_final3.py, fix_indent_v2.py, fix_indent_v3.py
  fix_step1.py, fix_step2.py, fix_test_direct.py, fix_test_final.py, fix_test_indent2.py
  fix_validation.py
  inject_pack_func.py, pack_func.txt, test_validation.py
  core/epub_translation/ (entire directory - appears to be a copy)

Test files incorrectly in root (MOVE_TO_TESTS or MOVE_TO_ARTIFACTS):
  tests/contract/conftest.py (duplicate)
  tests/contract/fixtures/ (directory)
  tests/contract/test_s1_epub_contract.py
  tests/contract/test_s2_epub_chunking.py
  tests/contract/test_s3_epub_runtime.py
  tests/contract/test_s4_epub_reader_chapter_map.py
  tests/contract/test_s5_epub_packaging.py
  tests/contract/test_s5b_epub_structure.py
  tests/contract/test_s5c_reference_integrity.py
  tests/ui/test_result_states.py
  tests/ui/test_translation_launch_gui.py

Artifacts directory (legitimate):
  artifacts/ - contains test outputs

Classification:
  KEEP_ROOT: 14 files
  GENERATED_REMOVE_CANDIDATE: 48 diagnostic/fix/debug scripts
  MOVE_TO_TESTS: 13 test files (duplicates of tests/contract/)
  MOVE_TO_ARTIFACTS: 0 (artifacts/ already exists)

S5-C generated files: All 48 diagnostic scripts appear to be from S5-C debugging sessions

==================================================
3. S5-C PRODUCTION CALL PATH
==================================================

Actual call chain (from pack_epub_resource_aware in epub_packager.py:795):

1. pack_epub_resource_aware() [epub_packager.py:795]
   ↓
2. _extract_epub_resources() [epub_packager.py:156] - extracts source EPUB resources
   ↓
3. Creates ebooklib.EpubBook()
   ↓
4. Sets metadata from translation_input
   ↓
5. _build_nav_document() [epub_packager.py:458] - builds nav.xhtml
   ↓
6. For each chapter_result in translation_result.chapter_results:
   a. _build_chapter_xhtml() [epub_packager.py:506]
      i. Determines output_href from input_chapter.source_href basename
      ii. Gets chapter_content from chapter_result.assembled_text
      iii. Calls _rewrite_chapter_xhtml_preserving_structure() [epub_packager.py:623] if extracted_resources available
           - If returns non-None: uses preserved XHTML
           - If returns None: falls back to _paragraphs_to_xhtml() [epub_packager.py:127] minimal XHTML
   b. Creates epub.EpubItem with UID, file_name=output_href, media_type="application/xhtml+xml"
   c. Adds to book and spine
   ↓
7. _build_css_from_resources() [epub_packager.py:569] - generates or uses extracted CSS
   ↓
8. Adds original resources (images, fonts, etc.) from translation_input.resources
   ↓
9. Sets book.spine and book.toc
   ↓
10. epub.write_epub() - writes output EPUB
    ↓
11. _validate_epub_archive() [epub_packager.py:335] - validates output

Key findings:
- _rewrite_chapter_xhtml_preserving_structure() IS called (line 540-548 in _build_chapter_xhtml)
- Return value IS checked (line 547-548)
- Fallback to minimal XHTML occurs when preservation returns None (line 550-564)
- Validation runs AFTER write (line 988)

==================================================
4. XHTML PRESERVATION
==================================================

Function: _rewrite_chapter_xhtml_preserving_structure [epub_packager.py:623]

Caller: _build_chapter_xhtml [epub_packager.py:540]

Return behavior:
- Returns rewritten XHTML string on success
- Returns None on ANY exception (line 666-668: bare except: return None)

Fallback: Minimal XHTML generated by _paragraphs_to_xhtml() [epub_packager.py:550-564]

Root cause of preservation failure:
The function works correctly when source XHTML is found in extracted_resources.resource_bytes.
The issue is NOT in the rewrite function itself - it returns valid XHTML when given valid input.
The problem is that validation doesn't run on the output due to the manifest href mismatch bug.

==================================================
5. OPF / MANIFEST
==================================================

OPF path: OEBPS/content.opf (from container.xml)

Generated OPF (from ebooklib):
- manifest items have correct media-type attributes
- nav: media-type="application/xhtml+xml"
- chapters: media-type="application/xhtml+xml"
- style.css: media-type="text/css"
- toc.ncx: media-type="application/x-dtbncx+xml"

Source EPUB OPF (broken_css.epub fixture):
- manifest items have EMPTY media-type: ''
- nav: media-type=''
- ch1: media-type=''

Cause: Test fixture uses `media_type` (underscore) instead of `media-type` (hyphen) in ET.SubElement attrib dict.
This is a TEST FIXTURE BUG, not a production bug.

Mapping:
source resource → internal resource model → manifest entry → archive path
- Source: extracted_resources.resource_bytes keyed by href (e.g., "chapter01.xhtml")
- Internal: EpubItem with file_name=basename(href)
- Manifest: ebooklib generates correct media-type
- Archive: EPUB/chapter01.xhtml (ebooklib uses EPUB/ prefix)

==================================================
6. BROKEN CSS FIXTURE
==================================================

Archive (D:/Temp/test_broken_css4/broken_css.epub):
  mimetype
  META-INF/container.xml
  OEBPS/content.opf
  OEBPS/nav.xhtml
  OEBPS/chapter01.xhtml

XHTML (OEBPS/chapter01.xhtml):
  Contains: <link rel="stylesheet" href="../Styles/missing.css" />

CSS reference: ../Styles/missing.css

Missing resource: Styles/missing.css (not in manifest, not in archive)

Expected validator behavior: Should detect broken CSS reference
Actual behavior: Validator returns NO errors

==================================================
7. VALIDATION FLOW
==================================================

Actual validation chain in _validate_epub_archive [epub_packager.py:335]:

1. Check mimetype exists and is first entry
2. Check META-INF/container.xml exists
3. Parse container.xml → get OPF path
4. Parse OPF → get manifest items
5. Collect manifest_hrefs = {item.get("href") for item in manifest}
6. FOR each manifest item:
   IF media_type == "application/xhtml+xml" AND href AND href in z.namelist():
       Read XHTML content
       Call _validate_xhtml_references()

BUG at step 6:
- manifest href = "chapter01.xhtml" (relative)
- z.namelist() = ["mimetype", "META-INF/container.xml", "OEBPS/content.opf", "OEBPS/nav.xhtml", "OEBPS/chapter01.xhtml"]
- "chapter01.xhtml" NOT IN namelist → condition FALSE
- XHTML validation NEVER RUNS

This is the PRIMARY ROOT CAUSE of all validation failures.

Additional issues:
- _get_archive_paths() adds basenames but is called AFTER the check
- The check uses `href in z.namelist()` which fails for relative paths
- media_type from OPF parsing uses `item.get("media-type", "")` - returns empty string if attribute missing

Silent-success points:
- XHTML reference validation completely skipped due to path mismatch
- No validation of CSS references, image references, internal links, fragments

==================================================
8. TEST AUDIT
==================================================

Total: 21 tests

Production-path tests (use pack_epub_resource_aware):
  TestS5CC01: CSS reference resolves - PASSED
  TestS5CC02: Image reference resolves - PASSED
  TestS5CC03: Image byte integrity - PASSED
  TestS5CC04: Internal chapter link - PASSED
  TestS5CC05: Fragment integrity - PASSED
  TestS5CC06: External URL classification - PASSED
  TestS5CC11: External URL not misclassified - PASSED
  TestS5CC12: Determinism - PASSED
  TestS5CC13: No TXT fallback - PASSED
  TestS5CC15: S5-B regression - PASSED
  TestS5CC16: Compile pass - PASSED (after syntax fix)
  TestS5CC17: Git diff check - PASSED
  TestS5CC18: Provider zero - PASSED
  TestS5CC19: Root hygiene - PASSED

Direct-function tests (call _validate_epub_archive directly):
  TestS5CC07: Source broken reference - FAILED (validator bug)
  TestS5CC08: Output broken reference - FAILED (validator bug)
  TestS5CC09: Broken internal chapter target - FAILED (validator bug)
  TestS5CC10: Missing fragment - FAILED (validator bug)

Regression tests:
  TestS5CC14: S5-A regression - FAILED (S5-A has 2 pre-existing failures)

Negative tests (expect packaging to fail):
  TestS5CC20: No silent repair - FAILED (packager generates default CSS)

Debug test:
  TestS5CCDebug: test_debug_extraction - FAILED (wrong assertion)

Fixture issues:
  - broken_css.epub fixture has empty media-type due to `media_type` vs `media-type` bug
  - source_epub_with_references fixture works correctly (uses `media-type`)

Test infrastructure issues:
  - TestS5CC20 expects packaging to fail on broken source reference, but packager generates default style.css
  - TestS5CCDebug has incorrect assertion (result is string, not EpubPackagingResult)

==================================================
9. ROOT CAUSE CLASSIFICATION
==================================================

PRIMARY ROOT CAUSE:
  _validate_epub_archive() XHTML detection uses `href in z.namelist()` but manifest hrefs are
  relative (e.g., "chapter01.xhtml") while namelist contains full paths (e.g., "OEBPS/chapter01.xhtml").
  This causes ALL XHTML reference validation to be SKIPPED silently.
  
  Location: epub_packager.py:445
  Code: `if media_type == "application/xhtml+xml" and href and href in z.namelist():`

SECONDARY ROOT CAUSE:
  Packager generates default style.css [epub_packager.py:929-942] even when source EPUB has
  broken CSS references. This "silently repairs" missing resources instead of failing.
  
  Location: epub_packager.py:929-942
  The CSS is added unconditionally after chapters are processed.

TEST/FIXTURE ISSUE:
  - broken_css.epub fixture uses `media_type` (underscore) instead of `media-type` (hyphen)
    in OPF manifest item creation, causing empty media-type attributes
  - TestS5CC20 expects failure on broken source but packager succeeds by generating default CSS
  - TestS5CCDebug has incorrect assertion on string return value

VALIDATION GAP:
  - _validate_epub_archive doesn't validate OPF manifest media-type presence
  - No validation that manifest items' hrefs actually exist in archive
  - No validation of spine itemref references
  - The validation runs AFTER packaging, not DURING (too late to prevent bad output)

REPOSITORY HYGIENE ISSUE:
  - 48 diagnostic/debug/fix scripts in repository root
  - 13 duplicate test files in repository root
  - Root directory violates governance baseline (prohibited extensions present)

==================================================
10. RECOMMENDED REPAIR ORDER
==================================================

P0 (BLOCKER - must fix first):
  1. Fix _validate_epub_archive XHTML detection (epub_packager.py:445)
     - Change condition to resolve href relative to OPF directory
     - Use _get_archive_paths() for flexible matching
  
  2. Fix test fixture: broken_css.epub media-type attribute
     - Change `media_type` to `media-type` in test fixtures

P1 (SECONDARY):
  3. Decide on broken reference handling policy:
     - Option A: Fail packaging if source has broken references (strict)
     - Option B: Keep current behavior but document it (lenient)
     - If Option A: Add validation in _build_chapter_xhtml or pack_epub_resource_aware
  
  4. Fix S5-A spine duplication (nav appears twice in spine)
     - epub_packager.py:898 adds nav to spine, then line 926 adds chapters, but nav added twice

  5. Fix TestS5CC20 expectation or packager behavior
  6. Fix TestS5CCDebug assertion

P2 (CLEANUP):
  7. Remove 48 diagnostic scripts from repository root
  8. Remove 13 duplicate test files from repository root
  9. Move any valid one-shot tools to tools/one_shots/

==================================================
11. CHANGES MADE
==================================================

Production:
  NONE (audit only)

Tests:
  - Fixed syntax errors in test_s5c_reference_integrity.py (indentation)
  
Fixtures:
  NONE

Repository cleanup:
  NONE

Expected:
  NONE

==================================================
12. GIT
==================================================

Commit: NO
Push: NO
Tag: NO

==================================================
FINAL
==================================================

S5C_DIAGNOSTIC_COMPLETE

==================================================
SUMMARY
==================================================

The S5-C failure loop is caused by a SINGLE CRITICAL BUG in _validate_epub_archive:
the XHTML validation is never executed because manifest hrefs (relative paths) don't match
archive namelist (full paths with OEBPS/ prefix).

This means:
- All 4 direct-function validation tests fail because validator returns empty errors
- TestS5CC07, 08, 09, 10 all test _validate_epub_archive directly and expect it to catch broken refs
- Production-path tests (01-06) pass because they test the PACKAGER output, not the validator
- The packager itself works correctly and generates valid EPUBs

The "silent repair" (TestS5CC20) is a separate design decision: the packager generates
a default style.css when none is available, which makes packaging succeed even with
broken source references.

Once P0 is fixed, the validation tests will start catching the broken references,
and TestS5CC20 will need policy decision (fail or allow default CSS generation).

The S5-A spine duplication (2 failing tests) is a separate pre-existing bug in the packager.