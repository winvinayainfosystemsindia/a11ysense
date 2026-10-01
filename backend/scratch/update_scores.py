import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common.database.connection import get_session_local
from common.database.models import AuditSession

db = get_session_local()()
sessions = db.query(AuditSession).all()
for s in sessions:
    if s.summary:
        summary = dict(s.summary)
        passes = summary.get('passes_count', 0)
        viols = summary.get('total_violations', 0)
        tot = passes + viols
        if tot > 0:
            new_score = round((passes / tot) * 100, 1)
            print(f"Updating task {s.task_id}: old score={summary.get('accessibility_score')}, new score={new_score}")
            summary['accessibility_score'] = new_score
            s.summary = summary
db.commit()
db.close()
print("Done updating audit session summaries in DB.")
