import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from common.database.connection import get_session_local
from backend.app.repository.estimation_repo import estimation_repo
from backend.app.core.estimation.calculator import calculate_total_estimate

def test_estimation_persistence_and_crud():
    db = get_session_local()()
    try:
        sample_pages = [
            {
                "url": "https://test.example.com",
                "title": "Example Home",
                "complexity": "simple",
                "summary_rationale": "Static site",
                "triggers": ["Static content"],
                "counts": {
                    "links": 5, "buttons": 1, "headings": 2, "paragraphs": 4,
                    "lists": 0, "images": 1, "forms": 0, "inputs": 0,
                    "tables": 0, "media": 0, "total_elements": 13
                },
                "status": "success"
            },
            {
                "url": "https://test.example.com/checkout",
                "title": "Checkout Flow",
                "complexity": "complex",
                "summary_rationale": "Multi-step form wizard",
                "triggers": ["Form wizard"],
                "counts": {
                    "links": 12, "buttons": 8, "headings": 5, "paragraphs": 6,
                    "lists": 3, "images": 4, "forms": 2, "inputs": 10,
                    "tables": 1, "media": 0, "total_elements": 65
                },
                "status": "success"
            }
        ]

        # Calculate
        calc_res = calculate_total_estimate(
            sample_pages,
            hourly_rate=45.0,
            platform_fee_per_page=12.0,
            profit_margin_pct=35.0
        )

        assert calc_res["summary"]["total_pages"] == 2
        assert calc_res["summary"]["simple_pages"] == 1
        assert calc_res["summary"]["complex_pages"] == 1

        # 1. Create in DB
        created = estimation_repo.create_estimation(
            db=db,
            title="E-Commerce Audit Proposal",
            base_url="https://test.example.com",
            mode="discover",
            pages=calc_res["pages"],
            summary=calc_res["summary"],
            hourly_rate=45.0,
            platform_fee=12.0,
            profit_margin_pct=35.0
        )
        assert created.id is not None
        assert created.title == "E-Commerce Audit Proposal"
        assert created.total_pages == 2
        created_id = str(created.id)

        # 2. Get from DB
        fetched = estimation_repo.get_estimation(db, created_id)
        assert fetched is not None
        assert fetched.title == "E-Commerce Audit Proposal"
        assert len(fetched.pages) == 2

        # 3. List
        all_records = estimation_repo.list_estimations(db)
        assert any(str(r.id) == created_id for r in all_records)

        # 4. Update
        updated = estimation_repo.update_estimation(
            db=db,
            estimate_id=created_id,
            title="Updated E-Commerce Audit Proposal",
            hourly_rate=50.0
        )
        assert updated is not None
        assert updated.title == "Updated E-Commerce Audit Proposal"
        assert updated.hourly_rate == 50.0

        # 5. Delete
        deleted = estimation_repo.delete_estimation(db, created_id)
        assert deleted is True

        assert estimation_repo.get_estimation(db, created_id) is None
        print("Estimation persistence & CRUD tests passed successfully!")

    finally:
        db.close()


def test_discover_request_unlimited_pages():
    from backend.app.api.estimation import DiscoverRequest, EstimationRequest

    # Valid without max_pages (defaults to None -> unlimited)
    req = DiscoverRequest(url="https://example.com", depth=2)
    assert req.max_pages is None

    # Valid with explicit max_pages if provided
    req_with_limit = DiscoverRequest(url="https://example.com", depth=1, max_pages=50)
    assert req_with_limit.max_pages == 50

    # EstimationRequest without max_pages
    est_req = EstimationRequest(url="https://example.com", depth=2)
    assert est_req.max_pages is None


if __name__ == "__main__":
    test_estimation_persistence_and_crud()
    test_discover_request_unlimited_pages()
