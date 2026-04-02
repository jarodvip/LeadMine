# Leads Efficiency Version Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a leads-efficiency release that strengthens list filtering/sorting, keeps export aligned with active filters, improves batch-action feedback, and adds minimal note/owner visibility without introducing a new subsystem.

**Architecture:** Extend the existing FastAPI leads endpoints and the single Vue leads list view instead of introducing new services or pages. Reuse the existing `Lead` fields (`status`, `assigned_to`, `sales_notes`, `published_at`, `confidence`) and keep the current-page batch-selection model. Frontend work stays in `web/src/views/Leads.vue` and `web/src/api/index.js`; backend work stays in `backend/app/api/leads.py`, existing Pydantic schemas, and API tests.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, Vue 3, axios, Vitest

---

## File Structure

- Modify: `backend/app/api/leads.py`
  - Add explicit source/sort filtering for list and export, reuse one filter-building path, and return clearer batch-operation summaries.
- Modify: `backend/app/schemas/__init__.py`
  - Extend batch response shape only if needed for explicit success counts/messages; keep existing lead update schema for notes and assignee edits.
- Modify: `backend/tests/api/test_leads.py`
  - Add regression coverage for source filtering, explicit sorting, export filter alignment, batch response payloads, and note updates.
- Modify: `web/src/api/index.js`
  - Make export return blob data and keep API helpers aligned with backend query params.
- Modify: `web/src/views/Leads.vue`
  - Add source and sort controls, assignee/note visibility, better batch feedback, and export parameter parity.
- Modify: `web/src/views/__tests__/Leads.test.js`
  - Add UI tests for filter param propagation, export param propagation, batch feedback, and minimal note editing flow.

---

### Task 1: Tighten backend list/export query behavior

**Files:**
- Modify: `backend/tests/api/test_leads.py`
- Modify: `backend/app/api/leads.py`
- Test: `backend/tests/api/test_leads.py`

- [ ] **Step 1: Write the failing API tests for source filtering, explicit sorting, and export parity**

Add these tests under `class TestLeadsList` and a new export test section in `backend/tests/api/test_leads.py`:

```python
    def test_get_leads_filter_by_source_name(self, client, auth_headers):
        client.post(
            "/api/v1/leads",
            json={
                "company_name": "来源公司A",
                "event_type": "financing",
                "source_name": "36氪",
                "confidence": 80,
            },
            headers=auth_headers,
        )
        client.post(
            "/api/v1/leads",
            json={
                "company_name": "来源公司B",
                "event_type": "product",
                "source_name": "虎嗅",
                "confidence": 60,
            },
            headers=auth_headers,
        )

        response = client.get("/api/v1/leads?source_name=36氪", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["source_name"] == "36氪"

    def test_get_leads_sort_by_published_at_asc(self, client, auth_headers):
        client.post(
            "/api/v1/leads",
            json={
                "company_name": "排序公司A",
                "event_type": "financing",
                "published_at": "2026-03-28T00:00:00",
                "confidence": 80,
            },
            headers=auth_headers,
        )
        client.post(
            "/api/v1/leads",
            json={
                "company_name": "排序公司B",
                "event_type": "financing",
                "published_at": "2026-03-29T00:00:00",
                "confidence": 80,
            },
            headers=auth_headers,
        )

        response = client.get(
            "/api/v1/leads?sort_by=published_at&sort_order=asc",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data[0]["company_name"] == "排序公司A"


class TestLeadExport:
    """测试线索导出接口"""

    def test_export_leads_respects_filters(self, client, auth_headers):
        client.post(
            "/api/v1/leads",
            json={
                "company_name": "导出公司A",
                "event_type": "financing",
                "source_name": "36氪",
                "confidence": 88,
            },
            headers=auth_headers,
        )
        client.post(
            "/api/v1/leads",
            json={
                "company_name": "导出公司B",
                "event_type": "product",
                "source_name": "虎嗅",
                "confidence": 70,
            },
            headers=auth_headers,
        )

        response = client.get(
            "/api/v1/leads/export?source_name=36氪&keyword=导出公司A",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        content = response.text
        assert "导出公司A" in content
        assert "导出公司B" not in content
```

- [ ] **Step 2: Run the targeted backend tests and verify they fail**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/api/test_leads.py -k "source_name or published_at_asc or export_leads_respects_filters" -v
```

Expected:

```text
FAILED tests/api/test_leads.py::TestLeadsList::test_get_leads_filter_by_source_name
FAILED tests/api/test_leads.py::TestLeadsList::test_get_leads_sort_by_published_at_asc
FAILED tests/api/test_leads.py::TestLeadExport::test_export_leads_respects_filters
```

- [ ] **Step 3: Implement shared filter/sort handling in the leads API**

Update `backend/app/api/leads.py` so `get_leads` and `export_leads` both support `source_name`, `sort_by`, and `sort_order`. Use this code pattern inside the file:

```python
ALLOWED_SORT_FIELDS = {
    "created_at": Lead.created_at,
    "published_at": Lead.published_at,
    "confidence": Lead.confidence,
}


def apply_lead_filters(
    query,
    *,
    status=None,
    event_type=None,
    confidence=None,
    keyword=None,
    source_name=None,
    start_date=None,
    end_date=None,
):
    if status:
        query = query.filter(Lead.status == status)
    if event_type:
        query = query.filter(Lead.event_type == event_type)
    if keyword:
        query = query.filter(Lead.company_name.contains(keyword))
    if source_name:
        query = query.filter(Lead.source_name == source_name)
    if start_date:
        query = query.filter(Lead.published_at >= start_date)
    if end_date:
        query = query.filter(Lead.published_at <= end_date)
    if confidence == "high":
        query = query.filter(Lead.confidence >= 70)
    elif confidence == "medium":
        query = query.filter(Lead.confidence >= 50, Lead.confidence < 70)
    elif confidence == "low":
        query = query.filter(Lead.confidence < 50)
    return query


def apply_lead_sorting(query, sort_by: str = "confidence", sort_order: str = "desc"):
    sort_column = ALLOWED_SORT_FIELDS.get(sort_by, Lead.confidence)
    if sort_order == "asc":
        return query.order_by(sort_column.asc(), Lead.created_at.desc())
    return query.order_by(sort_column.desc(), Lead.created_at.desc())
```

Then update `get_leads` signature and body to include:

```python
    source_name: Optional[str] = None,
    sort_by: str = Query("confidence", pattern="^(created_at|published_at|confidence)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
```

and replace the inline filter/order logic with:

```python
    query = apply_lead_filters(
        db.query(Lead),
        status=status,
        event_type=event_type,
        confidence=confidence,
        keyword=keyword,
        source_name=source_name,
        start_date=start_date,
        end_date=end_date,
    )
    total = query.count()
    offset = (page - 1) * page_size
    leads = apply_lead_sorting(query, sort_by=sort_by, sort_order=sort_order).offset(offset).limit(page_size).all()
```

Update `export_leads` signature to include `confidence`, `source_name`, `sort_by`, and `sort_order`, and replace its query logic with:

```python
    query = apply_lead_filters(
        db.query(Lead),
        status=status,
        event_type=event_type,
        confidence=confidence,
        keyword=keyword,
        source_name=source_name,
        start_date=start_date,
        end_date=end_date,
    )
    leads = apply_lead_sorting(query, sort_by=sort_by, sort_order=sort_order).all()
```

- [ ] **Step 4: Run the targeted backend tests and verify they pass**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/api/test_leads.py -k "source_name or published_at_asc or export_leads_respects_filters" -v
```

Expected:

```text
PASSED tests/api/test_leads.py::TestLeadsList::test_get_leads_filter_by_source_name
PASSED tests/api/test_leads.py::TestLeadsList::test_get_leads_sort_by_published_at_asc
PASSED tests/api/test_leads.py::TestLeadExport::test_export_leads_respects_filters
```

- [ ] **Step 5: Commit the backend query behavior change**

```bash
git add backend/app/api/leads.py backend/tests/api/test_leads.py
git commit -m "feat: align leads filters and export"
```

---

### Task 2: Add minimal note coverage and clearer batch response assertions

**Files:**
- Modify: `backend/tests/api/test_leads.py`
- Modify: `backend/app/api/leads.py`
- Modify: `backend/app/schemas/__init__.py`
- Test: `backend/tests/api/test_leads.py`

- [ ] **Step 1: Write the failing tests for note updates and batch response payloads**

Add these tests to `backend/tests/api/test_leads.py`:

```python
    def test_update_lead_sales_notes(self, client, auth_headers, sample_lead):
        response = client.patch(
            f"/api/v1/leads/{sample_lead['id']}",
            json={"sales_notes": "首轮电话沟通后下周继续跟进"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sales_notes"] == "首轮电话沟通后下周继续跟进"


class TestBatchOperations:
    def test_batch_update_status_returns_updated_count(self, client, auth_headers):
        leads = []
        for i in range(2):
            resp = client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"状态反馈公司{i}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )
            leads.append(resp.json()["id"])

        response = client.post(
            "/api/v1/leads/batch/update-status",
            json={"lead_ids": leads, "status": "contacted"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["updated_count"] == 2
        assert data["message"] == "成功更新 2 条线索状态"

    def test_batch_assign_returns_updated_count(self, client, auth_headers):
        leads = []
        for i in range(2):
            resp = client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"分配反馈公司{i}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )
            leads.append(resp.json()["id"])

        response = client.post(
            "/api/v1/leads/batch/assign",
            json={"lead_ids": leads, "assigned_to": "销售员B"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["updated_count"] == 2
        assert data["message"] == "成功分配 2 条线索"
```

- [ ] **Step 2: Run the targeted backend tests and verify any missing assertions fail**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/api/test_leads.py -k "sales_notes or returns_updated_count" -v
```

Expected:

```text
FAILED tests/api/test_leads.py::TestBatchOperations::test_batch_update_status_returns_updated_count
FAILED tests/api/test_leads.py::TestBatchOperations::test_batch_assign_returns_updated_count
```

- [ ] **Step 3: Implement explicit batch response messages using the existing response schema**

In `backend/app/api/leads.py`, update the two batch handlers to return deterministic payloads like this:

```python
    updated_count = query.update({Lead.status: request.status}, synchronize_session=False)
    db.commit()
    return {
        "message": f"成功更新 {updated_count} 条线索状态",
        "updated_count": updated_count,
    }
```

and:

```python
    updated_count = query.update({Lead.assigned_to: request.assigned_to}, synchronize_session=False)
    db.commit()
    return {
        "message": f"成功分配 {updated_count} 条线索",
        "updated_count": updated_count,
    }
```

Do not introduce a new schema unless the current `BatchOperationResponse` becomes insufficient.

- [ ] **Step 4: Run the targeted backend tests and verify they pass**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/api/test_leads.py -k "sales_notes or returns_updated_count" -v
```

Expected:

```text
PASSED tests/api/test_leads.py::TestLeadUpdate::test_update_lead_sales_notes
PASSED tests/api/test_leads.py::TestBatchOperations::test_batch_update_status_returns_updated_count
PASSED tests/api/test_leads.py::TestBatchOperations::test_batch_assign_returns_updated_count
```

- [ ] **Step 5: Commit the backend response and note regression coverage**

```bash
git add backend/app/api/leads.py backend/tests/api/test_leads.py backend/app/schemas/__init__.py
git commit -m "test: cover leads note and batch feedback"
```

---

### Task 3: Make frontend filters/export match backend capabilities

**Files:**
- Modify: `web/src/views/__tests__/Leads.test.js`
- Modify: `web/src/api/index.js`
- Modify: `web/src/views/Leads.vue`
- Test: `web/src/views/__tests__/Leads.test.js`

- [ ] **Step 1: Write the failing frontend tests for source/sort propagation and export params**

Append these tests to `web/src/views/__tests__/Leads.test.js`:

```javascript
  it('includes source and sort params when fetching leads', async () => {
    const wrapper = await mountLeads()

    const selects = wrapper.findAll('select')
    await selects[2].setValue('36氪')
    await selects[3].setValue('published_at_desc')

    expect(apiMocks.getList).toHaveBeenLastCalledWith({
      page: 1,
      page_size: 20,
      source_name: '36氪',
      sort_by: 'published_at',
      sort_order: 'desc'
    })
  })

  it('passes active filters to export API', async () => {
    apiMocks.exportLeads.mockResolvedValue({ data: new Blob(['csv']) })
    global.URL.createObjectURL = vi.fn(() => 'blob:test')
    global.URL.revokeObjectURL = vi.fn()

    const wrapper = await mountLeads()
    const selects = wrapper.findAll('select')
    await selects[0].setValue('new')
    await selects[2].setValue('36氪')

    const exportButton = wrapper.findAll('button').find(button => button.text() === '导出')
    await exportButton.trigger('click')

    expect(apiMocks.exportLeads).toHaveBeenCalledWith({
      status: 'new',
      source_name: '36氪'
    })
  })
```

- [ ] **Step 2: Run the targeted frontend tests and verify they fail**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/web && npm test -- --run web/src/views/__tests__/Leads.test.js
```

Expected:

```text
FAIL  web/src/views/__tests__/Leads.test.js
```

- [ ] **Step 3: Update the frontend API helper for blob export**

In `web/src/api/index.js`, change the export helper to:

```javascript
  exportLeads: (params) => api.get('/leads/export', {
    params,
    responseType: 'blob'
  }),
```

- [ ] **Step 4: Add source and sort filters to the leads view**

In `web/src/views/Leads.vue`, extend the reactive filter state:

```javascript
const filters = reactive({
  status: '',
  event_type: '',
  keyword: '',
  start_date: '',
  end_date: '',
  source_name: '',
  sort: 'confidence_desc'
})
```

Add these helpers in the script block:

```javascript
const sortOptions = {
  confidence_desc: { sort_by: 'confidence', sort_order: 'desc' },
  published_at_desc: { sort_by: 'published_at', sort_order: 'desc' },
  published_at_asc: { sort_by: 'published_at', sort_order: 'asc' },
  created_at_desc: { sort_by: 'created_at', sort_order: 'desc' }
}

const buildLeadParams = () => {
  const params = {
    page: pagination.value.page,
    page_size: pagination.value.page_size
  }

  if (filters.status) params.status = filters.status
  if (filters.event_type) params.event_type = filters.event_type
  if (filters.keyword) params.keyword = filters.keyword
  if (filters.start_date) params.start_date = filters.start_date
  if (filters.end_date) params.end_date = filters.end_date
  if (filters.source_name) params.source_name = filters.source_name

  Object.assign(params, sortOptions[filters.sort] || sortOptions.confidence_desc)
  return params
}
```

Replace the fetch params construction with:

```javascript
    const response = await leadsAPI.getList(buildLeadParams())
```

Replace export param construction with:

```javascript
    const params = buildLeadParams()
    delete params.page
    delete params.page_size
    const response = await leadsAPI.exportLeads(params)
```

Add two new selects in the filter bar template after the event type select:

```vue
        <select class="filter-select" v-model="filters.source_name" @change="fetchLeads">
          <option value="">全部来源</option>
          <option value="36氪">36氪</option>
          <option value="虎嗅">虎嗅</option>
        </select>
        <select class="filter-select" v-model="filters.sort" @change="fetchLeads">
          <option value="confidence_desc">按置信度</option>
          <option value="published_at_desc">最新发布时间</option>
          <option value="published_at_asc">最早发布时间</option>
          <option value="created_at_desc">最新创建时间</option>
        </select>
```

Update `resetFilters` to reset `source_name` and `sort`:

```javascript
  filters.source_name = ''
  filters.sort = 'confidence_desc'
```

- [ ] **Step 5: Run the targeted frontend tests and verify they pass**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/web && npm test -- --run web/src/views/__tests__/Leads.test.js
```

Expected:

```text
✓ web/src/views/__tests__/Leads.test.js
```

- [ ] **Step 6: Commit the frontend filter/export parity change**

```bash
git add web/src/api/index.js web/src/views/Leads.vue web/src/views/__tests__/Leads.test.js
git commit -m "feat: extend leads filters and export"
```

---

### Task 4: Surface assignee/notes and improve batch-action feedback in the list UI

**Files:**
- Modify: `web/src/views/__tests__/Leads.test.js`
- Modify: `web/src/views/Leads.vue`
- Test: `web/src/views/__tests__/Leads.test.js`

- [ ] **Step 1: Write the failing frontend tests for assignee visibility, note editing, and batch feedback alerts**

Add these tests to `web/src/views/__tests__/Leads.test.js`:

```javascript
  it('shows assigned owner in the list when present', async () => {
    apiMocks.getList.mockResolvedValueOnce({
      data: {
        data: [{ ...sampleLeads[0], assigned_to: '销售员A', sales_notes: '下周回访' }],
        page: 1,
        page_size: 20,
        total: 1
      }
    })

    const wrapper = await mountLeads()
    expect(wrapper.text()).toContain('销售员A')
    expect(wrapper.text()).toContain('下周回访')
  })

  it('updates notes for a single lead from the list', async () => {
    const promptSpy = vi.spyOn(window, 'prompt').mockReturnValue('记录首轮沟通结果')
    apiMocks.update = vi.fn().mockResolvedValue({})

    const wrapper = await mountLeads()
    const noteButton = wrapper.findAll('button').find(button => button.text() === '备注')
    await noteButton.trigger('click')

    expect(apiMocks.update).toHaveBeenCalledWith(1, { sales_notes: '记录首轮沟通结果' })
    promptSpy.mockRestore()
  })

  it('shows updated count after batch assign succeeds', async () => {
    const promptSpy = vi.spyOn(window, 'prompt').mockReturnValue('销售员A')
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    apiMocks.batchAssign.mockResolvedValue({ data: { updated_count: 2, message: '成功分配 2 条线索' } })

    const wrapper = await mountLeads()
    const checkboxes = wrapper.findAll('tbody input[type="checkbox"]')
    await checkboxes[0].setValue(true)
    await checkboxes[1].setValue(true)

    const assignButton = wrapper.findAll('button').find(button => button.text() === '批量分配')
    await assignButton.trigger('click')

    expect(alertSpy).toHaveBeenCalledWith('成功分配 2 条线索')
    promptSpy.mockRestore()
    alertSpy.mockRestore()
  })
```

Also update the mock definition at the top of the test file to include `update`:

```javascript
  update: vi.fn(),
```

and expose it in the mocked `leadsAPI` object:

```javascript
    update: apiMocks.update,
```

- [ ] **Step 2: Run the targeted frontend tests and verify they fail**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/web && npm test -- --run web/src/views/__tests__/Leads.test.js
```

Expected:

```text
FAIL  web/src/views/__tests__/Leads.test.js
```

- [ ] **Step 3: Add owner/note columns and list-level note editing**

In `web/src/views/Leads.vue`, add two columns before the action column:

```vue
                <th>负责人</th>
                <th>备注</th>
```

and render them in the row:

```vue
                <td>{{ lead.assigned_to || '-' }}</td>
                <td class="sales-notes">{{ lead.sales_notes || '-' }}</td>
```

Add a note action button next to the existing buttons:

```vue
                    <button class="action-btn" @click="editLeadNote(lead)">备注</button>
```

Add the handler in the script block:

```javascript
const editLeadNote = async (lead) => {
  const note = window.prompt('请输入跟进备注', lead.sales_notes || '')
  if (note === null) return

  try {
    await leadsAPI.update(lead.id, { sales_notes: note })
    await fetchLeads()
    alert('备注已更新')
  } catch (error) {
    alert('备注更新失败')
  }
}
```

Remember to increase the empty-row `colspan` from `12` to `14`.

- [ ] **Step 4: Show backend batch feedback messages in the UI**

Update the three batch handlers in `web/src/views/Leads.vue` to use response messages:

```javascript
    const response = await leadsAPI.batchUpdateStatus(selectedLeadIds.value, status)
    await fetchLeads()
    clearSelection()
    alert(response.data.message)
```

```javascript
    const response = await leadsAPI.batchAssign(selectedLeadIds.value, assignedTo)
    await fetchLeads()
    clearSelection()
    alert(response.data.message)
```

Keep delete behavior unchanged unless you choose to align it in the same style after tests pass.

- [ ] **Step 5: Run the targeted frontend tests and verify they pass**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/web && npm test -- --run web/src/views/__tests__/Leads.test.js
```

Expected:

```text
✓ web/src/views/__tests__/Leads.test.js
```

- [ ] **Step 6: Commit the list-efficiency UI change**

```bash
git add web/src/views/Leads.vue web/src/views/__tests__/Leads.test.js
git commit -m "feat: surface leads owner and notes"
```

---

### Task 5: Run the full verification baseline

**Files:**
- Test: `backend/tests/api/test_leads.py`
- Test: `web/src/views/__tests__/Leads.test.js`

- [ ] **Step 1: Run the backend leads API suite**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest tests/api/test_leads.py -v
```

Expected:

```text
... all leads API tests pass ...
```

- [ ] **Step 2: Run the frontend leads view suite**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/web && npm test -- --run web/src/views/__tests__/Leads.test.js
```

Expected:

```text
✓ web/src/views/__tests__/Leads.test.js
```

- [ ] **Step 3: Run the repository minimum verification commands**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && python3 -m pytest
cd /Users/jarod/Dev/LeadMine/web && npm test
```

Expected:

```text
backend: all tests pass
frontend: all tests pass
```

- [ ] **Step 4: Commit the final verification checkpoint**

```bash
git add backend/tests/api/test_leads.py web/src/views/__tests__/Leads.test.js
git commit -m "test: verify leads efficiency baseline"
```

---

## Self-Review

- **Spec coverage:**
  - P0 导出：Task 1 + Task 3
  - P0 批量状态/分配反馈：Task 2 + Task 4
  - P1 筛选/排序/source 维度：Task 1 + Task 3
  - P2 备注与负责人可见：Task 2 + Task 4
- **Placeholder scan:** no TBD/TODO placeholders remain.
- **Type consistency:** backend uses `source_name`, `sort_by`, `sort_order`, `sales_notes`, `assigned_to`; frontend plan uses the same names.
