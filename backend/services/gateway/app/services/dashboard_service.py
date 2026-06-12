from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from common.database.models import User
from app.repository.dashboard_repo import dashboard_repo

class DashboardService:
    def list_all_audits(self, current_user: User, db: Session) -> list:
        org_id = current_user.organization_id
        sessions = dashboard_repo.list_audits(db, org_id)

        results = []
        for s in sessions:
            results.append({
                "task_id": s.task_id,
                "url": s.url,
                "timestamp": s.timestamp.isoformat(),
                "status": s.status,
                "accessibility_score": s.summary.get("accessibility_score", 100.0) if s.summary else 100.0,
                "total_violations": s.summary.get("total_violations", 0) if s.summary else 0,
                "project_name": s.project.name if s.project else "Default Project"
            })
        return results

    def get_dashboard_stats(self, time_range: str, current_user: User, db: Session) -> dict:
        org_id = current_user.organization_id
        since = None
        if time_range == "24h":
            since = datetime.utcnow() - timedelta(hours=24)
        elif time_range == "7d":
            since = datetime.utcnow() - timedelta(days=7)
        elif time_range == "30d":
            since = datetime.utcnow() - timedelta(days=30)

        sessions = dashboard_repo.get_sessions_by_timerange(db, org_id, since)

        total_audits = len(sessions)
        completed_audits = [s for s in sessions if s.status == "completed"]
        failed_audits = [s for s in sessions if s.status == "failed"]
        active_audits = [s for s in sessions if s.status not in ["completed", "failed"]]

        # Average accessibility score across completed audits
        avg_score = 100.0
        if completed_audits:
            total_score = 0.0
            valid_scores = 0
            for s in completed_audits:
                if s.summary and "accessibility_score" in s.summary:
                    total_score += float(s.summary["accessibility_score"])
                    valid_scores += 1
            if valid_scores > 0:
                avg_score = round(total_score / valid_scores, 1)

        # Violation impact breakdown
        total_violations = 0
        impact_counts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
        for s in completed_audits:
            if s.summary:
                total_violations += s.summary.get("total_violations", 0)
                breakdown = s.summary.get("violations_by_impact", {})
                for impact, count in breakdown.items():
                    imp = impact.lower()
                    if imp in impact_counts:
                        impact_counts[imp] += count
                    else:
                        impact_counts[imp] = impact_counts.get(imp, 0) + count

        # Total LLM token usage across organization
        total_tokens_used = 0
        for s in completed_audits:
            if s.summary and "token_usage" in s.summary:
                total_tokens_used += s.summary["token_usage"].get("tokens_total", 0)

        recent_sessions = []
        for s in sessions[:10]:
            recent_sessions.append({
                "task_id": s.task_id,
                "url": s.url,
                "timestamp": s.timestamp.isoformat(),
                "status": s.status,
                "accessibility_score": s.summary.get("accessibility_score", 100.0) if s.summary else 100.0,
                "total_violations": s.summary.get("total_violations", 0) if s.summary else 0,
                "project_name": s.project.name if s.project else "Default Project"
            })

        return {
            "total_audits": total_audits,
            "completed_audits_count": len(completed_audits),
            "failed_audits_count": len(failed_audits),
            "active_audits_count": len(active_audits),
            "average_score": avg_score,
            "total_violations": total_violations,
            "violations_by_impact": impact_counts,
            "total_tokens_used": total_tokens_used,
            "recent_audits": recent_sessions
        }

    def get_historical_trends(self, time_range: str, current_user: User, db: Session) -> dict:
        org_id = current_user.organization_id
        since = None
        if time_range == "24h":
            since = datetime.utcnow() - timedelta(hours=24)
        elif time_range == "7d":
            since = datetime.utcnow() - timedelta(days=7)
        elif time_range == "30d":
            since = datetime.utcnow() - timedelta(days=30)

        sessions = dashboard_repo.get_completed_sessions_by_timerange(db, org_id, since)

        score_trend = []
        violation_trend = []

        for s in sessions:
            date_str = s.timestamp.strftime("%Y-%m-%d %H:%M")
            score = s.summary.get("accessibility_score", 100.0) if s.summary else 100.0
            violations = s.summary.get("total_violations", 0) if s.summary else 0

            score_trend.append({"date": date_str, "score": score, "url": s.url})
            violation_trend.append({"date": date_str, "violations": violations, "url": s.url})

        return {
            "score_trend": score_trend,
            "violation_trend": violation_trend
        }

dashboard_service = DashboardService()
