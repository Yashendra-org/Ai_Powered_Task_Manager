# Horizontal Scaling & 100M+ (10 Crore) User Architecture Blueprint

## What Is Built Into the Application Codebase
1. **Stateless Multi-Pod Web Tier (`gunicorn.conf.py`, `config/settings.py`)**:
   - Thread-pooled Gunicorn workers (`gthread`) with `max_requests=2000` worker recycling.
   - `cached_db` session store backed by Redis Cluster (`USE_REDIS_CACHE=True`) for sub-millisecond session reads.
2. **Distributed Rate Limiting (`config/middleware.py`)**:
   - Shared Redis cache counters (`rl:<key>:<bucket>`) enforce identical IP + per-account limits across all auto-scaled pods, with bounded LRU local fallback.
3. **Database Query-Splitting & Composite Indexes (`config/db_router.py`, `models.py`)**:
   - `PrimaryReplicaRouter` sends read traffic (`analytics`, `tasks`, `habits`, `assignments`, `notes`, `reminders`) to `DATABASE_READ_REPLICA_URL` while keeping all writes/migrations on `default`.
   - `USE_PGBOUNCER=True` configures transaction pooling (`CONN_MAX_AGE=0`, `DISABLE_SERVER_SIDE_CURSORS=True`).
   - Composite indexes deployed on hot user/status/date query paths (`idx_task_user_del_due`, `idx_task_user_del_stat`, `idx_habit_user_active`, `idx_hlog_habit_stat_date`, `idx_assign_user_stat_due`, `idx_audit_user_created`).
4. **Zero-N+1 SQL Aggregation & API Pagination (`apps/analytics/views.py`, `apps/api/views.py`, `config/views.py`)**:
   - Batched 1-query habit streak calculation (`Habit.compute_streaks_for_habits`).
   - Single-pass `TruncDate` / `Count` SQL aggregations with short-TTL Redis caching.
   - Offset/limit API pagination capped at `100` records per response (`?limit=50&offset=0`).
5. **Constant-Memory Streaming Exports (`apps/accounts/views.py`, `apps/habits/views.py`)**:
   - JSON, CSV, and RFC 5545 `.ics` exports stream chunks via `StreamingHttpResponse` + `.iterator(chunk_size=1000)`.
6. **Cloud Object Storage Ready (`config/settings.py`)**:
   - Set `USE_S3_STORAGE=True` with `django-storages` credentials to store user attachments on S3 / Cloudflare R2 instead of container disk.

---

## Required Cloud Infrastructure for 10 Crore Concurrent Users
Application code alone is only half of planetary-scale engineering; deploying to **100M+ concurrent users** requires provisioning the following external infrastructure and setting the environment flags:

| Layer | Infrastructure Component | Required Environment Config |
| :--- | :--- | :--- |
| **Edge / WAF / Static** | Cloudflare CDN + WAF + DDoS Protection | Static `/static/` & `/media/` offloaded to CDN |
| **Load Balancing** | Multi-Region Kubernetes Ingress / Envoy + HPA | `TRUST_PROXY_HEADERS=True`, `ALLOWED_HOSTS=<domain>` |
| **Distributed Cache** | Redis Cluster (Sentinel / Multi-Shard) | `USE_REDIS_CACHE=True`, `REDIS_URL=rediss://...` |
| **Primary + Sharded DB** | PostgreSQL 16 (Patroni HA + Citus Sharding by `user_id`) + Read Replicas + PgBouncer | `DATABASE_URL=...`, `DATABASE_READ_REPLICA_URL=...`, `USE_PGBOUNCER=True` |
| **Object Storage** | Amazon S3 or Cloudflare R2 | `USE_S3_STORAGE=True` |
| **Async Workers** | Horizontally scaled Celery Workers + Beat | `CELERY_BROKER_URL=rediss://...`, `CELERY_TASK_ALWAYS_EAGER=False` |
| **Secrets & TLS** | Secrets Manager (Vault / AWS KMS) | Unique high-entropy `SECRET_KEY`, `DEBUG=False` |
