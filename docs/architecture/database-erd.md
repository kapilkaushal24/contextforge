# Database ERD (conceptual)

```mermaid
erDiagram
    ORGANIZATION ||--o{ TEAM : has
    ORGANIZATION ||--o{ POLICY : defines
    ORGANIZATION ||--o{ AUDIT_LOG : generates
    TEAM ||--o{ USER : contains
    USER ||--o{ API_KEY : owns
    USER ||--o{ OPTIMIZATION_REQUEST : submits
    OPTIMIZATION_REQUEST ||--|| OPTIMIZATION_RESULT : produces
    OPTIMIZATION_REQUEST }o--|| AI_PROVIDER : "optionally routed to"
    AI_PROVIDER ||--o{ MODEL : offers
    OPTIMIZATION_REQUEST }o--|| MODEL : "used"
    OPTIMIZATION_RESULT ||--o{ OPTIMIZATION_METRIC : "rolls up into"
    ORGANIZATION ||--o{ POLICY : "applies to requests"

    ORGANIZATION {
        uuid id PK
        string name
        string plan_tier
        timestamptz created_at
    }
    TEAM {
        uuid id PK
        uuid organization_id FK
        string name
    }
    USER {
        uuid id PK
        uuid team_id FK
        string email
        string role
        timestamptz created_at
    }
    API_KEY {
        uuid id PK
        uuid user_id FK
        string key_hash
        timestamptz expires_at
        boolean revoked
    }
    OPTIMIZATION_REQUEST {
        uuid id PK
        uuid user_id FK
        string platform
        string optimization_mode
        int original_tokens
        boolean raw_text_stored
        text raw_text "nullable, encrypted, opt-in only"
        timestamptz created_at
    }
    OPTIMIZATION_RESULT {
        uuid id PK
        uuid request_id FK
        int optimized_tokens
        float reduction_percentage
        float confidence
        boolean applied_by_user
        jsonb changes
        timestamptz created_at
    }
    OPTIMIZATION_METRIC {
        uuid id PK
        uuid organization_id FK
        date bucket_date
        int total_requests
        int total_tokens_saved
        float avg_reduction_percentage
        float estimated_cost_saved
    }
    AI_PROVIDER {
        uuid id PK
        string name
        string status
    }
    MODEL {
        uuid id PK
        uuid provider_id FK
        string name
        numeric input_price_per_1k
        numeric output_price_per_1k
    }
    POLICY {
        uuid id PK
        uuid organization_id FK
        string name
        jsonb rules
        boolean enforce_local_only
    }
    AUDIT_LOG {
        uuid id PK
        uuid organization_id FK
        uuid actor_user_id FK
        string action
        jsonb metadata
        timestamptz created_at
    }
```

## Notes

- `OPTIMIZATION_REQUEST.raw_text` is nullable and only populated when `raw_text_stored = true`
  (opt-in per user/org policy); when stored, it is encrypted at the column level.
- `OPTIMIZATION_METRIC` is a pre-aggregated rollup table so the dashboard/analytics service
  never needs to scan raw request rows for common queries.
- Business logic never touches these tables directly — access goes through a repository layer
  in `services/optimization-service/app/infrastructure`.
- Migrations managed via Alembic (SQLAlchemy 2.x).
