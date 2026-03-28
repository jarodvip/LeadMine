# 2026-03-28 WeChat RSSHub Ingestion Design

## Summary

Implement `wechat` data sources as a business-facing alias for RSSHub-backed RSS ingestion. Users will keep selecting `wechat` as the source type, but backend crawling will reuse the existing `RSSParser` path. This fixes the current mismatch where `wechat` is exposed in the schema/UI but is not supported by the crawler factory.

## Goal

Make `wechat` data sources actually crawlable with the smallest safe change.

## Non-goals

- Do not auto-generate RSSHub URLs from公众号 ID.
- Do not add a new dedicated WeChat crawler.
- Do not redesign the source management UI.
- Do not introduce new scheduler or processing architecture.

## Current Problem

Current state in the repo:
- `wechat` is a valid `SourceTypeEnum` value and is accepted by source schemas.
- The sources UI allows users to choose `wechat`.
- `SpiderFactory.crawl_source()` only supports `news` and `rss`.
- As a result, a saved `wechat` source cannot be crawled and falls into the unsupported-type path.

## Proposed Design

### 1. Preserve `wechat` as a first-class source type

Keep `DataSource.type = wechat` unchanged in storage, API responses, and UI.

Why:
- It preserves product semantics.
- It allows future reporting/filtering to distinguish WeChat sources from generic RSS sources.
- It avoids collapsing business meaning into implementation detail.

### 2. Reuse `RSSParser` for `wechat`

Update crawler dispatch so both `rss` and `wechat` use `RSSParser`.

Behavior:
- `news` continues to use dedicated spiders.
- `rss` continues to use `RSSParser`.
- `wechat` also uses `RSSParser`.
- Other source types remain unsupported for now.

This makes `wechat` a semantic alias over an existing ingestion path, not a new crawler type.

### 3. Preserve article source type during parsing

`RSSParser` currently emits parsed articles with `source_type = "rss"`.

Update parsing so the emitted article source type reflects the configured source type:
- `rss` source => parsed article `source_type = rss`
- `wechat` source => parsed article `source_type = wechat`

Why:
- Downstream filtering, analytics, and display should reflect the original source classification.
- Without this, all WeChat-ingested articles become indistinguishable from normal RSS articles.

### 4. Input contract

For this iteration, `wechat` sources must provide a complete RSSHub URL in the existing `url` field.

Example shape:
- type: `wechat`
- url: full RSSHub feed URL

The system will not derive or validate公众号 ID structure beyond existing fetch/parse behavior.

### 5. Error handling

Use the same behavior as current RSS ingestion:
- Missing URL => parser returns empty result / warning path
- Request failure => parser logs error and returns empty list
- Invalid feed => parser logs error and returns empty list

No new error surface is introduced in this iteration.

## Files Expected to Change

### Backend
- `backend/scrapers/spider_factory.py`
  - Route `wechat` to `RSSParser`
- `backend/app/processors/rss_parser.py`
  - Derive emitted `source_type` from input config instead of hardcoding `rss`

### Tests
Update focused regression coverage in:
- `backend/tests/scrapers/test_spider_factory.py`
  - Verify `wechat` dispatches through `RSSParser`
- `backend/tests/processors/test_rss_parser.py`
  - Verify parsed articles preserve configured `source_type`
- `backend/tests/api/test_resources.py`
  - Verify a stored `wechat` source can be triggered through the normal crawl workflow

### Explicitly unchanged in this iteration
- `backend/app/api/resources.py`
- `backend/app/services/scheduler.py`
- `backend/app/services/article_service.py`
- `backend/app/models/models.py`
- `web/src/views/Sources.vue`

These files already support the approved design or are intentionally left unchanged for the minimal fix.

## Testing Strategy

### Automated
Add focused regression coverage for:
1. `SpiderFactory.crawl_source()` accepts `wechat` and reuses the RSS parser path.
2. `RSSParser._parse_entry()` preserves `source_type = wechat` when the source config type is `wechat`.
3. `POST /api/v1/sources/{id}/crawl` succeeds for enabled `wechat` sources through the existing scheduler/article ingestion workflow.

### Manual
Smoke test:
1. Create a `wechat` data source with a valid RSSHub URL.
2. Trigger `/api/v1/sources/{id}/crawl`.
3. Confirm crawl completes without unsupported-type failure.
4. Confirm created articles are stored with `source_type = wechat`.
5. Confirm no WeChat-specific API or scheduler branch was needed for the flow to succeed.

## Trade-offs

### Benefits
- Smallest viable change
- Reuses stable existing code
- Fixes a real user-visible gap quickly
- Preserves future flexibility for a dedicated WeChat path later

### Limitations
- Requires users to know and paste a full RSSHub URL
- No special validation or URL generation help
- Still depends on RSSHub feed quality and availability

## Alternatives Considered

### A. Auto-generate RSSHub URLs from公众号 ID
Rejected for now because it adds input parsing, validation, and more UI/API decisions than needed for the first usable version.

### B. Treat WeChat as plain `rss`
Rejected because it loses the business distinction between generic RSS and WeChat sources.

### C. Build a dedicated WeChat crawler
Rejected because it is much larger in scope and unnecessary when RSSHub is already the intended mechanism.

## Rollout Result

After this change:
- Users can continue selecting `wechat` in the source UI.
- `wechat` sources become crawlable immediately if they use a valid RSSHub URL.
- Resulting articles keep `wechat` classification through ingestion.

## Out of Scope Follow-up

Possible next iteration after this design:
- Add optional RSSHub URL helper/generator in the UI
- Add WeChat-specific URL validation
- Add source-level help text/examples for RSSHub usage
