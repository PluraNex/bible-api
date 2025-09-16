from prometheus_client import Counter, Gauge, Histogram, Info

# Build/Deploy info (populated once at startup)
BUILD_INFO = Info("bible_build_info", "Build/Deploy info")


# HTTP level metrics with business labels
REQUESTS = Counter(
    "bible_http_requests_total",
    "Bible API HTTP requests with business labels",
    ["method", "status", "view", "lang", "version"],
)

LATENCY = Histogram(
    "bible_http_request_latency_seconds",
    "Bible API HTTP request latency with business labels",
    ["view", "lang", "version"],
    buckets=[0.05, 0.1, 0.2, 0.3, 0.5, 1, 2, 5],
)


# Optional business metrics (placeholders; to be updated by business logic)
BIBLE_VERSES_SERVED = Counter(
    "bible_verses_served_total",
    "Served verses by book/chapter/verse/version/lang",
    ["book", "chapter", "verse", "version", "lang"],
)

INDEX_BUILDS = Gauge(
    "inprogress_index_builds",
    "Number of indexes/build tasks in progress",
)

# RAG metrics
RAG_RETRIEVE_TOTAL = Counter(
    "rag_retrieve_total",
    "Total RAG retrieval requests",
    ["status", "version", "lang"],
)

RAG_RETRIEVE_LATENCY = Histogram(
    "rag_retrieve_latency_seconds",
    "Latency of RAG retrieval",
    ["version", "lang"],
    buckets=[0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 1, 2],
)
