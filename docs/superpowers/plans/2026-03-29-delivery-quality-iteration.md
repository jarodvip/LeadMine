# Delivery Quality Iteration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize the frontend test entrypoint, lock in the repo’s minimum verification commands, prepare a reusable Chinese release note, and align core docs with the current shipped state.

**Architecture:** Keep this iteration documentation-first and behavior-neutral. The only code change is exposing the existing Vitest command through `web/package.json`; the rest of the work updates written delivery artifacts so they match the already-shipped backend/frontend capabilities.

**Tech Stack:** npm, Vitest, Python pytest, Markdown documentation

---

## File Structure

- Modify: `web/package.json`
  - Add a standard frontend `test` script that maps to the existing Vitest runner.
- Modify: `docs/PRD.md`
  - Align high-level product capability statements with current shipped functionality.
- Modify: `docs/开发计划.md`
  - Mark already-finished capability areas as complete/current and avoid presenting shipped work as still pending.
- Modify: `docs/技术方案设计.md`
  - Align architecture and capability descriptions with the current source types and shipped frontend/backend behavior.
- Create: `docs/superpowers/release-notes/2026-03-29-mainline-delivery-summary.md`
  - Store the reusable Chinese release note for the recent mainline changes.

---

### Task 1: Expose the frontend test entrypoint

**Files:**
- Modify: `web/package.json`
- Test: `web/package.json`

- [ ] **Step 1: Write the failing check for the missing script**

Use this command to prove the standard script is missing:

```bash
cd /Users/jarod/Dev/LeadMine/web && npm test
```

Expected:

```text
npm error Missing script: "test"
```

- [ ] **Step 2: Add the minimal `test` script**

Update `web/package.json` so the `scripts` block becomes:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest run",
    "preview": "vite preview"
  }
}
```

- [ ] **Step 3: Run the frontend test command to verify it now passes**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/web && npm test
```

Expected:

```text
Test Files  1 passed (1)
Tests  3 passed (3)
```

- [ ] **Step 4: Commit the script-only change**

```bash
git add web/package.json
git commit -m "chore: add frontend test script"
```

---

### Task 2: Record the verification baseline in delivery docs

**Files:**
- Create: `docs/superpowers/release-notes/2026-03-29-mainline-delivery-summary.md`
- Modify: `docs/开发计划.md`
- Test: `web/package.json`

- [ ] **Step 1: Create the release note with explicit verification commands**

Create `docs/superpowers/release-notes/2026-03-29-mainline-delivery-summary.md` with this content:

```markdown
# 2026-03-29 主线交付说明

## 本次已交付

- 新增微信 RSSHub 来源支持，微信公众号来源可沿用 RSS 抓取链路接入。
- Leads 页面支持当前页批量操作，并补齐前端回归测试覆盖。
- 修复 Leads 首屏按 keyword 初始化加载的问题，避免进入页面后漏掉首轮请求。
- 补强数据处理真实字段断言与来源类型相关回归测试。
- 将规划与产品文档整理到 `docs/` 与 `docs/superpowers/` 结构下，便于后续维护。

## 最小验证方式

### 后端

```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest
```

### 前端

```bash
cd /Users/jarod/Dev/LeadMine/web && npm test
```

## 备注

- 本说明只覆盖已合入主线并已验证通过的内容。
- 下一迭代优先处理交付质量基线，不在此文档中承诺新的业务功能。
```

- [ ] **Step 2: Mark the current development plan as already past the initial delivery phases**

In `docs/开发计划.md`, replace the top project summary block:

```markdown
## 1. 项目概述

- **项目名称**：LeadMine（线索矿工）
- **项目类型**：B2B销售线索挖掘系统
- **技术栈**：Python + FastAPI + Vue3 + MySQL + Elasticsearch + Docker
- **预计周期**：6周
```

with:

```markdown
## 1. 项目概述

- **项目名称**：LeadMine（线索矿工）
- **项目类型**：B2B销售线索挖掘系统
- **技术栈**：Python + FastAPI + Vue3 + MySQL + Elasticsearch + Docker
- **当前状态**：核心采集、处理、线索管理主流程已具备可运行版本，近期已完成微信 RSSHub 来源支持、Leads 批量操作与前后端回归测试补强。
- **本阶段重点**：收口交付质量，统一测试入口、验证方式与交付说明。
```

- [ ] **Step 3: Verify the baseline commands referenced in the release note are runnable**

Run these commands in order:

```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest
cd /Users/jarod/Dev/LeadMine/web && npm test
```

Expected:

```text
backend: 198 passed
frontend: 3 passed
```

- [ ] **Step 4: Commit the release note and plan alignment**

```bash
git add docs/superpowers/release-notes/2026-03-29-mainline-delivery-summary.md docs/开发计划.md
git commit -m "docs: capture delivery baseline"
```

---

### Task 3: Align the PRD with shipped capability language

**Files:**
- Modify: `docs/PRD.md`
- Test: `docs/PRD.md`

- [ ] **Step 1: Update the product goal wording to match current shipped workflows**

In `docs/PRD.md`, replace this line in section 2.1:

```markdown
5. **高效线索管理**：提供Web后台进行线索查看、筛选、分配、跟进
```

with:

```markdown
5. **高效线索管理**：提供Web后台进行线索查看、筛选、批量操作、分配、跟进
```

- [ ] **Step 2: Update the RSS requirement wording to reflect RSSHub-backed WeChat support**

In `docs/PRD.md`, replace this table row:

```markdown
| RSSHub集成 | P1 | 支持RSSHub将微信公众号、微博等转为RSS |
```

with:

```markdown
| RSSHub集成 | P1 | 支持通过RSSHub接入微信公众号等可转RSS来源，当前已支持以 wechat 类型配置来源 |
```

- [ ] **Step 3: Add the current-page batch-action capability to the leads list requirements**

In the leads list section table, add this row directly after the existing筛选/搜索相关行:

```markdown
| 批量操作 | P1 | 支持对当前页线索执行批量状态更新、批量分配、批量删除 |
```

If the table already contains a line about batch operations, update that line instead of duplicating it.

- [ ] **Step 4: Review the PRD diff to ensure it only states shipped behavior**

Run:

```bash
git diff -- docs/PRD.md
```

Expected:

```text
Only wording changes for RSSHub-backed WeChat support and leads batch actions; no unrelated PRD rewrites.
```

- [ ] **Step 5: Commit the PRD alignment**

```bash
git add docs/PRD.md
git commit -m "docs: align prd with shipped features"
```

---

### Task 4: Align the technical design doc with current implementation facts

**Files:**
- Modify: `docs/技术方案设计.md`
- Test: `docs/技术方案设计.md`

- [ ] **Step 1: Update ingestion-layer wording to reflect the current supported source paths**

In `docs/技术方案设计.md`, replace the ingestion layer labels:

```text
│  │  新闻网站    │  │   RSS采集    │  │  微信公众号   │  │  社交媒体  │ │
│  │  (Scrapy)   │  │ (feedparser) │  │  (RSSHub)    │  │  (RSSHub)  │ │
```

with:

```text
│  │  新闻网站    │  │   RSS / 微信  │  │  微信公众号   │  │  社交媒体  │ │
│  │  (Scrapy)   │  │ (feedparser) │  │ (RSSHub来源) │  │  (规划中)  │ │
```

- [ ] **Step 2: Update the RSSHub tech-stack description so it does not overclaim social support**

Replace this row:

```markdown
| **RSSHub** | RSSHub | latest | 自建RSS转换服务 |
```

with:

```markdown
| **RSSHub** | RSSHub | latest | 为微信公众号等来源提供 RSS 转换接入能力 |
```

- [ ] **Step 3: Update the source table descriptions to reflect current source types**

Replace this line in the `data_sources` table definition comment block:

```sql
    type ENUM('news', 'rss', 'wechat', 'social') NOT NULL COMMENT '数据源类型',
```

with:

```sql
    type ENUM('news', 'rss', 'wechat', 'social') NOT NULL COMMENT '数据源类型（当前已验证 news、rss、wechat）',
```

- [ ] **Step 4: Review the technical design diff for scope control**

Run:

```bash
git diff -- docs/技术方案设计.md
```

Expected:

```text
Only factual wording alignment for current source support; no architecture redesign.
```

- [ ] **Step 5: Commit the technical-doc alignment**

```bash
git add docs/技术方案设计.md
git commit -m "docs: align technical design with current source support"
```

---

### Task 5: Final verification and wrap-up

**Files:**
- Modify: `web/package.json`
- Modify: `docs/PRD.md`
- Modify: `docs/开发计划.md`
- Modify: `docs/技术方案设计.md`
- Create: `docs/superpowers/release-notes/2026-03-29-mainline-delivery-summary.md`

- [ ] **Step 1: Run the final verification commands**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest
cd /Users/jarod/Dev/LeadMine/web && npm test
```

Expected:

```text
backend: 198 passed
frontend: 3 passed
```

- [ ] **Step 2: Review the final changed file list**

Run:

```bash
git diff --name-only HEAD~4..HEAD
```

Expected:

```text
web/package.json
docs/PRD.md
docs/开发计划.md
docs/技术方案设计.md
docs/superpowers/release-notes/2026-03-29-mainline-delivery-summary.md
```

If commit count differs from the exact `HEAD~4..HEAD` range, use `git status --short` and `git diff --name-only` to confirm the same file set before the final commit.

- [ ] **Step 3: Write the final working-tree summary for handoff**

Use this summary in the handoff note or PR body:

```markdown
## 本轮交付质量收口

- 前端新增标准 `npm test` 入口，统一现有 Vitest 回归验证方式。
- 固化前后端最小验证命令，降低后续交付前的确认成本。
- 新增一版可直接复用的中文主线交付说明。
- 修正文档中与当前已交付能力不一致的描述，使 PRD、开发计划、技术方案与现状对齐。
```

- [ ] **Step 4: Commit the final documentation sweep if anything remains unstaged**

```bash
git add web/package.json docs/PRD.md docs/开发计划.md docs/技术方案设计.md docs/superpowers/release-notes/2026-03-29-mainline-delivery-summary.md
git commit -m "docs: finalize delivery quality baseline"
```

Skip this step only if the working tree is already clean because every earlier task commit has been created exactly as written.
