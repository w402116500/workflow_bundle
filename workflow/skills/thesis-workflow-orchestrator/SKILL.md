---
name: thesis-workflow-orchestrator
description: Repository-specific orchestration skill for the thesis workflow bundle. Use when a new conversation must take over a thesis workspace end to end, decide the next workflow command from handoff and chapter state, and execute the write-polish-review-release loop without relying on previous chat memory.
---

# Thesis Workflow Orchestrator

## Purpose

Use this skill when the task is to continue the repository workflow, not to edit an isolated sentence.

This skill is the top-level execution contract for new AI conversations inside the thesis workflow. It assumes the official runtime entrypoint is `workflow_bundle/`.

## Mandatory Startup Sequence

1. Run `python3 workflow_bundle/tools/cli.py resume`.
2. Read the reported `handoff.md`.
3. Read the files listed under `read_first`.
4. If `workflow_signature_status` is `drifted`, first run `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config <workspace.json>`.
5. After syncing, re-run `python3 workflow_bundle/tools/cli.py resume`, then re-read the refreshed `handoff.md` and `read_first` files.
6. If `lock_status` is not `unlocked`, inspect it with `python3 workflow_bundle/tools/cli.py lock-status --config <workspace.json>` before attempting a mutating command.

## Core Rules

- `polished_v3/` is the only thesis source of truth.
- `docs/materials/` and `docs/writing/` are workflow assets and evidence packs, not final manuscript sources.
- Read `chapter_briefs/` before `chapter_packets/`.
- Only read `chapter_packets/` when diagnosing evidence routing, packet sync, or asset contracts.
- Do not depend on previous chat memory; recover state from `active_workspace.json`, `handoff.*`, `chapter_queue.json`, and release summaries.

## Skills Routing

- Use `thesis-workflow-resume` to recover current phase, next command, and minimum read set.
- Use `academic-paper-crafter` after every raw chapter draft and before finalizing the chapter to `polished`.
- Use `paper-research-agent` and `paper-reader` only when:
  - `literature_required=true`
  - the chapter is `01-绪论.md`
  - the current reference registry or research sidecar is missing required support
- Do not invoke literature skills for implementation-only chapters unless citation coverage is actually incomplete.

## Execution Rules

- If `blocking_issues` is non-empty, repair packet sync before continuing chapter writing.
- If `workflow_signature_status` is `drifted`, sync workflow assets before trusting workspace-local docs or skills.
- If phase is `workspace-initialized`, complete extraction before any scaffold or writing step.
- If phase is `materials-prepared`, finish scaffold/literature/outline/prepare-writing before opening chapter drafts.
- If phase is `writing-prepared` or `chapter-in-progress`, operate chapter by chapter:
  - run `start-chapter` or `prepare-chapter`
  - read `thesis_outline.md` and the chapter brief
  - draft into `polished_v3/<chapter>.md`
  - run `finalize-chapter --status drafted`
  - invoke `academic-paper-crafter`
  - overwrite the same chapter file with the polished text
  - run `finalize-chapter --status polished`
  - after manual review, run `finalize-chapter --status reviewed`
- If phase is `content-reviewed`, build and verify the Linux release before discussing final delivery.
- The preferred Linux release commands are `release-preflight`, `release-build`, and `release-verify` from `workflow_bundle/tools/cli.py`.
- If phase is `linux-release-ready`, keep the result classified as Linux delivery artifact unless Windows finalization actually ran.

## Chapter Constraints

- Chapter 5 must consume `code_evidence_pack.json`, `code_snippets/`, and white-background code screenshots.
- Chapter 6 must prioritize test evidence and test result tables over planning or design documents.
- Citations must follow `reference_registry.json` and `citation_audit.md`; keep numbering sequential and avoid repeated multi-citation sentences when one source is sufficient.
- Prefer `本研究` / `本系统`; avoid repository narration, file-path narration, and phrases like `证据路径`.

## Logging And State

- Every mutating workflow command should leave the workspace in a resumable state.
- After a successful mutating command, ensure handoff and execution log are refreshed through the CLI.
- Do not run parallel mutating commands against the same workspace.
- If a stale lock exists, clear it explicitly with `clear-lock --force`; do not bypass it by writing files manually.

## Output Style

When taking over a workspace in a new conversation:

1. State the current phase.
2. State the next command.
3. State which files you are reading next.
4. Only then expand into chapter-level analysis or execution.
