"""
Primary / Read-Replica Database Router for High-Scale Read Splitting.
Routes read queries to 'read_replica' when DATABASE_READ_REPLICA_URL is configured,
while keeping writes and migrations strictly on 'default' (Primary Leader).
"""
from django.conf import settings


class PrimaryReplicaRouter:
    """
    Automatic Read/Write DB router (Pillar 1, #3).
    Falls back seamlessly to 'default' if no replica is configured.
    """
    def _has_replica(self) -> bool:
        return "read_replica" in settings.DATABASES

    def db_for_read(self, model, **hints):
        # Never route auth/session mutations or immediately-consistent reads during tests
        if not self._has_replica():
            return "default"
        # Analytics, history, tasks, habits, notes, assignments read queries scale horizontally on replicas
        if model._meta.app_label in ("analytics", "tasks", "habits", "assignments", "notes", "reminders"):
            return "read_replica"
        return "default"

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        db_set = {"default", "read_replica"}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == "default"
