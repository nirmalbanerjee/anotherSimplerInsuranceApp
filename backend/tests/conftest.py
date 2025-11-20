import logging
import re

_records = []

class RequestEndFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, str) and 'request.end' in record.msg:
            _records.append(record)
        return True

logging.getLogger('insurance').addFilter(RequestEndFilter())

# Pytest hook to print summary

def pytest_sessionfinish(session, exitstatus):
    if not _records:
        print("\n[request summary] no request.end records captured")
        return
    total = len(_records)
    errors = sum(1 for r in _records if r.levelno >= logging.ERROR)
    avg_ms = int(sum(getattr(r, 'duration_ms', 0) for r in _records) / max(total,1))
    print(f"\n[request summary] total={total} errors={errors} avg_duration_ms={avg_ms}")
