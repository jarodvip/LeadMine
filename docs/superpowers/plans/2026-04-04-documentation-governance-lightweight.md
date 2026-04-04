# Documentation Governance Lightweight Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a reliable documentation entrypoint and rolling status pages, then align the core project docs so LeadMine’s documentation reflects current reality without rewriting the whole doc set.

**Architecture:** Keep the existing `docs/` and `docs/superpowers/` layout. Add two new top-level docs for the single source of truth and rolling progress, then make small, explicit edits to `docs/PRD.md`, `docs/开发计划.md`, and `docs/技术方案设计.md` so each document has one clear responsibility and points readers to the right place.

**Tech Stack:** Markdown, git, existing repository documentation

---

## File Structure

- Create: `docs/项目现状总览.md`
  - Single entrypoint summarizing shipped capabilities, current phase, next candidates, verification baseline, and links to key docs.
- Create: `docs/当前开发计划.md`
  - Rolling status page for current phase, completed work, next steps, risks, and verification.
- Modify: `docs/PRD.md`
  - Add document-positioning blocks and lightly align wording so product scope is separated from implementation status.
- Modify: `docs/开发计划.md`
  - Add document-positioning blocks and make it explicit that this is the original phase plan, not the live delivery tracker.
- Modify: `docs/技术方案设计.md`
  - Add document-positioning blocks and distinguish current implementation from planned expansion.
- Reference only: `docs/superpowers/specs/2026-04-04-documentation-governance-lightweight-design.md`
  - The approved design spec that this plan implements.
- Reference only: `docs/superpowers/release-notes/2026-03-29-mainline-delivery-summary.md`
  - Canonical recent shipped-state summary for current baseline wording.

---

### Task 1: Add the documentation entrypoint

**Files:**
- Create: `docs/项目现状总览.md`
- Reference: `docs/superpowers/release-notes/2026-03-29-mainline-delivery-summary.md`
- Reference: `docs/superpowers/specs/2026-03-31-leads-efficiency-version-design.md`

- [ ] **Step 1: Write the new overview document content**

Create `docs/项目现状总览.md` with this content:

```markdown
# 项目现状总览

## 项目当前状态

LeadMine 当前已具备从资讯采集、内容处理到线索管理的最小可运行主链路，现阶段重点从“继续扩功能”转向“交付质量收口 + 线索处理提效后的文档与协作对齐”。

## 当前已交付

### 数据采集
- RSS 订阅采集
- 36氪新闻采集
- 虎嗅新闻采集
- 通过 RSSHub 接入微信公众号来源

### 数据处理
- 文本清洗
- 去重处理
- NLP 分词与关键词提取
- 线索识别与基础富化

### 线索管理
- Leads 列表与分页浏览
- 多维筛选与关键词搜索
- 当前页批量操作（状态更新、分配、删除）
- 导出能力
- 负责人与销售备注可见/可维护

### 交付基线
- 后端 pytest 回归
- 前端 npm test 回归
- 最近一轮交付说明已沉淀到 release note

## 当前阶段

- 文档治理轻量改造
- 已交付能力与主文档对齐
- 为后续迭代建立稳定入口与滚动计划页

## 下一阶段候选

- 用户权限管理补强
- 监控与日志能力完善
- 更多来源扩展
- 线索识别准确率优化

## 当前验收基线

### 后端

```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest
```

### 前端

```bash
cd /Users/jarod/Dev/LeadMine/web && npm test
```

## 关键文档入口

- [产品需求文档](./PRD.md)
- [当前开发计划](./当前开发计划.md)
- [历史开发计划](./开发计划.md)
- [技术方案设计](./技术方案设计.md)
- [文档治理轻量改造设计](./superpowers/specs/2026-04-04-documentation-governance-lightweight-design.md)
- [最近主线交付说明](./superpowers/release-notes/2026-03-29-mainline-delivery-summary.md)
- [线索提效版设计](./superpowers/specs/2026-03-31-leads-efficiency-version-design.md)
```

- [ ] **Step 2: Read the file and verify the structure is complete**

Run: read `docs/项目现状总览.md`
Expected sections:
- `## 项目当前状态`
- `## 当前已交付`
- `## 当前阶段`
- `## 下一阶段候选`
- `## 当前验收基线`
- `## 关键文档入口`

- [ ] **Step 3: Commit the entrypoint doc**

```bash
git add docs/项目现状总览.md
git commit -m "docs: add project status overview"
```

---

### Task 2: Add the rolling development plan

**Files:**
- Create: `docs/当前开发计划.md`
- Reference: `docs/superpowers/release-notes/2026-03-29-mainline-delivery-summary.md`
- Reference: `docs/superpowers/specs/2026-03-31-leads-efficiency-version-design.md`
- Reference: `docs/superpowers/plans/2026-03-31-leads-efficiency-version.md`

- [ ] **Step 1: Write the rolling plan document content**

Create `docs/当前开发计划.md` with this content:

```markdown
# 当前开发计划

## 当前阶段

交付质量收口已完成基线整理，当前进入文档治理轻量改造阶段，目标是让项目现状、历史规划与技术实现边界表达一致。

## 已完成

### 主链路能力
- RSS、36氪、虎嗅与微信 RSSHub 来源已打通基础采集链路。
- 数据清洗、去重、NLP 处理与线索提取已形成最小可运行流程。
- Leads 列表、筛选、详情、基础状态流转已具备可用版本。

### 近期交付
- Leads 当前页批量操作已支持状态更新、分配与删除。
- Leads 首屏 keyword 初始化加载问题已修复。
- Leads 列表与导出参数已对齐，导出复用当前筛选条件。
- Leads 列表已补充负责人和销售备注字段可见性。
- 批量操作结果反馈与回归测试已补强。

### 文档与验证
- 交付质量基线文档已整理。
- 最近主线交付说明已补充。
- 当前最小验证命令已明确为 backend pytest 与 web npm test。

## 进行中

- 文档治理轻量改造实施：建立总览入口、滚动计划页，并校准核心主文档定位。

## 下一步计划

1. 完成 `项目现状总览` 与 `当前开发计划` 两份入口文档。
2. 给 `PRD`、`开发计划`、`技术方案设计` 增加定位与状态说明。
3. 修正主文档中与当前实现明显冲突的表述。
4. 建立每轮迭代后的最小文档更新规则。

## 风险与阻塞

- 若后续迭代只改代码不改总览/滚动计划，文档仍会重新漂移。
- `开发计划.md` 仍保留历史周计划结构，若缺少定位提示，容易继续被误读。
- `技术方案设计.md` 中若不明确区分已实现与规划中，仍可能造成错误预期。

## 验收方式

### 后端

```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest
```

### 前端

```bash
cd /Users/jarod/Dev/LeadMine/web && npm test
```

### 人工检查
- `docs/项目现状总览.md` 可作为统一入口。
- `docs/当前开发计划.md` 可独立表达当前阶段与下一步。
- 旧主文档不再被误读为实时状态页。
```

- [ ] **Step 2: Read the file and verify it answers current-state questions**

Run: read `docs/当前开发计划.md`
Expected sections:
- `## 当前阶段`
- `## 已完成`
- `## 进行中`
- `## 下一步计划`
- `## 风险与阻塞`
- `## 验收方式`

- [ ] **Step 3: Commit the rolling plan doc**

```bash
git add docs/当前开发计划.md
git commit -m "docs: add rolling development plan"
```

---

### Task 3: Add positioning blocks to the product and planning docs

**Files:**
- Modify: `docs/PRD.md`
- Modify: `docs/开发计划.md`
- Reference: `docs/当前开发计划.md`

- [ ] **Step 1: Insert the positioning block near the top of `docs/PRD.md`**

Add this block immediately after the title line `# LeadMine 产品需求文档 (PRD)`:

```markdown
## 文档定位

本文档描述 LeadMine 的产品目标、功能范围、优先级和成功指标，不作为当前开发完成度的唯一依据。

## 当前状态说明

项目部分核心能力已落地，实际开发进度、近期交付与当前阶段重点请参考《当前开发计划》与《项目现状总览》。

## 最后校准时间

2026-04-04
```

- [ ] **Step 2: Insert the positioning block near the top of `docs/开发计划.md`**

Add this block immediately after the title line `# LeadMine 开发计划`:

```markdown
## 文档定位

本文档保留 LeadMine 项目初版阶段规划、周次拆分与路线图，作为历史背景参考。

## 当前状态说明

项目当前实际进度不再按本文档周计划滚动维护；现行开发状态、已完成事项与下一步安排请参考《当前开发计划》与《项目现状总览》。

## 最后校准时间

2026-04-04
```

- [ ] **Step 3: Read both files and verify the new guidance appears before the old body**

Run: read `docs/PRD.md` and `docs/开发计划.md`
Expected:
- Both files show `## 文档定位`
- Both files show `## 当前状态说明`
- Both files show `## 最后校准时间`
- The original main content remains below those new sections

- [ ] **Step 4: Commit the positioning changes**

```bash
git add docs/PRD.md docs/开发计划.md
git commit -m "docs: clarify product and plan document roles"
```

---

### Task 4: Align the technical design doc with current reality

**Files:**
- Modify: `docs/技术方案设计.md`
- Reference: `docs/当前开发计划.md`

- [ ] **Step 1: Insert the positioning block near the top of `docs/技术方案设计.md`**

Add this block immediately after the title line `# LeadMine 技术方案设计`:

```markdown
## 文档定位

本文档描述 LeadMine 当前实现架构与关键技术设计，不等同于完整未来蓝图。

## 当前状态说明

文中提及的能力如果尚未在仓库中落地，应显式理解为规划中或扩展方向；当前已交付状态请结合《项目现状总览》与《当前开发计划》阅读。

## 最后校准时间

2026-04-04
```

- [ ] **Step 2: Replace the architecture summary sentence with one that matches the repo**

Replace:

```markdown
LeadMine采用微服务架构设计，整体系统分为五个层次：
```

with:

```markdown
LeadMine 当前采用分层单体后端 + 独立前端的实现方式，并结合独立的采集与处理模块组织整体系统；下图展示的是当前实现结构与预留扩展方向的合并视图。
```

- [ ] **Step 3: Make the expansion language explicit in the search/storage row if still needed**

If the table row still reads as a fully required current dependency, replace the Elasticsearch row:

```markdown
| **搜索引擎** | Elasticsearch | 8.11+ | 全文搜索 |
```

with:

```markdown
| **搜索引擎** | Elasticsearch | 8.11+ | 全文搜索扩展能力，当前为可选组件 |
```
```

- [ ] **Step 4: Read the file and verify it now distinguishes current implementation from expansion**

Run: read `docs/技术方案设计.md`
Expected:
- The new positioning block appears near the top
- The architecture sentence no longer claims the repo is already a microservice system
- Optional/expansion capabilities are described as optional or planned where appropriate

- [ ] **Step 5: Commit the technical doc alignment**

```bash
git add docs/技术方案设计.md
git commit -m "docs: align technical design with current architecture"
```

---

### Task 5: Cross-link the new docs and verify the lightweight governance baseline

**Files:**
- Modify: `docs/项目现状总览.md`
- Modify: `docs/当前开发计划.md`
- Modify: `docs/PRD.md`
- Modify: `docs/开发计划.md`
- Modify: `docs/技术方案设计.md`

- [ ] **Step 1: Ensure cross-links are present in the new and updated docs**

Verify the following references exist after the earlier tasks:

```markdown
- `docs/项目现状总览.md` links to `PRD.md`, `当前开发计划.md`, `开发计划.md`, `技术方案设计.md`
- `docs/PRD.md` mentions `《当前开发计划》` and `《项目现状总览》`
- `docs/开发计划.md` mentions `《当前开发计划》` and `《项目现状总览》`
- `docs/技术方案设计.md` mentions `《项目现状总览》` and `《当前开发计划》`
```

If any are missing, add the minimal missing sentence or markdown link in the relevant file.

- [ ] **Step 2: Run the manual review pass defined by the spec**

Read these files in order:

1. `docs/项目现状总览.md`
2. `docs/当前开发计划.md`
3. `docs/PRD.md`
4. `docs/开发计划.md`
5. `docs/技术方案设计.md`

Confirm all of the following are true:
- A new reader can find the project status from the overview page
- Current progress is expressed only in the rolling plan
- The historical plan is clearly marked as historical
- The technical design doc distinguishes current state vs planned/optional capability

- [ ] **Step 3: Commit the final doc-governance pass**

```bash
git add docs/项目现状总览.md docs/当前开发计划.md docs/PRD.md docs/开发计划.md docs/技术方案设计.md
git commit -m "docs: establish lightweight documentation governance"
```

---

## Self-Review

### Spec coverage
- Unified entrypoint: covered by Task 1.
- Rolling progress page: covered by Task 2.
- Positioning blocks for PRD / 开发计划 / 技术方案设计: covered by Tasks 3 and 4.
- Small-scope wording alignment with current reality: covered by Tasks 3, 4, and 5.
- Governance rules and stable maintenance path: covered by Task 5.

### Placeholder scan
- No `TODO`, `TBD`, or deferred implementation markers remain.
- Every changed file has explicit content or exact replacement text.
- Every task includes a verification read/review step and a commit step.

### Type consistency
- New document names are used consistently: `项目现状总览.md` and `当前开发计划.md`.
- Core edited files remain consistent with the approved spec.
- The plan keeps `docs/superpowers/` archive files unchanged except as references.
