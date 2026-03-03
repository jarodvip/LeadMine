"""
告警 API
"""

from fastapi import APIRouter, Depends
from typing import List, Dict

from app.core.security import get_current_user
from app.models import User
from app.services.alert import check_alerts, get_alerts

router = APIRouter(prefix="/alerts", tags=["告警"])


@router.get("", response_model=List[Dict])
def list_alerts(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
):
    """获取告警列表"""
    return get_alerts(limit)


@router.post("/check")
def trigger_check(
    current_user: User = Depends(get_current_user),
):
    """手动触发告警检查"""
    alerts = check_alerts()
    return {"alerts": alerts, "count": len(alerts)}
