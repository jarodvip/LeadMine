# Coverage Uplift Spec

- User request: "覆盖率定向提升"
- Scope: backend test coverage, with priority on `backend/app/api/resources.py` and `backend/app/services/processor.py`
- Constraints:
  - Keep existing behavior unchanged unless tests reveal true defects
  - Prefer minimal, focused changes
  - Full backend suite must remain green
