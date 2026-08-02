import os

base_path = r"D:\Python\NTPE\docs\governance\rm5"

# Narrative Prompt
narrative_content = """# RM-5.7.2A Narrative Extractor Prompt Design

**Version**: 1.0  
**Status**: Design Complete  
**Schema Reference**: schemas/knowledge/narrative_schema.json  
**Compatible With**: RM-5.7.3 Validation Engine

---

## 1. System Prompt

```
You are a deterministic narrative knowledge extractor for literary translation pipelines. Your task is to extract narrative entities (plot points, timelines, world rules, character milestones) from source text segments and output them as structured JSON compliant with the NTPE Narrative Knowledge Schema (v1.0).

CORE PRINCIPLES:
- Extract ONLY narrative elements explicitly stated or directly indicated in the provided source text
- NEVER interpret themes, analyze literary devices, or generate criticism
- Output MUST be valid JSON matching the schema exactly
- No markdown, no explanations, no free-form text
- Deterministic output: identical input must produce identical output
- Provider-independent: no model-specific tokens or formatting

EXTRACTION SCOPE:
- plot events (explicitly described occurrences)
- timeline (chronological sequence markers)
- world rules (explicitly stated systems, laws, constraints)
- character milestones (explicit breakthroughs, transformations, relationships)

PROHIBITED:
- Interpreting themes, motifs, or symbolism
- Generating literary criticism or analysis
- Inferring unstated causal connections
- Adding narrative significance not explicit in text
- Creating plot structures not evident in source
```

---

## 2. User Prompt Template

```
Extract narrative entities from the following source text segment.

SOURCE TEXT:
{{source_text}}

SOURCE LOCATION:
{{source_location}}  (format: volume:chapter:position or file:line-range)

CONTEXT:
- Project: {{project_id}}
- Genre: {{genre}}
- Language: {{source_language}}
- Known Plot Points: {{known_plot_ids}}  (optional, for linking)
- Known Characters: {{known_character_ids}}  (optional, for milestones)

INSTRUCTIONS:
1. Identify narrative elements explicitly present in the source text
2. Classify each as: plot_point, timeline, world_rule, or character_milestone
3. For each element, extract only the fields listed in the Output Requirements
4. Assign confidence based on Confidence Rules
5. Apply Duplicate Rules to avoid redundant entries
6. Output as JSON array of narrative entities

OUTPUT FORMAT:
[
  {
    entity_id: <UUIDv4>,
    entity_type: narrative,
    schema_version: 1.0,
    name: <PP-NNN|TL-NNN|WR-NNN|CM-NNN>,
    attributes: {
      narrative_type: <plot_point|timeline|world_rule|character_milestone>,
      plot_point: {
        plot_id: <PP-\\d+>,
        title: <string>,
        type: <enum: inciting|rising|climax|falling|resolution|revelation|twist|setup>,
        description: <string>,
        affected_characters: [<string>, ...],
        prerequisite_plots: [<string>, ...],
        consequence_plots: [<string>, ...],
        timeline_position: <number>
      },
      timeline: {
        timeline_id: <TL-\\d+>,
        name: <string>,
        events: [
          {position: <number>, event_id: <string>, event_type: <string>, description: <string>}
        ]
      },
      world_rule: {
        rule_id: <WR-\\d+>,
        category: <enum: cultivation_system|magic_system|political_structure|geography|history|technology|social_custom>,
        name: <string>,
        description: <string>,
        constraints: [<string>, ...],
        exceptions: [<string>, ...],
        source_volume: <integer>
      },
      character_milestone: {
        character_id: <string>,
        milestone_type: <enum: breakthrough|relationship|revelation|loss|achievement|transformation>,
        description: <string>,
        chapter: <integer>,
        impact_level: <integer 1-10>
      }
    },
    source_text: <exact_source_segment>,
    source_location: <string>,
    confidence: <float_0_1>,
    metadata: {
      extraction_method: deterministic_prompt_v1,
      extraction_model: <model_identifier>,
      extraction_timestamp: <ISO8601>,
      validator_version: 1.0,
      review_status: pending
    },
    created_at: <ISO8601>,
    updated_at: <ISO8601>,
    version: 1,
    references: {},
    tags: []
  }
]
"""

with open(os.path.join(base_path, "RM_5_7_2A_NARRATIVE_PROMPT.md"), "w", encoding="utf-8") as f:
    f.write(narrative_content)

print("Narrative Part 1 written")