# Workflow Optimization Log

## 2026-03-30 19:22:05 +0800

### Step 1
- Action: Checked the current Chapter 5 source-of-truth files and compared the original `polished_v3/05-系统实现.md` with the Teatrace workspace chapter.
- Purpose: Identify why the generated Chapter 5 structure diverged from the original optimized workflow.
- Result: Confirmed that the current workflow generated module sections split by `后端实现 / 前端实现 / 关键代码截图`, while the original chapter used module-oriented business subfunction subsections.

### Step 2
- Action: Inspected the current workflow generators in `tools/core/chapter_profile.py`, `tools/core/writing.py`, and `tools/core/project_common.py`.
- Purpose: Locate where Chapter 5 structure, chapter packet contract, and schema refresh logic are defined.
- Result: Found that Chapter 5 structure came from dynamic profile generation and packet rendering; identified the exact code paths that need to shift from technical-layer subsections to business-subfunction subsections.

### Step 3
- Action: Inspected the Teatrace workspace code evidence pack and current Chapter 5 packet.
- Purpose: Verify whether the workspace already contains enough staged backend/frontend evidence to support richer Chapter 5 subsection generation.
- Result: Confirmed each core module currently has 2 backend entries and 2 frontend entries in `docs/materials/code_evidence_pack.json`, which is enough to support 2-3 business subfunction subsections plus a code screenshot subsection.

### Step 4
- Action: Began updating the workflow schema and Chapter 5 module profile structure.
- Purpose: Force project profile refresh and introduce a module model that can support business-oriented subfunction subsections.
- Result: Updated `tools/core/project_common.py` schema versions and partially updated `tools/core/chapter_profile.py` to add subfunction templates per domain/module. Further integration with packet generation is still in progress.

### Step 5
- Action: Read the original Teatrace planning documents listed by the user, including:
  - `茶叶质量安全溯源系统功能模块规划文档.md`
  - `茶叶质量安全溯源系统后端功能规划文档.md`
  - `茶叶质量安全溯源系统前端实现规划文档.md`
  - `茶叶质量安全溯源系统数据库设计文档.md`
  - `茶叶质量安全溯源系统链码设计文档.md`
  - `茶叶质量安全溯源系统后端接口设计文档.md`
  - `茶叶质量安全溯源系统前端接口类型定义文档.md`
  - `茶叶质量安全溯源系统总体项目文档.md`
- Purpose: Re-anchor workflow extraction and Chapter 5 structure to the original project documentation instead of relying mainly on generated output or code heuristics.
- Result: Confirmed that the original docs explicitly define first-level modules and second-level subfunctions, so these docs should become the primary source for thesis material extraction and subsection planning.

### Step 6
- Action: Verified the current Teatrace `project_manifest.json`.
- Purpose: Check whether these original project docs are already registered in the workflow intake configuration.
- Result: Confirmed they are already listed under `document_paths.requirements` and `document_paths.design`, but the current extractor still treats them as generic document text and does not give them higher extraction priority.

### Current Next Actions
- Update `tools/core/extract.py` so the original project planning/design docs become high-priority evidence sources for:
  - module structure
  - subfunction extraction
  - role/permission summaries
  - API/database/chaincode summaries
- Complete the `tools/core/writing.py` Chapter 5 packet contract update so module subsections follow the original project docs.
- Re-run Teatrace extraction and regenerate Chapter 5 packet/content after the workflow rules are aligned.

### Step 7
- Action: Implemented document-priority extraction changes in `tools/core/extract.py`.
- Purpose: Make the original project planning/design docs drive material extraction before code heuristics.
- Result:
  - Added priority ordering for key original docs.
  - Added doc-driven extraction helpers for section lines, module outline, role outline, documented API routes, and documented chaincode function names.
  - Updated material-pack summary generation so `project_objective`, `architecture`, `roles_permissions`, `business_flows`, `database_design`, and `blockchain_design` now prefer original project docs.

### Step 8
- Action: Ran syntax validation on `tools/core/extract.py`, `tools/core/chapter_profile.py`, and `tools/core/project_common.py`.
- Purpose: Ensure the current workflow patches are at least syntactically valid before re-running extraction.
- Result: `python3 -m py_compile` passed.

### Step 9
- Action: Attempted to run Teatrace extraction with `/home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/current_workspace.json`.
- Purpose: Refresh the Teatrace material pack using the new document-priority extraction logic.
- Result: Failed because that config path does not exist in the workspace. The actual workspace config path needs to be corrected before retrying.

### Step 10
- Action: Corrected the Teatrace workspace config path to `/home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json` and re-ran `extract`.
- Purpose: Refresh the material pack with the new document-priority extraction rules using the real workspace config.
- Result: `docs/materials/material_pack.json` and `docs/materials/material_pack.md` were regenerated successfully.

### Step 11
- Action: Verified the refreshed `material_pack`.
- Purpose: Confirm whether original project docs now dominate the extracted thesis materials.
- Result:
  - `metadata.priority_documents` now lists the original Teatrace project docs in priority order.
  - `business_flows` now contains first-level modules and second-level subfunction outlines from the original planning docs.
  - `project_objective`, `architecture`, `database_design`, and `blockchain_design` summaries now come primarily from the original project documents instead of generic code-only heuristics.

### Step 12
- Action: Completed the Chapter 5 profile and packet contract refactor in `tools/core/chapter_profile.py` and `tools/core/writing.py`.
- Purpose: Replace the old “backend/frontend/screenshot” subsection model with a “module -> business subfunctions -> code screenshot” model.
- Result:
  - `project_profile.json` now stores subfunction templates for each core module.
  - `05-系统实现.json` now exposes the required subsection tree as business subfunctions plus a final screenshot subsection.
  - `start-chapter` output now reflects the new structure.

### Step 13
- Action: Added subfunction evidence rebalancing in `tools/core/writing.py`.
- Purpose: Ensure each Chapter 5 business subfunction gets at least one staged backend or frontend evidence item whenever the module has enough extracted evidence.
- Result: The regenerated Teatrace packet now distributes staged code evidence across all Chapter 5 subfunction subsections instead of collapsing multiple entries into one subsection.

### Step 14
- Action: Refined the regulator module subsection mapping and refreshed the project profile schema multiple times to force workspace rebuilds.
- Purpose: Correct the mapping between real frontend pages/backend services and the intended subfunction sections.
- Result: The current Chapter 5 packet now maps:
  - `WarningsPage.vue` -> `5.6.1 质量预警发现与处置实现`
  - `admin_extra_service.go` -> `5.6.2 批次冻结解冻与状态恢复实现`
  - `blockchain_service.go` + `DashboardPage.vue` -> `5.6.3 交易审计与运行态分析实现`

### Current Next Actions
- Rewrite `/home/ub/thesis_materials/workspaces/teatrace_thesis/polished_v3/05-系统实现.md` to follow the new Chapter 5 packet and original project-doc-driven subsection structure.
- Finalize the rewritten chapter through the workflow status pipeline after content verification.

### Step 15
- Action: Re-checked the Teatrace workspace `project_profile.json`, Chapter 5 packet, and review artifacts after the earlier structure refactor.
- Purpose: Verify whether the workspace cache actually upgraded to the new Chapter 5 module/subfunction contract.
- Result:
  - `project_profile.json` is still at `schema_version: 8`.
  - Chapter 5 required page screenshots still target the obsolete section `5.2.2 前端实现`.
  - The stale value is a workspace regeneration issue, not a missing code patch in `tools/core/chapter_profile.py`.

### Current Next Actions
- Re-run `prepare-writing` and Chapter 5 packet generation against `/home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json` to force the workspace artifacts to adopt the new schema and section targets.
- Re-verify `project_profile.json`, `05-系统实现.json`, `05-系统实现.md`, and the review artifact after regeneration.

### Step 16
- Action: Re-ran the Teatrace writing workflow for Chapter 5 using:
  - `python3 tools/cli.py prepare-writing --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
  - `python3 tools/cli.py start-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md --status polished`
- Purpose: Force the workspace cache, chapter packet, start packet, and review artifacts to adopt the new Chapter 5 schema and section contract.
- Result:
  - `project_profile.json` refreshed to `schema_version: 9`.
  - Chapter 5 required screenshot assets now point to `5.2.3 用户管理与权限治理实现`.
  - Chapter 5 packet and start packet were regenerated successfully.
  - Review artifact was refreshed successfully.

### Step 17
- Action: Re-verified the regenerated Chapter 5 outputs.
- Purpose: Confirm that the stale “前端实现/后端实现” packet contract no longer remains in the Teatrace workspace.
- Result:
  - `project_profile.md` and `05-系统实现.md` packet files now expose the correct module/subfunction structure.
  - `asset_to_section_map` now maps both page screenshots to `5.2.3 用户管理与权限治理实现`.
  - The current polished Chapter 5正文 no longer contains the obsolete `5.2.2 前端实现` / `后端实现` structure.
  - The remaining placeholder is the intentional `图5.1 系统功能结构图` figure slot.

### Current Next Actions
- Continue workflow optimization by checking whether Chapter 6 and appendix asset contracts need the same doc-driven refinement depth as Chapter 5.
- If the user wants to continue Teatrace writing immediately, move on to the next chapter packet and keep logging each regeneration step.

### Step 18
- Action: Inspected the regenerated Chapter 6 and appendix packets after the Chapter 5 cache refresh.
- Purpose: Check whether non-implementation chapters still contain Chapter-5-specific writing constraints or other cross-chapter prompt pollution.
- Result:
  - Chapter 6 packet structure is now module-aware at the测试功能层，覆盖五个核心业务模块的功能测试小节。
  - Appendix packet keeps the expected appendix-item contract.
  - A new workflow issue was found: the generic `raw_prompt` still embedded Chapter 5-only implementation instructions even for Chapter 6 and Appendix packets.

### Step 19
- Action: Updated `tools/core/writing.py` so Chapter 5 module/subfunction/code-screenshot instructions are injected only when generating `05-系统实现.md`, then re-ran `py_compile` and regenerated Chapter 5 / Chapter 6 / Appendix packets.
- Purpose: Prevent Chapter 5-specific prompt rules from leaking into other chapters and affecting later automatic drafting.
- Result:
  - Syntax validation passed after the patch.
  - `06-系统测试.md` and `09-附录.md` packets no longer contain Chapter 5-only prompt lines.
  - `05-系统实现.md` packet still retains the dedicated module-subfunction-code-screenshot constraints as expected.

### Current Next Actions
- Continue aligning the workflow around Chapter 6 and Appendix output quality, especially whether their derived tables and appendix entries need richer doc-driven detail from the original Teatrace documents.
- If the user wants direct thesis推进 instead of more workflow hardening, start executing the next chapter with the cleaned packet chain.

## 2026-04-06 01:28:11 +0800

### Step 1
- Action: Ran `python3 tools/cli.py intake --project-root /home/ub/rural --title '基于区块链的乡村教育众筹资金明白账系统设计与实现' --out /home/ub/rural_work/rural_education_donation_thesis_workspace` against the new rural education donation project.
- Purpose: Validate whether the current intake workflow can correctly classify this project before material extraction.
- Result: Found two workflow defects that materially affected the generated workspace metadata:
  - `.gocache` directories under the project and chaincode tree were not ignored, which flooded `intake_report.md` detection reasons with cache noise.
  - The Node.js backend was recognized as `unknown` because `detect_stack()` only looked for Express markers in Java text instead of JS/TS or `package.json`.

### Step 2
- Action: Patched `tools/core/intake.py`.
- Purpose: Make intake output accurate enough for downstream `extract`, `scaffold`, and `prepare-writing` on JS + Fabric projects.
- Result:
  - Added `.gocache` and `vendor` to `IGNORED_PARTS`.
  - Deduplicated chain-detection reasons before writing the intake report.
  - Extended backend stack detection to recognize Express from backend JS/TS source and `package.json`.

### Step 3
- Action: Ran `python3 -m py_compile tools/core/intake.py` and re-ran the same `intake` command to refresh the workspace.
- Purpose: Verify the patch is syntactically valid and that the real workspace artifacts are corrected, not just the source file.
- Result:
  - Syntax validation passed.
  - `/home/ub/rural_work/rural_education_donation_thesis_workspace/workflow/configs/project_manifest.json` now reports `backend_framework: "express"`.
  - `/home/ub/rural_work/rural_education_donation_thesis_workspace/docs/materials/intake_report.md` no longer includes `.gocache`-driven detection noise.

### Current Next Actions
- Continue the required formal CLI chain for the new workspace:
  - `extract-code`
  - `extract`
  - `scaffold`
  - `literature`
  - `prepare-outline`
  - `prepare-writing`
- Preserve any still-missing project documents in `missing_inputs` instead of inventing thesis evidence.

### Step 20
- Action: Inspected the current Chapter 6 / Appendix packet content, `material_pack.json`, and Teatrace original testing documents.
- Purpose: Determine why Chapter 6 tables and Appendix indexes still looked generic even after Chapter 5 had been aligned.
- Result:
  - Found that Appendix A still had `source: unknown`.
  - Found that blockchain appendix still mixed in undocumented helper functions.
  - Found that Chapter 6 test tables were still built mainly from generic counts instead of manual test docs / backend test report.
  - Found that Teatrace already contains strong testing evidence not fully used by the workflow:
    - `backend/TEST_REPORT.md`
    - `茶叶质量安全溯源系统全流程手动测试文档.md`
    - `茶叶质量安全溯源系统前端全流程手动测试文档.md`

### Step 21
- Action: Refactored `tools/core/extract.py` and bumped `MATERIAL_PACK_SCHEMA_VERSION` to `5` in `tools/core/project_common.py`.
- Purpose: Make Chapter 6 and Appendix extraction more document-driven and less dependent on weak generic derivation.
- Result:
  - Added supporting-doc auto-discovery for test/report markdown files under the project.
  - Added structured parsing for backend interface design doc routes, database design doc table用途, and chaincode design doc method用途.
  - API appendix entries now carry interface title / permission / table / chaincode hints instead of `source: unknown`.
  - Database appendix now combines数据库设计文档用途 with SQL字段摘要.

## 2026-04-06 02:15:00 +0800

### Step 22
- Action: Updated `tools/core/project_common.py`, `tools/core/chapter_profile.py`, and `tools/core/extract.py` for the rural education donation workspace, then validated syntax and re-ran the formal workflow chain on the real workspace.
- Purpose: Generalize the workflow so education-crowdfunding theses can obtain chapter-ready outlines and test assets from the formal generators, instead of relying on traceability-oriented defaults.
- Result:
  - Bumped `PROJECT_PROFILE_SCHEMA_VERSION` to `17` to force workspace refresh when chapter structure changes.
  - Extended the `education_crowdfunding` chapter profile with richer三级小节 for Chapter 1 / 3 / 4 / 6, plus refined Chapter 5 module subfunction labels.
  - Replaced Chapter 6 required asset titles/section mappings for the education-crowdfunding domain and added `exception-test-table` generation.
  - Made `tech-stack-summary`, test environment rows, module test case specs, and Chapter 6 derived tables domain-aware for donation transparency / education accountability scenarios.
  - Re-ran `extract`, `prepare-outline`, `prepare-writing`, `prepare-chapter`, and `start-chapter` on `/home/ub/rural_work/rural_education_donation_thesis_workspace`, and confirmed `check-workspace` passes after regeneration.

### Current Next Actions
- Keep monitoring whether future education-crowdfunding projects expose stronger test reports; if so, prefer filling Chapter 6 result columns from real reports instead of derived `待补` placeholders.
- The formal workflow is now ready to support正文 drafting for the refreshed rural education donation workspace without manual outline patching.

### Step 23
- Action: Added a derived missing-input bridge in `tools/core/extract.py` and re-ran the rural education donation workspace extraction.
- Purpose: Ensure Chapter 6 testing-evidence shortages are written into formal missing-item artifacts, not only emitted as packet validation warnings.
- Result:
  - When fewer than 2 reusable `test-document` assets are found, extraction now appends `missing test evidence documents: fewer than 2 reusable Chapter 6 test docs` to the rendered missing-items output.
  - The refreshed workspace now exposes this gap consistently in `docs/materials/missing_items.md`, `material_pack.md`, and Chapter 6 writing briefs.

### Step 24
- Action: Updated `tools/core/intake.py` so document detection better handles English-named implementation/manual-test docs and keeps `requirements` missing unless a real requirements/overview doc exists.
- Purpose: Prevent the workflow from silently inventing a requirements document category when the project only provides implementation/design materials, while still loading the new docs into the workspace.
- Result:
  - `design` detection now accepts filenames such as `backend-implementation.md`, `frontend-implementation.md`, `database-design.md`, `chaincode-design.md`, and `frontend-manual-test.md`.
  - `requirements` no longer falls back to an arbitrary first markdown file; it now remains missing unless an actual requirements/overview-style doc is present.

### Step 25
- Action: Updated `tools/core/extract.py` and `tools/core/chapter_profile.py` to support English doc lookup, `docs/assets` screenshot scanning, and screenshot-based Chapter 6 test evidence selection; then re-ran the rural education donation workspace chain.
- Purpose: Make newly added local docs and screenshots materially improve chapter packets instead of sitting outside the asset pipeline.
- Result:
  - `_find_doc_text()` now matches by filename, path, and document content, which lets Chinese-titled markdown inside English filenames drive extraction.
  - Supporting-doc discovery now also scans `docs/**/*.md` for manual-test/test files.
  - `_scan_image_candidates()` and demo-evidence summaries now include `docs/assets`.
  - Manual-test screenshots are classified as `test-screenshot` assets for Chapter 5 / 6 instead of generic supporting images.
  - Chapter 6’s required “测试章节至少引用 2 项测试证据” contract now accepts generic `test_artifacts`, so screenshots can satisfy the evidence requirement alongside test docs.
  - After rerunning `intake -> extract-code -> extract -> scaffold -> literature --skip-research-sidecar -> prepare-outline -> prepare-writing`, the workspace now records the new design docs, clears the old `design` missing-input flag, and validates Chapter 6 without the previous evidence warning.
  - Blockchain appendix now prefers documented chaincode methods and no longer leaks internal helper functions as primary appendix entries.
  - Chapter 6 test environment / test case / test result tables now prefer:
    - `backend/TEST_REPORT.md`
    - full manual test docs
    - runtime screenshots
    - deployment/startup docs

### Step 22
- Action: Ran `py_compile`, re-executed `extract`, and regenerated Chapter 6 / Appendix packets multiple times while tightening the test-evidence ranking rules.
- Purpose: Ensure the new extraction logic actually changes workspace outputs instead of only changing source code.
- Result:
  - `material_pack.json` now reports `schema_version: 5`.
  - `demo_test_evidence.summary` now starts with:
    - `backend/TEST_REPORT.md`
    - `茶叶质量安全溯源系统全流程手动测试文档.md`
    - `茶叶质量安全溯源系统前端全流程手动测试文档.md`
  - Chapter 6 `test-case-matrix` now maps module rows to real testing evidence instead of generic design docs.
  - Chapter 6 required test artifacts now correctly resolve to:
    - `backend/TEST_REPORT.md`
    - `茶叶质量安全溯源系统全流程手动测试文档.md`
  - Appendix packet now uses richer API / database / chaincode appendix lines with explicit document sources.

### Current Next Actions
- The workflow layer for Chapter 6 and Appendix is now materially stronger; the next logical step is to regenerate or rewrite `polished_v3/06-系统测试.md` and `polished_v3/09-附录.md` using the refreshed packets.
- Keep logging each chapter regeneration and compare the rewritten正文 against the previous outputs to catch any residual stale manual content.

### Step 23
- Action: Continued refining `tools/core/extract.py` after verification.
- Purpose: Fix the remaining Teatrace-specific weaknesses in Chapter 6 test evidence selection.
- Result:
  - The test-case matrix candidate pool now excludes generic design docs and README noise.
  - `demo_test_evidence` ordering now prioritizes real testing materials:
    - `backend/TEST_REPORT.md`
    - `茶叶质量安全溯源系统全流程手动测试文档.md`
    - `茶叶质量安全溯源系统前端全流程手动测试文档.md`

## 2026-04-01 16:46:30 +0800

### Step 24
- Action: Completed the remaining Chapter 5 inline-code workflow refactor in `workflow_bundle/tools/core/chapter_profile.py` and `workflow_bundle/tools/core/writing.py`, then re-synced the root compatibility mirror.
- Purpose: Replace the last “关键代码截图” assumptions in the bundle so new conversations and regenerated packets default to inline code blocks inside each Chapter 5 subfunction.
- Result:
  - Chapter 5 module policy now locks to `module-subfunctions-with-inline-code`.
  - `require_code_screenshot_section` is `False` and `required_code_screenshot_count` can fall to `0`.
  - Packet / brief rendering no longer force-display empty screenshot sections when the module contract is inline-code-only.
  - `sync_root_compat.sh` and `check_bundle_sync.sh` both passed.

### Step 25
- Action: Refreshed the Teatrace workspace workflow assets and regenerated Chapter 5 writing artifacts with:
  - `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 workflow_bundle/tools/cli.py prepare-writing --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 workflow_bundle/tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
- Purpose: Make the workspace consume the new bundle contract instead of the stale screenshot-oriented Chapter 5 packet.
- Result:
  - Regenerated Chapter 5 packet no longer contains `5.2.4 关键代码截图`.
  - `module_implementation_policy` now records inline-code requirements, mandatory `后端实现。/前端实现。` paragraph order, and frontend page-screenshot preference.
  - Chapter 5 packet now reports `required_code_screenshot_count: 0`.

### Step 26
- Action: Rewrote the `5.2 用户与权限管理模块实现` section in `workspaces/teatrace_thesis/polished_v3/05-系统实现.md`.
- Purpose: Align the current thesis正文 with the original optimized sample style instead of leaving it as abstract overview prose.
- Result:
  - `5.2.1` now uses real backend registration/login code plus a real registration-login page screenshot already staged in the workspace.
  - `5.2.2` now uses real backend institution-audit / chain-identity-binding code and real frontend audit-page code.
  - `5.2.3` now uses real backend user-query / role-update code and real frontend user-management code, while keeping the existing admin dashboard and forbidden-page screenshots.
  - The obsolete `5.2.4 关键代码截图` subsection was removed from the正文.
  - Figure numbering in Chapter 5 was rebalanced so the newly inserted page screenshot does not break later figure order.

### Step 27
- Action: Ran syntax validation and post-change verification.
- Purpose: Confirm that both the workflow code and regenerated workspace artifacts are internally consistent after the Chapter 5 inline-code migration.
- Result:
  - `python3 -m py_compile workflow_bundle/tools/core/chapter_profile.py workflow_bundle/tools/core/writing.py` passed.
  - The regenerated Chapter 5 packet and brief now expose the new subsection tree and inline-code writing contract.

### Current Next Actions
- Continue rewriting the remaining Chapter 5 modules (`5.3` to `5.6`) from “代码截图小节” to “子功能内联代码” so the current Teatrace正文 fully matches the new workflow contract.
- When needed later, generate white-background black-text code images from the already embedded code blocks instead of reintroducing screenshot-only writing rules.

### Step 28
- Action: Refactored `workflow_bundle/tools/core/code_evidence.py` to extract multiple code snippets from a single source file and to include both script snippets and template snippets for Vue pages when useful.
- Purpose: Fix the material gap where the inline-code Chapter 5 workflow knew the correct subsection structure but still lacked enough staged source evidence to cover every subfunction.
- Result:
  - The identity module code evidence pack now includes separate backend entries such as `Register`, `Login`, `UpdateUserRole`, `AuditOrg`, and `BindChainIdentity`.
  - The identity module frontend evidence now includes real page code from `RegisterPage.vue`, `LoginPage.vue`, `UsersPage.vue`, and `PendingOrgsPage.vue`.
  - White-background code screenshots are still generated as artifacts, but they are now by-products of richer snippet extraction rather than the primary Chapter 5 writing target.

### Step 29
- Action: Updated Chapter 5 subfunction keyword matching and code-contract selection logic in `workflow_bundle/tools/core/chapter_profile.py` and `workflow_bundle/tools/core/writing.py`.
- Purpose: Make packet generation choose code evidence by subfunction coverage instead of taking the first few snippets in module order.
- Result:
  - Chapter 5 modules now prefer up to four backend and four frontend code entries per module.
  - The code-selection step now first covers each business subfunction, then uses remaining quota to补强 the most relevant subfunction instead of falling back to arbitrary early files.
  - The stale `project_profile` cache was invalidated by bumping `PROJECT_PROFILE_SCHEMA_VERSION` so the new preference counts actually take effect in the workspace.

### Step 30
- Action: Re-ran bundle sync, re-executed `extract`, and regenerated the Teatrace Chapter 5 packet after the new code-evidence logic landed.
- Purpose: Verify that the workflow can now auto-assemble materially better Chapter 5 writing inputs for the user-and-permission module.
- Result:
  - The regenerated Chapter 5 packet now maps the identity module as follows:
    - `5.2.1` gets backend registration code and frontend registration/login code.
    - `5.2.2` gets backend institution-audit plus chain-identity-binding code and frontend pending-organization audit code.
    - `5.2.3` gets backend user-role-governance code and frontend user-management code.
  - This resolves the earlier workflow defect where `5.2.2` lacked frontend evidence and `5.2.3` lacked backend evidence.
  - Chapter 6 required `test_artifacts` now resolve to the backend test report and full manual test document instead of falling back to the overall project doc and task book.

### Step 24
- Action: Rewrote `/home/ub/thesis_materials/workspaces/teatrace_thesis/polished_v3/09-附录.md` using the refreshed appendix packet and appendix-item assets, then refreshed its workflow review artifact with `finalize-chapter --status polished`.
- Purpose: Eliminate stale appendix content such as outdated interface entries and align the actual chapter output with the improved workflow.
- Result:
  - The new appendix now matches the current workflow packet and extracted assets.
  - Appendix A uses current backend interface design entries instead of stale manually summarized routes.
  - Appendix B uses database用途 + SQL字段摘要.
  - Appendix C uses documented chaincode transaction responsibilities instead of undocumented helper functions.
  - Appendix D now reflects the current runtime screenshot evidence pack.

### Current Next Actions
- Rewrite `/home/ub/thesis_materials/workspaces/teatrace_thesis/polished_v3/06-系统测试.md` using the strengthened Chapter 6 packet so the正文 fully reflects the refreshed testing evidence tables and required test artifacts.
- After Chapter 6 is refreshed, compare the regenerated正文 with the old version and continue the same packet-driven sync approach for any remaining stale chapters.

### Step 25
- Action: Updated `/home/ub/thesis_materials/workspaces/teatrace_thesis/polished_v3/06-系统测试.md` using the refreshed Chapter 6 packet and current testing assets, then refreshed the chapter review artifact with `finalize-chapter --status polished`.
- Purpose: Make the actual Chapter 6正文 inherit the workflow improvements instead of keeping only the old prose version.
- Result:
  - Inserted `表6.1 系统测试环境`.
  - Inserted `表6.2 功能测试用例设计`.
  - Inserted `表6.3 功能测试结果汇总`.
  - Replaced generic testing-basis wording with references to the current backend test report and full manual test documents.
  - Chapter 6 now better reflects the strengthened packet contract and no longer relies on prose-only testing description.

### Step 26
- Action: Completed the current Chapter 6 / Chapter 9 sync loop.
- Purpose: Close the gap between improved workflow assets and actual `polished_v3` outputs for the testing and appendix chapters.
- Result:
  - Workflow side:
    - Chapter 6 and Appendix packets now use richer doc-driven assets.
    - Material pack now prefers real testing docs and report artifacts for Chapter 6 evidence selection.
  - Output side:
    - `06-系统测试.md` now includes required tables.
    - `09-附录.md` now aligns with the refreshed appendix contract.
    - Both chapters were re-finalized to `polished`.

### Current Next Actions
- Run a focused comparison between the refreshed `06-系统测试.md` / `09-附录.md` and the previous versions to identify any remaining stale phrasing or missing asset markers.

### Step 27
- Action: Validated the latest `tools/core/writing.py` marker-filter patch with `py_compile`, regenerated the Chapter 5 and Chapter 6 packets, and re-ran the packet-vs-polished marker consistency scan.
- Purpose: Confirm that count-style requirements such as “至少插入/至少引用” no longer pollute `required_output_markers`, so the workflow only reports real output mismatches.
- Result:
  - `tools/core/writing.py` passed `python3 -m py_compile`.
  - `prepare-chapter` was rerun for:
    - `05-系统实现.md`
    - `06-系统测试.md`
  - Current marker scan result:
    - `04-系统设计.md`: no missing markers
    - `05-系统实现.md`: no missing markers
    - `06-系统测试.md`: no missing markers
    - `09-附录.md`: no missing markers
  - The workflow can now distinguish literal chapter outputs from count-style execution constraints, which removes the false-positive gap reports seen in previous checks.

### Current Next Actions
- Compare the original `/home/ub/thesis_materials/polished_v3` against `/home/ub/thesis_materials/workspaces/teatrace_thesis/polished_v3` to identify remaining content-shape differences that still need to be absorbed into the workflow.
- If the remaining differences are workflow-relevant, convert them into extraction or packet-generation rules rather than patching one chapter manually.

### Step 28
- Action: Removed the appendix chapter from the default thesis workflow and the active Teatrace workspace, then regenerated the workflow artifacts.
- Purpose: Align the workflow with the updated writing policy that the thesis no longer needs a standalone appendix chapter, and prevent `scaffold` / `prepare-writing` / `build` from reintroducing `09-附录.md`.
- Result:
  - Core workflow rules updated:
    - Removed `09-附录.md` from `tools/core/project_common.py` chapter blueprint and writing order.
    - Removed `09-附录.md` from `tools/core/chapter_profile.py`.
    - Removed appendix-specific defaults from `tools/core/writing.py`.
    - Removed appendix from `tools/core/build_final_thesis_docx.py` default build order.
  - Config templates updated:
    - `workflow/templates/workspace-config.template.json`
    - `workflow/configs/current_workspace.json`
    - `workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Workflow docs updated:
    - `workflow/WORKSPACE_SPEC.md`
    - `workflow/THESIS_WORKFLOW.md`
  - Extraction rules updated:
    - Stopped emitting appendix-only `appendix_items` assets.
    - Removed `09-附录.md` from shared asset `chapter_candidates`.
    - Material pack validation no longer warns about missing appendix items.
  - Workspace artifacts refreshed:
    - Re-ran `extract`, `scaffold`, `prepare-writing`, and regenerated retained chapter packets.
    - Deleted:
      - `workspaces/teatrace_thesis/polished_v3/09-附录.md`
      - `workspaces/teatrace_thesis/docs/writing/chapter_packets/09-附录.json`
      - `workspaces/teatrace_thesis/docs/writing/chapter_packets/09-附录.md`
      - `workspaces/teatrace_thesis/docs/writing/review/09-附录.md`
  - Verification:
    - `chapter_queue.json` no longer contains `09-附录.md`.
    - `project_profile.json` no longer defines `09-附录.md`.
    - `material_pack.json` and regenerated chapter packets no longer contain `09-附录.md`.
    - `python3 tools/cli.py build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json` succeeded.
    - New build artifact confirmed at `workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`.

### Current Next Actions
- Continue on the no-appendix workflow baseline and focus the next optimization pass on body chapters only.
- If needed, refresh the remaining chapter prose to better match the new packet contracts, but keep the workflow source of truth as the primary target.

### Step 29
- Action: Ran a focused audit between the original optimized article set `/home/ub/thesis_materials/polished_v3` and the current Teatrace workspace article set `/home/ub/thesis_materials/workspaces/teatrace_thesis/polished_v3`, then traced the regression back to the workflow implementation.
- Purpose: Distinguish expected project-domain differences from real workflow regressions before continuing any further chapter alignment work.
- Result:
  - The current gap is no longer a normal “content difference” problem.
  - A P0 workflow regression was identified:
    - `tools/core/scaffold.py` writes scaffold chapter templates directly into `polished_v3/` with no overwrite protection.
    - Re-running `python3 tools/cli.py scaffold ...` therefore overwrites already-written thesis正文 with scaffold placeholders.
  - Current Teatrace `polished_v3` now shows scaffold-placeholder content across:
    - `01-绪论.md`
    - `02-系统开发工具及技术介绍.md`
    - `03-需求分析.md`
    - `04-系统设计.md`
    - `05-系统实现.md`
    - `06-系统测试.md`
    - `07-结论与展望.md`
    - `08-致谢.md`
  - Front matter is also still placeholder-level:
    - `00-摘要.md`
    - `00-Abstract.md`
    - `REFERENCES.md`
  - The chapter-structure layer itself is still valid:
    - Chapter 3-6 structures are correctly adapted to the tea-traceability project.
    - The failure is at the final正文 persistence layer, not at the profile/packet layer.
  - The appendix removal is not part of this regression; it remains an intentional workflow change.
  - Audit report written to:
    - `/home/ub/thesis_materials/docs/current_vs_original_article_audit_2026-03-30.md`

### Current Next Actions
- Fix the `scaffold` overwrite behavior before doing any more正文 regeneration work.
- After that fix, restore or rewrite the current Teatrace正文 from packets/materials on a safe path that cannot be overwritten by scaffold again.

### Step 30
- Action: Fixed the `scaffold` overwrite regression in `tools/core/scaffold.py`, updated the CLI/doc wording, and verified the new behavior on both the live workspace and a temporary copied workspace.
- Purpose: Ensure `python3 tools/cli.py scaffold ...` can no longer destroy existing `polished_v3`正文 when the workflow is rerun.
- Result:
  - `tools/core/scaffold.py` now only initializes chapter files that are missing or blank.
  - Existing non-empty `polished_v3/*.md` files are skipped instead of being overwritten.
  - `tools/cli.py scaffold` now reports:
    - `initialized_chapters`
    - `skipped_existing_chapters`
  - Workflow docs updated to reflect the safe behavior:
    - `workflow/README.md`
    - `workflow/CHAPTER_EXECUTION.md`
  - Verification on the live Teatrace workspace:
    - rerunning `scaffold` returned `initialized_chapters: 0`
    - rerunning `scaffold` returned `skipped_existing_chapters: 11`
    - file hashes for representative chapters remained unchanged before/after rerun:
      - `01-绪论.md`
      - `05-系统实现.md`
      - `06-系统测试.md`
      - `REFERENCES.md`
  - Verification on a temporary copied workspace:
    - after deleting `07-结论与展望.md`, rerunning `scaffold` restored only the missing file
    - temporary run returned `initialized_chapters: 1`
    - temporary run returned `skipped_existing_chapters: 10`

### Current Next Actions
- The P0 workflow regression is now fixed.
- The remaining task is content recovery: current Teatrace `polished_v3` still contains scaffold placeholders and must be restored or rewritten from packets/materials without risking another scaffold overwrite.

### Step 31
- Action: Added an explicit thesis-outline stage and citation-order governance to the workflow implementation and docs.
- Purpose: Close two workflow gaps raised during Teatrace recovery:
  - the workflow must lock the thesis目录/大纲 before drafting chapters
  - in-text references must be normalized into first-appearance numeric order, with duplicate-use warnings
- Result:
  - Added new writing artifacts:
    - `docs/writing/thesis_outline.json`
    - `docs/writing/thesis_outline.md`
    - `docs/writing/citation_audit.md`
  - Added new CLI commands:
    - `python3 tools/cli.py prepare-outline --config <workspace.json>`
    - `python3 tools/cli.py normalize-citations --config <workspace.json>`
  - `prepare-writing` now auto-refreshes the thesis outline artifact.
  - `prepare-chapter` packets now include the thesis outline as an input contract.
  - `finalize-chapter` now auto-normalizes citation numbering by first appearance across the thesis and emits a citation audit report with duplicate-use warnings.
  - Chapter reference selection now prefers not-yet-used references first, so the workflow better aligns with the “one primary use per reference” writing preference.
  - Workflow docs updated:
    - `workflow/README.md`
    - `workflow/CHAPTER_EXECUTION.md`
    - `workflow/references/command-map.md`

### Current Next Actions
- Run the new outline and citation normalization steps against the live Teatrace workspace.
- Continue正文恢复 on top of the new outline-first and citation-governed workflow baseline.

### Step 32
- Action: Executed the new outline and citation-governance steps on the live Teatrace workspace, then adjusted Chapter 1 to remove unnecessary duplicate citations and reran citation normalization.
- Purpose: Verify that the new workflow stage is not only documented in code, but also usable on the current thesis workspace before continuing later chapter recovery.
- Result:
  - Ran successfully:
    - `python3 tools/cli.py prepare-outline --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 tools/cli.py prepare-writing --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 tools/cli.py normalize-citations --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Generated workspace artifacts:
    - `workspaces/teatrace_thesis/docs/writing/thesis_outline.json`
    - `workspaces/teatrace_thesis/docs/writing/thesis_outline.md`
    - `workspaces/teatrace_thesis/docs/writing/citation_audit.md`
  - `chapter_queue.json` now explicitly records:
    - `thesis_outline_json`
    - `thesis_outline_md`
    - `citation_audit_md`
  - Verified the live citation policy on current正文:
    - `01-绪论.md` citations were normalized into first-appearance order
    - unnecessary duplicate citations were removed from the current Chapter 1 text
    - regenerated `citation_audit.md` now shows Chapter 1 with ordered first appearances and no remaining duplicate-use warnings

### Step 33
- Action: Rewrote the placeholder Teatrace body chapters `05-系统实现.md`, `06-系统测试.md`, `07-结论与展望.md`, and `08-致谢.md` directly in `workspaces/teatrace_thesis/polished_v3/`, then refreshed their workflow review artifacts.
- Purpose: Complete the current正文 recovery on top of the already-fixed workflow baseline so the live workspace once again contains real thesis prose instead of scaffold placeholders.
- Result:
  - `05-系统实现.md` now follows the packet-enforced module/subfunction structure and includes:
    - `图5.1 系统功能结构图` placeholder
    - 2 staged page screenshots under `docs/images/chapter5/`
    - 5 groups of backend/frontend white-background code screenshots from `docs/materials/code_screenshots/`
  - `06-系统测试.md` now includes:
    - `表6.1 系统测试环境`
    - `表6.2 功能测试用例设计`
    - `表6.3 功能测试结果汇总`
    - explicit references to the current test evidence documents
  - `07-结论与展望.md` and `08-致谢.md` were rewritten from placeholder text into complete thesis prose.
  - Finalization executed successfully for:
    - `05-系统实现.md` -> `polished`
    - `06-系统测试.md` -> `polished`
    - `07-结论与展望.md` -> `polished`
    - `08-致谢.md` -> `reviewed`
  - `normalize-citations` was rerun successfully after chapter recovery.
  - Latest `citation_audit.md` confirms:
    - citation order remains first-appearance based
    - no order warnings
    - no duplicate-use warnings

### Step 34
- Action: Investigated and fixed a DOCX build regression in `tools/core/build_final_thesis_docx.py`, then rebuilt and re-verified the Teatrace workspace deliverable.
- Purpose: Prevent config-based workspaces from inheriting stale default figure paths such as `docs/images/image-5.png`, which belonged to the old bundled example and caused build failures in new project workspaces.
- Result:
  - Root cause confirmed:
    - the build tool always inherited the legacy default `figure_map`
    - when a workspace config omitted explicit figure mappings, the builder still tried to load the old template images
  - Fix applied:
    - config-based builds now start from an empty `figure_map`
    - only figures explicitly declared by the workspace config are loaded
  - Validation:
    - `python3 -m py_compile tools/core/build_final_thesis_docx.py` passed
    - `python3 tools/cli.py build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json` succeeded
    - rebuilt artifact timestamp confirmed:
      - `workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx` at `2026-03-30 22:13:45 +0800`
    - `python3 tools/cli.py verify /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json` succeeded with:
      - `ref fields: 8`
      - `bookmarks: 8`
      - `anchors missing bookmarks: 0`

### Current Next Actions
- The live Teatrace workspace now contains recovered正文, refreshed review artifacts, clean citation governance output, and a working DOCX build path.
- The next optimization pass should focus on:
  - replacing remaining figure placeholders such as `图4.1`-`图4.5` and `图5.1` with staged project-specific assets
  - deciding whether test/page screenshots should be extracted into the workspace automatically instead of being referenced or staged manually
  - refining the final release path if a Windows Word post-process artifact is still required

### Step 35
- Action: Productized the new figure-generation stage in workflow docs and release scripts.
- Purpose: Make project-specific figures part of the standard workflow instead of a one-off manual recovery step, and prevent future workspaces from silently exporting placeholder-only Chapter 4/5 content.
- Result:
  - Updated workflow docs:
    - `workflow/README.md`
    - `workflow/CHAPTER_EXECUTION.md`
    - `workflow/references/command-map.md`
    - `tools/README.md`
  - Added `prepare-figures` to the documented standard sequence for:
    - project intake and chapter execution
    - release preparation
    - standalone CLI usage
  - Updated release wrappers:
    - `workflow/scripts/build_release.sh` now runs `python3 tools/cli.py prepare-figures --config <workspace.json>` before `build`
    - `workflow/scripts/verify_release.sh` now refreshes figures before rebuilding and verifying when invoked with a workspace config
  - Workflow rule clarified:
    - project-specific figures are generated by an explicit pipeline step
    - the build tool no longer owns hidden figure synthesis logic

### Step 36
- Action: Rebuilt and re-verified the live Teatrace workspace through the updated release path, then inspected the generated DOCX package.
- Purpose: Confirm that the workflow change works end-to-end in the real workspace and that the exported document now contains actual figures and screenshots instead of正文-only output.
- Result:
  - Validation commands succeeded:
    - `python3 -m py_compile tools/cli.py tools/core/figure_assets.py tools/core/build_final_thesis_docx.py`
    - `bash workflow/scripts/build_release.sh /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `bash workflow/scripts/verify_release.sh /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Release wrappers now visibly refresh figure assets before build:
    - `generated_figures: 6`
    - `4.1` ~ `4.5`
    - `5.1`
  - Rebuilt artifact timestamps confirmed:
    - `workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx` at `2026-03-30 22:37:07 +0800`
    - `workspaces/teatrace_thesis/word_output/figure_insert_log.csv` at `2026-03-30 22:37:07 +0800`
  - Verification output remained clean:
    - `ref fields: 8`
    - `bookmarks: 8`
    - `anchors missing bookmarks: 0`
  - DOCX package inspection confirmed non-textual content is really embedded:
    - `word/media/` contains 18 image objects
    - `word/document.xml` contains `图4.1` ~ `图4.5` and `图5.1`
    - `figure_insert_log.csv` records the generated Chapter 4 figures, Chapter 5 function structure figure, Chapter 5 page screenshots, and Chapter 5 white-background code screenshots

### Current Next Actions
- The figure stage is now integrated into the workflow and validated on Teatrace.
- The next workflow-hardening targets are:
  - decide whether Chapter 6 test screenshots/tables should gain an auto-preparation step similar to `prepare-figures`
  - decide whether Chapter 5 page screenshots under `docs/images/chapter5/` should also be auto-extracted instead of being staged manually
  - if a fully finalized submission artifact is required, run the Windows Word post-process path separately and record that output as `Windows终稿`

### Step 37
- Action: Promoted all remaining `polished` chapters in the live Teatrace workspace to `reviewed`.
- Purpose: Close the thesis chapter state machine at the workflow layer before continuing with any later automation hardening, so the current正文 can be treated as a reviewed Linux delivery baseline instead of a partially finalized draft set.
- Result:
  - Executed `python3 tools/cli.py finalize-chapter --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter <chapter> --status reviewed` serially for:
    - `02-系统开发工具及技术介绍.md`
    - `03-需求分析.md`
    - `04-系统设计.md`
    - `05-系统实现.md`
    - `06-系统测试.md`
    - `01-绪论.md`
    - `07-结论与展望.md`
    - `00-摘要.md`
    - `00-Abstract.md`
  - Queue verification confirmed:
    - all thesis chapters are now `reviewed`
    - `REFERENCES.md` remains `managed` as intended
  - Review artifact directory now contains the full reviewed chapter set under `workspaces/teatrace_thesis/docs/writing/review/`
  - `citation_audit.md` was refreshed during the finalize cycle:
    - `generated_at: 2026-03-30T23:20:34+08:00`
    - first-appearance numbering remains clean
    - no order warnings
    - no reuse warnings

### Current Next Actions
- The chapter-state closure task is complete.
- Remaining unfinished work is now outside the review state machine:
  - Windows Word post-process finalization, if a `Windows终稿` is still required
  - optional cleanup of正文中的图占位文案 so Markdown source is closer to the rendered DOCX result
  - optional automation for Chapter 5 page screenshots and future Chapter 6 test assets

### Step 38
- Action: Replaced visible figure placeholder sentences in the Teatrace正文 source with hidden figure markers, and extended the DOCX builder to recognize those markers.
- Purpose: Keep `polished_v3` closer to the actual rendered thesis text while preserving the existing config-driven auto-insert figure workflow for Chapter 4 and Figure 5.1.
- Result:
  - Updated `tools/core/build_final_thesis_docx.py`:
    - added hidden marker support in the form `<!-- figure:4.1 -->`
    - preserved backward compatibility with the old visible placeholder syntax
  - Updated正文 source:
    - `workspaces/teatrace_thesis/polished_v3/04-系统设计.md`
    - `workspaces/teatrace_thesis/polished_v3/05-系统实现.md`
    - visible `（配图占位，终稿插入图...）` lines were replaced by hidden markers
  - Updated workflow doc:
    - `workflow/CHAPTER_EXECUTION.md` now documents the hidden marker form for cleaner Markdown source
  - Re-synced reviewed sidecar artifacts using idempotent `finalize-chapter --status reviewed` for:
    - `04-系统设计.md`
    - `05-系统实现.md`
  - Review verification confirmed:
    - `review/04-系统设计.md` now reports `placeholder_count: 0`
    - `review/05-系统实现.md` now reports `placeholder_count: 0`
  - Rebuilt and re-verified the Teatrace DOCX:
    - rebuilt artifact timestamp: `2026-03-30 23:47:17 +0800`
    - citation anchor verification still passed
    - `word/media/` still contains 18 images
    - `figure_insert_log.csv` still records `图4.1` ~ `图4.5` and `图5.1`
    - hidden marker text does not leak into `word/document.xml`

### Current Next Actions
- The正文 visible-figure-placeholder cleanup is complete.
- Remaining unfinished work is now narrowed to:
  - Windows Word post-process finalization, if a `Windows终稿` is still required
  - optional automation for Chapter 5 page screenshots
  - optional future automation for Chapter 6 test assets

### Step 39
- Action: Aligned the Teatrace thesis workflow and正文 style with the original `polished_v3` reference chapters identified by the user.
- Purpose: Correct the current workflow tendency to generate project-commentary prose instead of thesis-manuscript prose, especially in the areas of self-reference, citation usage, repository-facing wording, and meta narration.
- Result:
  - Updated workflow generation rules in `tools/core/writing.py`:
    - added explicit prompt constraints to prefer `本研究` / `本系统` / `全文` over `本文`
    - added explicit prompt constraints to avoid repository-facing wording such as `证据路径`
    - added explicit prompt constraints to avoid lead-ins such as `从运行环境看` / `从接口分组看` / `从目录结构看`
    - added explicit prompt constraints to avoid stacked citation clusters such as `[1][2][3]`
  - Added style diagnostics to chapter finalization:
    - `finalize-chapter` now emits `Style Warnings` in review artifacts
    - queue entries now record `style_issue_count`
  - Updated extraction logic in `tools/core/extract.py`:
    - technology summary table now uses `主要作用` instead of `证据路径`
    - API summary table no longer emits repository evidence-path columns
    - database summary table no longer emits repository evidence-path columns
    - blockchain transaction table no longer emits repository evidence-path columns

### Step 40
- Action: Rewrote the currently reviewed Teatrace正文 chapters to match the intended thesis voice and citation style, then regenerated workflow artifacts.
- Purpose: Ensure the live workspace itself reflects the improved workflow rules instead of only updating generator code for future runs.
- Result:
  - Revised live thesis chapters:
    - `workspaces/teatrace_thesis/polished_v3/00-摘要.md`
    - `workspaces/teatrace_thesis/polished_v3/01-绪论.md`
    - `workspaces/teatrace_thesis/polished_v3/02-系统开发工具及技术介绍.md`
    - `workspaces/teatrace_thesis/polished_v3/03-需求分析.md`
    - `workspaces/teatrace_thesis/polished_v3/04-系统设计.md`
    - `workspaces/teatrace_thesis/polished_v3/05-系统实现.md`
    - `workspaces/teatrace_thesis/polished_v3/07-结论与展望.md`
    - `workspaces/teatrace_thesis/polished_v3/08-致谢.md`
  - Main正文 fixes applied:
    - replaced `本文` with `本研究` / `本章` / `全文` where appropriate
    - rewrote Chapter 1 literature review so `[1]` ~ `[8]` are no longer stacked as `[1][2][3]` style clusters
    - removed `证据路径` and similar repository-facing table columns from current正文
    - removed deployment/script narration such as `project-start.sh` from Chapter 2 thesis prose
    - removed repeated “从……看” lead-ins and rewrote them as direct thesis statements
    - removed meta-paper wording such as “便于论文说明”“论文实验验证”等不适合作为正文叙述的表达
  - Regenerated workflow artifacts:
    - reran `extract`
    - reran `prepare-writing`
    - reran `prepare-chapter` for Chapters `01` ~ `05`
    - reran `finalize-chapter --status reviewed` for all modified chapters
  - Verification confirmed:
    - `review/01-绪论.md` reports `Style Warnings: none`
    - `review/02-系统开发工具及技术介绍.md` reports `Style Warnings: none`
    - modified reviewed chapters now show `style_issue_count: 0` in `chapter_queue.json`
    - `citation_audit.md` refreshed at `2026-03-31T00:10:08+08:00`
    - `python3 tools/cli.py verify .../workspace.json` still passed with `anchors missing bookmarks: 0`
    - rebuilt DOCX timestamp: `2026-03-31 00:11:11 +0800`

### Current Next Actions
- The thesis voice and citation-style alignment task is complete for the current Teatrace workspace baseline.
- Remaining unfinished work is now limited to:
  - Windows Word post-process finalization, if a `Windows终稿` is still required
  - optional automation for Chapter 5 page screenshots
  - optional future automation for Chapter 6 test assets

### Step 41
- Action: Strengthened the workflow around thesis outline locking and citation diagnostics.
- Purpose: Fix the remaining process gap where the outline file did not fully expose subsection hierarchy, and make citation review catch thesis-unfriendly multi-citation sentences earlier in the workflow.
- Result:
  - Updated `tools/core/writing.py`:
    - `prepare-outline` now renders the human-readable `thesis_outline.md` as a true nested directory tree instead of only listing first-level sections
    - citation diagnostics now also check sentence-level citation usage and report single-sentence multi-citation cases
    - style diagnostics now strip Markdown image/code artifacts before checking wording and additionally warn on inline script/path-style narration such as backticked file or script references
    - citation audit report generation was simplified and now emits a dedicated `Sentence Warnings` section per chapter
    - chapter review sidecars now emit `## Citation Sentence Warnings`
  - Updated workflow docs:
    - `workflow/README.md` now states that `prepare-outline` expands to chapter / section / subsection level
    - `workflow/README.md` now states that `citation_audit.md` also reports single-sentence multi-citation warnings
    - `workflow/CHAPTER_EXECUTION.md` now makes the same requirements explicit in the chapter execution protocol

### Step 42
- Action: Re-ran the updated outline and citation-review workflow for the Teatrace workspace and refreshed review sidecars.
- Purpose: Ensure the workflow improvements are not only in code but also reflected in the live project workspace the user is using for writing.
- Result:
  - Regenerated:
    - `workspaces/teatrace_thesis/docs/writing/thesis_outline.json`
    - `workspaces/teatrace_thesis/docs/writing/thesis_outline.md`
    - `workspaces/teatrace_thesis/docs/writing/reference_registry.json`
    - `workspaces/teatrace_thesis/docs/writing/citation_audit.md`
  - Refreshed reviewed sidecars for:
    - `00-摘要.md`
    - `00-Abstract.md`
    - `01-绪论.md`
    - `02-系统开发工具及技术介绍.md`
    - `03-需求分析.md`
    - `04-系统设计.md`
    - `05-系统实现.md`
    - `06-系统测试.md`
    - `07-结论与展望.md`
    - `08-致谢.md`
  - Verification confirmed:
    - new `thesis_outline.md` now expands second-level and third-level headings, including Chapter 5 module subfunctions and Chapter 6 test subsections
    - refreshed `citation_audit.md` now includes `Sentence Warnings`
    - current Teatrace workspace still reports `Sentence Warnings: none` for reviewed chapters
    - `python3 -m py_compile tools/core/writing.py tools/cli.py tools/core/chapter_profile.py` passed
    - `python3 tools/cli.py verify .../workspace.json` still passed with `ref fields: 8`, `bookmarks: 8`, `anchors missing bookmarks: 0`

### Current Next Actions
- The workflow now has a usable outline-lock artifact and stronger citation diagnostics.
- If continuing workflow optimization, the next high-value step is to audit whether future chapter packets should surface an explicit “outline snapshot / outline last generated at” field so writing rounds can detect stale packets earlier.

### Step 43
- Action: Implemented outline snapshot and stale-packet detection for chapter packets.
- Purpose: Ensure the “lock outline before drafting” rule is visible and enforceable at the packet layer instead of remaining a documentation-only convention.
- Result:
  - Updated workflow code:
    - `tools/core/project_common.py`
      - bumped `CHAPTER_PACKET_SCHEMA_VERSION` from `5` to `6`
    - `tools/core/writing.py`
      - added per-chapter `outline_snapshot` generation with deterministic signature
      - added packet-level `outline_sync` metadata including:
        - `outline_generated_at`
        - `packet_generated_at`
        - `outline_signature`
        - sync `status`
        - sync `warning`
      - `prepare-writing` now computes packet sync state for every chapter and writes these fields into `chapter_queue.json`
      - `prepare-chapter` now emits full packet outline snapshot/sync metadata and updates queue packet status fields
      - `finalize-chapter` now compares the current outline against the prepared packet and writes an `## Outline Sync` section into review sidecars
      - added packet-kind recognition so the workflow can distinguish `stub` and `full` packets when reporting sync state
  - Updated workflow docs:
    - `workflow/README.md` now explains that chapter packets carry `outline_snapshot` and `outline_sync`
    - `workflow/CHAPTER_EXECUTION.md` now explicitly requires re-running `prepare-chapter` when `outline_sync.status` is not `current`

### Step 44
- Action: Re-ran the updated packet workflow for the Teatrace workspace and refreshed packet/review artifacts.
- Purpose: Apply the new packet outline-sync mechanism to the live thesis workspace instead of leaving it only in code.
- Result:
  - Re-ran:
    - `prepare-writing`
    - `prepare-chapter` for:
      - `00-摘要.md`
      - `00-Abstract.md`
      - `01-绪论.md`
      - `02-系统开发工具及技术介绍.md`
      - `03-需求分析.md`
      - `04-系统设计.md`
      - `05-系统实现.md`
      - `06-系统测试.md`
      - `07-结论与展望.md`
      - `08-致谢.md`
    - `finalize-chapter --status reviewed` for the same reviewed chapters to refresh review sidecars
  - Verification confirmed:
    - `workspaces/teatrace_thesis/docs/writing/chapter_queue.json` now records packet metadata such as:
      - `packet_kind`
      - `packet_generated_at`
      - `packet_outline_generated_at`
      - `packet_outline_status`
    - sample queue entries for `05-系统实现.md` / `01-绪论.md` / `08-致谢.md` now report `packet_outline_status: current`
    - sample packet `workspaces/teatrace_thesis/docs/writing/chapter_packets/05-系统实现.md` now contains a visible `## Outline Sync` section
    - sample review `workspaces/teatrace_thesis/docs/writing/review/05-系统实现.md` now contains a visible `## Outline Sync` section and reports `packet_outline_status: current`
    - `python3 -m py_compile tools/core/writing.py tools/core/project_common.py tools/cli.py` passed

### Step 45
- Action: Tightened the Chapter 5 writing rules against repository filenames/route literals and cleaned the live Teatrace Chapter 5 prose accordingly.
- Purpose: Eliminate another class of thesis-unfriendly wording that remained after earlier style cleanup, namely direct mentions of component filenames, service filenames, and route path literals inside正文.
- Result:
  - Updated `tools/core/writing.py` prompts:
    - raw-draft prompt now explicitly forbids repository filenames, page component filenames, backend service filenames, and literal route paths in thesis prose
    - polish prompt now explicitly removes the same class of wording
  - Revised live thesis file:
    - `workspaces/teatrace_thesis/polished_v3/05-系统实现.md`
    - replaced file/component/path-oriented narration such as service filenames, Vue page filenames, and literal trace-route strings with direct thesis-language descriptions of the corresponding business pages, backend processing flows, and query entrances
  - Re-ran:
    - `prepare-chapter` for all current chapters again so the strengthened prompt text is written into the live packet files
    - `finalize-chapter --status reviewed` for all reviewed chapters again to refresh review sidecars
  - Verification confirmed:
    - `workspaces/teatrace_thesis/docs/writing/chapter_packets/05-系统实现.md` now contains the strengthened prompt constraint against filenames/component names/route literals
    - `workspaces/teatrace_thesis/docs/writing/review/05-系统实现.md` now reports:
      - `Style Warnings: none`
      - `packet_outline_status: current`

### Current Next Actions
- The packet layer now tracks whether a chapter writing pack is aligned with the latest outline, and Chapter 5 no longer uses repository filename narration in the current Teatrace baseline.
- If continuing workflow optimization, the next high-value step is to surface packet sync status in a dedicated workspace check command or release preflight so stale packets can be detected without opening `chapter_queue.json` or individual review files.

### Step 46
- Action: Added a dedicated workspace preflight command and connected it to the release wrappers.
- Purpose: Surface packet outline-sync status through a standard command path and stop release execution early when chapter packets are stale, legacy, or missing.
- Result:
  - Added new workflow checker:
    - `tools/core/workspace_checks.py`
      - checks core workspace paths
      - reads `chapter_queue.json`
      - summarizes `packet_outline_status` and `packet_kind`
      - reports blocking packet sync issues for `stale / legacy / missing`
      - summarizes review warning counts from `style_issue_count` and `placeholder_count`
  - Added new CLI entrypoint:
    - `python3 tools/cli.py check-workspace --config <workspace.json>`
  - Updated wrapper scripts:
    - `workflow/scripts/check_workspace.sh` now delegates to the CLI checker
    - `workflow/scripts/build_release.sh` now runs workspace preflight before figure preparation and DOCX build
    - `workflow/scripts/verify_release.sh` now runs workspace preflight before figure preparation and rebuild when invoked with a workspace config
  - Updated workflow docs:
    - `workflow/README.md`
    - `workflow/references/command-map.md`
    - `workflow/08-dual-platform-release.md`
    - these now document that workspace check includes packet sync status and that release wrappers will stop on blocking packet sync issues
  - Verification confirmed:
    - `python3 -m py_compile tools/core/workspace_checks.py tools/cli.py` passed
    - both:
      - `python3 tools/cli.py check-workspace --config .../workspace.json`
      - `bash workflow/scripts/check_workspace.sh .../workspace.json`
      successfully reported the Teatrace workspace packet sync summary

### Step 47
- Action: Used the new workspace preflight to locate and clear residual style warnings in the Teatrace baseline chapters.
- Purpose: Ensure the new checker reports a clean baseline instead of only exposing packet sync health while正文仍保留明显的论文化问题。
- Result:
  - Revised live thesis files:
    - `workspaces/teatrace_thesis/polished_v3/02-系统开发工具及技术介绍.md`
      - removed raw `/api/...` interface path narration
      - replaced Bearer header literal and route grouping narration with business-domain descriptions
    - `workspaces/teatrace_thesis/polished_v3/04-系统设计.md`
      - removed “从批次视角查看”式表述
      - replaced raw table names / relation narration with thesis-language descriptions of data entities and relationships
    - `workspaces/teatrace_thesis/polished_v3/06-系统测试.md`
      - removed repository file names, script names, route literals, and deployment-path narration from test prose/tables
      - replaced them with generic descriptions such as backend test report, hand-test records, deployment notes, backend management entrance, and public trace entrance
      - removed “从测试结果看”式表述
  - Updated workflow generator rules:
    - `tools/core/writing.py`
      - added `从测试结果看` to the thesis-unfriendly wording detector
  - Re-ran:
    - `finalize-chapter --status reviewed` for:
      - `02-系统开发工具及技术介绍.md`
      - `04-系统设计.md`
      - `06-系统测试.md`
  - Verification confirmed:
    - direct `_style_diagnostics` checks on the current chapter files returned no warnings
    - queue entries for the cleaned chapters now show `style_issue_count: 0`
    - refreshed `python3 tools/cli.py check-workspace --config .../workspace.json` now reports:
      - `packet_outline_status: current=10`
      - `packet_kind: full=10`
      - `Blocking packet sync issues: none`
      - `style_issue_count: none`
      - `placeholder_count: none`

### Step 48
- Action: Trial-ran the updated release verification wrapper with the Teatrace workspace config.
- Purpose: Confirm that the new preflight actually executes at the front of the release chain instead of existing only as an isolated CLI command.
- Result:
  - `bash workflow/scripts/verify_release.sh .../workspace.json` did begin by printing the new workspace preflight summary before entering figure preparation
  - The later `prepare-figures` stage remained slow / non-returning in this run, so the process was terminated after confirming the preflight hook itself had executed
  - This indicates:
    - workspace preflight integration is active
    - full release verification still depends on the existing figure-generation performance path, which was not the target of this change

### Current Next Actions
- Workspace preflight and release-preflight gating are now in place, and the current Teatrace baseline passes the checker cleanly.
- If continuing workflow optimization, the next high-value step is to inspect why `prepare-figures` can remain slow/non-returning during full release verification and decide whether to add a cache/skip strategy for unchanged generated figures.

### Step 49
- Action: Implemented cache / reuse logic for generated figure assets.
- Purpose: Remove the repeated Mermaid network-render cost from every Linux release verification run when figure inputs have not changed.
- Result:
  - Updated figure generator:
    - `tools/core/figure_assets.py`
      - added per-figure `spec_hash`
      - added `renderer` and `source_paths` tracking on generated figure specs
      - added two reuse modes:
        - `adopted`: existing output accepted into cache for legacy workspaces when source inputs are not newer than the image
        - `cached`: existing output reused directly when `spec_hash` already matches
      - `prepare-figures` now writes `renderer` and `spec_hash` into `workspace.json.figure_map`
      - generated figure result items now report a `status`
    - `tools/cli.py`
      - `prepare-figures` output now prints `figure_no [status]: path`
  - Updated workflow docs:
    - `workflow/README.md`
    - `workflow/08-dual-platform-release.md`
    - these now document that unchanged figure assets are reused rather than re-rendered every time
  - Verification confirmed on the Teatrace workspace:
    - first run after the cache feature reported all 6 project figures as `adopted`
    - second run reported all 6 figures as `cached`
    - cached `prepare-figures` runtime dropped to about `0.18s`
    - `workspace.json.figure_map` now contains per-figure `renderer` and `spec_hash`

### Step 50
- Action: Fixed a release-wrapper bug in `verify_release.sh` and re-verified the full Linux release chain.
- Purpose: Ensure release verification actually rebuilds the DOCX before running citation-anchor checks, instead of only printing the target output path.
- Result:
  - Updated wrapper script:
    - `workflow/scripts/verify_release.sh`
      - replaced the prior `build --print-output-path`-only behavior with:
        - real `build --config ...`
        - then a separate `build --print-output-path` to resolve the path for verification
  - Verification confirmed on the Teatrace workspace:
    - `bash workflow/scripts/verify_release.sh /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json` now completed successfully in about `3.0s`
    - output showed:
      - workspace preflight summary
      - `prepare-figures` all `cached`
      - citation verification passed with:
        - `ref fields: 8`
        - `bookmarks: 8`
        - `anchors missing bookmarks: 0`
    - rebuilt DOCX timestamp advanced from:
      - `2026-03-31 00:11:11 +0800`
      - to `2026-03-31 00:54:17 +0800`

### Current Next Actions
- Linux release verification is now genuinely end-to-end: workspace preflight, cached figure preparation, DOCX rebuild, and citation-anchor verification all pass on the Teatrace workspace.
- If continuing workflow optimization, the next high-value step is to add a small release summary artifact that records:
  - preflight result
  - figure cache statuses
  - rebuilt DOCX path and timestamp
  - citation verification result
  so each release run leaves a concise machine-readable audit trail.

### Step 51
- Action: Added release-summary artifact generation to the release verification workflow.
- Purpose: Ensure each verified Linux release leaves a concise machine-readable audit trail instead of only printing transient terminal output.
- Result:
  - Updated citation verification core:
    - `tools/core/verify_citation_links.py`
      - added `inspect_citation_links(...)` to return structured verification data
      - kept existing terminal output behavior through `verify_citation_links(...)`
  - Added release summary generator:
    - `tools/core/release_summary.py`
      - reads current workspace preflight state
      - reads latest figure-preparation summary
      - inspects rebuilt DOCX path, size, and modification time
      - records structured citation verification results
      - writes:
        - `word_output/release_summary.json`
        - `word_output/release_runs/release_summary_<timestamp>.json`
  - Updated figure preparation:
    - `tools/core/figure_assets.py`
      - now also writes `word_output/figure_prepare_summary.json`
  - Added CLI entrypoint:
    - `python3 tools/cli.py write-release-summary --config <workspace.json> --docx <docx-path>`
  - Updated wrapper script:
    - `workflow/scripts/verify_release.sh`
      - now calls `write-release-summary` after successful citation verification when running in workspace-config mode
      - avoids writing a misleading summary when invoked with a raw DOCX path outside workspace-config mode
  - Updated docs:
    - `workflow/README.md`
    - `workflow/references/command-map.md`
    - `workflow/08-dual-platform-release.md`
    - `tools/README.md`
    - these now document the new summary artifacts and command entrypoints

### Step 52
- Action: Re-ran the full Teatrace Linux release verification workflow and verified the generated summary artifacts.
- Purpose: Confirm that the release summary is not only generated in code but also correctly populated in the live workspace after a real verified release run.
- Result:
  - `bash workflow/scripts/verify_release.sh /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json` completed successfully in about `3.26s`
  - Output confirmed:
    - workspace preflight passed
    - all 6 figures were `cached`
    - citation verification passed with:
      - `ref fields: 8`
      - `bookmarks: 8`
      - `anchors missing bookmarks: 0`
    - release summary files were emitted:
      - `workspaces/teatrace_thesis/word_output/figure_prepare_summary.json`
      - `workspaces/teatrace_thesis/word_output/release_summary.json`
      - `workspaces/teatrace_thesis/word_output/release_runs/release_summary_20260331T005915_0800.json`
  - Verified summary content:
    - `figure_prepare_summary.json` records all 6 generated figures with `status: cached`
    - `release_summary.json` records:
      - workspace config/title/platform
      - preflight counters and blocking-entry arrays
      - embedded figure cache summary
      - rebuilt DOCX path, file size, and modification time
      - structured citation verification result
  - Verified rebuilt DOCX artifact:
    - `workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`
    - timestamp updated to `2026-03-31 00:59:15 +0800`

## 2026-03-31 01:17:10 +0800

### Step 53
- Action: Inspected the current release-audit implementation and release scripts, including:
  - `tools/core/release_summary.py`
  - `tools/cli.py`
  - `workflow/scripts/build_release.sh`
  - `workflow/scripts/verify_release.sh`
  - `workflow/README.md`
  - `workflow/references/command-map.md`
  - `workflow/08-dual-platform-release.md`
  - `tools/README.md`
- Purpose: Confirm the remaining gap after the previous release-summary hardening and implement the user-selected next priority of `Build 审计`.
- Result:
  - Confirmed `verify_release.sh` already writes `release_summary.json` and release history archives.
  - Confirmed `build_release.sh` still had no machine-readable audit artifact.
  - Confirmed the correct design boundary is to keep verified release audit and plain build audit as separate artifact types instead of overloading `release_summary.json`.

### Step 54
- Action: Refactored `tools/core/release_summary.py` and extended `tools/cli.py`.
- Purpose: Add an explicit build-audit path without changing the semantics of the existing verified release summary.
- Result:
  - Added shared summary assembly helpers for workspace, preflight, figure-prepare, and DOCX metadata.
  - Added `run_write_build_summary(...)`.
  - Added CLI entrypoint `python3 tools/cli.py write-build-summary --config <workspace.json> --docx <docx-path>`.
  - `build_summary.json` now records:
    - workspace metadata
    - preflight result
    - figure cache/result summary
    - built DOCX metadata
    - `build.status / artifact_type / verified`
  - `release_summary.json` continues to record citation verification and does not gain build-only semantics.

### Step 55
- Action: Updated `workflow/scripts/build_release.sh` and workflow documentation.
- Purpose: Wire the new build-audit artifact into the official Linux build path and document the split clearly.
- Result:
  - `build_release.sh` now:
    - runs preflight
    - refreshes figures
    - builds the DOCX
    - resolves the actual output path
    - writes `word_output/build_summary.json`
    - archives `word_output/build_runs/build_summary_<timestamp>.json`
  - Updated docs:
    - `workflow/README.md`
    - `workflow/references/command-map.md`
    - `workflow/08-dual-platform-release.md`
    - `tools/README.md`
  - Documentation now explicitly distinguishes:
    - `build_summary`: base build audit for `基础排版稿`
    - `release_summary`: verified Linux release audit with citation-check result

### Step 56
- Action: Ran static validation on the modified workflow entrypoints.
- Purpose: Catch Python or shell-level regressions before executing the Teatrace release chain.
- Result:
  - `python3 -m py_compile tools/core/release_summary.py tools/cli.py` passed.
  - `bash -n workflow/scripts/build_release.sh workflow/scripts/verify_release.sh workflow/scripts/check_workspace.sh` passed.

### Step 57
- Action: Executed the full Teatrace build/verify validation chain using:
  - `bash workflow/scripts/build_release.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `bash workflow/scripts/verify_release.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
- Purpose: Verify that the new build-audit flow works on a real workspace and does not corrupt the previously verified release-audit behavior.
- Result:
  - `build_release.sh` passed on the Teatrace workspace.
  - New build audit artifacts were written successfully:
    - `workspaces/teatrace_thesis/word_output/build_summary.json`
    - `workspaces/teatrace_thesis/word_output/build_runs/build_summary_20260331T011556_0800.json`
  - The generated `build_summary.json` contains `build.verified = false` and does not contain `citation_verify`.
  - `verify_release.sh` still passed and preserved the old verified-release contract:
    - `workspaces/teatrace_thesis/word_output/release_summary.json`
    - `workspaces/teatrace_thesis/word_output/release_runs/release_summary_20260331T011629_0800.json`
  - Re-check confirmed `release_summary.json` still contains `citation_verify` and does not contain `build`.

### Current Next Actions
- The Linux build-vs-release audit split is now implemented and verified on Teatrace.
- If further audit hardening is needed, the next logical extension is to decide whether the Windows postprocess stage should also emit a dedicated finalization summary instead of relying only on file outputs.

## 2026-03-31 01:29:20 +0800

### Step 58
- Action: Inspected the current Windows postprocess path, including:
  - `workflow/scripts/postprocess_release.sh`
  - `workflow/scripts/postprocess_release_linux.sh`
  - `tools/windows/postprocess_word_format.py`
  - `tools/cli.py`
  - release/workspace docs that describe `postprocess_release.sh <workspace.json>`
- Purpose: Determine how to add a dedicated Windows finalization audit artifact without breaking the existing Linux release path.
- Result:
  - Confirmed the Linux branch still works as a verification-only delivery path.
  - Found a workflow contract bug: documentation already claimed `postprocess_release.sh <workspace.json>` was supported, but the Windows branch did not actually parse `workspace.json` and only accepted raw `input_docx output_docx`.
  - Confirmed the next implementation must fix both:
    - Windows workspace-config entrypoint parsing
    - finalization summary artifact generation

### Step 59
- Action: Added a standard postprocess path contract to the workflow core.
- Purpose: Give the workflow a stable way to resolve:
  - base DOCX input
  - Windows final DOCX output
  - final figure-log output
  - final summary output
- Result:
  - Updated `tools/core/project_common.py` so new workspaces now carry a default `postprocess` section.
  - Added `tools/core/postprocess_paths.py` to resolve:
    - `final_dir`
    - `output_docx`
    - `output_figure_log`
    - `final_summary.json`
    - `final_runs/`
  - Default contract now targets `final/` as the Windows终稿 directory, keeping it separate from `word_output/`.

### Step 60
- Action: Extended the audit and CLI chain for Windows finalization.
- Purpose: Make Windows终稿 generation leave a machine-readable audit trail just like build/release already do.
- Result:
  - Extended `tools/core/release_summary.py` with `run_write_finalization_summary(...)`.
  - Added CLI entrypoint:
    - `python3 tools/cli.py write-finalization-summary --config <workspace.json> --base-docx <docx> --final-docx <docx>`
  - Extended `python3 tools/cli.py postprocess` to support:
    - `--config <workspace.json>`
    - automatic input/output path resolution
    - `--print-output-path`
  - After successful Windows postprocess in config mode, the CLI now auto-writes:
    - `final/final_summary.json`
    - `final/final_runs/final_summary_<timestamp>.json`
  - `final_summary.json` records:
    - workspace metadata
    - latest preflight snapshot
    - latest figure-prepare summary
    - base DOCX metadata
    - final DOCX metadata
    - final figure-log metadata

### Step 61
- Action: Fixed the wrapper/documentation mismatch and updated workflow docs.
- Purpose: Ensure the official wrapper script and the docs now describe the same real behavior.
- Result:
  - Updated `workflow/scripts/postprocess_release.sh`:
    - Windows branch now accepts `workspace.json`
    - no-argument mode now falls back to `workflow/configs/current_workspace.json`
    - raw `input_docx output_docx` mode remains compatible
  - Updated docs:
    - `workflow/README.md`
    - `workflow/references/command-map.md`
    - `workflow/08-dual-platform-release.md`
    - `workflow/CHAPTER_EXECUTION.md`
    - `workflow/07-current-project-execution-checklist.md`
    - `workflow/WORKSPACE_SPEC.md`
    - `workflow/templates/workspace-config.template.json`
    - `tools/README.md`
  - Documentation now explicitly distinguishes three audit artifacts:
    - `build_summary` for `基础排版稿`
    - `release_summary` for verified Linux release
    - `final_summary` for Windows Word终排结果

### Step 62
- Action: Ran validation for the new finalization path in the current Linux environment.
- Purpose: Verify all non-Word-dependent behavior now works, while clearly separating that from real Windows COM validation.
- Result:
  - Static validation passed:
    - `python3 -m py_compile tools/core/project_common.py tools/core/postprocess_paths.py tools/core/release_summary.py tools/cli.py`
    - `bash -n workflow/scripts/postprocess_release.sh workflow/scripts/postprocess_release_linux.sh`
  - Path resolution validation passed:
    - `python3 tools/cli.py postprocess --config workspaces/teatrace_thesis/workflow/configs/workspace.json --print-output-path`
    - resolved to `workspaces/teatrace_thesis/final/hyperledger-fabric_windows_final.docx`
  - Finalization-summary generation was validated on a temporary copied Teatrace workspace by staging:
    - copied base DOCX as simulated final DOCX
    - copied figure log as simulated final figure log
    - then running `write-finalization-summary`
  - Temporary validation successfully wrote:
    - `final/final_summary.json`
    - `final/final_runs/final_summary_<timestamp>.json`
  - Re-check confirmed the generated summary included:
    - `base_docx`
    - `final_docx`
    - `figure_log`
    - `finalization.artifact_type = Windows终稿`
  - Linux wrapper regression check also passed:
    - `bash workflow/scripts/postprocess_release.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - still delegates to Linux verification flow and does not claim Word finalization
  - Limitation:
    - actual Microsoft Word COM postprocess was not executed in this environment, so real Windows终稿 formatting behavior still requires a Windows machine with Word installed for final confirmation

### Current Next Actions
- The workflow now has three separate machine-readable release stages: build, verified Linux release, and Windows finalization.
- If you want to keep pushing workflow hardening, the next high-value step is to add a small final QA check that compares:
  - `build_summary`
  - `release_summary`
  - `final_summary`
  and flags missing stage transitions before delivery.

## 2026-03-31 01:41:05 +0800

### Step 63
- Action: Re-checked the user-reported wording issue around Chapter 2 chaincode subsection and ran a focused prose scan on the live Teatrace `polished_v3`.
- Purpose: Determine whether “根据某文档/测试报告” remained an isolated sentence or a broader thesis-style regression.
- Result:
  - Confirmed the exact sentence still existed in:
    - `workspaces/teatrace_thesis/polished_v3/02-系统开发工具及技术介绍.md`
      - `2.3.1 链码职责与接口摘要`
  - Found the same style family also remained in multiple live chapters, including:
    - `04-系统设计.md`
    - `05-系统实现.md`
    - `06-系统测试.md`
    - `07-结论与展望.md`
  - Confirmed the issue was not mainly packet-structure related; it was thesis prose still carrying document/report narration.

### Step 64
- Action: Tightened workflow style rules in `tools/core/writing.py`.
- Purpose: Prevent future drafts/polish passes from reintroducing source-document narration and user-disliked viewpoint wording.
- Result:
  - Added `本项目` to style-avoid diagnostics.
  - Added explicit prompt rules to avoid phrasing such as:
    - `根据链码设计文档`
    - `根据数据库设计文档`
    - `根据测试报告`
    - `测试依据主要来自……文档/报告`
  - Extended diagnostics with regex-based detection for:
    - `根据/依据/基于 ... 文档|报告|说明`
    - `主要来自/来自 ... 文档|报告|说明`
  - Polish prompt now also要求把这类“文档来源叙述”改写为直接结论表达。

### Step 65
- Action: Revised the live Teatrace thesis正文 to remove the remaining document-sourcing narration.
- Purpose: Fix the current thesis output immediately instead of only fixing the generator rules.
- Result:
  - Updated `workspaces/teatrace_thesis/polished_v3/02-系统开发工具及技术介绍.md`
    - removed `根据链码设计文档`
    - replaced remaining `本项目` with `本研究/本系统`
  - Updated `workspaces/teatrace_thesis/polished_v3/04-系统设计.md`
    - removed `根据数据库设计文档`
  - Updated `workspaces/teatrace_thesis/polished_v3/05-系统实现.md`
    - replaced `在测试报告中` with direct `测试结果表明`
  - Updated `workspaces/teatrace_thesis/polished_v3/06-系统测试.md`
    - removed `测试依据主要来自……文档/报告`
    - removed table-level document-source narration
    - rewrote test paragraphs to use direct `测试结果表明` / `测试过程中`
    - replaced `本项目` with `本研究`
  - Updated `workspaces/teatrace_thesis/polished_v3/07-结论与展望.md`
    - removed `依据后端测试报告、全流程手动测试文档和前端联调文档`

### Step 66
- Action: Ran validation after the prose and workflow-style changes.
- Purpose: Confirm both the code-level style checker and the live Teatrace workspace now agree that this class of wording has been cleared.
- Result:
  - `python3 -m py_compile tools/core/writing.py` passed.
  - Focused regex scan across `workspaces/teatrace_thesis/polished_v3/` found no remaining matches for:
    - `根据 ... 文档/报告/说明`
    - `主要来自 ... 文档/报告/说明`
    - `本项目`
    - `证据路径`
    - `从运行环境看 / 从接口分组看 / 从目录结构看`
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.
  - Workspace preflight summary now reports:
    - `packet_outline_status: current=10`
    - `style_issue_count: none`
    - `placeholder_count: none`

### Current Next Actions
- The live Teatrace正文 and the workflow style checker are now aligned on this thesis-voice rule.
- If continuing this cleanup direction, the next useful pass is a broader rhetoric sweep for:
  - overuse of `说明`
  - overly tool-facing deployment details
  - residual “测试记录/联调记录” style phrasing that is not yet wrong enough to trigger the current checker

## 2026-03-31 01:49:20 +0800

### Step 67
- Action: Performed a second rhetoric sweep on the live Teatrace `polished_v3` and compared the remaining wording against the original bundled sample chapters.
- Purpose: Continue the cleanup beyond the already-fixed “根据某文档/报告” pattern and remove softer workflow/material voice residue.
- Result:
  - Identified the remaining high-signal material-style phrases in live正文:
    - `现有项目代码`
    - `测试文档`
    - `代码证据`
    - `页面联调 / 流程联调`
  - Confirmed these phrases were concentrated in:
    - `00-摘要.md`
    - `01-绪论.md`
    - `06-系统测试.md`
    - one remaining sentence in `05-系统实现.md`

### Step 68
- Action: Tightened the style checker again and revised the live thesis prose accordingly.
- Purpose: Ensure this softer class of workflow-material wording is both fixed now and blocked in future drafting/polish passes.
- Result:
  - Extended `tools/core/writing.py` with targeted material-voice diagnostics for:
    - `测试报告`
    - `测试记录`
    - `测试文档`
    - `联调文档 / 联调记录`
    - `项目总体说明`
    - `部署说明 / 启动说明`
    - `现有项目代码`
    - `代码证据`
  - Updated live正文:
    - `workspaces/teatrace_thesis/polished_v3/00-摘要.md`
      - replaced `结合现有项目代码与测试文档` with direct system-validation wording
    - `workspaces/teatrace_thesis/polished_v3/01-绪论.md`
      - replaced `代码证据` with `关键代码`
    - `workspaces/teatrace_thesis/polished_v3/05-系统实现.md`
      - compressed `测试结果表明……说明……` into direct conclusion phrasing
    - `workspaces/teatrace_thesis/polished_v3/06-系统测试.md`
      - replaced `页面联调 / 流程联调` with `页面验证 / 流程验证 / 交互验证`
      - kept the chapter in thesis-testing voice rather than workflow-material voice

### Step 69
- Action: Re-ran validation after the second rhetoric sweep.
- Purpose: Confirm that the newly added material-voice diagnostics do not re-flag the current cleaned Teatrace正文.
- Result:
  - `python3 -m py_compile tools/core/writing.py` passed.
  - Focused scan across `workspaces/teatrace_thesis/polished_v3/` found no remaining matches for:
    - `测试文档`
    - `测试报告`
    - `测试记录`
    - `联调文档 / 联调记录`
    - `代码证据`
    - `现有项目代码`
    - `项目总体说明`
    - `部署说明 / 启动说明`
    - `默认端口 / 默认运行在`
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.
  - Workspace summary remained:
    - `packet_outline_status: current=10`
    - `style_issue_count: none`
    - `placeholder_count: none`

### Current Next Actions
- The Teatrace正文 has now been cleaned at two levels:
  - obvious document-sourcing narration
  - softer material/workflow voice residue
- If continuing prose hardening, the next pass should focus on sentence texture rather than source wording, especially:
  - repetitive `说明/表明` chains
  - summary paragraphs that still read slightly像“章节说明”
  - places where implementation descriptions can be made more concise and more like finished thesis prose

## 2026-03-31 01:55:45 +0800

### Step 70
- Action: Compared the remaining Teatrace rhetoric hotspots against the original bundled `polished_v3` chapter style and revised the live thesis正文.
- Purpose: Remove the remaining mechanical “说明式” and “表明…说明…” sentence patterns so the current thesis reads more like finalized academic prose rather than workflow narration.
- Result:
  - Updated live正文:
    - `workspaces/teatrace_thesis/polished_v3/00-摘要.md`
    - `workspaces/teatrace_thesis/polished_v3/01-绪论.md`
    - `workspaces/teatrace_thesis/polished_v3/02-系统开发工具及技术介绍.md`
    - `workspaces/teatrace_thesis/polished_v3/03-需求分析.md`
    - `workspaces/teatrace_thesis/polished_v3/04-系统设计.md`
    - `workspaces/teatrace_thesis/polished_v3/05-系统实现.md`
    - `workspaces/teatrace_thesis/polished_v3/06-系统测试.md`
    - `workspaces/teatrace_thesis/polished_v3/07-结论与展望.md`
  - Main prose changes:
    - rewrote chapter summaries from `进行了说明 / 主要说明 / 展开说明` into direct academic conclusions
    - removed remaining `这样 / 由此`-heavy transitions in implementation sections where they made the prose feel procedural
    - rewrote several test/result paragraphs to avoid `测试结果表明……说明……` chains
    - tightened literature-review verbs from repetitive `说明 / 表明` into more varied direct reporting verbs such as `指出 / 发现 / 验证`

### Step 71
- Action: Hardened `tools/core/writing.py` style diagnostics for this rhetoric class.
- Purpose: Prevent future chapter drafting or polishing passes from reintroducing the same mechanical thesis voice.
- Result:
  - Added targeted style warnings for:
    - `需要说明的是`
    - `进行了说明`
    - `展开说明`
    - `主要说明`
    - `总体设计说明`
    - `进一步说明`
  - Added regex-based detection for same-sentence chain patterns matching `表明 ... 说明`.

### Step 72
- Action: Re-ran focused rhetoric scan, Python syntax validation, and workspace preflight verification.
- Purpose: Confirm that both the live thesis output and the workflow checker agree that this style pass is clean.
- Result:
  - Focused scan on `workspaces/teatrace_thesis/polished_v3/` found no remaining matches for:
    - `需要说明的是`
    - `进行了说明`
    - `展开说明`
    - `主要说明`
    - `总体设计说明`
    - `进一步说明`
    - `表明 ... 说明`
    - `这样设计 / 这样一来 / 这样既`
    - `由此`
  - `python3 -m py_compile tools/core/writing.py` passed.
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.
  - Workspace summary remained:
    - `packet_outline_status: current=10`
    - `style_issue_count: none`
    - `placeholder_count: none`

### Current Next Actions
- The current Teatrace正文 has now moved from “source narration cleanup” into “sentence texture cleanup”.
- If continuing this direction, the next useful workflow-first step is to compare the full live Teatrace正文 against the bundled original sample chapter by chapter and extract reusable prose heuristics for:
  - chapter opening paragraph rhythm
  - section closing paragraph rhythm
  - implementation/test chapter conclusion style

## 2026-03-31 08:35:49 +0800

### Step 73
- Action: Compared the original bundled `polished_v3/06-系统测试.md` with the live Teatrace Chapter 6 and rewrote the live chapter toward the original sample’s testing-chapter structure.
- Purpose: Align Teatrace Chapter 6 with the original optimized sample’s writing pattern instead of the more condensed summary-style version that had drifted away from the sample.
- Result:
  - Rewrote `workspaces/teatrace_thesis/polished_v3/06-系统测试.md` into the sample-like structure:
    - `6.1 系统测试环境`
      - `6.1.1 服务器端`
      - `6.1.2 客户端`
    - `6.2 功能测试`
      - module-by-module test subsections with dedicated result tables
      - `核心流程用例汇总` table
    - `6.3 非功能测试`
    - `6.4 本章小结`
  - Replaced the previous compact “test design + result summary” matrix style with the original sample’s “逐项测试表 + 汇总表” narration rhythm.
  - Preserved Teatrace-specific test facts, including:
    - duplicate `mspId` returns `409`
    - batch creation and trace-code generation
    - full lifecycle stage submission
    - public trace query and anti-fake anomaly trigger
    - warning handling, freeze/unfreeze, and manual retry

### Step 74
- Action: Collected concrete local environment facts and re-ran workspace verification after the rewrite.
- Purpose: Avoid inventing environment data while keeping the Chapter 6 environment section aligned with the original sample’s server/client table style.
- Result:
  - Used local environment facts for Chapter 6 test environment tables:
    - CPU: `AMD Ryzen 9 7945HX`
    - Memory: `15GiB`
    - Disk: `1007GB SSD`
    - OS: `Linux 6.6.87.2-microsoft-standard-WSL2`
  - `python3 -m py_compile tools/core/writing.py` passed.
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.
  - Workspace summary remained:
    - `packet_outline_status: current=10`
    - `style_issue_count: none`
    - `placeholder_count: none`

### Current Next Actions
- Chapter 6 is now much closer to the original bundled sample in both structure and chapter rhythm.
- If continuing this alignment path, the next workflow-first step is to abstract the sample-like Chapter 6 pattern into the Chapter 6 drafting rules so future projects generate:
  - environment subsections with server/client tables
  - module-wise function test tables
  - a final core-flow summary table

## 2026-03-31 08:42:14 +0800

### Step 75
- Action: Refactored the workflow-level Chapter 6 profile contract in `tools/core/chapter_profile.py` and bumped schema versions in `tools/core/project_common.py`.
- Purpose: Convert Chapter 6 from the old “summary-table-only” contract into the original bundled sample’s testing-chapter structure so future projects no longer drift back to a compact matrix style.
- Result:
  - Bumped:
    - `MATERIAL_PACK_SCHEMA_VERSION` -> `6`
    - `PROJECT_PROFILE_SCHEMA_VERSION` -> `10`
    - `CHAPTER_PACKET_SCHEMA_VERSION` -> `7`
  - Updated Chapter 6 structure to include:
    - `6.2.6 核心流程用例汇总`
  - Replaced the old required-table contract:
    - `表6.1 系统测试环境`
    - `表6.2 功能测试用例设计`
    - `表6.3 功能测试结果汇总`
    with the sample-like required-table set:
    - `表6.1 服务器端硬件配置表`
    - `表6.2 服务器端软件配置表`
    - `表6.3 客户端硬件配置表`
    - `表6.4 客户端软件配置表`
    - `表6.5` ~ `表6.9` 模块测试表
    - `表6.10 功能测试用例（核心流程汇总）`
    - `表6.11 非功能测试项`

### Step 76
- Action: Extended `tools/core/extract.py` to derive the new Chapter 6 test tables from existing Teatrace testing materials.
- Purpose: Ensure the workflow can populate the new Chapter 6 table contract with structured rows instead of only changing headings and markers.
- Result:
  - Added derived table assets for:
    - server/client hardware and software config tables
    - module-wise function test tables
    - core-flow summary table
    - nonfunctional-test table
  - Kept the old summary-style Chapter 6 derived tables as supplementary assets, but they are no longer part of the required contract.
  - The new Chapter 6 table derivation now uses:
    - `backend/TEST_REPORT.md`
    - `茶叶质量安全溯源系统全流程手动测试文档.md`
    - `茶叶质量安全溯源系统前端全流程手动测试文档.md`
    - deployment/startup/project-overview docs

### Step 77
- Action: Rebuilt the Teatrace workspace artifacts and verified the new Chapter 6 packet.
- Purpose: Confirm that the workflow hardening actually reached the live workspace rather than only changing source code.
- Result:
  - Ran successfully:
    - `python3 tools/cli.py extract --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 tools/cli.py prepare-writing --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 06-系统测试.md`
  - `workspaces/teatrace_thesis/docs/writing/project_profile.md` now shows:
    - `schema_version: 10`
    - Chapter 6 required assets: `12`
    - subsection `6.2.6 核心流程用例汇总`
  - `workspaces/teatrace_thesis/docs/writing/chapter_packets/06-系统测试.md` now requires output markers `表6.1` through `表6.11`.
  - `python3 -m py_compile tools/core/project_common.py tools/core/chapter_profile.py tools/core/extract.py tools/core/writing.py` passed.
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.

### Current Next Actions
- Chapter 6 has now been aligned at both levels:
  - live Teatrace正文
  - reusable workflow contract
- If continuing workflow hardening, the next logical step is to refine how Chapter 6 hardware environment tables are filled:
  - prefer project-provided environment facts when available
  - otherwise keep placeholder rows explicit rather than silently inventing machine data

## 2026-03-31 08:46:54 +0800

### Step 78
- Action: Refined the Chapter 6 environment-table extraction strategy in `tools/core/extract.py`.
- Purpose: Stop relying on loosely stitched environment descriptions and make the Chapter 6 environment section prefer stable project-documented facts, while keeping missing hardware/browser fields explicitly unresolved.
- Result:
  - Added a markdown-table parser helper so extraction can read the project’s technical-route table directly from `茶叶质量安全溯源系统总体项目文档.md`.
  - Chapter 6 environment extraction now prefers:
    - project technical-route table for:
      - backend framework
      - database
      - blockchain platform
      - frontend framework
      - UI component library
      - chain interaction component
    - project runtime/port section for:
      - backend default port
      - frontend default port
    - backend test report for:
      - Fabric network sibling path
      - chaincode name
  - Hardware rows continue to use explicit `待根据当前测试主机补充` placeholders when the project docs do not provide machine specs.
  - Browser row now stays explicit as `待根据实际页面验证浏览器补充` instead of pretending to know a specific browser.

### Step 79
- Action: Re-ran extraction and regenerated the Teatrace Chapter 6 packet after the environment-source refinement.
- Purpose: Confirm that the new source-priority rule is active in the live workspace and not only in source code.
- Result:
  - Ran successfully:
    - `python3 tools/cli.py extract --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 06-系统测试.md`
  - The Chapter 6 packet still retains the full `表6.1` ~ `表6.11` contract.
  - Environment table specs remain present, but the extraction strategy is now explicitly document-first and placeholder-safe for missing machine/browser facts.
  - `python3 -m py_compile tools/core/extract.py tools/core/chapter_profile.py tools/core/project_common.py tools/core/writing.py` passed.
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.

### Current Next Actions
- Chapter 6 environment extraction is now substantially safer for reuse across different projects.
- If continuing workflow optimization, the next high-value step is to make the Chapter 6正文 generation prefer these derived per-table rows directly when writing, so the polished chapter follows the packet even more strictly without manual reshaping.

## 2026-03-31 08:50:41 +0800

### Step 80
- Action: Tightened Chapter 6 drafting prompts in `tools/core/writing.py` and bumped `CHAPTER_PACKET_SCHEMA_VERSION` to `8`.
- Purpose: Make the Chapter 6正文 generation phase follow the already-aligned sample-like packet contract more strictly, instead of only knowing the section skeleton and required marker list.
- Result:
  - Added Chapter 6-specific raw-prompt rules requiring:
    - server/client environment tables in fixed order
    - one dedicated real table per function-test subsection
    - a real core-flow summary table in `6.2.6`
    - a real nonfunctional-test table in `6.3`
    - short analysis paragraphs after tables rather than replacing tables with prose
  - Added a new `Structured table specs to render literally when applicable` block to the raw prompt.
  - The raw prompt now embeds table titles, headers, and row content from `table_specs` directly, including explicit placeholder rows when facts are missing.

### Step 81
- Action: Regenerated the Teatrace Chapter 6 packet and verified the prompt payload.
- Purpose: Confirm that the new prompt hardening is active in the live workspace packet rather than only in source code.
- Result:
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 06-系统测试.md` passed.
  - The live Chapter 6 packet JSON and Markdown now contain:
    - `Structured table specs to render literally when applicable`
    - row-level Chapter 6 table data
    - the Chapter 6-specific sample-like testing-chapter prompt rules
  - `python3 -m py_compile tools/core/project_common.py tools/core/writing.py tools/core/extract.py tools/core/chapter_profile.py` passed.
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.

### Current Next Actions
- Chapter 6 is now aligned across four layers:
  - live正文
  - chapter structure contract
  - extracted table assets
  - raw drafting prompt
- If continuing workflow hardening, the next step is to apply the same “contract -> extracted rows -> prompt literalization” method to other chapters that are still prone to drifting from the bundled sample style.

## 2026-03-31 08:55:44 +0800

### Step 82
- Action: Extended chapter-specific drafting constraints in `tools/core/writing.py` from Chapter 6 to Chapter 2 and Chapter 4, and bumped `CHAPTER_PACKET_SCHEMA_VERSION` to `9`.
- Purpose: Reduce style drift in the technical-foundation and system-design chapters, which were still structurally correct but prompt-wise too permissive compared with the bundled sample.
- Result:
  - Added Chapter 2-specific prompt rules requiring:
    - a technical-foundation chapter voice rather than implementation recap
    - literal rendering of the technology-stack table in `2.1`
    - focus on technical roles, selection logic, and responsibility boundaries
    - a technical-summary-style chapter closing paragraph
  - Added Chapter 4-specific prompt rules requiring:
    - the design chapter to follow the sequence `architecture -> modules -> database -> blockchain/chaincode -> business flows -> security/privacy`
    - visible figure/table captions to use the required output markers even if staged assets are labeled `草案`
    - literal rendering of `表4.1` and `表4.2` from packet table specs
    - flow subsections to explain trigger, backend coordination, and chain-side effect in order
    - a design-summary-style chapter closing paragraph

### Step 83
- Action: Regenerated the Teatrace packets for Chapter 2 and Chapter 4 and verified the new prompt content.
- Purpose: Confirm that the workflow hardening reached the live workspace packets rather than remaining only in source code.
- Result:
  - Ran successfully:
    - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 02-系统开发工具及技术介绍.md`
    - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 04-系统设计.md`
  - Verified live packet prompt content now includes:
    - Chapter 2:
      - `For chapter 2, write it as a technical-foundation chapter`
      - `Section 2.1 must keep the required technology-stack table as a real markdown table`
    - Chapter 4:
      - `For chapter 4, write it as a system-design chapter with a clear sequence`
      - `Keep every required figure and table marker literally in the manuscript`
    - both chapters also now benefit from the prompt-level `Structured table specs to render literally when applicable` block
  - `python3 -m py_compile tools/core/project_common.py tools/core/writing.py tools/core/extract.py tools/core/chapter_profile.py` passed.
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.

### Current Next Actions
- The “sample-alignment” workflow method has now been extended beyond Chapter 6 to:
  - Chapter 2
  - Chapter 4
- If continuing this hardening path, the next likely target is Chapter 1 or Chapter 5, focusing on:
  - chapter-opening paragraph rhythm
  - chapter-closing summary rhythm
  - stricter prevention of implementation/test voice leaking into non-implementation chapters

## 2026-03-31 09:00:48 +0800

### Step 84
- Action: Extended chapter-specific drafting constraints in `tools/core/writing.py` to Chapter 1 and Chapter 5, and bumped `CHAPTER_PACKET_SCHEMA_VERSION` to `10`.
- Purpose: Continue the sample-alignment hardening path so the workflow can generate introduction and implementation chapters with the same writing rhythm as the bundled sample, rather than relying on later manual cleanup.
- Result:
  - Added Chapter 1-specific prompt rules requiring:
    - the opening logic `领域背景 -> 结构性痛点 -> 区块链适配性 -> 研究意义`
    - `1.2` to read as an academic literature review rather than a material summary
    - `1.4` to remain a concise chapter-organization section
    - `1.5` to act as a short research-basis summary leading into Chapter 2
    - explicit prevention of implementation/deployment/testing voice leaking into the introduction
  - Added Chapter 5-specific prompt rules requiring:
    - the chapter opening to explain implementation organization from business modules and role collaboration
    - each module to start from business responsibility before implementation details
    - continued integration of backend/frontend evidence inside subfunction sections
    - explicit prevention of pure backend/frontend development-chronology narration
    - a chapter closing paragraph that summarizes implementation landing and transitions into system testing

### Step 85
- Action: Recompiled the updated workflow code and regenerated the Teatrace Chapter 1 and Chapter 5 packets.
- Purpose: Ensure the new chapter-level constraints are active in the live workspace packets instead of existing only in source code.
- Result:
  - `python3 -m py_compile tools/core/project_common.py tools/core/writing.py` passed.
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 01-绪论.md` passed.
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md` passed.
  - Verified live packet prompt content now includes:
    - Chapter 1:
      - `For chapter 1, write it as an introduction chapter with the sample-like logic of domain background -> structural pain points -> blockchain suitability -> research significance.`
      - `Section 1.5 should be a short research-basis summary that closes the introduction and leads naturally into the technical foundation chapter, not a repeated outline recap.`
    - Chapter 5:
      - `For chapter 5, open the chapter by explaining the implementation organization rationale in terms of business modules and role collaboration, not by listing backend/frontend layers separately.`
      - `The chapter closing paragraph should summarize the implemented business capabilities and their support for subsequent system testing, rather than repeating the section list.`

### Step 86
- Action: Ran the workspace integrity check after packet regeneration.
- Purpose: Confirm that the workflow hardening did not break packet synchronization, source-of-truth detection, or review summaries in the active Teatrace workspace.
- Result:
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.
  - Current summary remains:
    - `packet_outline_status: current=10`
    - `packet_kind: full=10`
    - `style_issue_count: none`
    - `placeholder_count: none`

### Current Next Actions
- The sample-alignment hardening path has now been extended to:
  - Chapter 1
  - Chapter 2
  - Chapter 4
  - Chapter 5
  - Chapter 6
- The next workflow-level target should be cross-chapter constraints that are still enforced mainly by manual review, especially:
  - unique-citation usage discipline across the generated manuscript
  - chapter opening/closing rhythm checks at workspace level
  - thesis-outline-first gating before chapter drafting starts

## 2026-03-31 09:08:34 +0800

### Step 87
- Action: Promoted citation diagnostics from per-chapter review files into queue metadata and workspace checks by updating `tools/core/writing.py` and `tools/core/workspace_checks.py`.
- Purpose: Make the workflow directly expose the two citation rules repeatedly emphasized during optimization:
  - references should follow first-appearance numbering order
  - repeated use and multi-citation sentences should be easy to audit without manually opening every chapter review file
- Result:
  - `run_finalize_chapter(...)` now writes these queue fields:
    - `citation_order_ok`
    - `citation_order_warning_count`
    - `citation_reuse_warning_count`
    - `citation_sentence_warning_count`
  - queue merge logic now preserves these citation-diagnostic fields across later `prepare-writing` refreshes
  - `check_workspace` now summarizes:
    - `citation_order_warning_count`
    - `citation_reuse_warning_count`
    - `citation_sentence_warning_count`

### Step 88
- Action: Recompiled the updated workflow code and reran the Teatrace workspace check.
- Purpose: Confirm that the new citation-audit summary integrates cleanly into the existing workflow readiness report.
- Result:
  - `python3 -m py_compile tools/core/writing.py tools/core/workspace_checks.py tools/core/project_common.py` passed.
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.
  - The live workspace check output now includes:
    - `citation_order_warning_count`
    - `citation_reuse_warning_count`
    - `citation_sentence_warning_count`
  - Current Teatrace summary remains clean:
    - `packet_outline_status: current=10`
    - `packet_kind: full=10`
    - `style_issue_count: none`
    - `placeholder_count: none`
    - `citation_order_warning_count: none`
    - `citation_reuse_warning_count: none`
    - `citation_sentence_warning_count: none`

### Current Next Actions
- The workflow now covers two of the previously weak cross-chapter controls more explicitly:
  - outline synchronization
  - citation diagnostics visibility
- The next hardening target should be the remaining “outline-first” behavior at execution level, namely:
  - making the start-drafting flow refuse stale or legacy packets more explicitly
  - surfacing the outline lock requirement earlier in start briefs and execution docs

## 2026-03-31 09:12:27 +0800

### Step 89
- Action: Strengthened the `start-chapter` brief template in `tools/core/writing.py`.
- Purpose: Push the “outline-first” and “citation-discipline” rules into the actual drafting entrypoint, so future projects do not rely on memory or manual reminders before writing a chapter.
- Result:
  - Added explicit start-brief guidance that:
    - requires `prepare-outline` + `prepare-writing` to be rerun before drafting if the directory structure changes
    - states “目录先于正文”
    - reminds the writer that citation numbering is normalized by first appearance
    - reminds the writer to keep one citation per sentence when possible
    - reminds the writer to avoid repeated use of the same reference unless necessary

### Step 90
- Action: Recompiled `tools/core/writing.py` and regenerated a live start brief for Teatrace Chapter 1.
- Purpose: Verify that the new execution-level constraints have reached the real workspace output rather than remaining only in the source template.
- Result:
  - `python3 -m py_compile tools/core/writing.py` passed.
  - `python3 tools/cli.py start-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 01-绪论.md` passed.
  - Verified the generated start brief now contains:
    - `prepare-outline`
    - `目录先于正文`
    - `单句尽量单引`
    - `文献尽量单次主用`

### Current Next Actions
- The workflow has now been tightened at three layers:
  - chapter prompt layer
  - workspace review/check layer
  - start-drafting brief layer
- If continuing the same optimization path, the next sensible step is to make stale/legacy packet states more strongly block execution commands instead of only being shown as warnings in reports.

## 2026-03-31 09:16:56 +0800

### Step 91
- Action: Added a blocking outline-sync gate to `run_finalize_chapter(...)` in `tools/core/writing.py`.
- Purpose: Convert the “outline-first” rule from a reporting hint into an execution guard, so a chapter cannot be finalized against a stale, legacy, or missing packet snapshot after the thesis directory changes.
- Result:
  - `finalize-chapter` now raises an explicit error when `packet_outline_status` is one of:
    - `stale`
    - `legacy`
    - `missing`
  - the remediation path is explicit in the error message:
    - rerun `prepare-outline`
    - rerun `prepare-writing`
    - rerun `prepare-chapter`

### Step 92
- Action: Recompiled `tools/core/writing.py`, executed a real finalize flow on Teatrace Chapter 1, and rechecked the workspace.
- Purpose: Confirm that the new finalize gate does not block the normal path when the packet is current, while also persisting the newly added citation-diagnostic queue fields into the live workspace.
- Result:
  - `python3 -m py_compile tools/core/writing.py` passed.
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 01-绪论.md --status reviewed` passed.
  - Verified live queue entry for `01-绪论.md` now contains:
    - `citation_order_ok=True`
    - `citation_order_warning_count=0`
    - `citation_reuse_warning_count=0`
    - `citation_sentence_warning_count=0`
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.
  - Current workspace summary remains clean:
    - `packet_outline_status: current=10`
    - `packet_kind: full=10`
    - `style_issue_count: none`
    - `placeholder_count: none`
    - `citation_order_warning_count: none`
    - `citation_reuse_warning_count: none`
    - `citation_sentence_warning_count: none`

### Current Next Actions
- The workflow now enforces the thesis-writing process across four layers:
  - outline and packet synchronization
  - chapter drafting prompts
  - start-brief execution constraints
  - workspace citation/review diagnostics
- The next optimization stage should focus on full-manuscript consistency items that are still mainly content-side rather than workflow-side, such as:
  - chapter opening/closing sentence rhythm checks
  - sample-style language linting for “本研究/本系统” and prohibited narration patterns

## 2026-03-31 09:12:44 +0800

### Step 93
- Action: Added a categorized manuscript-style lint layer in `tools/core/writing.py`.
- Purpose: Move the most common manual prose-review rules into the workflow itself, especially the rules repeatedly emphasized during Teatrace alignment:
  - prefer `本研究` / `本系统` over `本文` / `本项目`
  - avoid document-sourcing narration and repository-facing wording
  - avoid weak lead-in phrases such as `从……看`
  - detect chapter-opening recital style and chapter-summary outline recap style
- Result:
  - Added `Style Summary` output to chapter review files with these counters:
    - `preferred_subject_warning_count`
    - `source_narration_warning_count`
    - `repository_voice_warning_count`
    - `weak_leadin_warning_count`
    - `opening_rhythm_warning_count`
    - `summary_recap_warning_count`
  - Added dedicated review sections for:
    - `Opening Rhythm Warnings`
    - `Summary Recap Warnings`
  - The style lint remains lightweight and rule-based; it is intended as a workflow guardrail rather than a full language-quality model.

### Step 94
- Action: Persisted the new style-lint counters into queue metadata and exposed them in `tools/core/workspace_checks.py`.
- Purpose: Ensure these prose-quality checks are visible at workspace level, not only inside individual review files.
- Result:
  - `run_finalize_chapter(...)` now writes the six new style counters into `chapter_queue.json`.
  - `check_workspace` now summarizes:
    - `style_preferred_subject_warning_count`
    - `style_source_narration_warning_count`
    - `style_repository_voice_warning_count`
    - `style_weak_leadin_warning_count`
    - `style_opening_rhythm_warning_count`
    - `style_summary_recap_warning_count`

### Step 95
- Action: Recompiled the updated workflow code, refreshed live review metadata for Teatrace Chapter 1 and Chapter 5, corrected a missing queue refresh by rerunning Chapter 1 finalize, and reran the workspace check.
- Purpose: Verify that the new style-lint layer reached the real workspace outputs and queue metadata rather than remaining only in source code.
- Result:
  - `python3 -m py_compile tools/core/writing.py tools/core/workspace_checks.py` passed.
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 01-绪论.md --status reviewed` passed.
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md --status reviewed` passed.
  - Verified live review files for Chapter 1 and Chapter 5 now contain `## Style Summary`.
  - Verified live queue entries for Chapter 1 and Chapter 5 now contain all six new style counters with value `0`.
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.
  - Current workspace summary remains clean:
    - `style_issue_count: none`
    - `style_preferred_subject_warning_count: none`
    - `style_source_narration_warning_count: none`
    - `style_repository_voice_warning_count: none`
    - `style_weak_leadin_warning_count: none`
    - `style_opening_rhythm_warning_count: none`
    - `style_summary_recap_warning_count: none`
    - `citation_order_warning_count: none`
    - `citation_reuse_warning_count: none`
    - `citation_sentence_warning_count: none`

### Current Next Actions
- The workflow now has a visible consistency-lint layer for both citation discipline and prose discipline.
- If continuing workflow hardening, the next logical step is to convert some remaining style checks from “count and report” into “hard block before release”, but only for rules that are stable enough to avoid false positives.

## 2026-03-31 09:20:09 +0800

### Step 96
- Action: Compared the bundled sample Chapter 4 and the live Teatrace Chapter 4 with a table-first focus, then manually revised the Teatrace Chapter 4 tables in `workspaces/teatrace_thesis/polished_v3/04-系统设计.md`.
- Purpose: The user pointed out that the chapter-level prose was still not aligned, and the most visible gap was table organization. The bundled sample uses denser design-stage tables, while the Teatrace chapter had only two tables and weaker table transitions.
- Result:
  - Added a new module-design mapping table:
    - `表4.1 功能模块—设计落点映射`
  - Renumbered the former database summary table to:
    - `表4.2 核心数据表摘要`
  - Renumbered the former chaincode transaction table to:
    - `表4.3 链码事务与关键链上能力清单`
  - Added a new security design summary table:
    - `表4.4 安全机制—风险—落点汇总`
  - Revised the table lead-in and follow-up paragraphs so the writing now reads more like a thesis design chapter rather than a project note.
  - Removed markdown backtick styling from table-cell identifiers where it made the tables read too much like repository or code documentation.

### Step 97
- Action: Re-finalized the revised Teatrace Chapter 4 and reran workspace checks.
- Purpose: Confirm that the manual table alignment did not introduce style or workflow regressions in the active thesis workspace.
- Result:
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 04-系统设计.md --status reviewed` passed.
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.
  - The live Chapter 4 table numbering is now continuous:
    - `表4.1`
    - `表4.2`
    - `表4.3`
    - `表4.4`

### Current Next Actions
- The current Teatrace Chapter 4正文 has been table-aligned manually.
- There is now a workflow gap to address later:
  - the live Chapter 4 chapter packet still models only the older two-table contract
  - if this richer table density should become repeatable across future projects, Chapter 4 extraction and prompt rules need a follow-up hardening pass

## 2026-03-31 09:39:44 +0800

### Step 98
- Action: Reworked the `4.3.3 主要数据表结构描述` section in `workspaces/teatrace_thesis/polished_v3/04-系统设计.md` from a summary-style table into field-level data-dictionary tables.
- Purpose: The user identified the biggest remaining mismatch: Teatrace Chapter 4 still described database tables with a coarse three-column summary, while the target thesis style expects field-level tables using the columns `字段名 / 类型 / 长度 / 允许为空 / 是否为主键 / 字段描述`.
- Result:
  - Removed the old summary table `表4.2 核心数据表摘要`.
  - Replaced it with eight field-level core-table structures:
    - `表4.2-1 机构表 sys_org`
    - `表4.2-2 用户表 sys_user`
    - `表4.2-3 茶叶批次表 tea_batch`
    - `表4.2-4 农事记录表 tea_farm_record`
    - `表4.2-5 质检报告表 tea_inspection_report`
    - `表4.2-6 溯源码表 tea_trace_code`
    - `表4.2-7 链上交易映射表 bc_tx_record`
    - `表4.2-8 溯源查询日志表 log_trace_query`
  - Field metadata was derived from the real Teatrace SQL schema and database design document, not re-invented manually.
  - The section now reads more like a thesis database design chapter and less like a project inventory note.

### Step 99
- Action: Re-finalized the revised Teatrace Chapter 4 and reran the workspace check.
- Purpose: Confirm that the new field-level table format did not introduce workflow, citation, or style regressions.
- Result:
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 04-系统设计.md --status reviewed` passed.
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.
  - The live Chapter 4 now contains repeated six-column table headers:
    - `字段名`
    - `类型`
    - `长度`
    - `允许为空`
    - `是否为主键`
    - `字段描述`
  - The active workspace remains clean:
    - `style_issue_count: none`
    - `citation_order_warning_count: none`
    - `style_summary_recap_warning_count: none`

### Current Next Actions
- Teatrace Chapter 4正文 is now closer to the expected thesis data-dictionary style.
- A remaining workflow-level gap still exists:
  - the live Chapter 4 packet and extraction contract still generate only the older summary-style database table
  - if this field-level table structure should become automatic for future projects, extraction and chapter-4 prompt contracts must be upgraded next

## 2026-03-31 10:01:59 +0800

### Step 100
- Action: Re-checked the Chapter 4 workflow gap against the current Teatrace chapter, `tools/core/chapter_profile.py`, `tools/core/extract.py`, `tools/core/writing.py`, and the original Teatrace planning/design documents.
- Purpose: Confirm whether the remaining problem was only the database field-table format or whether Chapter 4 still had other manually maintained tables that were not yet part of the repeatable workflow.
- Result:
  - Confirmed the workflow had already covered `表4.2-1` through `表4.2-8` and `表4.3`.
  - Confirmed two manually added Chapter 4 tables were still outside the workflow contract:
    - `表4.1 功能模块—设计落点映射`
    - `表4.4 安全机制—风险—落点汇总`
  - Confirmed the best source materials for deriving these tables are the original Teatrace documents rather than the already polished chapter text:
    - `茶叶质量安全溯源系统功能模块规划文档.md`
    - `茶叶质量安全溯源系统前端实现规划文档.md`
    - `茶叶质量安全溯源系统后端功能规划文档.md`
    - `茶叶质量安全溯源系统数据库设计文档.md`
    - `茶叶质量安全溯源系统链码设计文档.md`

### Step 101
- Action: Implemented the Chapter 4 workflow hardening in source code:
  - `tools/core/project_common.py`
  - `tools/core/chapter_profile.py`
  - `tools/core/extract.py`
  - `tools/core/writing.py`
- Purpose: Make the richer Chapter 4 structure repeatable for future traceability/blockchain projects instead of relying on one-off manual edits inside `polished_v3/04-系统设计.md`.
- Result:
  - Bumped workflow schemas to force workspace refresh:
    - `MATERIAL_PACK_SCHEMA_VERSION = 8`
    - `PROJECT_PROFILE_SCHEMA_VERSION = 12`
    - `CHAPTER_PACKET_SCHEMA_VERSION = 12`
  - Updated the traceability-domain Chapter 4 required asset contract to include:
    - `表4.1 功能模块—设计落点映射`
    - `表4.4 安全机制—风险—落点汇总`
  - Added extraction logic that derives:
    - a module-to-design mapping table using the original module planning, frontend planning, backend planning, database, and chaincode documents
    - a security-risk summary table using the original security, permission, database, and chaincode design materials
  - Strengthened the Chapter 4 raw prompt so automatic drafting must keep:
    - `表4.1`
    - `表4.2-*`
    - `表4.3`
    - `表4.4`
    as literal structured tables rather than collapsing them into prose.

### Step 102
- Action: Ran syntax validation and the first Teatrace workspace refresh cycle:
  - `python3 -m py_compile tools/core/project_common.py tools/core/chapter_profile.py tools/core/extract.py tools/core/writing.py`
  - `python3 tools/cli.py extract --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 tools/cli.py prepare-writing --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 04-系统设计.md`
- Purpose: Verify that the new workflow rules reached the live Teatrace workspace instead of remaining only in source code.
- Result:
  - `py_compile` passed.
  - `material_pack.json` refreshed to `schema_version: 8` and now contains real derived assets:
    - `module-design-mapping-table`
    - `security-risk-summary-table`
  - The first regenerated Chapter 4 packet still showed `表4.1` and `表4.4` as placeholders.
  - Root cause was identified as refresh ordering:
    - `prepare-writing` and `prepare-chapter` had completed before the longer-running `extract` finished, so the packet consumed stale material-pack content rather than the newly generated derived assets.

### Step 103
- Action: Re-ran the Teatrace refresh in the correct order after `extract` completed, then regenerated and re-finalized Chapter 4.
- Purpose: Remove the stale packet cache and confirm the new derived Chapter 4 tables are selected as real assets rather than downgraded to placeholders.
- Result:
  - Re-ran:
    - `python3 tools/cli.py prepare-writing --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 04-系统设计.md`
    - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 04-系统设计.md --status reviewed`
  - Verified `workspaces/teatrace_thesis/docs/writing/chapter_packets/04-系统设计.md` now contains:
    - `schema_version: 12`
    - `required_table_types` including `module-design-mapping-table` and `security-risk-summary-table`
    - `表4.1 功能模块—设计落点映射 -> evidence=derived`
    - `表4.4 安全机制—风险—落点汇总 -> evidence=derived`
  - Verified the packet now renders actual table specs instead of placeholders:
    - `表4.1` has five module rows and headers `功能模块 / 主要职责 / 前端落点 / 后端/服务落点 / 数据与链上落点`
    - `表4.4` has five risk rows and headers `风险 / 主要表现 / 设计机制 / 落点`

### Step 104
- Action: Performed a final validation pass on the refreshed Teatrace workspace.
- Purpose: Confirm that the new Chapter 4 workflow contract does not introduce packet-sync or chapter-review regressions.
- Result:
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.
  - Current workspace summary remains clean:
    - `packet_outline_status: current=10`
    - `packet_kind: full=10`
    - `style_issue_count: none`
    - `placeholder_count: none`
    - `citation_order_warning_count: none`
    - `citation_reuse_warning_count: none`
    - `citation_sentence_warning_count: none`

### Current Next Actions
- The Chapter 4 workflow contract is now much closer to the manually aligned Teatrace chapter:
  - `表4.1`
  - `表4.2-*`
  - `表4.3`
  - `表4.4`
  are all part of the repeatable extraction + packet pipeline.
- If continuing this line of work, the next logical step is to compare the new auto-generated Chapter 4 packet tables against the current polished Chapter 4正文 and decide whether the derived row wording should be tightened further for sample-style consistency before using the packet for a full redraft.

## 2026-03-31 10:30:34 +0800

### Step 105
- Action: Compared the refreshed Chapter 4 packet table rows against the current live Teatrace Chapter 4正文 and the original planning/design documents.
- Purpose: The earlier workflow hardening had already made `表4.1` and `表4.4` appear as real derived assets, but some cell content still read like raw document-heading aggregation rather than thesis-ready design phrasing.
- Result:
  - Confirmed the structural problem was solved.
  - Identified a remaining wording problem:
    - `表4.1` still contained heading-like cells such as `机构审核与用户管理` and `后台管理与运维监控模块`.
    - `表4.4` still used overly extraction-oriented落点内容 such as only listing tables/functions instead of the more design-oriented cross-layer landing points expected in正文.

### Step 106
- Action: Refined the traceability-domain Chapter 4 derived-table wording in `tools/core/extract.py`.
- Purpose: Make the workflow produce packet rows that are closer to the polished thesis style, so future Chapter 4 drafting can use the packet more directly without another manual table rewrite.
- Result:
  - `表4.1` rows now use thesis-style canonical outputs for:
    - front-end landing points
    - back-end/service landing points
    - concise data / chain landing points
  - `表4.4` rows now use thesis-style canonical outputs for:
    - risk manifestation
    - protection mechanism wording
    - design landing-point wording
  - The updated packet row wording now aligns much more closely with the live Teatrace chapter, for example:
    - `登录页、个人中心、机构审核页、用户管理页`
    - `认证中间件、用户服务、管理员服务`
    - `前端路由、中间件、业务服务、链码组织校验`
    - `批次状态字段、各阶段提交事务`
    - `业务表、交易映射表、账本记录`

### Step 107
- Action: Re-ran the Teatrace refresh and validation chain after the wording refinement:
  - `python3 -m py_compile tools/core/extract.py`
  - `python3 tools/cli.py extract --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 tools/cli.py prepare-writing --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 04-系统设计.md`
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 04-系统设计.md --status reviewed`
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
- Purpose: Confirm that the refined wording is actually present in the live packet and that the workspace remains clean.
- Result:
  - `py_compile` passed.
  - The live Chapter 4 packet now shows refined `表4.1` rows such as:
    - `用户与权限管理 | 登录、机构审核、身份绑定与角色治理 | 登录页、个人中心、机构审核页、用户管理页 | 认证中间件、用户服务、管理员服务 | sys_user、sys_org、sys_user_chain_identity`
    - `监管预警与审计分析 | 预警发现、冻结解冻与交易审计 | 管理员工作台、预警页、交易记录页 | 监管服务、交易服务 | 预警表、交易映射表、FreezeBatch、UnfreezeBatch`
  - The live Chapter 4 packet now shows refined `表4.4` rows such as:
    - `非授权主体录入或查询 | 非茶农创建批次、非质检机构提交质检记录、越权访问页面 | JWT 鉴权、角色校验、组织身份校验 | 前端路由、中间件、业务服务、链码组织校验`
    - `链下记录被篡改 | 数据库明细被修改后难以证明原始状态 | 摘要上链、交易 ID 回写、状态比对 | 业务表、交易映射表、账本记录`
  - Workspace check still passes with:
    - `packet_outline_status: current=10`
    - `packet_kind: full=10`
    - `style_issue_count: none`
    - `placeholder_count: none`
    - `citation_order_warning_count: none`

### Current Next Actions
- The Chapter 4 packet content is now much closer to the current Teatrace polished chapter, not only in table presence but also in row-level phrasing.
- If continuing workflow hardening, the next efficient step is to perform the same “packet wording vs polished正文” tightening pass for any remaining chapter packets that still read like extracted inventories instead of thesis-ready drafting material, with Chapter 5 and Chapter 6 being the most likely next targets.

## 2026-03-31 11:00:46 +0800

### Step 108
- Action: Inspected the live Teatrace Chapter 5 and Chapter 6 packets after the earlier packet refresh and compared their material summaries against the original Teatrace testing documents.
- Purpose: Determine why the packets still read like raw repository/test-report inventories instead of thesis-ready evidence notes.
- Result:
  - Confirmed that `demo_test_evidence` still contained extraction-oriented lead-ins such as:
    - `当前系统主链路测试应至少覆盖以下步骤`
    - `在毕业设计或论文撰写时，可将以下内容作为实验与验证依据`
  - Confirmed that the backend regression summary still leaked raw English report sentences into the packet.
  - Confirmed that the Chapter 6 required test-document selection had regressed away from the strongest testing evidence set.

### Step 109
- Action: Hardened Chapter 5/6 testing-summary extraction in `tools/core/extract.py`.
- Purpose: Make the material pack output thesis-oriented testing summaries instead of raw source-document wording.
- Result:
  - Added numbered-list extraction for test sections so packet summaries now pull the actual test items rather than the source document's instructional lead-ins.
  - Replaced raw English backend regression-line stitching with a Chinese regression-summary combiner that maps verified scenarios and key results into thesis-style coverage/result sentences.
  - Reworked deployment summary extraction so the backend environment line now reads as a Chinese runtime statement instead of echoing the original `Backend: ...` report line.
  - The refreshed packets now use wording such as:
    - `接口回归验证覆盖：登录鉴权、机构审核、角色切换与链上身份绑定、批次建档与阶段流转、溯源码管理与公开查询、监管预警、交易重试与运行审计。`
    - `关键回归结果表明：查询阈值调整后可即时生效，连续查询可触发防伪异常标记、召回分析结果与人工冻结处置保持一致、失败交易重试后可生成新的成功交易记录、工作台统计、日志与监管接口返回结果正常。`
    - `后端联调服务采用 Gin、GORM、MySQL、Fabric Gateway 组合。`

### Step 110
- Action: Reworked Chapter 6 test-document asset ordering in `tools/core/extract.py`.
- Purpose: Ensure the testing chapter cites real testing evidence first, rather than allowing broader overview/planning docs to occupy the required `test_artifacts` slots.
- Result:
  - Inserted explicit priority ordering for:
    - `backend/TEST_REPORT.md`
    - `茶叶质量安全溯源系统全流程手动测试文档.md`
    - `茶叶质量安全溯源系统前端全流程手动测试文档.md`
  - Excluded the overall project doc from the generic test-document promotion path so it no longer competes with the real testing documents for the Chapter 6 required evidence slots.

### Step 111
- Action: Fixed two underlying workflow bugs discovered during the Chapter 6 evidence re-ranking pass.
- Purpose: Remove hidden workflow defects that would otherwise keep reintroducing wrong Chapter 6 evidence picks in future projects.
- Result:
  - Fixed a material-pack asset-ID collision in `tools/core/extract.py`:
    - root cause: `_make_asset()` relied on `_slug(title)`, and Chinese-only titles collapsed to the same `asset` suffix.
    - impact: multiple Chinese-titled `test_artifacts` silently overwrote each other.
    - fix: when the title slug collapses to `asset`, append a stable SHA-1-based fingerprint derived from title/source-path fields.
  - Fixed a multi-asset selection bug in `tools/core/writing.py`:
    - root cause: when `min_count > 1`, the resolver selected `candidate_pool[idx]` from the *remaining* pool, which skipped the first remaining asset on the second selection.
    - impact: Chapter 6 could incorrectly select the 1st and 3rd testing documents instead of the 1st and 2nd.
    - fix: always consume the first remaining match before falling back to a placeholder.

### Step 112
- Action: Re-ran the Teatrace Chapter 5/6 refresh and validation chain after the extraction and asset-selection fixes:
  - `python3 -m py_compile tools/core/extract.py tools/core/writing.py`
  - `python3 tools/cli.py extract --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 tools/cli.py prepare-writing --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 06-系统测试.md`
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md --status reviewed`
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 06-系统测试.md --status reviewed`
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
- Purpose: Verify that the fixes are present in the live Teatrace workspace and that no review/packet-sync regressions were introduced.
- Result:
  - `py_compile` passed.
  - The live Chapter 5 and Chapter 6 packets now show thesis-ready Chinese testing summaries rather than raw instructional or English report text.
  - The live Chapter 6 packet now selects the intended required testing evidence:
    - `后端回归测试报告`
    - `全流程手动测试文档`
  - The material pack test-document ordering is now:
    - `后端回归测试报告`
    - `全流程手动测试文档`
    - `前端全流程手动测试文档`
  - Workspace check still passes with:
    - `packet_outline_status: current=10`
    - `packet_kind: full=10`
    - `style_issue_count: none`
    - `placeholder_count: none`
    - `style_preferred_subject_warning_count: none`
    - `style_source_narration_warning_count: none`
    - `style_repository_voice_warning_count: none`
    - `citation_order_warning_count: none`
    - `citation_reuse_warning_count: none`
    - `citation_sentence_warning_count: none`

### Current Next Actions
- The Chapter 5/6 packet layer is now substantially closer to the bundled sample style in both evidence wording and Chapter 6 test-evidence selection.
- If continuing workflow hardening from here, the next useful step is to trim the long-tail optional `test_artifacts` pool so planning/design docs are less likely to appear as extra auto-selected test evidence when they are not needed for正文 drafting.

## 2026-03-31 11:14:05 +0800

### Step 113
- Action: Audited the remaining `demo_test_evidence -> test_artifacts` pool after the previous Chapter 6 fixes.
- Purpose: Verify whether non-testing documents were still being promoted as optional Chapter 6 test evidence.
- Result:
  - Confirmed that the required Chapter 6 evidence had already been corrected.
  - Confirmed a remaining pool-noise problem:
    - planning/design/interface/task documents were still entering `test_artifacts` as optional assets
    - deployment/startup notes were also still being promoted as test-document assets even though they belong to runtime/deployment evidence rather than test evidence

### Step 114
- Action: Tightened optional test-document classification in `tools/core/extract.py`.
- Purpose: Restrict `test_artifacts` to real testing evidence and stop treating broad project/planning materials as test documents merely because they mention testing.
- Result:
  - Added an exclusion rule set for non-test document classes, including:
    - overall project docs
    - task books
    - planning/design docs
    - interface/database/chaincode docs
    - README files
    - deployment/startup notes
  - Added a score-based optional test-document classifier so only documents with strong testing signals are promoted, such as:
    - test reports
    - manual/full-flow/front-end testing docs
    - acceptance/regression style documents with explicit test structure markers

### Step 115
- Action: Applied the new classification in both `demo_test_evidence` extraction and Chapter 6 test-asset building.
- Purpose: Ensure the material pack and the chapter packet both honor the stricter test-document boundary instead of only fixing one layer.
- Result:
  - `_extract_demo_evidence()` now only adds optional document evidence for strong test documents and skips duplicates of already-promoted primary testing docs.
  - `_build_test_assets()` now filters generic `.md/.txt` candidates through the same stricter classifier before promoting them to `test_artifacts`.
  - As a result, deployment/startup notes remain available through environment/table source paths, but they no longer appear as test-document assets.

### Step 116
- Action: Re-ran the Teatrace refresh and verification chain after tightening the optional test-document rules:
  - `python3 -m py_compile tools/core/extract.py tools/core/writing.py`
  - `python3 tools/cli.py extract --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 tools/cli.py prepare-writing --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 06-系统测试.md`
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md --status reviewed`
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 06-系统测试.md --status reviewed`
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
- Purpose: Confirm that the stricter rules produce a cleaner live asset pool without introducing review or packet-sync regressions.
- Result:
  - `py_compile` passed.
  - The live material-pack `test_artifacts` pool is now reduced to:
    - `后端回归测试报告`
    - `全流程手动测试文档`
    - `前端全流程手动测试文档`
    - runtime test screenshots
  - Planning/design/interface/task/deployment/startup docs no longer appear as optional `test_artifacts`.
  - The live Chapter 6 packet still selects the intended required testing evidence:
    - `后端回归测试报告`
    - `全流程手动测试文档`
  - Workspace check still passes with:
    - `packet_outline_status: current=10`
    - `packet_kind: full=10`
    - `style_issue_count: none`
    - `placeholder_count: none`
    - `citation_order_warning_count: none`
    - `citation_reuse_warning_count: none`
    - `citation_sentence_warning_count: none`

### Current Next Actions
- The optional Chapter 6 test-evidence pool is now substantially cleaner and better aligned with how the bundled sample uses real testing materials.
- If continuing workflow hardening from here, the next likely optimization is screenshot-side filtering: rank or cluster the many runtime screenshots so Chapter 5/6 auto-selection can prefer the most representative pages instead of carrying a large flat screenshot pool.

## 2026-03-31 11:21:56 +0800

### Step 117
- Action: Audited the Chapter 5 and Chapter 6 screenshot payload after cleaning the optional `test_artifacts` pool.
- Purpose: Determine whether runtime screenshots were still entering the chapter packets as a large flat set even after the document-evidence cleanup.
- Result:
  - Confirmed that the material-pack still carried a broad screenshot inventory, which is acceptable as a source pool.
  - Confirmed that the chapter packets themselves were still too noisy:
    - Chapter 5 carried virtually the entire runtime screenshot set as figure assets.
    - Chapter 6 also carried a flat screenshot set instead of a small representative testing sample.

### Step 118
- Action: Added screenshot profiling metadata in `tools/core/extract.py`.
- Purpose: Give runtime screenshots explicit selection semantics so packet assembly can prefer representative screenshots instead of treating every runtime image equally.
- Result:
  - Added a runtime screenshot profile layer with:
    - chapter/section candidates
    - representative selection score
    - selection group
    - auto-select flag
  - Classified common Teatrace screenshots into more meaningful evidence groups, including:
    - identity/permission screenshots
    - registration screenshots
    - batch and stage-flow screenshots
    - trace query success/invalid screenshots
    - low-value repetitive role-default/debug screenshots marked as non-auto-select

### Step 119
- Action: Updated packet asset resolution in `tools/core/writing.py`.
- Purpose: Make required/preferred figure selection honor screenshot priority and avoid dragging the full screenshot pool into Chapter 5/6 packets.
- Result:
  - Added section-aware asset ranking so requirement matching now prefers screenshots whose recommended section aligns with the target chapter subsection.
  - Added grouped multi-pick logic so when multiple screenshots are requested, the resolver prefers different screenshot groups instead of selecting near-duplicates.
  - Fixed preferred-asset handling so `min_count > 1` is now respected for preferred assets as well.
  - Disabled blanket auto-add for Chapter 5 and Chapter 6 after required/preferred assets are chosen, preventing the entire screenshot pool from being appended to the packet.

### Step 120
- Action: Added priority ordering for Chapter 6 required test-document assets while validating the new screenshot resolver.
- Purpose: Ensure the screenshot cleanup did not regress Chapter 6's required document-evidence selection.
- Result:
  - Assigned explicit document selection scores so Chapter 6 continues to pick:
    - `后端回归测试报告`
    - `全流程手动测试文档`
    before `前端全流程手动测试文档`.

### Step 121
- Action: Re-ran the Teatrace refresh and verification chain after the screenshot-selection changes:
  - `python3 -m py_compile tools/core/extract.py tools/core/writing.py`
  - `python3 tools/cli.py extract --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 tools/cli.py prepare-writing --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 06-系统测试.md`
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md --status reviewed`
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 06-系统测试.md --status reviewed`
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
- Purpose: Confirm that the screenshot ranking and packet-assembly changes produce cleaner chapter assets without breaking workspace integrity.
- Result:
  - `py_compile` passed.
  - The live Chapter 5 packet now keeps only 3 figure assets:
    - `系统功能结构图草案`
    - `admin dashboard and forbidden business route`
    - `admin dashboard fixed flow`
  - The live Chapter 6 packet now keeps only 2 representative screenshots:
    - `admin dashboard and forbidden business route`
    - `public trace success`
  - The live Chapter 6 packet still keeps the intended required test documents:
    - `后端回归测试报告`
    - `全流程手动测试文档`
  - Workspace check still passes with:
    - `packet_outline_status: current=10`
    - `packet_kind: full=10`
    - `style_issue_count: none`
    - `placeholder_count: none`
    - `citation_order_warning_count: none`
    - `citation_reuse_warning_count: none`
    - `citation_sentence_warning_count: none`

### Current Next Actions
- The Chapter 5/6 packet layer is now much cleaner in both document evidence and screenshot evidence.
- If continuing workflow hardening from here, the next practical step is to tune section-level screenshot diversity for Chapter 5, so different implementation modules can optionally map to different representative page screenshots instead of both required screenshots landing under the same early subsection.

## 2026-03-31 11:34:47 +0800

### Step 122
- Action: Audited the new Chapter 5 screenshot-contract helper against the live Teatrace chapter packet after the earlier modularization patch.
- Purpose: Confirm whether the second representative screenshot should stay under `5.4.3 批次阶段推进与结果展示实现` or be redirected to the trace-query module.
- Result:
  - Verified with an isolated `PYTHONPATH=/home/ub/thesis_materials/tools python3` probe that the helper logic should prefer:
    - `5.2.3 用户管理与权限治理实现`
    - `5.5.3 公开追溯查询与结果展示实现`
  - Confirmed the live packet was still stuck on the older mapping:
    - `5.2.3 用户管理与权限治理实现`
    - `5.4.3 批次阶段推进与结果展示实现`
  - Located the real issue in workflow cache invalidation rather than in packet assembly itself:
    - the new helper logic existed in code
    - but `prepare-writing` reused the cached `project_profile.json`, so the updated Chapter 5 contract was not being rebuilt into the workspace

### Step 123
- Action: Refined `tools/core/chapter_profile.py` screenshot module scoring and bumped `PROJECT_PROFILE_SCHEMA_VERSION` in `tools/core/project_common.py` from `13` to `14`.
- Purpose: Make externally visible trace/query pages outrank internal stage-result pages for Chapter 5 screenshot contracts, and force existing workspaces to refresh stale `project_profile.json` files.
- Result:
  - Split the previous broad high-priority signal into more precise weights:
    - trace / qrcode / 溯源 / 追溯 gained the strongest priority
    - query / audit remained high, but below explicit trace signals
    - result / display / 结果 / 展示 became only a small supplemental score
  - This removed the accidental bias where the record module won simply because its terminal subfunction contained “结果展示”.
  - After the schema bump and refresh, the Teatrace project profile now records the intended Chapter 5 required screenshot contract:
    - `实现章节代表性页面截图（1） -> 5.2.3 用户管理与权限治理实现`
    - `实现章节代表性页面截图（2） -> 5.5.3 公开追溯查询与结果展示实现`

### Step 124
- Action: Re-ran the Teatrace preparation and validation chain after the Chapter 5 screenshot-priority and cache-refresh fixes:
  - `python3 -m py_compile tools/core/project_common.py tools/core/chapter_profile.py tools/core/extract.py tools/core/writing.py`
  - `python3 tools/cli.py prepare-writing --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
  - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 06-系统测试.md`
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md --status reviewed`
  - `python3 tools/cli.py finalize-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 06-系统测试.md --status reviewed`
  - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
- Purpose: Verify that the new contract actually propagates into the chapter packet and does not regress Chapter 6 testing evidence.
- Result:
  - `py_compile` passed.
  - The refreshed `project_profile.json` now uses `schema_version: 14`.
  - The live Chapter 5 packet now maps its required screenshots to:
    - `admin dashboard and forbidden business route -> 5.2.3 用户管理与权限治理实现`
    - `public trace success -> 5.5.3 公开追溯查询与结果展示实现`
  - The previous `inspector fixed flow -> 5.4.3` mapping is no longer selected as the Chapter 5 required representative screenshot.
  - Chapter 6 stayed clean and stable:
    - required test documents remain `后端回归测试报告` and `全流程手动测试文档`
    - representative screenshots remain `admin dashboard and forbidden business route` and `public trace success`
  - Workspace check still passes with no packet-sync, style, placeholder, or citation warnings.

## 2026-03-31 13:11:51 +0800

### Step 125
- Action: Introduced a dual-output writing interface in the workflow code:
  - added `writing.chapter_briefs_dir`
  - added per-chapter `brief_md` paths into `chapter_queue`
  - kept `chapter_packets` unchanged as the debug-layer artifact
- Purpose: Separate the writing-facing chapter input from the debug/diagnostic packet so chapter drafting no longer has to consume raw provenance and source-path details.
- Result:
  - `tools/core/project_common.py` now resolves `chapter_briefs_dir` with a default path of `docs/writing/chapter_briefs`.
  - `tools/core/writing.py` now creates brief stubs during `prepare-writing`.
  - `prepare-chapter` now generates both:
    - debug packet: `docs/writing/chapter_packets/<chapter>.md`
    - writer brief: `docs/writing/chapter_briefs/<chapter>.md`
  - `chapter_queue.json` now stores `brief_md`, and live Teatrace entries show:
    - `05-系统实现.md -> docs/writing/chapter_briefs/05-系统实现.md`
    - `06-系统测试.md -> docs/writing/chapter_briefs/06-系统测试.md`

### Step 126
- Action: Added a dedicated writer-brief renderer and rewired `start-chapter` to treat the brief as the primary drafting input.
- Purpose: Ensure the new writing-layer artifact is not just emitted, but actually becomes the default chapter-writing interface for humans and chapter-polish skills.
- Result:
  - `tools/core/writing.py` now renders a `Writer Brief` that keeps:
    - chapter structure
    - required assets
    - literal table specs without provenance strings
    - material summaries
    - chapter-specific writing constraints
    - Chapter 5 code evidence as evidence IDs instead of source-code paths
  - The writer brief intentionally excludes debug-facing strings such as:
    - `source_path`
    - `render_as`
    - raw backend/frontend repository paths
    - multi-document `source=... | ... | ...` traces
  - `start-chapter` now emits a start brief that explicitly tells the writer to:
    - read `writer_brief` first
    - open `debug_packet_md` only when debugging evidence mapping or rule hits
  - `tools/cli.py` now prints `brief_md` for both `prepare-chapter` and `start-chapter`.

### Step 127
- Action: Synced workflow docs and validated the new dual-output flow on the Teatrace workspace.
- Purpose: Make the new interface official in the process documentation and confirm it does not regress the existing workspace checks.
- Result:
  - Updated workflow docs:
    - `workflow/WORKSPACE_SPEC.md`
    - `workflow/CHAPTER_EXECUTION.md`
    - `workflow/07-current-project-execution-checklist.md`
  - Validation chain completed successfully:
    - `python3 -m py_compile tools/core/project_common.py tools/core/writing.py tools/cli.py`
    - `python3 tools/cli.py prepare-writing --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
    - `python3 tools/cli.py start-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 06-系统测试.md`
    - `bash workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - The generated writer brief for Chapter 5 is now clean of debug provenance:
    - no `source_path`
    - no `render_as`
    - no `backend/internal/service`
    - no `frontend/src/pages`
    - no `source=...` trace strings
  - The workspace check still passes with:
    - `packet_outline_status: current=10`
    - `packet_kind: full=10`
    - no style, placeholder, or citation warnings

## 2026-03-31 13:28:55 +0800

### Step 128
- Action: Re-audited the live Teatrace workflow state against both the current workspace and the older article-difference audit document.
- Purpose: Determine whether the previously recorded “scaffold overwrite /正文仍为模板骨架” conclusion still matches the current workspace, or has already become stale.
- Result:
  - Confirmed that the older audit at `docs/current_vs_original_article_audit_2026-03-30.md` is now partially outdated.
  - Rechecked the live workspace and found that the current `polished_v3` no longer contains scaffold placeholder markers such as:
    - `本文件由 scaffold 自动生成`
    - `待补：`
    - `Fill the English abstract`
    - `待补正式参考文献`
  - Confirmed that key files now contain substantive content rather than template stubs:
    - `00-摘要.md`
    - `00-Abstract.md`
    - `05-系统实现.md`
    - `06-系统测试.md`
    - `08-致谢.md`
    - `REFERENCES.md`
  - Confirmed the chapter queue remains structurally healthy:
    - automatic chapters reviewed
    - `08-致谢.md` reviewed as manual
    - `REFERENCES.md` managed as registry
    - writer briefs now present for all chapters

### Step 129
- Action: Audited the release-layer freshness while preparing the new current-state report.
- Purpose: Avoid conflating “the release chain has passed before” with “the latest workspace state has already been rebuilt into a fresh delivery artifact”.
- Result:
  - Confirmed `workspaces/teatrace_thesis/word_output/` already contains Linux-side release artifacts:
    - `hyperledger-fabric.docx`
    - `build_summary.json`
    - `release_summary.json`
  - Confirmed those artifacts are timestamped around `2026-03-31 01:15-01:16`, which is earlier than the later queue/packet/brief refreshes around `2026-03-31 13:10+08:00`.
  - Therefore, the release path is historically verified, but the current workspace state has not yet been re-released into a fresh Linux delivery artifact.
  - Confirmed `workspaces/teatrace_thesis/final/` is still empty, so no live `Windows终稿` artifact exists in the current workspace.

### Step 130
- Action: Wrote a replacement current-state audit document at `docs/current_workflow_status_audit_2026-03-31.md`.
- Purpose: Provide an up-to-date status baseline that distinguishes:
  - resolved historical problems
  - stable current workflow capabilities
  - still-open delivery-layer gaps
- Result:
  - The new audit now records the current state as:
    - writing workflow no longer in template-only mode
    - packet/brief/citation/style layers stable
    - Chapter 5/6 evidence selection substantially hardened
    - Linux release chain historically successful but not freshly rebuilt after the latest workflow changes
    - Windows finalization still not materially closed in the live workspace

### Step 131
- Action: Re-ran the live Teatrace Linux release chain against the latest workspace state:
  - `bash workflow/scripts/build_release.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `bash workflow/scripts/verify_release.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `bash workflow/scripts/postprocess_release_linux.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
- Purpose: Convert the earlier “historically verified but timestamp-stale” Linux release state into a fresh delivery artifact that matches the current queue/packet/brief state.
- Result:
  - `build_release.sh` passed on the refreshed workspace state.
  - `verify_release.sh` passed and reported:
    - `docx: .../word_output/hyperledger-fabric.docx`
    - `ref fields: 8`
    - `bookmarks: 8`
    - `anchors missing bookmarks: 0`
  - `postprocess_release_linux.sh` passed and confirmed the Linux delivery artifact without claiming a Word finalization result.
  - `word_output/` artifacts are now refreshed to the current state:
    - `hyperledger-fabric.docx` updated to `2026-03-31 13:46`
    - `build_summary.json` updated to `2026-03-31 13:42`
    - `release_summary.json` updated to `2026-03-31 13:46`
  - The earlier “Linux release artifact is older than the latest workflow state” issue is now resolved.

### Step 132
- Action: Updated `docs/current_workflow_status_audit_2026-03-31.md` after the release refresh.
- Purpose: Keep the newly written current-state audit consistent with the live workspace after the Linux release chain was actually re-executed.
- Result:
  - The audit no longer lists “latest Linux delivery artifact not yet refreshed” as an open issue.
  - The audit now records:
    - Linux release chain refreshed and aligned with the latest workspace state
    - Windows finalization remains the main remaining delivery-layer gap

## 2026-03-31 17:05:12 +0800

### Step 133
- Action: Re-audited the current workflow asset layout before starting the new packaging pass.
- Purpose: Determine which files belong in a unified workflow entry directory, and which ones are debug artifacts, examples, or project-instance outputs that should stay outside.
- Result:
  - Confirmed the actual operational workflow is still split across:
    - `workflow/`
    - `tools/`
    - `paper-research-agent/`
    - `paper-reader/`
  - Confirmed the real local chapter-polish skill remains:
    - `workflow/skills/academic-paper-crafter/`
  - Confirmed the active Teatrace workspace config remains:
    - `workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Confirmed that `tools/node_modules/`, `tools/unpacked_*`, `tools/examples/health_record/`, and `workflow/fixtures/` should not be bundled into the new unified entry directory.

### Step 134
- Action: Created a new unified directory `workflow_bundle/` and copied the currently used workflow assets into it.
- Purpose: Give future AI conversations a single folder that contains the runnable workflow docs, scripts, tools, and skills, instead of forcing them to infer the process from scattered root-level directories.
- Result:
  - Added bundle-local workflow docs, scripts, references, configs, templates, and local skills under:
    - `workflow_bundle/workflow/`
  - Added bundle-local tool entrypoints and core Python implementation under:
    - `workflow_bundle/tools/`
  - Added bundle-local skill mirrors for runtime compatibility:
    - `workflow_bundle/paper-research-agent/`
    - `workflow_bundle/paper-reader/`
  - Added current workflow state references under:
    - `workflow_bundle/docs/`

### Step 135
- Action: Added bundle documentation files `workflow_bundle/README.md` and `workflow_bundle/BUNDLE_MANIFEST.md`.
- Purpose: Make the new directory understandable as a workflow handoff surface rather than a blind file dump.
- Result:
  - `README.md` now explains:
    - what the bundle is for
    - which commands are the official entrypoints
    - where the active Teatrace workspace still lives
    - why both `workflow/skills/...` and root-level research skill mirrors are kept
  - `BUNDLE_MANIFEST.md` now explicitly records:
    - which assets were included
    - which assets were intentionally excluded
    - the packaging rationale

## 2026-03-31 15:30:12 +0800

### Step 136
- Action: Implemented repo-level active workspace resolution and workspace-state utilities.
- Purpose: Stop new conversations and no-argument commands from silently falling back to the old bundled sample config.
- Result:
  - Added `tools/core/runtime_state.py`.
  - Added active workspace pointer support at:
    - `workflow_bundle/workflow/configs/active_workspace.json`
  - Added bundle signature calculation, handoff refresh, and workspace execution-log helpers.
  - Updated `tools/core/build_final_thesis_docx.py` so default config resolution now uses the active workspace pointer rather than `workflow/configs/current_workspace.json`.

### Step 137
- Action: Extended the CLI and workflow scripts for cold-start takeover.
- Purpose: Make the new workflow executable from a fresh AI dialogue without re-reading the full repo or relying on previous conversation memory.
- Result:
  - Added new CLI commands:
    - `set-active-workspace`
    - `resolve-active-workspace`
    - `refresh-handoff`
    - `resume`
  - Relaxed most workspace-bound `--config` arguments so they can use the active workspace pointer when omitted.
  - Updated shell wrappers:
    - `workflow/scripts/check_workspace.sh`
    - `workflow/scripts/build_release.sh`
    - `workflow/scripts/verify_release.sh`
    - `workflow/scripts/postprocess_release.sh`
    - `workflow/scripts/postprocess_release_linux.sh`
  - No-argument script mode now resolves the active workspace first instead of the old sample workspace.

### Step 138
- Action: Added canonical workspace handoff and workspace execution logging.
- Purpose: Give new AI conversations a single machine-readable and human-readable state surface, plus a separate per-workspace execution history.
- Result:
  - Added workspace-state paths via config convention:
    - `docs/workflow/handoff.json`
    - `docs/workflow/handoff.md`
    - `docs/workflow/execution_log.md`
  - Updated:
    - `tools/core/project_common.py`
    - `tools/core/intake.py`
    - `tools/core/writing.py`
    - workspace/template config files
  - Teatrace workspace now has:
    - `workspaces/teatrace_thesis/docs/workflow/handoff.json`
    - `workspaces/teatrace_thesis/docs/workflow/handoff.md`
    - `workspaces/teatrace_thesis/docs/workflow/execution_log.md`

### Step 139
- Action: Added the repo-specific cold-start skill and wired it into workspace creation and current workspace assets.
- Purpose: Formalize the “new conversation should read handoff first” behavior as a reusable local skill.
- Result:
  - Added new skill:
    - `workflow/skills/thesis-workflow-resume/SKILL.md`
  - Added `resume_skill_path` to workspace config generation and templates.
  - Intake now copies the new skill into generated workspaces.
  - Synced the skill into the live Teatrace workspace at:
    - `workspaces/teatrace_thesis/workflow/skills/thesis-workflow-resume/SKILL.md`

### Step 140
- Action: Updated workflow documentation and bundle entry documentation.
- Purpose: Align the official written process with the new runtime model: bundle-first, active-pointer-first, handoff-first.
- Result:
  - Updated workflow docs:
    - `workflow/README.md`
    - `workflow/references/command-map.md`
    - `workflow/WORKSPACE_SPEC.md`
    - `workflow/07-current-project-execution-checklist.md`
    - `tools/README.md`
  - Updated bundle docs:
    - `workflow_bundle/README.md`
    - `workflow_bundle/BUNDLE_MANIFEST.md`
  - Synced the updated workflow/docs/tools into `workflow_bundle/`.

### Step 141
- Action: Validated both root compatibility entrypoints and the new bundle-first entrypoints against the live Teatrace workspace.
- Purpose: Confirm that the new cold-start workflow is not only documented, but actually usable end to end.
- Result:
  - `python3 -m py_compile tools/cli.py tools/core/*.py tools/windows/*.py` passed.
  - `python3 tools/cli.py set-active-workspace --config workspaces/teatrace_thesis/workflow/configs/workspace.json` passed.
  - `python3 tools/cli.py resume` passed and correctly classified the live workspace as:
    - `phase: linux-release-ready`
  - `bash workflow/scripts/check_workspace.sh` now works in no-argument mode and correctly resolves the Teatrace workspace via the active pointer.
  - `python3 -m py_compile workflow_bundle/tools/cli.py workflow_bundle/tools/core/*.py workflow_bundle/tools/windows/*.py` passed.
  - `python3 workflow_bundle/tools/cli.py resume` passed.
  - `bash workflow_bundle/workflow/scripts/check_workspace.sh` passed in no-argument mode.

### Step 142
- Action: Removed stale Python cache artifacts from `workflow_bundle/`.
- Purpose: Keep the new official workflow entry directory free of `__pycache__` noise so future AI conversations do not confuse cache files with formal workflow assets.
- Result:
  - Deleted all `workflow_bundle/**/__pycache__/` contents and `.pyc` files.
  - Reconfirmed that the bundle no longer contains cached Python bytecode artifacts.

### Step 143
- Action: Hardened runtime state, CLI behavior, and workspace checks around orchestration, drift detection, and concurrency control.
- Purpose: Turn the workflow from “chat-memory-driven” execution into a deterministic state machine that new AI conversations can resume from local artifacts.
- Result:
  - Added new workspace config fields:
    - `workflow_state.workspace_lock_json`
    - `writing.orchestrator_skill_path`
  - Updated:
    - `tools/core/project_common.py`
    - `tools/core/runtime_state.py`
    - `tools/core/workspace_checks.py`
    - `tools/core/intake.py`
    - `tools/core/writing.py`
    - `tools/cli.py`
  - `resume` no longer refreshes handoff implicitly; it now reports live:
    - `workflow_signature_status`
    - `lock_status`
    - `orchestrator_skill_path`
    - `resume_skill_path`
  - Added CLI commands:
    - `lock-status`
    - `clear-lock --force`
    - `smoke-intake`
  - Added workspace lock handling for mutating workflow commands, with lock acquisition/release entries written to the workspace execution log.

### Step 144
- Action: Added the new top-level orchestration skill and updated cold-start guidance.
- Purpose: Ensure new AI conversations can reproduce the same thesis-writing workflow without depending on hidden prior chat context.
- Result:
  - Added new skill:
    - `workflow/skills/thesis-workflow-orchestrator/SKILL.md`
  - Updated:
    - `workflow/skills/thesis-workflow-resume/SKILL.md`
  - Intake now copies the new orchestrator skill into generated workspaces.
  - Synced the new orchestrator skill and updated resume skill into the live Teatrace workspace.

### Step 145
- Action: Reworked workflow docs and command references to make `workflow_bundle/` the official entry surface.
- Purpose: Remove ambiguity between root compatibility paths and the bundle-first operational path, and document the new lock/drift/orchestration model.
- Result:
  - Updated root workflow/docs:
    - `workflow/README.md`
    - `workflow/THESIS_WORKFLOW.md`
    - `workflow/CHAPTER_EXECUTION.md`
    - `workflow/WORKSPACE_SPEC.md`
    - `workflow/07-current-project-execution-checklist.md`
    - `workflow/08-dual-platform-release.md`
    - `workflow/MIGRATION.md`
    - `workflow/references/command-map.md`
    - `workflow/templates/workspace-config.template.json`
    - `tools/README.md`
  - Updated bundle-specific docs:
    - `workflow_bundle/README.md`
    - `workflow_bundle/BUNDLE_MANIFEST.md`
  - `compare_versions.sh` is now workspace-aware and resolves the active workspace when no config is provided.

### Step 146
- Action: Synced the updated workflow/tools into `workflow_bundle/`, added the bundle smoke fixture, and refreshed the live Teatrace workspace config/state.
- Purpose: Keep bundle/runtime copies aligned with the root implementation and ensure the current active workspace exposes the new orchestrator/lock interface explicitly.
- Result:
  - Synced updated files into:
    - `workflow_bundle/workflow/`
    - `workflow_bundle/tools/`
  - Added bundle-contained smoke fixture:
    - `workflow_bundle/workflow/fixtures/fabric_trace_demo/`
  - Updated live Teatrace workspace config:
    - `workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Refreshed live Teatrace queue so it now includes:
    - `orchestrator_skill_path`

### Step 147
- Action: Removed accidentally synced dependency/debug artifacts from `workflow_bundle/tools/`.
- Purpose: Preserve the bundle as a clean workflow entry directory rather than a dump of local dependency and unpacked DOCX artifacts.
- Result:
  - Deleted:
    - `workflow_bundle/tools/node_modules/`
    - `workflow_bundle/tools/unpacked_*`
  - Reconfirmed `workflow_bundle/tools/` now only contains:
    - `core/`
    - `windows/`
    - direct tool entry files

### Step 148
- Action: Validated the new workflow behavior on both the live Teatrace workspace and a newly created smoke workspace.
- Purpose: Prove that the new cold-start, lock, drift, and bundle-first paths are real runtime behavior rather than documentation-only changes.
- Result:
  - Teatrace validation passed:
    - `python3 workflow_bundle/tools/cli.py prepare-writing --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py refresh-handoff --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py resume --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py check-workspace --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `bash workflow_bundle/workflow/scripts/compare_versions.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `bash workflow_bundle/workflow/scripts/build_release.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `bash workflow_bundle/workflow/scripts/verify_release.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py lock-status --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py clear-lock --config workspaces/teatrace_thesis/workflow/configs/workspace.json --force`
  - Verified that Teatrace `resume` now reports:
    - `phase: linux-release-ready`
    - `workflow_signature_status: current`
    - `lock_status: unlocked`
    - `orchestrator_skill_path: /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/skills/thesis-workflow-orchestrator/SKILL.md`
  - New-workspace smoke validation passed:
    - `python3 workflow_bundle/tools/cli.py smoke-intake --project-root workflow_bundle/workflow/fixtures/fabric_trace_demo --title "Fabric Smoke Thesis" --out /tmp/workflow_smoke_fabric`
  - Smoke workspace successfully reached:
    - `phase: chapter-in-progress`
    - `packet_outline_status: current=10`
    - `packet_kind: stub=10`
    - `workflow_signature_status: current`
    - `lock_status: unlocked`

### Step 149
- Action: Added a dedicated root/bundle compatibility-mirror check and tightened the surrounding workflow documentation.
- Purpose: Finish the low-risk single-source收口 path by keeping `workflow_bundle/` as the only authoritative runtime while making root compatibility drift explicit and machine-checkable.
- Result:
  - Added new bundle-maintenance script:
    - `workflow_bundle/workflow/scripts/check_bundle_sync.sh`
  - Added root compatibility wrapper:
    - `workflow/scripts/check_bundle_sync.sh`
  - The new check now verifies:
    - root Python compatibility launchers still point to `workflow_bundle/tools/...`
    - root shell wrappers still point to `workflow_bundle/workflow/scripts/...`
    - root `tools/core/` remains byte-identical to `workflow_bundle/tools/core/`
  - Updated workflow/docs so the single-source rule is explicit:
    - `workflow/README.md`
    - `workflow_bundle/README.md`
    - `tools/README.md`
    - `workflow_bundle/tools/README.md`
    - `workflow/references/command-map.md`
    - `workflow_bundle/workflow/references/command-map.md`
  - The documented rule is now:
    - `workflow_bundle/tools/core/` is the authoritative runtime implementation
    - root `tools/core/` is retained only as a compatibility mirror for old import paths

### Step 150
- Action: Validated the new mirror-check path, re-checked root compatibility entrypoints, and refreshed the live Teatrace handoff after the bundle signature changed.
- Purpose: Ensure the new maintenance check works on real files and that a new AI conversation will still resume from a `current` workflow signature instead of seeing stale drift after this refactor.
- Result:
  - Initial validation exposed two checker bugs:
    - the bundle script initially resolved the repository root one level too shallow
    - raw directory diff initially included `__pycache__/` noise
  - Fixed both issues by:
    - rebasing the bundle script to the real repository root
    - excluding `__pycache__` / `*.pyc` from mirror comparison
  - Validation then passed for both entry surfaces:
    - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `bash workflow/scripts/check_bundle_sync.sh`
  - Compatibility/runtime smoke checks also passed:
    - `python3 -m py_compile tools/cli.py tools/build_final_thesis_docx.py tools/verify_citation_links.py tools/postprocess_word_format.py workflow_bundle/tools/cli.py`
    - `python3 tools/cli.py resume`
    - `bash workflow/scripts/check_workspace.sh`
  - Refreshed live Teatrace handoff/signature state:
    - `python3 workflow_bundle/tools/cli.py refresh-handoff --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - After refresh, the live workspace remains at:
    - `phase: linux-release-ready`
    - `workflow_signature_status: current`
    - `lock_status: unlocked`

### Step 151
- Action: Added a dedicated bundle-to-root compatibility sync script and updated the workflow docs to treat it as the standard follow-up after bundle-side tool changes.
- Purpose: Move the single-source cleanup beyond “detect drift” to “repair drift” so future maintenance does not require manual copying of `tools/core/*`.
- Result:
  - Added new authoritative sync script:
    - `workflow_bundle/workflow/scripts/sync_root_compat.sh`
  - Added root compatibility wrapper:
    - `workflow/scripts/sync_root_compat.sh`
  - The new sync path now:
    - uses `workflow_bundle/tools/core/` as the only source
    - refreshes root `tools/core/` with `rsync --delete`
    - ignores `__pycache__/` and `*.pyc` noise
    - leaves root wrapper launchers under `workflow/scripts/` and `tools/*.py` to `check_bundle_sync.sh`
  - Updated docs and migration references:
    - `workflow/README.md`
    - `workflow_bundle/README.md`
    - `tools/README.md`
    - `workflow_bundle/tools/README.md`
    - `workflow/references/command-map.md`
    - `workflow_bundle/workflow/references/command-map.md`
    - `workflow/MIGRATION.md`
    - `workflow_bundle/workflow/MIGRATION.md`

### Step 152
- Action: Executed the new sync command, re-ran the compatibility checks, and revalidated the live Teatrace workspace state.
- Purpose: Prove that the new maintenance path is usable in practice and does not break the current Linux-ready thesis workspace.
- Result:
  - The new sync command ran successfully:
    - `bash workflow_bundle/workflow/scripts/sync_root_compat.sh`
  - Bundle/root compatibility checks passed after sync:
    - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
  - Runtime verification passed:
    - `python3 workflow_bundle/tools/cli.py refresh-handoff --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py resume`
    - `python3 tools/cli.py resume`
    - `bash workflow/scripts/check_workspace.sh`
  - The live Teatrace workspace remains at:
    - `phase: linux-release-ready`
    - `workflow_signature_status: current`
    - `lock_status: unlocked`

### Step 153
- Action: Refactored the root-compat maintenance scripts to use a shared wrapper manifest instead of duplicating the compatibility wrapper list in multiple places.
- Purpose: Prevent the new automation layer itself from drifting by making `sync_root_compat.sh` and `check_bundle_sync.sh` read the same source-of-truth wrapper inventory.
- Result:
  - Added shared manifest:
    - `workflow_bundle/workflow/scripts/root_compat_manifest.sh`
  - `workflow_bundle/workflow/scripts/sync_root_compat.sh` now:
    - sources the shared manifest
    - regenerates root `tools/*.py` compatibility launchers
    - regenerates root `workflow/scripts/*.sh` compatibility wrappers
    - keeps root `tools/core/` mirrored from `workflow_bundle/tools/core/`
  - `workflow_bundle/workflow/scripts/check_bundle_sync.sh` now:
    - sources the same manifest
    - verifies both the generator marker and the bundle target path for every root wrapper
    - reports wrapper checks with clearer labels instead of repeated generic pass lines
  - Updated docs to state explicitly that root wrapper files are generated artifacts and should not be hand-maintained:
    - `workflow/README.md`
    - `workflow_bundle/README.md`
    - `tools/README.md`
    - `workflow_bundle/tools/README.md`
    - `workflow/MIGRATION.md`
    - `workflow_bundle/workflow/MIGRATION.md`

### Step 154
- Action: Regenerated the root compatibility layer from the new manifest-driven sync path and revalidated the live workspace.
- Purpose: Confirm that the wrapper generation model works end to end on the current repository instead of remaining a documentation-only convention.
- Result:
  - Root compatibility regeneration succeeded:
    - `bash workflow_bundle/workflow/scripts/sync_root_compat.sh`
  - Bundle/root compatibility verification passed with the new labeled output:
    - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
  - Runtime validation passed:
    - `python3 -m py_compile tools/cli.py tools/build_final_thesis_docx.py tools/verify_citation_links.py tools/postprocess_word_format.py workflow_bundle/tools/cli.py`
    - `python3 workflow_bundle/tools/cli.py refresh-handoff --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py resume`
    - `python3 tools/cli.py resume`
    - `bash workflow/scripts/check_workspace.sh`
  - The live Teatrace workspace remains at:
    - `phase: linux-release-ready`
    - `workflow_signature_status: current`
    - `lock_status: unlocked`

### Step 155
- Action: Hooked the root/bundle compatibility check into the official preflight scripts instead of leaving it as a manual maintenance-only command.
- Purpose: Ensure release-time execution stops early when bundle-side changes have not been propagated to the root compatibility layer.
- Result:
  - Updated bundle script entrypoints:
    - `workflow_bundle/workflow/scripts/check_workspace.sh`
    - `workflow_bundle/workflow/scripts/postprocess_release.sh`
    - `workflow_bundle/workflow/scripts/postprocess_release_linux.sh`
  - The new behavior is now:
    - `check_workspace.sh` runs `check_bundle_sync.sh` before the workspace JSON preflight
    - `build_release.sh` and `verify_release.sh` inherit the same compat preflight because they already call `check_workspace.sh`
    - both postprocess scripts now also run the compat preflight before continuing
  - Updated execution checklist docs:
    - `workflow/07-current-project-execution-checklist.md`
    - `workflow_bundle/workflow/07-current-project-execution-checklist.md`

### Step 156
- Action: Ran the updated preflight and Linux postprocess paths on the live Teatrace workspace, then refreshed handoff/signature state.
- Purpose: Verify that the new release-time compat gate actually executes on real workflow commands and leaves the current workspace usable.
- Result:
  - Updated preflight path executed successfully:
    - `bash workflow_bundle/workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Updated Linux postprocess path executed successfully:
    - `bash workflow_bundle/workflow/scripts/postprocess_release_linux.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Both commands now visibly run the root/bundle compat check before continuing.
  - Refreshed runtime status after the bundle signature changed:
    - `python3 workflow_bundle/tools/cli.py refresh-handoff --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py resume`
    - `bash workflow_bundle/workflow/scripts/check_workspace.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - The live Teatrace workspace remains at:
    - `phase: linux-release-ready`
    - `workflow_signature_status: current`
    - `lock_status: unlocked`

### Step 157
- Action: Introduced a dedicated `release_preflight.sh` entrypoint and rewired release-related scripts to use it as their shared preflight contract.
- Purpose: Remove the remaining shell-level duplication around config resolution and preflight sequencing so build/verify/postprocess flows all rely on the same release gate.
- Result:
  - Added new shared script:
    - `workflow_bundle/workflow/scripts/release_preflight.sh`
  - Added a generated root compatibility wrapper for it through:
    - `workflow_bundle/workflow/scripts/root_compat_manifest.sh`
    - `workflow_bundle/workflow/scripts/sync_root_compat.sh`
  - Updated bundle release entrypoints to consume the new shared preflight:
    - `workflow_bundle/workflow/scripts/check_workspace.sh`
    - `workflow_bundle/workflow/scripts/build_release.sh`
    - `workflow_bundle/workflow/scripts/verify_release.sh`
    - `workflow_bundle/workflow/scripts/postprocess_release.sh`
    - `workflow_bundle/workflow/scripts/postprocess_release_linux.sh`
  - Updated docs so `release_preflight.sh` is now documented as the unified release-time gate:
    - `workflow/README.md`
    - `workflow_bundle/README.md`
    - `workflow/07-current-project-execution-checklist.md`
    - `workflow_bundle/workflow/07-current-project-execution-checklist.md`
    - `workflow/references/command-map.md`
    - `workflow_bundle/workflow/references/command-map.md`

### Step 158
- Action: Regenerated root wrappers after adding `release_preflight.sh` and validated both bundle/root execution paths on the live Teatrace workspace.
- Purpose: Confirm that the new shared preflight entrypoint is available from both the official bundle path and the root compatibility path, and that it preserves the current workspace state.
- Result:
  - Regenerated compatibility layer:
    - `bash workflow_bundle/workflow/scripts/sync_root_compat.sh`
  - Validated bundle compatibility state:
    - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
  - Validated the new shared preflight entry:
    - `bash workflow_bundle/workflow/scripts/release_preflight.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `bash workflow/scripts/release_preflight.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Refreshed and rechecked runtime state:
    - `python3 workflow_bundle/tools/cli.py refresh-handoff --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py resume`
  - The live Teatrace workspace remains at:
    - `phase: linux-release-ready`
    - `workflow_signature_status: current`
    - `lock_status: unlocked`

### Step 159
- Action: Added a shared bundle-internal build helper so `build_release.sh` and `verify_release.sh` no longer duplicate the same `release_preflight -> prepare-figures -> build -> resolve docx path` shell sequence.
- Purpose: Continue reducing release-script duplication below the preflight layer and keep the public release entrypoints thin.
- Result:
  - Added new internal helper:
    - `workflow_bundle/workflow/scripts/build_release_docx.sh`
  - Updated bundle release entrypoints:
    - `workflow_bundle/workflow/scripts/build_release.sh`
    - `workflow_bundle/workflow/scripts/verify_release.sh`
  - The helper now:
    - resolves the active workspace when config is omitted
    - runs `release_preflight.sh`
    - runs `prepare-figures`
    - runs `build`
    - prints only the resolved DOCX path to stdout for caller scripts
  - Updated docs to reflect the new unified release-preflight language and the shared internal build path:
    - `workflow_bundle/workflow/README.md`
    - `workflow/08-dual-platform-release.md`
    - `workflow_bundle/workflow/08-dual-platform-release.md`

### Step 160
- Action: Validated the new internal build helper and the public build/verify wrappers on the live Teatrace workspace.
- Purpose: Prove that the de-duplicated build chain still produces the expected summaries and citation verification results.
- Result:
  - Direct helper validation passed:
    - `bash workflow_bundle/workflow/scripts/build_release_docx.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Public wrapper validation passed after running sequentially:
    - `bash workflow_bundle/workflow/scripts/build_release.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `bash workflow_bundle/workflow/scripts/verify_release.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Sequential validation also reconfirmed that workspace locking still blocks overlapping build/prepare operations during concurrent runs.
  - The updated release chain produced:
    - `word_output/build_summary.json`
    - `word_output/release_summary.json`
  - Refreshed runtime status after the bundle signature changed:
    - `python3 workflow_bundle/tools/cli.py refresh-handoff --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py resume`
  - The live Teatrace workspace remains at:
    - `phase: linux-release-ready`
    - `workflow_signature_status: current`
    - `lock_status: unlocked`

## 2026-03-31 18:49:16 +0800

### Step 161
- Action: Re-entered the workflow from the current bundle runtime using the orchestrator startup sequence, including `resume`, `handoff.md`, and the `read_first` state files.
- Purpose: Avoid relying on prior chat memory while continuing the workflow-hardening work on a drifted bundle signature.
- Result:
  - Confirmed the active workspace is still Teatrace:
    - `workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Confirmed the workspace phase before edits remained:
    - `phase: linux-release-ready`
  - Confirmed the new bundle edit set initially showed:
    - `workflow_signature_status: drifted`
    - `lock_status: unlocked`
  - Re-read:
    - `workspaces/teatrace_thesis/docs/workflow/handoff.md`
    - `workspaces/teatrace_thesis/docs/writing/chapter_queue.json`
    - `workspaces/teatrace_thesis/word_output/build_summary.json`
    - `workspaces/teatrace_thesis/word_output/release_summary.json`

### Step 162
- Action: Collapsed the bundle release shell entrypoints into thin delegates over the new public CLI release commands, and demoted `build_release_docx.sh` to an internal compatibility helper.
- Purpose: Make `workflow_bundle/tools/cli.py` the single authoritative release orchestration surface for new AI conversations, while keeping shell compatibility entrypoints available.
- Result:
  - Updated bundle release scripts:
    - `workflow_bundle/workflow/scripts/release_preflight.sh`
    - `workflow_bundle/workflow/scripts/build_release.sh`
    - `workflow_bundle/workflow/scripts/verify_release.sh`
    - `workflow_bundle/workflow/scripts/build_release_docx.sh`
  - Updated CLI release output contract:
    - `workflow_bundle/tools/cli.py`
  - `release-build` and `release-verify` now print:
    - `docx_path: ...`
  - `build_release_docx.sh` now:
    - calls the public `release-build` command
    - mirrors its stdout to stderr for debug visibility
    - extracts only the `docx_path` line for compatibility callers
  - Public shell release wrappers now only forward arguments to:
    - `python3 workflow_bundle/tools/cli.py release-preflight`
    - `python3 workflow_bundle/tools/cli.py release-build`
    - `python3 workflow_bundle/tools/cli.py release-verify`

### Step 163
- Action: Updated the workflow handoff and operator-facing docs to describe the new public release surface and the reduced role of shell wrappers.
- Purpose: Ensure a new AI conversation can reproduce the correct release path from repository files alone, without re-deriving or mixing old shell helper sequences.
- Result:
  - Updated bundle/root entry docs:
    - `workflow_bundle/README.md`
    - `workflow_bundle/workflow/README.md`
    - `workflow/README.md`
  - Updated command maps:
    - `workflow_bundle/workflow/references/command-map.md`
    - `workflow/references/command-map.md`
  - Updated dual-platform release docs:
    - `workflow_bundle/workflow/08-dual-platform-release.md`
    - `workflow/08-dual-platform-release.md`
  - The documented public Linux release path is now centered on:
    - `release-preflight`
    - `release-build`
    - `release-verify`
  - `build_release_docx.sh` is now explicitly documented as:
    - internal compatibility helper
    - not the normal release entry for new conversations

### Step 164
- Action: Ran static and runtime validation against the live Teatrace workspace after the release-surface refactor.
- Purpose: Verify that the new CLI-centered release flow and the updated compatibility wrappers still produce the expected artifacts, enforce locks, and preserve resumable workspace state.
- Result:
  - Static validation passed:
    - `python3 -m py_compile workflow_bundle/tools/cli.py`
    - `bash -n workflow_bundle/workflow/scripts/release_preflight.sh`
    - `bash -n workflow_bundle/workflow/scripts/build_release.sh`
    - `bash -n workflow_bundle/workflow/scripts/verify_release.sh`
    - `bash -n workflow_bundle/workflow/scripts/build_release_docx.sh`
  - Runtime validation passed:
    - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `python3 workflow_bundle/tools/cli.py release-preflight --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `bash workflow_bundle/workflow/scripts/release_preflight.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py release-build --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `bash workflow_bundle/workflow/scripts/build_release_docx.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `bash workflow_bundle/workflow/scripts/build_release.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py release-verify --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `bash workflow_bundle/workflow/scripts/verify_release.sh workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`
  - The updated release flow produced refreshed artifacts:
    - `workspaces/teatrace_thesis/word_output/build_summary.json`
    - `workspaces/teatrace_thesis/word_output/release_summary.json`
    - latest build run:
      - `workspaces/teatrace_thesis/word_output/build_runs/build_summary_20260331T184859_0800.json`
    - latest release run:
      - `workspaces/teatrace_thesis/word_output/release_runs/release_summary_20260331T184835_0800.json`
  - Confirmed compatibility helper behavior:
    - `build_release_docx.sh` returned `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`
  - Confirmed shell verify passthrough behavior:
    - `verify_release.sh <docx-path>` still supports direct citation verification without rebuilding
  - Confirmed lock enforcement still works on the new entrypoints:
    - starting `release-verify` while `build_release_docx.sh` was still building raised the expected workspace lock error
    - after the build finished, the same `release-verify` command succeeded sequentially

### Step 165
- Action: Refreshed handoff and resumed the workspace after the release validation run.
- Purpose: Leave the Teatrace workspace in a clean, resumable state with the new bundle signature recorded.
- Result:
  - Executed:
    - `python3 workflow_bundle/tools/cli.py refresh-handoff --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py resume`
  - The live Teatrace workspace now remains at:
    - `phase: linux-release-ready`
    - `workflow_signature_status: current`
    - `lock_status: unlocked`
    - `next_commands: none`

### Step 166
- Action: Cleaned the intake implementation and tightened the remaining workflow entry documentation around the new asset-sync semantics.
- Purpose: Make new conversations reproducible without relying on prior chat memory, and ensure `workflow_signature_status` is documented as a real workspace-asset sync state instead of a handoff timestamp proxy.
- Result:
  - Removed the unused `_copy_skill_tree` helper and its dead `shutil` import from:
    - `workflow_bundle/tools/core/intake.py`
  - Updated the command maps:
    - `workflow_bundle/workflow/references/command-map.md`
    - `workflow/references/command-map.md`
  - Updated the dual-platform release docs:
    - `workflow_bundle/workflow/08-dual-platform-release.md`
    - `workflow/08-dual-platform-release.md`
  - The documented cold-start path is now explicitly:
    - `resume --config`
    - `sync-workflow-assets --config` when status is `drifted`
    - optional `refresh-handoff --config`
    - `release-preflight -> release-build -> release-verify`
  - The docs now also state explicitly that:
    - `docs/workflow/workflow_assets_state.json` is the source of truth for `workflow_signature_status`
    - `refresh-handoff` does not clear drift on its own
    - shell scripts remain compatibility wrappers around the CLI-first release path

### Step 167
- Action: Revalidated the Teatrace workspace on the new cold-start flow, refreshed the workspace state files, and updated the formal status audit.
- Purpose: Confirm that the workflow can now be resumed from a fresh conversation by reading workspace state instead of relying on chat history, and capture the validation outcome in the audit baseline.
- Result:
  - Static validation passed:
    - `python3 -m py_compile workflow_bundle/tools/cli.py workflow_bundle/tools/core/runtime_state.py workflow_bundle/tools/core/project_common.py workflow_bundle/tools/core/workspace_checks.py workflow_bundle/tools/core/intake.py`
  - Bundle/root compatibility validation passed:
    - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `bash workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
  - Resume and asset-sync validation passed:
    - first `resume --config ...` returned `workflow_signature_status: drifted`
    - `sync-workflow-assets --config ...` refreshed workspace-local docs/skills and wrote `docs/workflow/workflow_assets_state.json`
    - `refresh-handoff --config ...` then `resume --config ...` returned:
      - `phase: linux-release-ready`
      - `workflow_signature_status: current`
      - `lock_status: unlocked`
      - `next_commands: none`
  - Release-path validation passed:
    - `python3 workflow_bundle/tools/cli.py release-preflight --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `bash workflow_bundle/workflow/scripts/build_release.sh workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py release-build --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py release-verify --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `bash workflow_bundle/workflow/scripts/verify_release.sh workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`
  - Lock enforcement was also confirmed:
    - launching `release-verify` while `release-build` still held the workspace lock raised the expected lock error
    - re-running `release-verify` sequentially succeeded
  - Latest aligned outputs:
    - `workspaces/teatrace_thesis/docs/workflow/workflow_assets_state.json` at `2026-03-31 19:39:01 +0800`
    - `workspaces/teatrace_thesis/word_output/build_summary.json` at `2026-03-31 19:39:38 +0800`
    - `workspaces/teatrace_thesis/word_output/release_summary.json` at `2026-03-31 19:39:57 +0800`
  - Updated audit baselines:
    - `docs/current_workflow_status_audit_2026-03-31.md`
    - `workflow_bundle/docs/current_workflow_status_audit_2026-03-31.md`

### Step 168
- Action: Added a human-facing AI prompt guide to the workflow, wired it into the repository entry docs, and verified that `sync-workflow-assets` now propagates it into live workspaces.
- Purpose: Make the workflow usable in a brand-new AI conversation without relying on informal chat memory, by giving the user copyable prompts that explicitly steer the model onto the repository's official execution path.
- Result:
  - Added new guide documents:
    - `workflow_bundle/workflow/06-ai-prompt-guide.md`
    - `workflow/06-ai-prompt-guide.md`
  - The new guide now covers:
    - what information the user must provide
    - mandatory cold-start rules
    - source-of-truth constraints
    - chapter/release/logging constraints
    - copyable prompts for:
      - resume existing workspace
      - intake new project
      - continue one chapter
      - polish one chapter
      - Linux release only
      - workflow troubleshooting
    - anti-pattern prompts such as vague `继续吧`
  - Updated repository entry docs to surface the new guide:
    - `workflow_bundle/README.md`
    - `workflow_bundle/workflow/README.md`
    - `workflow/README.md`
    - `workflow_bundle/workflow/THESIS_WORKFLOW.md`
    - `workflow/THESIS_WORKFLOW.md`
    - `workflow_bundle/workflow/07-current-project-execution-checklist.md`
    - `workflow/07-current-project-execution-checklist.md`
  - Updated runtime-managed workflow docs:
    - added `06-ai-prompt-guide.md` to `workflow_bundle/tools/core/runtime_state.py` `MANAGED_WORKFLOW_DOCS`
    - workspace-local generated `workflow/README.md` now also lists the prompt guide in managed workflow assets
  - Validation passed:
    - `python3 -m py_compile workflow_bundle/tools/core/runtime_state.py`
    - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh` initially detected the expected `runtime_state.py` mirror drift
    - `bash workflow_bundle/workflow/scripts/sync_root_compat.sh` refreshed root compatibility mirror and wrappers
    - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh` then passed
    - `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py resume --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Confirmed live workspace propagation:
    - `workspaces/teatrace_thesis/workflow/06-ai-prompt-guide.md` exists
    - `sync-workflow-assets` reported `synced_doc_count: 10`
    - Teatrace remained in:
      - `phase: linux-release-ready`
      - `workflow_signature_status: current`
      - `lock_status: unlocked`

### Step 169
- Action: Fixed DOCX table rendering so workflow-generated tables no longer inherit Word's full grid style and instead render as three-line tables.
- Purpose: Resolve the formatting issue where generated thesis tables looked like full bordered grid tables rather than the expected academic `三线表`.
- Result:
  - Updated:
    - `workflow_bundle/tools/core/build_final_thesis_docx.py`
  - Implementation changes:
    - added `_clear_table_style(table)` to remove `w:tblStyle` from generated tables
    - stopped assigning `Table Grid` in `_add_table(...)`
    - strengthened `_apply_three_line_table(...)` so it explicitly writes:
      - top border on the header row
      - bottom border on the header row
      - bottom border on the last row
      - no left/right borders
      - no inner horizontal/vertical borders
  - Synced bundle core back to root compatibility mirror:
    - `bash workflow_bundle/workflow/scripts/sync_root_compat.sh`
  - Validation passed:
    - `python3 -m py_compile workflow_bundle/tools/core/build_final_thesis_docx.py`
    - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `python3 workflow_bundle/tools/cli.py release-build --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - XML-level verification on regenerated `workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`:
    - `TableGrid count: 0`
    - `tblStyle count: 0`
    - `insideH nil` and `insideV nil` are present
    - top/bottom single borders with size `8` are present
  - Refreshed workspace-local workflow assets after the bundle signature changed:
    - `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 170
- Action: Fixed DOCX heading color export so generated titles and heading-linked character styles are forced to black instead of inheriting Word's blue theme color.
- Purpose: Resolve the formatting issue where generated chapter titles and heading text appeared blue rather than the required black.
- Result:
  - Updated:
    - `workflow_bundle/tools/core/build_final_thesis_docx.py`
  - Implementation changes:
    - added low-level helpers to force `w:color w:val="000000"` and strip `w:themeColor`, `w:themeTint`, and `w:themeShade` from run/style properties
    - applied the black-color helper to:
      - `Normal`
      - `Heading 1` to `Heading 4`
      - linked heading character styles corresponding to `Heading1Char` to `Heading4Char`
      - title runs created by `_add_title(...)`
      - superscript citation runs created by `_add_superscript_text(...)`
      - caption and TOC styles configured by the exporter
    - refined linked-style lookup to avoid the deprecated `style_id` access warning during build
  - Synced bundle core back to root compatibility mirror:
    - `bash workflow_bundle/workflow/scripts/sync_root_compat.sh`
  - Validation passed:
    - `python3 -m py_compile workflow_bundle/tools/core/build_final_thesis_docx.py`
    - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `python3 workflow_bundle/tools/cli.py release-build --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - XML-level verification on regenerated `workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`:
    - `Heading1`, `Heading2`, `Heading3`, and `Heading4` each resolve to `w:color w:val="000000"`
    - `Heading1Char`, `Heading2Char`, `Heading3Char`, and `Heading4Char` each resolve to `w:color w:val="000000"`
    - the heading style color nodes no longer carry theme-color attributes
  - Refreshed workspace-local workflow assets after the bundle signature changed:
    - `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 171
- Action: Tightened the Chapter 5 implementation-writing workflow to require explicit backend/frontend paragraphs in every subfunction, and rewrote the Teatrace Chapter 5 polished text to match the original sample style.
- Purpose: Resolve the remaining Chapter 5 style gap where module subfunctions were still written as mixed implementation prose instead of the expected “后端实现。/前端实现。” pattern used by the original optimized workflow.
- Result:
  - Updated workflow rules:
    - `workflow_bundle/tools/core/chapter_profile.py`
    - `workflow_bundle/tools/core/writing.py`
  - Updated live workspace chapter:
    - `workspaces/teatrace_thesis/polished_v3/05-系统实现.md`
  - Workflow changes:
    - added explicit Chapter 5 module policy fields requiring backend/frontend implementation paragraphs inside each subfunction
    - updated Chapter 5 packet prompt lines so every subfunction must use:
      - `后端实现。`
      - `前端实现。`
      in that fixed order
    - refined the Chinese chapter-writing rules so backend paragraphs focus on interfaces, services, database persistence, and chain interaction, while frontend paragraphs focus on page entry, form/list interaction, state feedback, and route flow
  - Chapter 5正文 changes:
    - rewrote all Teatrace Chapter 5 subfunction sections from `5.2.1` through `5.6.3`
    - each subfunction now explicitly contains both `后端实现。` and `前端实现。` paragraphs
    - retained the module-level white-background code screenshot subsections
  - Validation passed:
    - `python3 -m py_compile workflow_bundle/tools/core/chapter_profile.py workflow_bundle/tools/core/writing.py`
    - `bash workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `bash workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `python3 workflow_bundle/tools/cli.py sync-workflow-assets --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py prepare-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
    - `python3 workflow_bundle/tools/cli.py start-chapter --config workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
    - `python3 workflow_bundle/tools/cli.py release-build --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 workflow_bundle/tools/cli.py release-verify --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Packet and chapter verification:
    - refreshed `chapter_briefs/05-系统实现.md` now explicitly states every subfunction must contain `后端实现。` and `前端实现。`
    - refreshed `chapter_packets/05-系统实现.md` now explicitly states both backend and frontend paragraphs are mandatory in every Chapter 5 subfunction subsection
    - `workspaces/teatrace_thesis/polished_v3/05-系统实现.md` now contains explicit backend/frontend paragraph pairs for every subfunction section
  - State-machine note:
    - attempted `finalize-chapter --status polished` after packet refresh
    - workflow correctly rejected the invalid transition `reviewed -> polished` for Chapter 5, so no queue status was mutated by hand
  - Runtime status after verification:
    - `python3 workflow_bundle/tools/cli.py resume --config workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - workspace phase returned to `linux-release-ready`

### Step 172
- Action: Reworked the code screenshot renderer to use Chinese-capable fonts and larger image metrics, then regenerated the Teatrace code evidence pack and DOCX deliverable.
- Purpose: Fix the Chapter 5 code screenshots that were blurry in Word and rendered Chinese strings as garbled glyphs or empty boxes.
- Result:
  - Updated renderer:
    - `workflow_bundle/tools/core/code_evidence.py`
  - Workflow changes:
    - added ordered font candidates for code screenshots, prioritizing Chinese-capable fonts such as `WenQuanYi Zen Hei Mono`, `WenQuanYi Zen Hei`, `Noto Sans Mono CJK SC`, and `Noto Sans CJK SC`
    - added file-based fallback font paths for Linux environments where family names may differ
    - increased screenshot render density by raising default `font_size`, `image_pad`, and `line_pad`
  - Regenerated artifacts:
    - `workspaces/teatrace_thesis/docs/materials/code_evidence_pack.json`
    - `workspaces/teatrace_thesis/docs/materials/code_evidence_pack.md`
    - `workspaces/teatrace_thesis/docs/materials/code_screenshots/01-identity-frontend-07-submit.png`
    - `workspaces/teatrace_thesis/docs/materials/code_screenshots/01-identity-backend-01-register.png`
    - `workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`
  - Visual verification:
    - `01-identity-frontend-07-submit.png` regenerated as `1043x783`
    - `01-identity-backend-01-register.png` regenerated as `2225x888`
    - Chinese literals such as “通过审核时请填写联盟链组织标识” and “机构已通过审核” render normally in the regenerated frontend screenshot
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/code_evidence.py`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py extract-code --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - Release state:
    - Linux delivery artifact rebuilt successfully
    - citation verification summary remained clean with `anchors missing bookmarks: 0`

### Step 173
- Action: Fixed the code screenshot font-selection strategy to explicitly prefer a deterministic Chinese-capable monospace font, and added an environment-variable override for future custom fonts.
- Purpose: Remove ambiguity in screenshot rendering so the workflow does not depend on whichever font library happens to load first, and allow later replacement with a preferred thesis code font without patching the renderer again.
- Result:
  - Updated renderer:
    - `workflow_bundle/tools/core/code_evidence.py`
  - Workflow changes:
    - added `THESIS_CODE_SCREENSHOT_FONT` override support so a downloaded custom font path can be injected without code edits
    - changed the primary Linux font preference to the installed `WenQuanYi Zen Hei Mono` font file at `/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc`
    - kept secondary fallback candidates including `Sarasa Mono SC`, `Sarasa Mono Slab SC`, `Noto Sans Mono CJK SC`, and `Noto Sans CJK SC`
    - recorded the actually used screenshot font into `code_evidence_pack` metadata for later diagnosis
  - Regenerated artifacts:
    - `workspaces/teatrace_thesis/docs/materials/code_evidence_pack.json`
    - `workspaces/teatrace_thesis/docs/materials/code_evidence_pack.md`
    - `workspaces/teatrace_thesis/docs/materials/code_screenshots/01-identity-frontend-07-submit.png`
    - `workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`
  - Verification:
    - `code_evidence_pack.json` now records `code_screenshot_font` as `/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc`
    - regenerated frontend screenshot remains clear at `1043x783` and Chinese literals render normally
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/code_evidence.py`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py extract-code --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 174
- Action: Fixed the DOCX code-block renderer to use the same Chinese-capable font strategy as the extracted code screenshot renderer, then rebuilt the Teatrace Word deliverable.
- Purpose: Resolve the remaining Chinese garbling in Word where fenced Markdown code blocks were being rendered through a separate image path that still fell back to `ImageFont.load_default()` on Linux.
- Result:
  - Updated renderer:
    - `workflow_bundle/tools/core/build_final_thesis_docx.py`
  - Workflow changes:
    - added Linux-first code-block font candidates including `/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc`, `NotoSansMono-Regular.ttf`, and `NotoMono-Regular.ttf`
    - preserved Windows font candidates as fallback for Windows packaging
    - added `THESIS_CODE_SCREENSHOT_FONT` support to the DOCX code-block renderer so both screenshot paths can be overridden consistently
  - Verified outputs:
    - regenerated `word_output/processed_images/codeblock_05-系统实现_11.png` now renders the UsersPage Vue code block with correct Chinese text such as “按账号/姓名/机构关键词筛选”“角色筛选”“调角色”“绑链身份”
    - confirmed the regenerated code-block image is embedded into the rebuilt DOCX as `word/media/image20.png`
    - rebuilt deliverable: `workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/build_final_thesis_docx.py`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 175
- Action: Standardized code rendering style toward the thesis code-block layout rule, then regenerated both extracted code screenshots and the DOCX deliverable.
- Purpose: Align code presentation with the requested paper style by keeping code images on a white background with black text, adding a thin black border, tightening line spacing, and preferring a `Consolas`-like monospace font where available.
- Result:
  - Updated renderers:
    - `workflow_bundle/tools/core/build_final_thesis_docx.py`
    - `workflow_bundle/tools/core/code_evidence.py`
  - Workflow changes:
    - added `Consolas` Windows font paths to the priority list while keeping Linux Chinese-capable fallbacks
    - set DOCX code-block rendering to a smaller monospace size closer to 10pt visual output
    - reduced inter-line leading to a near single-line style
    - added a 1px black border around both Markdown code-block images and extracted code screenshot images
    - kept the background as pure white and the text as black as requested
    - added a small left-indent for DOCX code-block paragraphs to keep them left-aligned but visually separated from body text
  - Environment note:
    - current Linux host does not provide a native `Consolas` font, so rendering falls back to locally available Chinese-capable monospace fonts; if a real `Consolas` file is later installed or passed through `THESIS_CODE_SCREENSHOT_FONT`, the workflow will switch to it automatically
  - Verified outputs:
    - regenerated screenshot `workspaces/teatrace_thesis/docs/materials/code_screenshots/01-identity-frontend-06-userspage-template.png` now uses white background, black text, and a thin black border
    - regenerated DOCX code-block image `workspaces/teatrace_thesis/word_output/processed_images/codeblock_05-系统实现_11.png` now uses the same white-background black-text bordered style
    - rebuilt deliverable: `workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/build_final_thesis_docx.py /home/ub/thesis_materials/workflow_bundle/tools/core/code_evidence.py`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py extract-code --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 176
- Action: Bundled an official open-source monospace Chinese font into the workflow project and switched both code renderers to prefer the project-local font over system fonts.
- Purpose: Remove host-font dependency so code screenshots and DOCX code blocks render consistently across fresh environments and new AI sessions.
- Result:
  - Added bundled font assets:
    - `workflow_bundle/assets/fonts/sarasa-mono-sc/SarasaMonoSC-Regular.ttf`
    - `workflow_bundle/assets/fonts/sarasa-mono-sc/SarasaMonoSC-Bold.ttf`
    - `workflow_bundle/assets/fonts/sarasa-mono-sc/LICENSE`
    - `workflow_bundle/assets/fonts/README.md`
  - Font source:
    - official release: `https://github.com/be5invis/Sarasa-Gothic/releases/tag/v1.0.37`
    - package used: `SarasaMono-TTF-1.0.37.zip`
    - extracted only the SC regular and bold files needed by the workflow
  - Updated renderers:
    - `workflow_bundle/tools/core/code_evidence.py`
    - `workflow_bundle/tools/core/build_final_thesis_docx.py`
  - Workflow changes:
    - added project-local font discovery so renderers first search `assets/fonts/sarasa-mono-sc/SarasaMonoSC-Regular.ttf`
    - preserved system-font fallback only as a secondary safety net
    - documented the vendored font package and usage rules in `assets/fonts/README.md`
  - Verification:
    - `code_evidence_pack.json` now records `code_screenshot_font` as `/home/ub/thesis_materials/workflow_bundle/assets/fonts/sarasa-mono-sc/SarasaMonoSC-Regular.ttf`
    - regenerated screenshot `docs/materials/code_screenshots/01-identity-frontend-06-userspage-template.png` renders with the bundled font
    - regenerated DOCX code-block image `word_output/processed_images/codeblock_05-系统实现_11.png` renders with the bundled font and is embedded into the rebuilt DOCX
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/code_evidence.py /home/ub/thesis_materials/workflow_bundle/tools/core/build_final_thesis_docx.py`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py extract-code --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 177
- Action: Tried the user-provided SiYuan HeiTi font package and switched the workflow font preference to the bundled `SourceHanSansSC-Regular-2.otf`.
- Purpose: Compare a user-specified Chinese font against the bundled Sarasa font and verify whether it produces a cleaner visual result for the thesis code images.
- Result:
  - Added bundled font asset:
    - `workflow_bundle/assets/fonts/siyuan-heiti/SourceHanSansSC-Regular-2.otf`
  - Updated docs:
    - `workflow_bundle/assets/fonts/README.md`
  - Updated renderers:
    - `workflow_bundle/tools/core/code_evidence.py`
    - `workflow_bundle/tools/core/build_final_thesis_docx.py`
  - Workflow changes:
    - changed bundled-font preference order so renderers now try `siyuan-heiti/SourceHanSansSC-Regular-2.otf` before `sarasa-mono-sc/SarasaMonoSC-Regular.ttf`
  - Verification:
    - `code_evidence_pack.json` now records `code_screenshot_font` as `/home/ub/thesis_materials/workflow_bundle/assets/fonts/siyuan-heiti/SourceHanSansSC-Regular-2.otf`
    - regenerated `docs/materials/code_screenshots/01-identity-frontend-06-userspage-template.png` uses the new bundled font
    - regenerated `word_output/processed_images/codeblock_05-系统实现_11.png` uses the new bundled font and is embedded in the rebuilt DOCX
    - rebuilt deliverable: `workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/code_evidence.py /home/ub/thesis_materials/workflow_bundle/tools/core/build_final_thesis_docx.py`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py extract-code --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 178
- Action: Finalized SiYuan HeiTi as the default bundled code-rendering font for the workflow.
- Purpose: Lock the preferred code font choice so future workflow runs and new AI sessions consistently use the same font without re-deciding between SiYuan HeiTi and Sarasa Mono SC.
- Result:
  - Documentation updates:
    - `workflow_bundle/assets/fonts/README.md` now states that `siyuan-heiti/SourceHanSansSC-Regular-2.otf` is the current default code-rendering font
    - `Sarasa Mono SC` is kept as the secondary bundled fallback
  - Effective runtime state:
    - code screenshots default to `SourceHanSansSC-Regular-2.otf`
    - DOCX code-block images default to `SourceHanSansSC-Regular-2.otf`
    - rebuilt Linux delivery artifact remains current at `workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`

### Step 179
- Action: Replaced the `Pygments ImageFormatter` screenshot path with the same shared PIL-based code renderer used by DOCX code blocks.
- Purpose: Eliminate the last divergent rendering path after continued reports of garbled code screenshots even when fonts had already been switched, so all code images are now generated by one deterministic renderer.
- Result:
  - Added shared renderer:
    - `workflow_bundle/tools/core/code_image_renderer.py`
  - Updated renderers:
    - `workflow_bundle/tools/core/code_evidence.py`
    - `workflow_bundle/tools/core/build_final_thesis_docx.py`
  - Workflow changes:
    - removed code-evidence dependence on `Pygments ImageFormatter` for image generation
    - unified code screenshot rendering and DOCX fenced-code rendering onto the same PIL drawing implementation
    - both renderers now share the same bundled-font resolution path and the same white-background black-text bordered output style
  - Verification:
    - `code_evidence_pack.json` still records the bundled `SourceHanSansSC-Regular-2.otf` path as the effective code font
    - regenerated screenshot `docs/materials/code_screenshots/01-identity-frontend-06-userspage-template.png` and DOCX code-block image `word_output/processed_images/codeblock_05-系统实现_11.png` now come from the same renderer
    - rebuilt deliverable remains `workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/code_image_renderer.py /home/ub/thesis_materials/workflow_bundle/tools/core/code_evidence.py /home/ub/thesis_materials/workflow_bundle/tools/core/build_final_thesis_docx.py`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py extract-code --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 180
- Action: Fixed the remaining code-image square-box artifacts by normalizing tab indentation before drawing, synced workflow assets into the workspace, and rebuilt a fresh DOCX deliverable with a new filename.
- Purpose: Resolve the last user-reported "乱码" issue in Word after font replacement had already been completed, and verify that the regenerated DOCX actually embeds the updated code images instead of a stale cached artifact.
- Result:
  - Root cause confirmed:
    - the remaining artifacts were not Chinese glyph corruption
    - the visible square boxes came from literal `tab` indentation characters in code snippets being rendered directly into the image
  - Updated renderer:
    - `workflow_bundle/tools/core/code_image_renderer.py`
  - Workflow changes:
    - normalized every rendered code line with `line.expandtabs(4).replace("\\r", "")` before measuring and drawing
    - kept the shared white-background black-text bordered renderer for both `extract-code` evidence screenshots and DOCX fenced-code blocks
    - synced workspace workflow assets so the workspace signature returned to `current`
  - Verification:
    - regenerated evidence screenshot `workspaces/teatrace_thesis/docs/materials/code_screenshots/01-identity-backend-03-updateuserrole.png` no longer shows square-box indentation
    - regenerated processed DOCX code image `workspaces/teatrace_thesis/word_output/processed_images/codeblock_05-系统实现_11.png` is clean
    - hash check confirmed `codeblock_05-系统实现_11.png` is embedded into `workspaces/teatrace_thesis/word_output/hyperledger-fabric_siyuan_v3.docx` as `word/media/image20.png`
    - rebuilt deliverable: `workspaces/teatrace_thesis/word_output/hyperledger-fabric_siyuan_v3.docx`
  - Validation passed:
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py sync-workflow-assets --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v3.docx`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v3.docx`

### Step 181
- Action: Unified the visible code font size in the generated DOCX by changing both code-line wrapping and Word image insertion scale.
- Purpose: Fix the new issue where some code blocks looked larger and others smaller even though the renderer was using the same font size, which made the thesis implementation chapter look inconsistent.
- Result:
  - Root cause confirmed:
    - all code screenshots were rendered with the same pixel font size
    - but the DOCX builder inserted every code image at a fixed width of `6.0` inches
    - narrow images were enlarged while wide images were compressed, so the apparent font size became inconsistent in Word
  - Updated renderers:
    - `workflow_bundle/tools/core/code_image_renderer.py`
    - `workflow_bundle/tools/core/build_final_thesis_docx.py`
  - Workflow changes:
    - added maximum-width line wrapping in the shared code image renderer so extra-long lines are split before the image becomes excessively wide
    - replaced the fixed-width DOCX insertion rule with a fixed physical scale rule using `CODE_RENDER_MM_PER_PX = 0.25`
    - constrained DOCX code blocks to `CODE_RENDER_MAX_DISPLAY_WIDTH_MM = 155.0`, so code images keep a stable physical text size while still fitting the page
  - Verification:
    - regenerated chapter-5 code images now fall into a narrow width band such as `608x790`, `610x807`, `619x960`, instead of the previous `463x178` to `1295x705` spread
    - rebuilt deliverable: `workspaces/teatrace_thesis/word_output/hyperledger-fabric_siyuan_v4.docx`
    - workspace runtime returned to `workflow_signature_status: current`
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/code_image_renderer.py /home/ub/thesis_materials/workflow_bundle/tools/core/build_final_thesis_docx.py /home/ub/thesis_materials/workflow_bundle/tools/core/code_evidence.py`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v4.docx`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py sync-workflow-assets --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v4.docx`

### Step 182
- Action: Standardized the code-block frame width in the DOCX so the code boxes themselves are visually aligned, not only the text size inside them.
- Purpose: Complete the code-style normalization after the user confirmed the next refinement should also make the code frames look consistent across chapter 5.
- Result:
  - Updated renderers:
    - `workflow_bundle/tools/core/code_image_renderer.py`
    - `workflow_bundle/tools/core/build_final_thesis_docx.py`
  - Workflow changes:
    - added `fixed_canvas_width_px` support to the shared code image renderer
    - enabled a fixed canvas width for DOCX code blocks only, while leaving evidence screenshots flexible
    - the chapter-5 DOCX code images now all render at a uniform width of `620px`
  - Verification:
    - rebuilt deliverable: `workspaces/teatrace_thesis/word_output/hyperledger-fabric_siyuan_v5.docx`
    - regenerated code images show a uniform width set:
      - `620x1096`, `620x790`, `620x475`, `620x178`, `620x807`
    - workspace runtime remains `workflow_signature_status: current`
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/code_image_renderer.py /home/ub/thesis_materials/workflow_bundle/tools/core/build_final_thesis_docx.py`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v5.docx`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py sync-workflow-assets --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v5.docx`

### Step 183
- Action: Aligned the remaining chapter-5 implementation subsections to the established “后端实现 / 关键代码 / 前端实现 / 关键代码” writing rhythm and tightened several code excerpts.
- Purpose: Keep the implementation chapter consistent with the reference thesis style after the user pointed out that later subsections had drifted back toward prose-only description or under-specified code evidence.
- Result:
  - Updated thesis chapter:
    - `workspaces/teatrace_thesis/polished_v3/05-系统实现.md`
  - Chapter refinements:
    - added a concrete Vue template snippet to `5.5.2` so the trace-code management subsection now shows both page structure and action logic
    - expanded the `5.5.3` backend excerpt so the public trace-query logic includes query-count updates, anomaly-threshold handling, staged-record aggregation, and the returned result payload
    - added a concrete transaction-audit page template snippet to `5.6.3` and kept the dashboard parallel-loading code as the second frontend evidence block
  - Verification:
    - structural review confirms every functional subsection from `5.2.1` through `5.6.3` contains both `后端实现。` and `前端实现。`
    - chapter-5 functional subsections now consistently retain embedded code blocks instead of reverting to prose-only descriptions
  - Validation passed:
    - `python3 - <<'PY' ...` structural check over `workspaces/teatrace_thesis/polished_v3/05-系统实现.md` for subsection markers and code-block counts

### Step 184
- Action: Regenerated the Linux delivery DOCX after the latest chapter-5 alignment and reran release verification.
- Purpose: Produce a fresh thesis deliverable that includes the updated implementation-section wording and embedded code blocks, without overwriting the previous archived release.
- Result:
  - Generated deliverable:
    - `workspaces/teatrace_thesis/word_output/hyperledger-fabric_siyuan_v6.docx`
  - Generated summaries:
    - `workspaces/teatrace_thesis/word_output/build_runs/build_summary_20260402T010103_0800.json`
    - `workspaces/teatrace_thesis/word_output/release_runs/release_summary_20260402T010120_0800.json`
  - Verification:
    - release verification reported `anchors missing bookmarks: 0`
    - reference fields and bookmarks remained aligned at `8`
    - workspace runtime remained `workflow_signature_status: current`
  - Validation passed:
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py resume --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-preflight --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v6.docx`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v6.docx`

### Step 185
- Action: Removed the remaining standalone “关键代码截图” subsections from Chapter 5 and locked the workflow contract so Chapter 5 code screenshots must be embedded inside the matching subfunction instead of being emitted as separate subsection nodes.
- Purpose: Fix the remaining mismatch between the Teatrace implementation chapter and the intended thesis style after the user clarified that code screenshots belong inside backend/frontend implementation flows, not as standalone `5.x.4` subsections.
- Result:
  - Updated thesis chapter:
    - `workspaces/teatrace_thesis/polished_v3/05-系统实现.md`
  - Updated workflow core:
    - `workflow_bundle/tools/core/chapter_profile.py`
    - `workflow_bundle/tools/core/writing.py`
    - `tools/core/chapter_profile.py`
    - `tools/core/writing.py`
  - Updated workflow docs:
    - `workflow/CHAPTER_EXECUTION.md`
    - `workflow_bundle/workflow/CHAPTER_EXECUTION.md`
    - `workflow/06-ai-prompt-guide.md`
    - `workflow_bundle/workflow/06-ai-prompt-guide.md`
  - Workflow changes:
    - removed residual chapter-profile support for generating a standalone `关键代码截图` subsection in Chapter 5 outlines
    - strengthened the Chapter 5 writing prompt so any code screenshot must appear immediately after the matching backend/frontend code block inside the same subfunction
    - moved the existing code screenshots in the Teatrace chapter into `5.3.2/5.3.3/5.4.1/5.5.1/5.6.1/5.6.2` and removed the old `5.3.4/5.4.4/5.5.4/5.6.4` blocks
  - Verification:
    - no `### 5.[3-6].4` standalone screenshot subsection remains in `workspaces/teatrace_thesis/polished_v3/05-系统实现.md`
    - Chapter 5 code screenshots are now present only as inline figure inserts inside functional subsections
  - Validation passed:
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/chapter_profile.py /home/ub/thesis_materials/workflow_bundle/tools/core/writing.py /home/ub/thesis_materials/tools/core/chapter_profile.py /home/ub/thesis_materials/tools/core/writing.py`
    - `rg -n "^### 5\\.[3-6]\\.4" /home/ub/thesis_materials/workspaces/teatrace_thesis/polished_v3/05-系统实现.md`

### Step 186
- Action: Regenerated the Linux delivery DOCX after removing the standalone Chapter 5 screenshot subsections and verified the new release artifact.
- Purpose: Ensure the exported Word document reflects the new inline screenshot layout rather than the previously separate Chapter 5 screenshot blocks.
- Result:
  - Generated deliverable:
    - `workspaces/teatrace_thesis/word_output/hyperledger-fabric_siyuan_v7.docx`
  - Generated summaries:
    - `workspaces/teatrace_thesis/word_output/build_runs/build_summary_20260402T011220_0800.json`
    - `workspaces/teatrace_thesis/word_output/release_runs/release_summary_20260402T011243_0800.json`
  - Workflow runtime:
    - `sync-workflow-assets` refreshed the workspace signature from `drifted` back to `current`
  - Verification:
    - release verification reported `anchors missing bookmarks: 0`
    - reference fields and bookmarks remained aligned at `8`
  - Validation passed:
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py sync-workflow-assets --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py resume --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v7.docx`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v7.docx`

### Step 187
- Action: Removed the extra Chapter 5 `5.1 实现总体说明` node from the Teatrace workspace and from the workflow generation rules, then refreshed the chapter writing artifacts.
- Purpose: Restore Chapter 5 to the original reference structure after the user correctly pointed out that the source reference chapter does not use a standalone `5.1` implementation-overview subsection.
- Result:
  - Updated thesis chapter:
    - `workspaces/teatrace_thesis/polished_v3/05-系统实现.md`
  - Updated workflow core:
    - `workflow_bundle/tools/core/chapter_profile.py`
    - `workflow_bundle/tools/core/extract.py`
    - `workflow_bundle/tools/core/writing.py`
    - `tools/core/chapter_profile.py`
    - `tools/core/extract.py`
    - `tools/core/writing.py`
  - Updated workspace writing artifacts:
    - `workspaces/teatrace_thesis/docs/writing/project_profile.json`
    - `workspaces/teatrace_thesis/docs/writing/project_profile.md`
    - `workspaces/teatrace_thesis/docs/writing/thesis_outline.json`
    - `workspaces/teatrace_thesis/docs/writing/thesis_outline.md`
    - `workspaces/teatrace_thesis/docs/writing/chapter_packets/05-系统实现.json`
    - `workspaces/teatrace_thesis/docs/writing/chapter_packets/05-系统实现.md`
    - `workspaces/teatrace_thesis/docs/writing/chapter_briefs/05-系统实现.md`
  - Workflow changes:
    - removed the generated `5.1 实现总体说明` section node from the Chapter 5 outline tree
    - remapped figure 5.1 and related chapter-opening assets from the deleted `5.1` subsection to the chapter-level opening of `5 系统实现`
    - added a project-profile refresh condition so old workspaces containing `5.1 实现总体说明` are rebuilt automatically
  - Verification:
    - `workspaces/teatrace_thesis/polished_v3/05-系统实现.md` now goes directly from the chapter-opening paragraphs to `## 5.2 用户与权限管理模块实现`
    - `chapter_briefs/05-系统实现.md`, `thesis_outline.md`, and `chapter_packets/05-系统实现.md` no longer contain `5.1 实现总体说明`
  - Validation passed:
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py extract --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-outline --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-writing --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-chapter --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`

### Step 188
- Action: Regenerated the Linux delivery DOCX after removing the extra Chapter 5 `5.1` subsection and verified the new release artifact.
- Purpose: Ensure the exported document matches the restored original-style Chapter 5 structure instead of the workflow-added variant.
- Result:
  - Generated deliverable:
    - `workspaces/teatrace_thesis/word_output/hyperledger-fabric_siyuan_v8.docx`
  - Generated summaries:
    - `workspaces/teatrace_thesis/word_output/build_runs/build_summary_20260402T012614_0800.json`
    - `workspaces/teatrace_thesis/word_output/release_runs/release_summary_20260402T012630_0800.json`
  - Verification:
    - release verification reported `anchors missing bookmarks: 0`
    - reference fields and bookmarks remained aligned at `8`
    - workspace runtime remained `workflow_signature_status: current`
  - Validation passed:
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py sync-workflow-assets --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py resume --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v8.docx`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v8.docx`

### Step 189
- Action: Updated the Chapter 5 screenshot-writing rules and DOCX exporter so code screenshots remain inline but no longer generate numbered figure captions, then refreshed the Chapter 5 packet.
- Purpose: Align the workflow with the original sample style after confirming that Chapter 5 code screenshots should be retained as implementation evidence but must not appear as `图5.x` captioned figures.
- Result:
  - Updated workflow core:
    - `workflow_bundle/tools/core/build_final_thesis_docx.py`
    - `workflow_bundle/tools/core/writing.py`
    - `tools/core/build_final_thesis_docx.py`
    - `tools/core/writing.py`
  - Updated thesis chapter:
    - `workspaces/teatrace_thesis/polished_v3/05-系统实现.md`
  - Updated workspace writing artifacts:
    - `workspaces/teatrace_thesis/docs/writing/chapter_packets/05-系统实现.json`
    - `workspaces/teatrace_thesis/docs/writing/chapter_packets/05-系统实现.md`
    - `workspaces/teatrace_thesis/docs/writing/chapter_briefs/05-系统实现.md`
  - Workflow changes:
    - markdown images under `docs/materials/code_screenshots` are now treated as inline code-evidence images without figure-caption paragraphs in DOCX
    - Chapter 5 prompt rules now explicitly require code screenshots to stay unnumbered and captionless
    - Teatrace Chapter 5正文 no longer uses wording such as `如图5.5所示` for code screenshots
  - Verification:
    - `chapter_packets/05-系统实现.md` now contains the rule `do not assign figure numbers, 图5.x captions, or separate caption paragraphs to them`
    - `chapter_briefs/05-系统实现.md` now contains the rule `代码截图仅作为实现证据插图使用，不编号，不写“图5.x”题注`
    - `workspaces/teatrace_thesis/polished_v3/05-系统实现.md` retains the inline screenshots but removes the old `图5.5` to `图5.12` references
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/build_final_thesis_docx.py /home/ub/thesis_materials/workflow_bundle/tools/core/writing.py`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-chapter --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py sync-workflow-assets --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 190
- Action: Regenerated and verified the Linux delivery DOCX after the code-screenshot caption fix, then directly inspected the generated DOCX XML.
- Purpose: Confirm that the Chapter 5 code screenshots are still present in the document but no longer emit any visible caption paragraphs such as `图5.5` to `图5.12`.
- Result:
  - Generated deliverable:
    - `workspaces/teatrace_thesis/word_output/hyperledger-fabric_siyuan_v9.docx`
  - Generated summaries:
    - `workspaces/teatrace_thesis/word_output/build_runs/build_summary_20260402T013440_0800.json`
    - `workspaces/teatrace_thesis/word_output/release_runs/release_summary_20260402T013458_0800.json`
  - Verification:
    - release verification reported `anchors missing bookmarks: 0`
    - reference fields and bookmarks remained aligned at `8`
    - direct `document.xml` inspection confirmed that:
      - `图5.5 批次创建关键代码截图`
      - `图5.6 批次管理页面关键代码截图`
      - `图5.7 农事记录创建关键代码截图`
      - `图5.8 农事记录页面关键代码截图`
      - `图5.9 溯源码绑定关键代码截图`
      - `图5.10 二维码展示关键代码截图`
      - `图5.11 预警页面关键代码截图`
      - `图5.12 批次解冻关键代码截图`
      no longer exist in the generated Word body
    - direct `document.xml` inspection also confirmed that `关键代码截图` does not remain as any standalone caption paragraph text
    - normal numbered figures such as `图5.1 系统功能结构图` remain intact
  - Validation passed:
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v9.docx`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v9.docx`

### Step 191
- Action: Finished the workflow-maintenance round by adding a bundled `selftest` regression entrypoint, fixing the workflow-signature false-drift bug, syncing the Teatrace workspace assets again, and rerunning the full Linux regression path.
- Purpose: Ensure later AI conversations can verify the workflow itself rather than only reusing the current Teatrace outputs, and make `sync-workflow-assets` / `workflow_signature_status` consistent after bundle-side maintenance changes.
- Result:
  - Workflow bundle changes:
    - added regression entrypoints `workflow_bundle/tools/core/selftest.py` and `workflow_bundle/workflow/scripts/selftest.sh`
    - documented the regression path in workflow docs, command map, AI prompt guide, execution checklist, and skills
    - added lightweight literature regression support so fixture selftests can run with `--min-refs 1 --max-refs 1 --skip-research-sidecar`
    - fixed `tools/core/runtime_state.py` so `bundle_signature` is now computed from the exact managed workflow assets that are synced into each workspace: rendered `workflow/README.md`, managed workflow docs, and managed workflow skills
    - this removes the previous false-positive case where changing bundle `tools/` code made the workspace look drifted immediately even after a fresh `sync-workflow-assets`
  - Teatrace workspace verification:
    - refreshed workspace assets and recorded the new signature `c0817716505e`
    - full regression passed with summary `/tmp/workflow_bundle_selftest_lo2rk52k/selftest_summary.json`
    - generated regression DOCX `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/selftest_release.docx`
    - release verification stayed clean with `anchors missing bookmarks: 0`, `ref fields: 8`, and `bookmarks: 8`
    - Chapter 5 inline code-screenshot captions remained removed in the exported DOCX while normal numbered figure captions were still preserved
    - workspace lock ended as `unlocked`
    - reset the default active workspace pointer back to `/home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json` so new conversations resume from the real project instead of an old temporary fixture workspace
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/cli.py /home/ub/thesis_materials/workflow_bundle/tools/core/selftest.py /home/ub/thesis_materials/workflow_bundle/tools/core/runtime_state.py /home/ub/thesis_materials/workflow_bundle/tools/core/writing.py`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py sync-workflow-assets --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py selftest --workspace-config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py set-active-workspace --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 192
- Action: Reworked Chapter 5 code-image rendering so DOCX-exported code blocks use tighter single-line spacing, prefer the bundled Sarasa Mono SC font, auto-split overlong code blocks into multiple images, and clean stale generated code screenshots before rebuilding the evidence pack.
- Purpose: Fix the issue where code images in the exported thesis were not visually single-spaced and some long code images overflowed the Word page height so the lower part could not be seen.
- Result:
  - Renderer changes:
    - `tools/core/code_image_renderer.py` now exposes reusable layout helpers so code lines can be wrapped once and then split into multiple image chunks without changing font metrics mid-render
    - `tools/core/build_final_thesis_docx.py` now renders Markdown fenced code blocks at `13px` with `line_pad=0`, reduces the display width to `148mm`, caps display height to `135mm`, and emits `_partN` chunk images when a code block would otherwise exceed the page-safe height
    - `tools/core/code_evidence.py` now prefers bundled `SarasaMonoSC-Regular.ttf` before Source Han Sans, renders generated code screenshots with the same tighter single-line spacing profile, constrains screenshot width to the same fixed canvas width, and clears old `code_snippets/` and `code_screenshots/` outputs before regeneration
    - `tools/core/selftest.py` now asserts exported DOCX image extents stay within page-safe bounds, so future regressions will fail automatically if code images grow back to oversized dimensions
  - Teatrace workspace verification:
    - regenerated code evidence pack now records `SarasaMonoSC-Regular.ttf` as the selected screenshot font
    - regenerated referenced code screenshots were normalized from mixed historical sizes to a clean bounded set; after cleanup the `docs/materials/code_screenshots/` directory contains `78` current screenshots with `max_width=592px` and `max_height=684px`
    - rebuilt Linux deliverable `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/hyperledger-fabric_siyuan_v10.docx`
    - rebuilt release summaries:
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/build_runs/build_summary_20260402T133746_0800.json`
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/release_runs/release_summary_20260402T133825_0800.json`
    - processed code-block images now split automatically, for example `codeblock_05-系统实现_17_part1.png`, `codeblock_05-系统实现_17_part2.png`, and `codeblock_05-系统实现_17_part3.png`
    - exported DOCX image extents dropped from the previous oversized maximum `36.75cm` height to `15.0cm` max height and `15.0cm` max width
    - full workflow regression passed again with summary `/tmp/workflow_bundle_selftest_989vwdg8/selftest_summary.json`, including:
      - `anchors missing bookmarks: 0`
      - `citation_ref_bookmark_match: 8 vs 8`
      - `docx_max_image_height_cm: 15.0`
      - `docx_max_image_width_cm: 15.0`
      - `code_screenshot_caption_removed: true`
      - `normal_figure_caption_preserved: true`
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/code_image_renderer.py /home/ub/thesis_materials/workflow_bundle/tools/core/code_evidence.py /home/ub/thesis_materials/workflow_bundle/tools/core/build_final_thesis_docx.py /home/ub/thesis_materials/workflow_bundle/tools/core/selftest.py`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/check_bundle_sync.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py extract-code --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v10.docx`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v10.docx`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py selftest --workspace-config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 193
- Action: Reworked the Chapter 5 frontend page-screenshot workflow, staged additional real UI screenshots into the Teatrace workspace, repaired stale screenshot references in the current chapter, and added regression checks so future runs cannot silently drop or break those images.
- Purpose: Fix the gap where many frontend implementation subsections in Chapter 5 only had code evidence but no real page screenshots, and make the improved screenshot coverage reproducible in later AI conversations instead of being a one-off manual edit.
- Result:
  - Workflow bundle changes:
    - `tools/core/chapter_profile.py` now upgrades the traceability-domain Chapter 5 screenshot contract from “2 representative screenshots” to a section-level contract that requires:
      - `5.2.1 注册登录与会话建立实现` -> 1 real page screenshot
      - `5.2.3 用户管理与权限治理实现` -> 2 real page screenshots
      - `5.3.3 批次状态维护与全流程入口实现` -> 1 real page screenshot
      - `5.4.1 生产环节记录录入实现` -> 1 real page screenshot
      - `5.4.2 仓储物流等流转记录实现` -> 2 real page screenshots
      - `5.5.3 公开追溯查询与结果展示实现` -> 1 real page screenshot
    - `tools/core/extract.py` now remaps usable runtime screenshots to the correct subsection targets:
      - `processor-fixed-flow` -> `5.4.1`
      - `inspector-fixed-flow` -> `5.4.2`
      - `logistics-fixed-flow` -> `5.4.2`
      - `farmer-fixed-flow` -> `5.3.3`
      - `public-trace-success` -> `5.5.3`
    - `tools/core/extract.py` also lowers or disables poor default-route screenshots so blank / narrow runtime pages are no longer auto-selected:
      - `admin-dashboard-and-forbidden-business-route`
      - `tea-farmer-default-route-and-menu`
      - `processor-default-route-and-batch-trace`
      - `inspector-default-route-and-batch-trace`
      - `logistics-default-route-and-batch-trace`
    - `tools/core/writing.py` now forces `project_profile.json` to refresh whenever the Chapter 5 screenshot contract changes, and the Chapter 5 brief explicitly states that all selected `test-screenshot` assets must be embedded in the matching frontend subsection.
    - `tools/core/writing.py` now records figure `source_path` values in `asset_to_section_map`, so new conversations can see which real image file each required page screenshot comes from.
    - `tools/core/selftest.py` now asserts:
      - every Markdown image reference in `05-系统实现.md` resolves to an existing file
      - Chapter 5 page-screenshot references under `docs/images/chapter5/` meet the required screenshot count from `project_profile.json`
  - Teatrace workspace changes:
    - staged additional real page screenshots into `workspaces/teatrace_thesis/docs/images/chapter5/`:
      - `fig5-5-batch-management.png`
      - `fig5-6-process-records.png`
      - `fig5-7-inspection-report.png`
      - `fig5-8-logistics-records.png`
      - `fig5-9-public-trace.png`
    - updated `workspaces/teatrace_thesis/polished_v3/05-系统实现.md` so real page screenshots are now embedded in the frontend sections:
      - `5.3.3 批次状态维护与全流程入口实现`
      - `5.4.1 生产环节记录录入实现`
      - `5.4.2 仓储物流等流转记录实现`
      - `5.5.3 公开追溯查询与结果展示实现`
    - repaired stale Chapter 5 code-screenshot references after the regenerated `code_screenshots/` cleanup:
      - `03-record-frontend-01-loaddata.png` -> `03-record-frontend-01-farmrecordspage.png`
      - `04-trace-backend-01-bind.png` -> `04-trace-backend-01-bindtracecode.png`
      - `04-trace-frontend-01-showqrcode.png` -> `04-trace-frontend-02-showqrcode.png`
    - refreshed `project_profile.json`, `chapter_packets/05-系统实现.json`, and `chapter_briefs/05-系统实现.md`; the Chapter 5 packet now selects the expected real screenshots:
      - registration page
      - admin dashboard
      - forbidden page
      - batch management page
      - process records page
      - inspection report page
      - logistics records page
      - public trace result page
    - rebuilt Linux deliverable `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/hyperledger-fabric_siyuan_v11.docx`
    - rebuilt summaries:
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/build_runs/build_summary_20260402T141345_0800.json`
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/release_runs/release_summary_20260402T141413_0800.json`
    - full selftest passed again with summary `/tmp/workflow_bundle_selftest___nbcgey/selftest_summary.json`
    - workspace selftest assertions confirmed:
      - `chapter5_markdown_image_refs_exist: true`
      - `chapter5_page_screenshot_refs: actual=8, expected_min=8`
      - `docx_max_image_height_cm: 15.0`
      - `docx_max_image_width_cm: 15.0`
      - `code_screenshot_caption_removed: true`
      - `normal_figure_caption_preserved: true`
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/chapter_profile.py /home/ub/thesis_materials/workflow_bundle/tools/core/extract.py /home/ub/thesis_materials/workflow_bundle/tools/core/writing.py /home/ub/thesis_materials/workflow_bundle/tools/core/selftest.py`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py extract --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-writing --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-chapter --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v11.docx`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v11.docx`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py selftest --workspace-config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 194
- Action: Moved Chapter 5 runtime screenshot staging into the normal writing workflow by auto-copying selected page screenshots during `prepare-chapter`, exposing their workspace paths in the packet/brief, and keeping `prepare-figures` as a release-time resync fallback.
- Purpose: Ensure a brand-new AI conversation can immediately see and use local Chapter 5 page screenshots while drafting, instead of depending on prior manual copies or only discovering those assets during the final release build.
- Result:
  - Workflow bundle changes:
    - added `tools/core/page_screenshot_assets.py` to centralize Chapter 5 runtime screenshot filename mapping and workspace staging logic
    - `tools/core/writing.py` now:
      - adds `workspace_image_path` to selected Chapter 5 `test-screenshot` assets
      - writes those workspace paths into `asset_to_section_map`
      - renders a new `## 页面截图落点` section in the Chapter 5 writer brief
      - stages the selected runtime screenshots into `docs/images/chapter5/` during `prepare-chapter`
      - records the staging results in packet JSON as `staged_page_screenshots`
    - `tools/core/figure_assets.py` now reuses the same staging helper and writes `staged_chapter5_screenshots` into `figure_prepare_summary.json`, so release-time `prepare-figures` can restore the local screenshot set even if files were deleted after drafting
    - `tools/core/writing.py` packet markdown now shows both the original runtime `source` and the staged local `workspace` path for each Chapter 5 page screenshot, plus a dedicated `Staged Page Screenshots` snapshot with `cached/copied/updated` status
  - Teatrace workspace verification:
    - rerunning `prepare-chapter --chapter 05-系统实现.md` now stages `8` page screenshots automatically and records them in the packet:
      - `docs/images/chapter5/fig5-4-register-login.png`
      - `docs/images/chapter5/fig5-2-admin-dashboard.png`
      - `docs/images/chapter5/fig5-3-forbidden-page.png`
      - `docs/images/chapter5/fig5-5-batch-management.png`
      - `docs/images/chapter5/fig5-6-process-records.png`
      - `docs/images/chapter5/fig5-7-inspection-report.png`
      - `docs/images/chapter5/fig5-8-logistics-records.png`
      - `docs/images/chapter5/fig5-9-public-trace.png`
    - the refreshed Chapter 5 brief now exposes each screenshot’s runtime source and local workspace path directly, so later AI sessions can write against `docs/images/chapter5/...` without re-deriving filenames
    - rerunning `prepare-figures` now persists the same `8` staged screenshots under `word_output/figure_prepare_summary.json`
    - rebuilt Linux deliverable `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/hyperledger-fabric_siyuan_v12.docx`
    - rebuilt summaries:
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/build_runs/build_summary_20260402T143006_0800.json`
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/release_runs/release_summary_20260402T143038_0800.json`
    - full selftest passed again with summary `/tmp/workflow_bundle_selftest_am0fwu7m/selftest_summary.json`
    - workspace selftest assertions remained green:
      - `chapter5_markdown_image_refs_exist: true`
      - `chapter5_page_screenshot_refs: actual=8, expected_min=8`
      - `workspace_lock_released: true`
  - Validation passed:
    - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/page_screenshot_assets.py /home/ub/thesis_materials/workflow_bundle/tools/core/figure_assets.py /home/ub/thesis_materials/workflow_bundle/tools/core/writing.py`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-chapter --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-figures --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v12.docx`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v12.docx`
    - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py selftest --workspace-config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 195
- Action: Refactored Chapter 5 page screenshot staging to resolve workspace filenames primarily from semantic `selection_group` values, then from target Chapter 5 subsection candidates, while retaining a legacy source-stem compatibility fallback for older runtime artifact names.
- Purpose: Reduce the workflow's dependence on the current `Teatrace` runtime screenshot filenames so new projects and fresh AI conversations can reproduce the Chapter 5 image-staging flow from semantic evidence metadata instead of memorizing project-specific stems.
- Result:
  - Workflow bundle changes:
    - `tools/core/page_screenshot_assets.py` now applies this filename resolution priority:
      - `selection_group`
      - Chapter 5 `section_candidates`
      - legacy runtime source-stem compatibility map
      - generic slug fallback
    - the primary Chapter 5 mappings are now driven by semantic groups such as:
      - `identity-registration -> fig5-4-register-login.png`
      - `identity-dashboard -> fig5-2-admin-dashboard.png`
      - `identity-route-guard -> fig5-3-forbidden-page.png`
      - `batch-main-flow -> fig5-5-batch-management.png`
      - `record-process-flow -> fig5-6-process-records.png`
      - `record-inspection-flow -> fig5-7-inspection-report.png`
      - `record-logistics-flow -> fig5-8-logistics-records.png`
      - `trace-success -> fig5-9-public-trace.png`
    - added semantic fallback targets for less common groups and subsection-only matches, including generic Chapter 5 filenames such as `fig5-2-3-user-permission.png`, `fig5-4-3-stage-progress.png`, and `fig5-5-2-trace-code-control.png`
    - staged screenshot summaries now record:
      - `selection_group`
      - Chapter 5-only `section_candidates`
      - `name_source`, so later debugging can see whether the final workspace name came from `selection-group`, `section-candidate`, `legacy-source-stem`, or `slug`
    - `tools/core/writing.py` now exposes `selection_group` in `## 页面截图落点`, and packet markdown now shows both `selection_group` and `name_source` under `### Staged Page Screenshots`
  - Teatrace workspace verification:
    - rerunning `prepare-chapter --chapter 05-系统实现.md` preserved the existing `8` selected Chapter 5 screenshot targets and all `staged_page_screenshots` entries now resolve through `name_source: selection-group`
    - the refreshed brief `/home/ub/thesis_materials/workspaces/teatrace_thesis/docs/writing/chapter_briefs/05-系统实现.md` now exposes each screenshot's source path, workspace path, and semantic `selection_group`, so a fresh AI session can continue drafting directly from the brief without reopening packet JSON first
    - rerunning `prepare-figures` preserved the same `8` staged screenshot paths in `word_output/figure_prepare_summary.json`, also with `name_source: selection-group`
    - regenerated root compatibility mirror with `workflow/scripts/sync_root_compat.sh`, which refreshed `tools/core/page_screenshot_assets.py` under the root compatibility path
    - rebuilt Linux deliverable `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/hyperledger-fabric_siyuan_v13.docx`
    - rebuilt summaries:
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/build_runs/build_summary_20260402T143921_0800.json`
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/release_runs/release_summary_20260402T143951_0800.json`
    - full selftest passed again with summary `/tmp/workflow_bundle_selftest_mc6v6gdu/selftest_summary.json`
    - the updated screenshot staging metadata is now visible in both:
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/docs/writing/chapter_packets/05-系统实现.json`
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/figure_prepare_summary.json`
- Validation passed:
  - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/page_screenshot_assets.py /home/ub/thesis_materials/workflow_bundle/tools/core/figure_assets.py /home/ub/thesis_materials/workflow_bundle/tools/core/writing.py`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-chapter --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --chapter 05-系统实现.md`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-figures --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v13.docx`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v13.docx`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py selftest --workspace-config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 196
- Action: Reworked the generated Chapter 5 function-structure renderer so `图5.1 系统功能结构图` now uses a monochrome thesis-style module tree that matches the user's reference image more closely: top-level system title, horizontal module layer, and vertically listed subfunctions under each module.
- Purpose: Replace the previous blue/gray card-style structure figure with a more conventional academic paper function architecture diagram that reads like a论文功能架构图 instead of a product UI mock graphic.
- Result:
  - Workflow bundle changes:
    - `tools/core/figure_assets.py` now derives the root title with `_root_system_label()` so project titles like `...设计与实现` render as a clean system name in the top box
    - `_render_function_structure_png()` now renders:
      - white background
      - black outline boxes
      - black connector lines and arrow heads
      - centered top-level system box
      - a horizontal branch line from the root to all major modules
      - per-module vertical child branches with left-incoming arrows for subfunctions
    - added `FUNCTION_STRUCTURE_RENDERER_VERSION = "v2-monochrome-module-tree"` and injected it into the figure spec hash, so workflow reruns automatically invalidate the old cached `fig5-1-function-structure.png` instead of silently reusing the earlier colored version
  - Teatrace workspace verification:
    - rerunning `prepare-figures` regenerated only `5.1` and kept other figures cached:
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/docs/images/generated/fig5-1-function-structure.png`
    - the regenerated image shows monochrome dominant colors rather than the old blue theme; a quick pixel summary returned:
      - `(255, 255, 255)` as the dominant background color
      - `(0, 0, 0)` as the dominant outline/text color
    - synced root compatibility mirror with `workflow/scripts/sync_root_compat.sh`
    - rebuilt Linux deliverable:
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/hyperledger-fabric_siyuan_v14.docx`
    - rebuilt summaries:
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/build_runs/build_summary_20260403T112313_0800.json`
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/release_runs/release_summary_20260403T112359_0800.json`
- Validation passed:
  - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/figure_assets.py`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-figures --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-build --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v14.docx`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --output-name hyperledger-fabric_siyuan_v14.docx`

### Step 197
- Action: Added an explicit AI image-generation stage to the thesis workflow so selected thesis figures can be generated through a Zetatechs-compatible OpenAI image endpoint, materialized as local PNG assets, recorded into `figure_map`, and guarded by release-time preflight checks when they override built-in generated figure numbers.
- Purpose: Give the workflow a reproducible way to prepare higher-quality thesis illustration assets from prompts instead of relying only on local diagram renderers, while still keeping release behavior deterministic and preventing silent regressions when AI-generated replacement figures are missing.
- Result:
  - Workflow bundle changes:
    - added `tools/core/ai_image_generation.py`
      - declares workspace-level `image_generation` defaults and `ai_figure_specs` normalization
      - builds thesis-oriented prompts from figure caption, chapter, intent, project title, and chain platform
      - calls `POST /v1/images/generations` against the configured Zetatechs-compatible endpoint
      - writes generated images to `docs/images/generated_ai/`
      - persists prompt metadata to `prompt_manifest.json`
      - updates `workspace.json.figure_map` with `renderer: ai-image` and stable `spec_hash`
    - `tools/cli.py` now exposes `prepare-ai-figures --config <workspace.json> [--fig <图号>] [--force] [--dry-run]`
    - `tools/core/project_common.py` now seeds new workspace configs with `image_generation` and `ai_figure_specs`
    - `tools/core/figure_assets.py` now:
      - blocks `prepare-figures` when an `override_builtin=true` AI replacement PNG has not been prepared yet
      - preserves AI-backed `figure_map` entries for overridden built-in figure numbers instead of overwriting them with local renderer output
    - `tools/core/workspace_checks.py` now surfaces `Blocking AI figure override issues` during `release-preflight`
    - updated workflow docs and templates:
      - `tools/README.md`
      - `workflow/README.md`
      - `workflow/WORKSPACE_SPEC.md`
      - `workflow/references/command-map.md`
      - `workflow/templates/workspace-config.template.json`
      - `workflow/08-dual-platform-release.md`
      - `workflow/06-ai-prompt-guide.md`
      - `workflow/09-testing-and-regression.md`
  - Compatibility and reproducibility:
    - ran `workflow/scripts/sync_root_compat.sh` so root `tools/core/` now mirrors the bundle-side AI generation implementation
    - root `tools/cli.py` remains a wrapper to `workflow_bundle/tools/cli.py`, so the new command is reachable from the compatibility entry as well
    - root-side workflow prompt guidance was also updated so future fresh AI conversations reading the compatibility docs do not miss the explicit `prepare-ai-figures` stage
  - Validation highlights:
    - static compile passed for the new and modified Python modules
    - CLI help and dry-run path are available for the new command
    - a mocked end-to-end prepare flow successfully wrote a local PNG, updated `figure_map`, and let `prepare-figures` report `preserved-ai` for an overridden built-in figure
    - a real `release-preflight` run against a temp config with `override_builtin=true` and no prepared PNG failed as intended with a blocking AI override message
- Validation passed:
  - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/cli.py /home/ub/thesis_materials/workflow_bundle/tools/core/ai_image_generation.py /home/ub/thesis_materials/workflow_bundle/tools/core/figure_assets.py /home/ub/thesis_materials/workflow_bundle/tools/core/workspace_checks.py /home/ub/thesis_materials/workflow_bundle/tools/core/project_common.py`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-ai-figures --config /tmp/ai_fig_test_n263af7d/workspace.json --fig 5.1 --dry-run`
  - mocked `run_prepare_ai_figures()` integration on `/tmp/ai_fig_test_n263af7d/workspace.json`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-preflight --config /tmp/ai_fig_preflight_radp2bkj/workspace.json`
  - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/check_bundle_sync.sh`

### Step 198
- Action: Hardened the AI image-generation request path so when an OpenAI-compatible provider rejects the `response_format` field, the workflow automatically retries the same request without that parameter instead of failing the whole `prepare-ai-figures` command.
- Purpose: The Zetatechs-compatible endpoint accepted the image request only after removing `response_format`, so the workflow needed a provider-compatibility fallback to keep AI figure generation reproducible across slightly different OpenAI-style gateway implementations.
- Result:
  - Workflow bundle changes:
    - `tools/core/ai_image_generation.py` now imports `HTTPError` and wraps the initial image request
    - when the first request returns `HTTP 400` with `param=response_format` or an equivalent error message, the tool removes `response_format` from the payload and retries once automatically
    - this preserves the existing `b64_json`-first behavior for providers that support it, while letting URL-based fallbacks continue to work on providers that reject the parameter entirely
  - Teatrace workspace verification:
    - updated `/home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json` to add:
      - `ai_figure_specs.5.1`
      - `image_generation.default_model = gpt-image-1`
    - confirmed `.bashrc` exported `NEWAPI_API_KEY`, and identified that plain `source ~/.bashrc` in a non-interactive shell does not load it because the file returns early for non-interactive sessions
    - rerunning `prepare-ai-figures --fig 5.1` after the fallback fix succeeded and generated:
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/docs/images/generated_ai/fig5-1-ai.png`
    - `workspace.json.figure_map["5.1"]` now points to:
      - `docs/images/generated_ai/fig5-1-ai.png`
      - `renderer: ai-image`
    - rerunning `prepare-figures` preserved the AI override:
      - `5.1 [preserved-ai]`
    - rerunning `sync_root_compat.sh` refreshed the root compatibility mirror
    - rerunning `release-preflight` showed:
      - `Blocking AI figure override issues: none`
- Validation passed:
  - diagnostic provider call returned:
    - `400 {"error":{"message":"Unknown parameter: 'response_format'.","type":"invalid_request_error","param":"response_format","code":"unknown_parameter"}}`
  - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/ai_image_generation.py`
  - networked `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-ai-figures --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --fig 5.1`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-figures --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-preflight --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 199
- Action: Evaluated the user's request to switch the entire workflow to `gemini-3.1-flash-image-preview` for AI figure generation, verified it against the live Zetatechs endpoint, and kept the workflow default on `gpt-image-1` while adding a clearer unsupported-model error message.
- Purpose: Avoid leaving the thesis workflow in a broken default state. The current Zetatechs OpenAI image endpoint does not support `gemini-3.1-flash-image-preview`, so switching all defaults to that model would make future `prepare-ai-figures` runs fail.
- Result:
  - Workflow bundle changes:
    - kept `image_generation.default_model` at `gpt-image-1` in:
      - `tools/core/ai_image_generation.py`
      - `tools/core/project_common.py`
      - `workflow/templates/workspace-config.template.json`
      - `workflow/WORKSPACE_SPEC.md`
    - added clearer provider-compatibility handling in `tools/core/ai_image_generation.py`
      - when the provider returns an error message containing `not supported model for image generation`, the workflow now raises an explicit `RuntimeError` explaining that the current Zetatechs OpenAI image endpoint expects dedicated image models such as `gpt-image-1`, and that Gemini image-preview models require a different Gemini Generate Content flow
  - Teatrace workspace handling:
    - restored `/home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json` to `image_generation.default_model = gpt-image-1`
    - preserved the successfully generated AI override for `图5.1`, so the workspace remains usable and release-safe
  - Conclusion:
    - the request to switch all defaults to `gemini-3.1-flash-image-preview` could not be completed safely on the current provider path
    - if Gemini-family image generation is still desired later, the correct next step is not a model-name swap on `/v1/images/generations`, but a separate Gemini Generate Content integration against a provider/model combination that actually supports image output
- Validation passed:
  - diagnostic provider call for `gemini-3.1-flash-image-preview` returned:
    - `500 {"error":{"message":"not supported model for image generation, only imagen models are supported ...","type":"new_api_error","code":"convert_request_failed"}}`
  - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/ai_image_generation.py /home/ub/thesis_materials/workflow_bundle/tools/core/project_common.py`

### Step 200
- Action: Added a separate `zetatechs-gemini` AI image provider branch based on Gemini Generate Content, switched workflow defaults to that provider, and validated live image generation with `gemini-3.1-flash-image-preview`.
- Purpose: The user wanted the workflow to use Gemini-family image generation rather than only the OpenAI Image compatibility endpoint. A dedicated Gemini branch was required because the OpenAI Image path and the Gemini Generate Content path have different endpoints and payload formats.
- Result:
  - Workflow bundle changes:
    - `tools/core/ai_image_generation.py` now supports three provider labels:
      - `zetatechs-gemini`
      - `zetatechs`
      - `zetatechs-openai-image`
    - the default config now points to:
      - `provider: zetatechs-gemini`
      - `base_url: https://api.zetatechs.com`
      - `default_model: gemini-3.1-flash-image-preview`
    - added Gemini request handling through:
      - `POST /v1beta/models/{model}:generateContent?key=...`
      - `contents[].parts[].text`
      - `generationConfig.responseModalities = ["IMAGE", "TEXT"]`
      - `generationConfig.imageConfig`
    - Gemini responses are now parsed from `candidates[].content.parts[].inlineData`
    - kept the OpenAI Image compatibility branch intact for `zetatechs` / `zetatechs-openai-image`
    - updated workspace defaults in:
      - `tools/core/project_common.py`
      - `workflow/templates/workspace-config.template.json`
      - `workflow/WORKSPACE_SPEC.md`
      - `tools/README.md`
      - `workflow/README.md`
      - `workflow/06-ai-prompt-guide.md`
  - Live provider verification:
    - direct diagnostic calls confirmed that both:
      - `gemini-3.1-flash-image-preview`
      - `gemini-3-pro-image-preview`
      return `200` on the Zetatechs Gemini Generate Content endpoint and produce `inlineData`
    - reran Teatrace workspace `prepare-ai-figures --fig 5.1 --force` through the new Gemini branch and regenerated:
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/docs/images/generated_ai/fig5-1-ai.png`
    - `prompt_manifest.json` and `ai_figure_prepare_summary.json` now record:
      - `provider: zetatechs-gemini`
      - `model: gemini-3.1-flash-image-preview`
    - `figure_map["5.1"]` remains mapped to the AI override PNG and `prepare-figures` reports:
      - `5.1 [preserved-ai]`
- Validation passed:
  - direct Gemini endpoint diagnostics for:
    - `gemini-3.1-flash-image-preview`
    - `gemini-3-pro-image-preview`
  - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/ai_image_generation.py /home/ub/thesis_materials/workflow_bundle/tools/core/project_common.py`
  - networked `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-ai-figures --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --fig 5.1 --force`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-figures --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

### Step 201
- Action: Refined the AI figure prompt builder using the thesis diagram checklist and reference diagrams under `docs/images/`, shifting prompt generation from generic “academic illustration” language to structured thesis-diagram instructions with type-specific templates.
- Purpose: The existing prompts were too close to general illustration prompts, which risks generating concept art instead of the white-background, black-line, UML/flowchart/architecture style diagrams actually used in the thesis. The workflow needed explicit diagram-language prompts that match the repository's reference figures.
- Result:
  - Workflow bundle changes:
    - `tools/core/ai_image_generation.py` now supports richer `ai_figure_specs` fields:
      - `diagram_type`
      - `style_notes`
    - `_build_prompt()` was rewritten to emit:
      - explicit “论文技术图” framing
      - white-background / black-line / 2D technical-diagram constraints
      - simplified-Chinese label constraints
      - strong negative constraints against poster-like, illustrative, UI-screenshot, or decorative outputs
    - added diagram-type-specific prompt branches for:
      - `use_case`
      - `function_structure`
      - `flowchart`
      - `sequence`
      - `er`
      - `architecture`
      - generic technical fallback
    - prompt inference now derives a diagram type from caption/intent when `diagram_type` is not explicitly set
  - Teatrace workspace refinement:
    - `workspace.json` now sets `ai_figure_specs.5.1.diagram_type = function_structure`
    - `workspace.json` now sets `ai_figure_specs.5.1.style_notes` to match the repository reference image style:
      - white background
      - black lines
      - top root node
      - horizontally expanded first-level modules
      - vertically listed subfunctions under each module
    - reran `prepare-ai-figures --fig 5.1 --force`, which regenerated the current AI figure with the new prompt template
    - verified that `prompt_manifest.json` now stores the new thesis-diagram prompt text and a refreshed `spec_hash`
    - reran `prepare-figures`, which kept:
      - `5.1 [preserved-ai]`
    - reran `sync_root_compat.sh` so the root compatibility mirror now carries the optimized prompt builder too
- Validation passed:
  - reviewed reference sources:
    - `/home/ub/thesis_materials/docs/THESIS_DIAGRAMS_LIST.md`
    - `/home/ub/thesis_materials/docs/images/image.png`
    - `/home/ub/thesis_materials/docs/images/image-1.png`
    - `/home/ub/thesis_materials/docs/images/image-2.png`
    - `/home/ub/thesis_materials/docs/images/image-3.png`
    - `/home/ub/thesis_materials/docs/images/image-4.png`
    - `/home/ub/thesis_materials/docs/images/image-5.png`
  - `python3 -m py_compile /home/ub/thesis_materials/workflow_bundle/tools/core/ai_image_generation.py`
  - dry-run `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-ai-figures --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --fig 5.1 --dry-run`
  - networked `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-ai-figures --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --fig 5.1 --force`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-figures --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`

### Step 202
- Action: Synced the updated workflow bundle into the Teatrace workspace, reran workflow validation, and added a README-level rule that AI figure prompts must target thesis-style technical diagrams instead of generic illustrations.
- Purpose: The prompt builder change was already implemented, but the workspace signature still needed to be refreshed and the workflow entry docs still needed to tell future AI sessions how to keep using `diagram_type` and `style_notes` correctly. Without that final alignment, a new conversation could still drift back to generic image prompts.
- Result:
  - Runtime state:
    - `sync-workflow-assets` refreshed the Teatrace workspace bundle signature to `ec0e734f3d2a`
    - the workspace now reports:
      - `workflow_signature_status: current`
      - `current_bundle_signature: ec0e734f3d2a`
      - `recorded_bundle_signature: ec0e734f3d2a`
  - Validation state:
    - `release-preflight` now passes with:
      - no blocking packet sync issues
      - no blocking AI figure override issues
      - no citation/style review warnings
    - bundle `selftest` passed after the AI prompt refactor
  - Documentation refinement:
    - `workflow/README.md` now explicitly tells operators that `prepare-ai-figures` should use:
      - `diagram_type`
      - `style_notes`
      - thesis reference sources under `docs/THESIS_DIAGRAMS_LIST.md` and `docs/images/`
      - white-background / black-line / 2D thesis technical diagram constraints
- Validation passed:
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py sync-workflow-assets --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-preflight --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py selftest`

### Step 203
- Action: Raised the AI figure generation timeout baseline from `120s` to `300s` in the workflow bundle defaults and in the active Teatrace workspace after the new multi-figure technical-diagram run hit a network timeout.
- Purpose: The previous timeout was adequate for simple or single-image calls, but the Gemini technical-diagram requests under proxy conditions can exceed that window. The workflow needed a more realistic timeout so `prepare-ai-figures` does not fail prematurely during normal thesis use.
- Result:
  - workflow defaults updated:
    - `tools/core/ai_image_generation.py`
    - `workflow/WORKSPACE_SPEC.md`
    - `workflow/templates/workspace-config.template.json`
  - active workspace updated:
    - `workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `image_generation.timeout_sec = 300`
  - next execution strategy changed from one-shot batch generation to per-figure generation, so slow figures can complete independently and failures can be isolated by figure number.
- Validation in progress:
  - previous batch run failed with:
    - `urllib.error.URLError: <urlopen error timed out>`
  - next step is to rerun `prepare-ai-figures` with the raised timeout and explicit per-figure targets.

### Step 204
- Action: Completed direct-network AI figure generation for Teatrace figures `4.1`, `4.3`, `4.4`, and `4.5`, then resynced compatibility assets and reran workflow validation.
- Purpose: After timeout expansion, runtime troubleshooting showed the configured proxy path could hang on `api.zetatechs.com`, while direct elevated connectivity worked normally. The workflow needed a confirmed operational path so the new thesis-diagram prompt system could be exercised on real chapter figures rather than just a single demo figure.
- Result:
  - Connectivity findings:
    - `curl -I https://api.zetatechs.com` succeeded under escalated direct access
    - `curl -x http://10.225.123.246:7897 -I https://api.zetatechs.com` stalled, indicating the proxy path was the unstable leg for this environment
  - Generated AI figures:
    - `docs/images/generated_ai/fig4-1-ai.png`
    - `docs/images/generated_ai/fig4-3-ai.png`
    - `docs/images/generated_ai/fig4-4-ai.png`
    - `docs/images/generated_ai/fig4-5-ai.png`
    - existing `docs/images/generated_ai/fig5-1-ai.png` remained active
  - Workspace figure map now uses AI outputs for:
    - `4.1`
    - `4.3`
    - `4.4`
    - `4.5`
    - `5.1`
    - while `4.2` remains on deterministic Mermaid E-R generation
  - Workflow validation state:
    - reran `sync_root_compat.sh` to refresh root compatibility mirrors after the timeout-default change
    - reran `sync-workflow-assets` so the Teatrace workspace recorded the current bundle signature `bf829a9e0ce3`
    - reran `release-preflight`, which passed with no blocking AI override issues
    - reran `selftest`, which passed after the timeout-default change
- Validation passed:
  - `curl -I https://api.zetatechs.com`
  - `bash -ic 'python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-ai-figures --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --fig 4.1 --force'`
  - `bash -ic 'for fig in 4.3 4.4 4.5; do python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py prepare-ai-figures --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json --fig "$fig" --force || exit 1; done'`
  - `bash /home/ub/thesis_materials/workflow_bundle/workflow/scripts/sync_root_compat.sh`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py sync-workflow-assets --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-preflight --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py selftest`

### Step 205
- Action: Tightened the flowchart prompt rules to force thesis-style abstraction when process content is too dense, and refined the Teatrace `4.4` spec so the chart only shows the main inter-stage business flow instead of expanding every micro-operation.
- Purpose: The first AI version of `图4.4 核心业务流程图二` packed too many field-level and batch-ID details into a single page image, which made the layout crowded and reduced readability. The workflow needed explicit “compress rather than overcrowd” guidance for flowcharts.
- Result:
  - workflow rule update:
    - `tools/core/ai_image_generation.py` now tells `flowchart` prompts to:
      - merge repetitive micro-steps
      - keep node density suitable for a single thesis page
      - prefer short phrase labels over long field lists
      - abstract repeated `生成ID / 写入链上 / 返回结果` details unless they are essential
  - workspace refinement:
    - `workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `ai_figure_specs.4.4.intent` now explicitly asks for the main process line only
    - `ai_figure_specs.4.4.style_notes` now restricts each stage to one key business node plus the necessary on-chain submission node
  - next step:
    - regenerate `4.4` and verify that the updated image is less crowded and more suitable for direct insertion into the thesis

### Step 206
- Action: Added an explicit prompt rule that thesis diagrams must not contain embedded figure titles, chapter labels, sidebars, or stray vertical auxiliary text, and tightened the Teatrace `4.4` spec to forbid the unwanted left-edge labels that appeared in the regenerated flowchart.
- Purpose: The compressed `4.4` flowchart improved density, but the image still contained non-paper artifacts such as `系统设计章`, `整个段`, `上链进`, and `并链进` along the margin. These labels are not part of the intended business flow and must be blocked at the workflow prompt layer.
- Result:
  - workflow rule update:
    - `tools/core/ai_image_generation.py` now forbids:
      - duplicated figure titles inside the image
      - chapter wording such as `第X章` or `系统设计章`
      - left/right auxiliary bars
      - vertical edge labels and decorative side annotations
  - workspace refinement:
    - `workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `ai_figure_specs.4.4.style_notes` now explicitly bans:
      - `系统设计章`
      - `整个段`
      - `上链进`
      - `并链进`
      - any similar edge labels or extra sectional ornaments
  - next step:
    - regenerate `4.4`, then resync workflow assets and rerun validation

### Step 207
- Action: Strengthened the prompt guardrails again after inspection showed that some regenerated AI figures still contained page-header, page-footer, or in-image caption artifacts, and updated the Teatrace specs for `4.1`, `4.3`, and `4.5` to explicitly forbid those artifacts.
- Purpose: A single “no embedded title” rule was not strong enough for all figure types. The workflow needed explicit bans on edge text, header/footer lines, `Fig./Figure`, English process words, and any non-diagram layout text so the output image contains only the diagram body.
- Result:
  - workflow rule update:
    - `tools/core/ai_image_generation.py` now explicitly bans:
      - page headers and footers
      - paper titles and chapter titles inside the image
      - horizontal separator lines used as faux headers
      - `Fig.` and `Figure`
      - English flow words such as `Yes`, `No`, `End`, `Display`, `trace code`
      - side-lane decorations outside the actual chart body
  - workspace refinement:
    - `workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `ai_figure_specs.4.1.style_notes` now requires a pure architecture body with no top/bottom title text
    - `ai_figure_specs.4.3.style_notes` now requires a pure flowchart body with no header/footer text
    - `ai_figure_specs.4.5.style_notes` now requires simplified-Chinese-only labels and bans all English and side annotations
  - next step:
    - regenerate `4.1`, `4.3`, and `4.5`, then visually inspect the outputs

### Step 208
- Action: Added a deterministic fallback flowchart renderer for figure `4.3` and disabled the `4.3` AI override in the active Teatrace workspace after the AI provider returned `403 insufficient_user_quota`.
- Purpose: `4.3` could not be reliably regenerated through the Gemini image path because the current provider quota was exhausted, and the old deterministic fallback was a sequence diagram that no longer matched the chapter’s desired “核心业务流程图一” form. The workflow needed a quota-independent fallback that still fits the thesis style requirements.
- Result:
  - workflow bundle change:
    - `tools/core/figure_assets.py` now builds `4.3` from a dedicated deterministic Mermaid flowchart:
      - start
      - batch info entry
      - completeness check
      - main-record summary creation
      - `CreateBatch` chain submission
      - chain success/failure branching
      - result return
    - the output file name changed from:
      - `generated/fig4-3-batch-sequence.png`
      - to `generated/fig4-3-batch-flow.png`
  - workspace change:
    - `workspaces/teatrace_thesis/workflow/configs/workspace.json`
    - `ai_figure_specs.4.3.enabled = false`
    - this lets `prepare-figures` take ownership of `4.3` again while keeping AI overrides for the other figures
  - next step:
    - rerun `prepare-figures`, inspect the regenerated deterministic `4.3`, then resync workflow assets and rerun validation

### Step 209
- Action: Regenerated the Teatrace Linux delivery DOCX with the updated figure set, then audited the workflow docs for AI image-generation support and added the missing operating rules discovered during real use.
- Purpose: The document needed to be rebuilt after the figure-map refresh, and the workflow still lacked explicit written rules for two important operational details:
  - AI PNGs must not contain embedded captions or page-layout text
  - individual figures must be allowed to fall back from AI generation to deterministic generation when quota or quality blocks the AI path
- Result:
  - release output refreshed:
    - `python3 workflow_bundle/tools/cli.py release-verify --config <workspace.json>` rebuilt:
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/hyperledger-fabric.docx`
    - release summary updated:
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/release_summary.json`
      - `/home/ub/thesis_materials/workspaces/teatrace_thesis/word_output/release_runs/release_summary_20260403T161941_0800.json`
  - workflow doc refinements:
    - `workflow/README.md`
    - `workflow/06-ai-prompt-guide.md`
    - `workflow/WORKSPACE_SPEC.md`
    - `workflow/09-testing-and-regression.md`
    - `tools/README.md`
    - all now explicitly state that:
      - AI figure PNGs must contain only the diagram body
      - figure captions remain in Markdown / DOCX layout, not inside the image
      - a single figure can disable `ai_figure_specs.<fig>.enabled` and fall back to deterministic `prepare-figures`
      - AI figure review should include a visual check for embedded titles, header/footer text, `Fig.` / `Figure`, and other non-diagram artifacts
- Validation passed:
  - `python3 /home/ub/thesis_materials/workflow_bundle/tools/cli.py release-verify --config /home/ub/thesis_materials/workspaces/teatrace_thesis/workflow/configs/workspace.json`

## 2026-04-06 01:41:35 +0800

### Step 1
- Action: Inspected the rural education donation workspace outputs after the earlier intake fix, including `material_pack.json`, `literature_pack.json`, `code_evidence_pack.json`, and `project_profile.json`.
- Purpose: Verify whether the formal workflow was good enough to continue from the new workspace without additional workflow changes.
- Result: Found three new workflow quality defects:
  - `extract` treated this project as a generic traceability/Fabric app instead of an education donation crowdfunding system.
  - `extract` could not reliably summarize Express API routes or Fabric chaincode responsibilities from the actual JS/Go codebase.
  - `literature` generated mostly generic Fabric/traceability queries, which produced weak topic alignment for the thesis domain.

### Step 2
- Action: Updated `tools/core/code_evidence.py`, `tools/core/chapter_profile.py`, `tools/core/extract.py`, `tools/core/writing.py`, and bumped schema versions in `tools/core/project_common.py`.
- Purpose: Make the workflow materially support JS + Hyperledger Fabric + education crowdfunding / donation transparency projects.
- Result:
  - Added a dedicated `education_crowdfunding` domain profile for code evidence extraction and chapter planning.
  - Added donation-specific core modules, subfunctions, flow labels, and design asset requirements.
  - Added Express route extraction from JS/TS source.
  - Added donation-domain objective and business-flow derivation from code + SQL evidence.
  - Added donation-focused literature queries around crowdfunding, donation transparency, education accountability, and fund usage tracking.

### Step 3
- Action: Re-ran the new workspace through the formal CLI chain:
  - `intake`
  - `extract-code`
  - `extract`
  - `scaffold`
  - `literature`
  - `prepare-outline`
  - `prepare-writing`
- Purpose: Ensure the fixes changed real workspace artifacts, not only source code.
- Result:
  - `material_pack.json` now reports `schema_version: 9` and uses education-donation-specific objective and flow summaries.
  - `project_profile.json` now reports `domain_label: 教育众筹资金明白账`.
  - `code_evidence_pack.json` now reports `domain_key: education_crowdfunding` and contains non-zero backend/frontend evidence counts for all core modules.
  - `literature_pack.json` now uses focused donation-transparency / education-accountability query strings and returns more relevant references.

### Step 4
- Action: Fixed two newly exposed extractor edge cases during rerun.
- Purpose: Remove infrastructure noise from JS/Fabric scanning so the new domain logic remains stable.
- Result:
  - Added `is_file()` / `node_modules` protection to the JS Express API extractor after `extract` hit `backend/node_modules/ipaddr.js`.
  - Filtered `vendor` / `.gocache` in Fabric chaincode scanning and promoted real chaincode transaction names into `blockchain_design` summaries.

### Step 5
- Action: Refreshed the affected chapter packets and re-ran workspace checks.
- Purpose: Clear stale packet state caused by the domain/profile update and confirm the workspace is ready for drafting.
- Result:
  - Regenerated `03-需求分析.md`, `04-系统设计.md`, `05-系统实现.md`, and `06-系统测试.md` packets/briefs.
  - `python3 tools/cli.py check-workspace --config /home/ub/rural_work/rural_education_donation_thesis_workspace/workflow/configs/workspace.json` now passes with no blocking packet issues.
  - `resume` now points cleanly to `start-chapter --chapter 02-系统开发工具及技术介绍.md`.

## 2026-04-06 09:24:00 +0800

### Step 6
- Action: Extended `tools/core/extract.py` for the `education_crowdfunding` domain, then re-ran `extract -> prepare-writing -> prepare-chapter(03/04) -> check-workspace` on the rural education donation workspace.
- Purpose: Remove the last Chapter 4 placeholder-table gap from the formal workflow and clean Chapter 3 role extraction so the writing packets are directly usable for正文 drafting.
- Result:
  - Added a dedicated Chapter 4 design-table builder for education crowdfunding projects.
    - `表4.1 功能模块—设计落点映射` is now derived from the project's project/audit, donation, disbursement, usage, and traceability modules.
    - `表4.4 角色与审批职责映射` is now emitted as a real `role-matrix` asset instead of a placeholder.
  - Added role normalization for the education crowdfunding domain so noisy raw tokens such as `donor`, `admin`, `school`, and `用户` collapse into thesis-facing role labels.
  - Regenerated outputs now validate cleanly:
    - `docs/writing/chapter_briefs/03-需求分析.md` now shows clean role rows and `roles detected: 管理员, 监管方, 捐赠人, 审核人, 学校执行方, 项目申报人, 拨付审批人, 资金使用上报人`
    - `docs/writing/chapter_briefs/04-系统设计.md` now has `validation_status: ok` with both required Chapter 4 tables materialized
  - `python3 /home/ub/rural_work/workflow_bundle/tools/cli.py check-workspace --config /home/ub/rural_work/rural_education_donation_thesis_workspace/workflow/configs/workspace.json` passes after the refresh.

## 2026-04-06 12:14:50 +0800

### Step 1
- Action: Updated `/home/ub/rural_work/workflow_bundle/tools/core/figure_assets.py` and synced root compatibility wrappers with `workflow/scripts/sync_root_compat.sh`.
- Purpose: Make the formal workflow generate Chapter 4 design figures for the rural education donation thesis instead of leaving `4.1/4.2` missing and reusing old traceability flow content for `4.3/4.4/4.5`.
- Result:
  - Added deterministic local figure renderers for `图4.1 系统总体架构图` and `图4.2 数据库E-R图`.
  - Replaced the old traceability-oriented flow generation with education-crowdfunding-specific Chapter 4 business flow diagrams for `图4.3` to `图4.5`.
  - Kept `图5.1` on the existing local function-structure renderer, so the full `4.1` to `5.1` chain now builds without relying on remote Mermaid rendering.

### Step 2
- Action: Patched the rural education donation workspace source-of-truth chapter at `/home/ub/rural_work/rural_education_donation_thesis_workspace/polished_v3/04-系统设计.md`.
- Purpose: Insert workflow-readable hidden figure markers for `4.1` and `4.2` so the newly generated assets are actually embedded into the DOCX instead of staying only on disk.
- Result:
  - Added `<!-- figure: 4.1 -->` below `图4.1 系统总体架构图`.
  - Added `<!-- figure: 4.2 -->` below `图4.2 数据库E-R图`.
  - Removed the temporary `missing diagram source for figure 4.1/4.2` lines from `docs/materials/missing_items.md`, because these figures are now formally inferred by workflow.

### Step 3
- Action: Re-ran the official publish chain:
  - `python3 /home/ub/rural_work/workflow_bundle/tools/cli.py release-build --config /home/ub/rural_work/rural_education_donation_thesis_workspace/workflow/configs/workspace.json`
  - `python3 /home/ub/rural_work/workflow_bundle/tools/cli.py release-verify --config /home/ub/rural_work/rural_education_donation_thesis_workspace/workflow/configs/workspace.json`
- Purpose: Validate that the patched workflow really regenerates and inserts the new figures into the current thesis workspace.
- Result:
  - `word_output/figure_insert_log.csv` now includes `图4.1 系统总体架构图`, `图4.2 数据库E-R图`, `图4.3 项目申报与审核流程图`, `图4.4 公益捐赠与资金拨付流程图`, `图4.5 资金使用上报与链上追溯流程图`, and `图5.1 系统功能结构图`.
  - `word_output/thesis-workspace.docx` was rebuilt successfully with the updated figure set.
  - `word_output/release_summary.json` still reports `anchors missing bookmarks: 0`, so citation verification remains clean after the figure refresh.

## 2026-04-07 16:43:00 +0800

### Step 4
- Action: Refined the deterministic Chapter 4 architecture renderer in `/home/ub/rural_work/workflow_bundle/tools/core/figure_assets.py`.
- Purpose: The previous `图4.1 系统总体架构图` had drifted away from strict project evidence because it was later overridden by an AI image prompt, and even the deterministic fallback still mixed in excess English labels and a not-yet-fully-integrated completion table. The workflow needed an evidence-based fallback that matches the actual project structure and the user's wording constraints.
- Result:
  - Raised the deterministic renderer signature for `图4.1` so the figure is forced to regenerate.
  - Rewrote the deterministic architecture figure text to:
    - remove slash-heavy labels
    - remove non-essential English
    - keep only technical proper names such as `Vue 3`, `Vite`, `Element Plus`, `Node.js`, `Express`, `MySQL`, `Hyperledger Fabric`, and `donationtrace`
  - Replaced generic or over-claimed content with evidence-based labels:
    - user roles now use Chinese-only role groups
    - the backend is described as unified business service plus blockchain adapter and file-hash handling
    - the data layer now focuses on actual running data categories instead of foregrounding `project_completions`
    - the data layer explicitly states that the trace page currently reads mainly from database aggregation
    - the chain layer now states donation and usage notarization capability without implying that all trace queries are directly chain-driven

## 2026-04-07 18:35:00 +0800

### Step 5
- Action: Updated `/home/ub/rural_work/workflow_bundle/tools/core/figure_assets.py` to redesign the deterministic `pillow-er` renderer for `图4.2 数据库E-R图`.
- Purpose: The previous renderer produced a table-relationship diagram with field-list boxes, which did not match the user's requirement for a traditional E-R figure.
- Result:
  - Replaced the old table-relationship layout with a Chen-style monochrome E-R renderer.
  - The new renderer uses entity rectangles, relationship diamonds, attribute ellipses, key-attribute underlines, and explicit cardinality markers.
  - The figure content now uses concept-level Chinese entity and attribute labels derived from the actual project database evidence instead of raw table-schema boxes.

### Current Next Actions
- Sync the root compatibility mirror from `workflow_bundle/tools/core`.
- Re-run `prepare-figures` and `release-verify` on the rural education donation workspace.
- Visually inspect the regenerated `图4.2` and confirm that the published DOCX now uses the traditional E-R figure.

## 2026-04-08 12:58:00 +0800

### Step 6
- Action: Patched `/home/ub/rural_work/workflow_bundle/tools/core/build_final_thesis_docx.py` so the generated DOCX writes a real Word table-of-contents field instead of a plain placeholder sentence.
- Purpose: The current Linux delivery artifact contained only the literal text `（请在 Word 中插入“目录”，并更新域以生成目录。）`, so users could not right-click `更新域` because there was no field object at the TOC location at all.
- Result:
  - Replaced the placeholder-only TOC paragraph with a real field code:
    - `TOC \\o "1-3" \\h \\z \\u`
  - Marked the TOC field dirty so Word recognizes it as needing refresh.
  - Added `w:updateFields w:val="true"` to document settings so Word is prompted to refresh fields on open.
  - Verified with a temporary build at `/tmp/rural_toc_test_output/thesis-workspace.docx` that:
    - `word/document.xml` now contains a true TOC field block
    - `word/settings.xml` now contains `w:updateFields`
  - This means newly generated base DOCX files can be manually updated in Word without depending on a later Windows-only placeholder replacement step.

## 2026-04-08 13:12:00 +0800

### Step 7
- Action: Patched the fenced-code screenshot insertion path in `/home/ub/rural_work/workflow_bundle/tools/core/build_final_thesis_docx.py`.
- Purpose: Code blocks were rendered as screenshot images, but the containing paragraph still inherited the normal body-paragraph format with fixed line spacing, so the “代码截图所在段落” in the generated DOCX did not follow single-line spacing as required.
- Result:
  - Changed code-screenshot paragraphs to use single-line spacing instead of the body paragraph fixed spacing.
  - Kept the existing left indent for code screenshot placement, while marking the paragraph as `keep_together` to reduce split risk.
  - Verified with a temporary build at `/tmp/rural_toc_test_output/thesis-workspace.docx` that drawing paragraphs generated for code screenshots now serialize as:
    - `lineRule=auto`
    - `line=240`
  - This confirms the screenshot paragraphs now use Word single-line spacing rather than the thesis body fixed spacing.

## 2026-04-08 13:46:00 +0800

### Step 8
- Action: Patched the DOCX release path in `/home/ub/rural_work/workflow_bundle/tools/core/build_final_thesis_docx.py`, `/home/ub/rural_work/workflow_bundle/tools/core/verify_citation_links.py`, `/home/ub/rural_work/workflow_bundle/tools/cli.py`, `/home/ub/rural_work/workflow_bundle/tools/core/release_summary.py`, `/home/ub/rural_work/workflow_bundle/tools/README.md`, and `/home/ub/rural_work/workflow_bundle/workflow/README.md`.
- Purpose: The current base DOCX could pass citation verification while still missing page numbers entirely, because the builder never created footer PAGE fields and the verify chain did not inspect footer XML. The workflow needed to generate page-number footers and to fail fast if future DOCX outputs lose those fields again.
- Result:
  - Added a footer PAGE field generator for every document section, with centered footer paragraphs and explicit field-code serialization.
  - Inserted the footer configuration before `doc.save(...)`, so the exported DOCX now writes `word/footer*.xml` parts and section footer references.
  - Extended `verify` and `release-verify` to check:
    - real TOC field presence
    - footer PAGE field presence
    - `w:updateFields`
    - code screenshot single-line media paragraphs
    - expected figure captions declared by workspace figure markers
  - Updated `release_summary` so the machine-readable verification block captures the stronger DOCX checks.
  - Documented the stronger release verification contract in both bundle README files so later runs treat page numbers as a formal delivery invariant rather than a manual visual afterthought.

## 2026-04-08 14:02:00 +0800

### Step 9
- Action: Adjusted the page-number footer serializer in `/home/ub/rural_work/workflow_bundle/tools/core/build_final_thesis_docx.py`.
- Purpose: The previous footer implementation used a complex PAGE field with a cached display result of `1`. LibreOffice repaginated it correctly, but the user reported that in Word the page numbers could remain stuck at `1` on every page. The workflow needed a more Word-friendly footer field representation.
- Result:
  - Replaced the footer PAGE complex field with a simple field form:
    - `PAGE \\* MERGEFORMAT`
  - Kept the footer centered, black, and 10.5 磅, while changing only the field serialization strategy.
  - This makes the exported DOCX closer to the page-number field structure that Word commonly refreshes correctly in headers and footers.

## 2026-04-11 11:52:29 +0800

### Step 10
- Action: Introduced a generic `dbdia-er` workflow path for deterministic E-R figures.
- Purpose: The previous experimental E-R work was tied to one specific thesis project. The remote workflow needs a reusable, opt-in capability that does not change default behavior for existing workspaces.
- Result:
  - Added vendored `dbdia` + `graphviz_wasm` runtime assets under `vendor/`.
  - Extended `prepare-figures` so workspace configs can declare `er_figure_specs` keyed by figure number.
  - Kept `figure_map` as an output registry only; explicit E-R input now comes from `er_figure_specs`.
  - Enabled `.dbdia -> .dot -> .svg -> .png` generation with sidecar artifacts under `docs/images/generated_src/`.

### Step 11
- Action: Added generic regression coverage and submission-oriented docs for the E-R workflow.
- Purpose: Ensure the new capability can be replayed in bundle selftest without relying on a user-specific workspace, and document exactly how to enable it.
- Result:
  - Updated fixture selftest to inject a minimal `.dbdia` source and verify `dbdia-er` output plus sidecar assets.
  - Updated README/spec/testing/command-map docs to describe `er_figure_specs`, vendored runtime requirements, and cache recovery expectations.
  - Updated `.gitignore` so vendor build caches and local install artifacts stay out of git.

## 2026-04-12 13:35:00 +0800

### Step 210
- Action: Synced the validated health-record workflow fixes into the official git-tracked bundle repository, covering `chapter_profile`, `extract`, `page_screenshot_assets`, `workspace_checks`, `release_summary`, and `selftest`.
- Purpose: The health-record thesis onboarding and Chapter 5 screenshot repairs had already been validated in the local test bundle, but the remote repository still lacked the formal workflow support required to keep those fixes durable and shareable.
- Result:
  - added the full health-record Chapter 5 page-screenshot contract, deterministic screenshot staging paths, and section-level blocking validation
  - added health-record extraction support for `assets/frontend_manual_test_*`, FISCO-oriented Chapter 4 wording, and Chapter 6 health-record test tables
  - extended release summaries and selftests so stale / cross-section page screenshots are blocked and regression-tested



## 2026-04-12 14:32:31 +08:00

### Step 211
- Action: Patched `workflow_bundle/tools/core/figure_assets.py`, `workflow_bundle/tools/core/workspace_checks.py`, and `workflow_bundle/tools/core/selftest.py` to repair the remaining Chapter 3 / Chapter 4 figure workflow gaps around `图3.1` and `图4.1`, while preserving the previously released `dbdia-er` E-R rendering path.
- Purpose: The active health-record thesis workspace had already passed the Chapter 5 screenshot contract, but two earlier-chapter figure links still leaked through the workflow:
  - `图3.1 系统用例图` still depended too heavily on fresh workspace metadata; when the profile or domain tag lagged behind, the workflow could not reliably infer the health-record use-case layout required by Chapter 3.
  - `图4.1 系统总体架构图` was only generated when an upstream mermaid architecture block existed. For projects that lacked that source block, `prepare-figures` silently skipped `4.1`, and preflight only noticed the issue after the正文 side was manually inspected.
  - `check-workspace` also failed to block the case where a required figure had no `figure_map` asset entry at all, which meant missing mapped assets could slip through figure integration checks.
- Result:
  - added a deterministic `use_case` renderer path for `图3.1`, with domain inference fallback from title / roles so health-record projects still get a usable Chapter 3 use-case figure even when workspace metadata is stale
  - added a deterministic `pillow-architecture` fallback renderer for `图4.1`, so Chapter 4 can still receive a valid overall architecture figure when no source mermaid architecture block is present
  - preserved the existing `dbdia-er` explicit E-R workflow and merged the new 3.1 / 4.1 logic without regressing remote `4.2` support
  - strengthened `workspace_checks.py` so required figures now block on both missing mapped assets and mapped asset paths that do not exist on disk
  - extended `selftest.py` with a regression that deletes a required mapped figure asset, asserts `check-workspace` fails with the new blocking reason, then restores the config and confirms recovery
