from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from typing import List, Optional
from datetime import datetime, timedelta
import csv
import io

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Lead, LeadStatusEnum, LeadEventTypeEnum, User
from app.schemas import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    PaginatedResponse,
    DashboardResponse,
    LeadsByType,
)

router = APIRouter(prefix="/leads", tags=["线索管理"])


@router.get("", response_model=PaginatedResponse)
def get_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[LeadStatusEnum] = None,
    event_type: Optional[LeadEventTypeEnum] = None,
    keyword: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取线索列表"""
    query = db.query(Lead)

    # 筛选条件
    if status:
        query = query.filter(Lead.status == status)
    if event_type:
        query = query.filter(Lead.event_type == event_type)
    if keyword:
        query = query.filter(Lead.company_name.contains(keyword))
    if start_date:
        query = query.filter(Lead.published_at >= start_date)
    if end_date:
        query = query.filter(Lead.published_at <= end_date)

    # 总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    leads = query.order_by(desc(Lead.created_at)).offset(offset).limit(page_size).all()

    return {"total": total, "page": page, "page_size": page_size, "data": leads}


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取线索详情"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    return lead


@router.post("", response_model=LeadResponse, status_code=201)
def create_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建线索"""
    lead = Lead(**lead_data.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)

    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新线索"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    # 更新字段
    update_data = lead_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)

    return lead


@router.delete("/{lead_id}", status_code=204)
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除线索"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    db.delete(lead)
    db.commit()

    return None


@router.get("/stats/dashboard", response_model=DashboardResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """获取仪表盘统计数据"""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    # 统计各时间段的线索数
    today_leads = db.query(Lead).filter(Lead.created_at >= today_start).count()
    week_leads = db.query(Lead).filter(Lead.created_at >= week_start).count()
    month_leads = db.query(Lead).filter(Lead.created_at >= month_start).count()
    total_leads = db.query(Lead).count()

    # 按类型统计
    leads_by_type = {}
    for event_type in LeadEventTypeEnum:
        count = db.query(Lead).filter(Lead.event_type == event_type).count()
        leads_by_type[event_type.value] = count

    # 按来源统计
    sources = (
        db.query(Lead.source_name, func.count(Lead.id)).group_by(Lead.source_name).all()
    )
    leads_by_source = {source: count for source, count in sources}

    # 最近线索
    recent_leads = db.query(Lead).order_by(desc(Lead.created_at)).limit(5).all()

    return {
        "today_leads": today_leads,
        "week_leads": week_leads,
        "month_leads": month_leads,
        "total_leads": total_leads,
        "leads_by_type": leads_by_type,
        "leads_by_source": leads_by_source,
        "recent_leads": recent_leads,
    }


@router.get("/export")
def export_leads(
    format: str = Query("csv", regex="^(csv|excel)$"),
    status: Optional[LeadStatusEnum] = None,
    event_type: Optional[LeadEventTypeEnum] = None,
    keyword: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出线索"""
    query = db.query(Lead)

    if status:
        query = query.filter(Lead.status == status)
    if event_type:
        query = query.filter(Lead.event_type == event_type)
    if keyword:
        query = query.filter(Lead.company_name.contains(keyword))
    if start_date:
        query = query.filter(Lead.published_at >= start_date)
    if end_date:
        query = query.filter(Lead.published_at <= end_date)

    leads = query.order_by(desc(Lead.created_at)).all()

    # 生成CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # 写入表头
    writer.writerow(
        [
            "ID",
            "企业名称",
            "事件类型",
            "事件详情",
            "涉及金额",
            "来源",
            "发布时间",
            "置信度",
            "状态",
            "分配给",
            "创建时间",
        ]
    )

    # 写入数据
    for lead in leads:
        writer.writerow(
            [
                lead.id,
                lead.company_name,
                lead.event_type.value,
                lead.event_detail or "",
                lead.event_amount or "",
                lead.source_name or "",
                lead.published_at.strftime("%Y-%m-%d %H:%M")
                if lead.published_at
                else "",
                lead.confidence,
                lead.status.value,
                lead.assigned_to or "",
                lead.created_at.strftime("%Y-%m-%d %H:%M") if lead.created_at else "",
            ]
        )

    output.seek(0)

    filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/batch/update-status")
def batch_update_status(
    lead_ids: List[int],
    status: LeadStatusEnum,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量更新线索状态"""
    updated_count = (
        db.query(Lead)
        .filter(Lead.id.in_(lead_ids))
        .update(
            {Lead.status: status, Lead.updated_at: datetime.now()},
            synchronize_session=False,
        )
    )
    db.commit()

    return {
        "message": f"成功更新 {updated_count} 条线索",
        "updated_count": updated_count,
    }


@router.post("/batch/assign")
def batch_assign(
    lead_ids: List[int],
    assigned_to: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量分配线索"""
    updated_count = (
        db.query(Lead)
        .filter(Lead.id.in_(lead_ids))
        .update(
            {Lead.assigned_to: assigned_to, Lead.updated_at: datetime.now()},
            synchronize_session=False,
        )
    )
    db.commit()

    return {
        "message": f"成功分配 {updated_count} 条线索",
        "updated_count": updated_count,
    }


@router.post("/batch/delete")
def batch_delete(
    lead_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量删除线索"""
    deleted_count = (
        db.query(Lead).filter(Lead.id.in_(lead_ids)).delete(synchronize_session=False)
    )
    db.commit()

    return {
        "message": f"成功删除 {deleted_count} 条线索",
        "deleted_count": deleted_count,
    }
