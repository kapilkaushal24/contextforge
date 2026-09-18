# System Overview — High-Level, Component, and Data Flow Architecture

## 1. High-level architecture

```mermaid
flowchart TB
    subgraph Browser["Chrome Browser"]
        CS["Content Script<br/>(platform adapters)"]
        BG["Background Service Worker"]
        POPUP["Popup / Options UI<br/>(React)"]
    end

    subgraph Edge["API Gateway"]
        GW["Auth, rate limiting, routing"]
    end

    subgraph API["Optimization Service (FastAPI)"]
        CA["Content Analyzer"]
        TE["Token Estimator"]
        RD["Redundancy Detector"]
        OE["Optimization Engine"]
        SV["Semantic Validator"]
        MR["Model Router"]
    end

    subgraph Models["Model Layer"]
        LOCAL["Local / Deterministic Models"]
        CLOUD["Cloud LLM Providers"]
    end

    subgraph Data["Data Layer"]
        PG[(PostgreSQL)]
        RS[(Redis Cache)]
    end

    CS -->|extracted prompt| BG
    BG -->|HTTPS| GW
    GW --> API
    CA --> TE --> RD --> OE --> MR
    MR --> LOCAL
    MR --> CLOUD
    OE --> SV
    SV -->|result| GW
    GW -->|optimized prompt + metrics| BG
    BG --> CS
    POPUP -->|read stats| GW
    API -.->|metrics only, no raw prompt by default| PG
    API <-->|cache tokenization/policy| RS
```

## 2. Component architecture

| Component | Responsibility | Replaceable independently? |
|---|---|---|
| Platform Adapter | DOM detection/insertion for one AI site | Yes — isolated per adapter |
| Content Script | Wires adapter to extension messaging | No (thin glue) |
| Background Service Worker | Auth, API calls, cross-tab state | Partially |
| Popup/Options UI | User-facing controls & dashboard | Yes (pure UI) |
| Content Analyzer | Classifies prompt type (code/doc/chat/etc.) | Yes |
| Token Estimator | Provider-specific token counting | Yes, via `ITokenizer` |
| Redundancy Detector | Deterministic dedup/compression | Yes |
| Optimization Engine | Orchestrates strategies A–F | Yes, via `IOptimizationStrategy` |
| Semantic Validator | Confidence scoring pre-apply | Yes |
| Model Router | Chooses local vs cloud optimizer | Yes |
| Provider Adapters | Talk to OpenAI/Anthropic/Gemini/local | Yes, via `IAIProvider` |

## 3. Data flow (single optimization request)

```mermaid
sequenceDiagram
    participant U as User
    participant CS as Content Script
    participant BG as Background Worker
    participant API as Optimization API
    participant MR as Model Router
    participant M as Model (local/cloud)

    U->>CS: types prompt
    CS->>BG: extracted text + platform id
    BG->>API: POST /api/v1/optimize (mode, text, platform)
    API->>API: classify + estimate tokens
    API->>API: deterministic redundancy pass
    alt deterministic sufficient
        API-->>BG: optimized result (no LLM call)
    else needs semantic compression
        API->>MR: route(prompt_type, mode, privacy_policy)
        MR->>M: optimize(text)
        M-->>MR: candidate optimized text
        MR->>API: candidate
        API->>API: semantic validation + confidence score
        API-->>BG: optimized result + confidence
    end
    BG-->>CS: result
    CS-->>U: preview (accept/reject/undo)
```

## 4. Key architectural principle

The **cheapest safe transformation wins**: deterministic compression is tried first; an LLM
call only happens when deterministic/structural optimization is insufficient and the estimated
token savings justify the added latency/cost (see cost-optimization rule in
[docs/product/mvp-scope.md](../product/mvp-scope.md)).
