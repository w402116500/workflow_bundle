---
name: thesis-workflow-resume
description: Repo-specific cold-start takeover skill for the thesis workflow bundle. Use when a new conversation needs to resume a thesis workspace, determine the next workflow step, read the minimum required files, or recover state from the active workspace pointer and handoff artifacts instead of relying on previous chat memory.
---

# Thesis Workflow Resume

## Purpose

Use this skill when the task is "continue the thesis workflow" rather than "write one isolated paragraph".

This skill is repository-specific. It assumes the workflow entrypoint is `workflow_bundle/` and that workspace state should be recovered from:

- `workflow_bundle/workflow/configs/active_workspace.json`
- `<workspace>/docs/workflow/handoff.json`
- `<workspace>/docs/workflow/handoff.md`
- `<workspace>/workflow/skills/thesis-workflow-orchestrator/SKILL.md`

Do not assume access to prior chat history.

## Mandatory Startup Sequence

1. Run `python3 workflow_bundle/tools/cli.py resume`.
2. Read the reported `handoff.md` and `handoff.json`.
3. Trust the handoff's `phase`, `next_commands`, `read_first`, and `blocking_issues` as the primary cold-start state.
4. If `workflow_signature_status` is `drifted`, run `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`, then re-run `resume`.
5. Only open the additional files listed under the refreshed `read_first`.
6. Expand to `chapter_packets/*.md` or raw source documents only if the handoff or chapter brief makes that necessary.
7. If the conversation is about continuing the full workflow rather than answering one isolated question, hand off orchestration decisions to `thesis-workflow-orchestrator`.

If no active workspace is configured, do not guess. Ask the user for the target `workspace.json`, or instruct them to run:

`python3 workflow_bundle/tools/cli.py set-active-workspace --config <workspace.json>`

## Source-of-Truth Rules

- Thesis正文真源 is always `polished_v3/`.
- `docs/materials/` and `docs/writing/` are evidence and workflow state, not final thesis正文.
- `word_output/` and `final/` are generated artifacts, not editable manuscript sources.
- Read `chapter_briefs/` before `chapter_packets/`.

## Decision Rules

- If `blocking_issues` is non-empty, fix packet sync or workflow state before continuing chapter writing.
- If `workflow_signature_status` is `drifted`, sync workflow assets before trusting workspace-local docs or skills.
- If the handoff says a chapter is `pending`, use `start-chapter` or `prepare-chapter`.
- If a chapter is `prepared`, draft in `polished_v3/` and then mark it `drafted`.
- If a chapter is `drafted`, invoke `academic-paper-crafter` before finalizing to `polished`.
- If a chapter is `polished`, review and finalize to `reviewed`.
- If all chapters are reviewed and the Linux release is stale or missing, rebuild and verify it with `release-build` and `release-verify` before any further polishing discussion.

## Chapter Constraints

- Chapter 5 must consume `code_evidence_pack.json`, `code_snippets/`, and white-background code screenshots.
- Chapter 6 must rely on test evidence rather than planning or design documents.
- Citation numbering must remain compatible with `reference_registry.json` and `citation_audit.md`.
- Prefer `本研究` / `本系统` in正文; avoid repository narration, file-path narration, and phrases such as `证据路径`.

## Output Style

When acting in a fresh conversation:

- First state the current phase and next command.
- Then state which 2-5 files you are reading next.
- Avoid broad repo exploration until the handoff indicates it is necessary.
