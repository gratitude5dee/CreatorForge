from src.storage.db import Database
from src.storage.repository import Repository


def test_idempotent_audit_and_ad_events(tmp_path):
    db = Database(str(tmp_path / "repo.db"))
    db.initialize()
    repo = Repository(db)

    audit_one = repo.record_audit_event(
        "trace-1",
        "ceo",
        "request_received",
        {"buyer": "buyer-1"},
        idempotency_key="audit-key",
    )
    audit_two = repo.record_audit_event(
        "trace-1",
        "ceo",
        "request_received",
        {"buyer": "buyer-1"},
        idempotency_key="audit-key",
    )
    ad_one = repo.record_ad_event(
        "trace-1",
        "considered",
        "zeroclick",
        {"idempotency_key": "ad-key", "slot": "slot-1"},
    )
    ad_two = repo.record_ad_event(
        "trace-1",
        "considered",
        "zeroclick",
        {"idempotency_key": "ad-key", "slot": "slot-1"},
    )

    assert audit_one == audit_two
    assert ad_one == ad_two
    assert len(db.fetchall("SELECT * FROM audit_events")) == 1
    assert len(db.fetchall("SELECT * FROM ad_events")) == 1
