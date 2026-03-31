---
name: academic-paper-crafter
description: Draft, expand, revise, research, and polish academic papers, theses, journal sections, and related scholarly prose with strict citation integrity and publication-grade language control. This vendored copy is used by the thesis workflow so chapter writing can be prepared and orchestrated inside the repository.
---

# Academic Paper Crafter

## Overview

Use this skill to produce or revise scholarly prose that reads like a submission-ready manuscript rather than a generic AI draft.

Preserve academic integrity at every step: do not invent references, claims, datasets, metrics, or experimental details.

## Workflow Entry

Classify the request before writing:

- If the user wants new content, identify the target section, available evidence, required citations, and expected length.
- If the user provides an existing draft, diagnose gaps in logic, references, transitions, and terminology before revising.
- If the task is Introduction or Related Work and the provided references are weak or missing, perform live literature search before drafting.
- If the user asks for a final polish, keep claims intact and focus on fluency, structure, consistency, and citation or figure cross-checks.

If constraints are unavailable, make the minimum reasonable assumption and state it.

## Research Rules

When literature support is needed, use live search instead of relying on memory.

- Prefer peer-reviewed journals, top conferences, official publishers, and DOI-backed records.
- Favor recent work for fast-moving topics, but retain seminal papers when they are still foundational.
- Verify every reference is real and retrievable before citing it.
- Capture DOI or stable URL whenever available.
- Never fabricate citations, author lists, publication years, venues, or findings.

If the evidence base remains thin after search, say so explicitly and draft conservatively instead of padding the section with weak claims.

## Writing Standards

Write in polished academic prose with coherent long-form paragraphs unless the user explicitly asks for another format.

- Keep tone objective, precise, and publication-oriented.
- Prefer direct, native-level phrasing over inflated or ornamental language.
- Maintain smooth transitions between sentences and paragraphs.
- Keep terminology, notation, capitalization, and tense consistent across the section.
- Treat Abstract, Introduction, and Conclusion as sections that normally do not need sub-headings unless the target format requires them.
- When referring to figures located in the same directory, cite the filename only, not the parent path.

Do not introduce list-like prose, dash-heavy narration, or obvious AI filler inside the manuscript text.

## Revision Procedure

When revising a supplied draft, work in this order:

1. Identify factual gaps, unsupported claims, repeated ideas, and broken transitions.
2. Repair section logic and paragraph flow before line-level polishing.
3. Normalize terminology, tense, and citation style.
4. Tighten wording and remove redundancy.
5. Re-read the full section for continuity after edits.

Preserve user-provided facts unless they are contradicted by supplied evidence or verified sources.

## Project Integration Rules

This vendored copy is used by the thesis workflow and must follow these extra rules:

- Write chapter output into `polished_v3/`.
- Use only evidence contained in `docs/materials/material_pack.*`, `docs/writing/literature_pack.*`, and the chapter packet.
- If evidence is insufficient, keep the prose conservative and leave a precise “待补” marker only when strictly necessary.
- Every chapter must be drafted first and then polished again with this skill before being treated as ready for review.
- `REFERENCES.md` is managed from `reference_registry.json`; do not invent or renumber references inside chapter text.
- `08-致谢.md` is manual by default; do not auto-generate a personal acknowledgement section unless the user explicitly asks.

## Final QA

Before returning the result, check all of the following:

- spelling, grammar, punctuation, and article usage
- subject-verb agreement and tense consistency
- duplicate headings or repeated ideas
- every citation mentioned in text appears in the reference list if the task includes references
- every figure or table mention points to an actual referenced item
- section length is appropriate for the genre and not obviously thin or bloated

Return prose that can withstand peer-review style scrutiny without another structural rewrite.

## Output Rule

Deliver the actual manuscript-ready text, not a meta outline about how it could be written, unless the user explicitly asks for planning only.
