import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

const routeState = vi.hoisted(() => ({
  query: {}
}))

const apiMocks = vi.hoisted(() => ({
  getList: vi.fn(),
  batchUpdateStatus: vi.fn(),
  batchAssign: vi.fn(),
  batchDelete: vi.fn(),
  exportLeads: vi.fn(),
  deleteLead: vi.fn()
}))

vi.mock('../../api', () => ({
  leadsAPI: {
    getList: apiMocks.getList,
    batchUpdateStatus: apiMocks.batchUpdateStatus,
    batchAssign: apiMocks.batchAssign,
    batchDelete: apiMocks.batchDelete,
    exportLeads: apiMocks.exportLeads,
    delete: apiMocks.deleteLead
  }
}))

vi.mock('vue-router', () => ({
  useRoute: () => routeState
}))

import Leads from '../Leads.vue'

const sampleLeads = [
  {
    id: 1,
    company_name: '测试公司A',
    event_type: 'financing',
    event_detail: '完成融资',
    source_name: '36氪',
    grade: 'A',
    score: 90,
    confidence: 85,
    status: 'new',
    published_at: '2026-03-28T00:00:00Z'
  },
  {
    id: 2,
    company_name: '测试公司B',
    event_type: 'product',
    event_detail: '发布新产品',
    source_name: '虎嗅',
    grade: 'B',
    score: 75,
    confidence: 72,
    status: 'contacted',
    published_at: '2026-03-27T00:00:00Z'
  }
]

const mountLeads = async () => {
  const wrapper = mount(Leads, {
    global: {
      stubs: {
        Layout: {
          template: '<div><slot /></div>'
        },
        RouterLink: {
          template: '<a><slot /></a>'
        }
      }
    }
  })

  await Promise.resolve()
  await nextTick()
  return wrapper
}

describe('Leads batch selection', () => {
  beforeEach(() => {
    routeState.query = {}
    apiMocks.getList.mockReset()
    apiMocks.batchUpdateStatus.mockReset()
    apiMocks.batchAssign.mockReset()
    apiMocks.batchDelete.mockReset()

    apiMocks.getList.mockResolvedValue({
      data: {
        data: sampleLeads,
        page: 1,
        page_size: 20,
        total: sampleLeads.length
      }
    })
  })

  it('uses route keyword on initial fetch', async () => {
    routeState.query = { keyword: '融资' }

    await mountLeads()

    expect(apiMocks.getList).toHaveBeenCalledTimes(1)
    expect(apiMocks.getList).toHaveBeenNthCalledWith(1, {
      page: 1,
      page_size: 20,
      keyword: '融资'
    })
  })

  it('shows batch actions after selecting leads from the list', async () => {
    const wrapper = await mountLeads()

    const checkboxes = wrapper.findAll('tbody input[type="checkbox"]')
    expect(checkboxes).toHaveLength(2)

    await checkboxes[0].setValue(true)
    await checkboxes[1].setValue(true)

    expect(wrapper.text()).toContain('已选择 2 条线索')
    expect(wrapper.text()).toContain('批量更新状态')
    expect(wrapper.text()).toContain('批量分配')
    expect(wrapper.text()).toContain('批量删除')
  })

  it('calls batch status API with selected lead ids', async () => {
    const promptSpy = vi.spyOn(window, 'prompt').mockReturnValue('contacted')
    apiMocks.batchUpdateStatus.mockResolvedValue({})

    const wrapper = await mountLeads()
    const checkboxes = wrapper.findAll('tbody input[type="checkbox"]')
    await checkboxes[0].setValue(true)
    await checkboxes[1].setValue(true)

    const batchStatusButton = wrapper.findAll('button').find(button => button.text() === '批量更新状态')
    await batchStatusButton.trigger('click')

    expect(apiMocks.batchUpdateStatus).toHaveBeenCalledWith([1, 2], 'contacted')

    promptSpy.mockRestore()
  })
})
