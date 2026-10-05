from ..models.progress_report import ProgressReport
from .base import Repository


class ProgressReportRepository(Repository):
    def for_assignment(self, assignment_id: int, *, offset: int = 0, limit: int = 100) -> list[ProgressReport]:
        return self.list(ProgressReport, assignment_id=assignment_id, offset=offset, limit=limit)