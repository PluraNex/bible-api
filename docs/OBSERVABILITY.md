# Observabilidade — Bible API

Este documento descreve a stack completa de observabilidade do projeto, como executar em desenvolvimento, quais métricas e dashboards estão disponíveis, práticas de segurança e como estender a instrumentação para métricas de negócio.

## Componentes
- Prometheus (coletor de métricas)
  - Endpoint scrape: `GET /metrics/prometheus/` (formato Prometheus, via `django-prometheus`)
- Grafana (visualização de dashboards)
  - Provisionado com datasource Prometheus e dashboard “Bible API — Observability”
- Django + django-prometheus (instrumentação padrão)
  - Métricas HTTP, latência, DB, cache, processo
- Middleware de Observabilidade (custom)
  - Métricas com labels de negócio: `lang`, `version` e `view`
  - Arquivos: `common/observability/middleware.py`, `common/observability/metrics.py`

## Endpoints
- `GET /health/` — básico (JSON)
- `GET /health/liveness/` — liveness probe (200 quando processo está vivo)
- `GET /health/readiness/` — readiness probe (200 quando DB/Cache OK; 503 caso contrário)
- `GET /metrics/` — legado (JSON simples para smoke)
- `GET /metrics/prometheus/` — métricas Prometheus (para Prometheus/Grafana)

## Como rodar localmente
1) Subir stack base
```bash
make dev            # ou: docker-compose up -d web db redis
```
2) Subir Prometheus e Grafana
```bash
make prometheus-up  # Prometheus em http://localhost:9090
make grafana-up     # Grafana em http://localhost:3000 (admin/admin)
```
3) Verificar
```bash
curl -s http://localhost:8000/metrics/prometheus/ | head
open http://localhost:9090/targets
open http://localhost:3000
```

## Métricas Principais
Padrão (django-prometheus):
- `django_http_requests_total_by_method{method,status}`
- `django_http_requests_total_by_status{status}`
- `django_http_requests_latency_seconds_bucket{le}`
- `django_db_execute_total`, `django_db_connections_total`
- `django_cache_requests_total{operation}`
- `process_resident_memory_bytes`, `process_cpu_seconds_total`

Custom (middleware):
- `bible_http_requests_total{method,status,view,lang,version}`
- `bible_http_request_latency_seconds_bucket{view,lang,version,le}`
- `bible_build_info{service,version}` (Info)
- Placeholders de negócio: `bible_verses_served_total{book,chapter,verse,version,lang}`, `inprogress_index_builds`

## Dashboard (Grafana)
Arquivo: `grafana/dashboards/bible-api-dashboard.json`

Variáveis:
- `job` (default: bible-api)
- `instance` (múltipla, all por padrão)
- `lang`, `version`, `endpoint` (oriundas das métricas custom)

Seções e painéis chave:
- Overview: req/s, error rate, p95 (ms), scrape up
- HTTP Requests: por método e por status; inflight
- Latency: p50/p95/p99 + heatmap
- Database: QPS e conexões/s
- App Runtime: CPU e memória (RSS)
- Cache: requests por operação e hit ratio
- Views: Top views (req/s)
- Language & Versions:
  - Tráfego por idioma (sum por `lang`)
  - Error rate por idioma (%)
  - p95 por idioma (ms)
  - Endpoint p95 (top 10)
  - SLO burn (p95 > 300ms)
  - Hot verses (negócio) — depende de instrumentação `bible_verses_served_total`
  - Pre-warm/Indexes in progress — depende de `inprogress_index_builds`

## Segurança (desenvolvimento vs. produção)
- Credenciais padrão do Grafana (apenas DEV): `admin/admin`.
  - Em produção: defina `GF_SECURITY_ADMIN_PASSWORD` (via secrets) e desabilite provisionamento por volume, se necessário.
- `ALLOWED_HOSTS`: ampliado para scraping (hostnames Docker) somente quando `DEBUG=True` — sem impacto em produção.
- Exposição de métricas:
  - Restrinja `/metrics/prometheus/` a redes internas/seguras em produção (Ingress, IP allowlist ou mTLS).
  - Proteja Prometheus/Grafana atrás de autenticação (reverse proxy, OIDC/SAML) e TLS.
- Logs: evite PII/segredos; use `X-Request-ID` para correlação (vide `API_STANDARDS.md`).
- Recursos: defina limites de CPU/Mem em produção para Prometheus/Grafana; ajuste retenção de séries.

## Kubernetes (exemplo)
Liveness/Readiness probes:
```yaml
livenessProbe:
  httpGet: { path: /health/liveness/, port: 8000 }
  initialDelaySeconds: 10
  periodSeconds: 15
readinessProbe:
  httpGet: { path: /health/readiness/, port: 8000 }
  initialDelaySeconds: 15
  periodSeconds: 15
```
ServiceMonitor (Prometheus Operator) — ajuste selectors:
```yaml
spec:
  endpoints:
    - port: http
      path: /metrics/prometheus/
      interval: 15s
      scrapeTimeout: 10s
```

## Alertas (exemplos de regras)
HighErrorRate (5m):
```
( sum(rate(django_http_requests_total_by_status{status=~"5..",job=~"$job"}[5m]))
  / clamp_min(sum(rate(django_http_requests_total_by_method{job=~"$job"}[5m])), 1)
) > 0.02
```
P95LatencySLOBreach (10m):
```
1000 * histogram_quantile(0.95,
  sum by (le) (rate(django_http_requests_latency_seconds_bucket{job=~"$job"}[5m]))
) > 300
```
TargetDown (3m):
```
avg_over_time(up{job=~"$job"}[3m]) < 1
```

## Como estender a instrumentação
1) Métricas de negócio (ex.: versos servidos)
   - Incrementar `BIBLE_VERSES_SERVED.labels(book,chapter,verse,version,lang).inc()` nos pontos em que o verso é retornado (ex.: em views de Verses).
2) Métricas de cache/RAG
   - `RAG_CACHE_HITS/MISSES` (Counters), `INDEX_BUILDS` (Gauge) — ver exemplos em `common/observability/metrics.py`.
3) Novos painéis
   - Adicione JSON de dashboard em `grafana/dashboards/` e referencie em `grafana/provisioning/dashboards/dashboards.yml`.

## Operação & Troubleshooting
- `make api-test` — smoke de endpoints principais
- `make prometheus-up` — sobe Prometheus (http://localhost:9090)
- `make grafana-up` — sobe Grafana (http://localhost:3000)
- Targets Prometheus: ver “/targets” e inspecionar erros de scrape
- Se métricas custom não aparecem, gere tráfego e valide `/metrics/prometheus/` manualmente

## Referências
- `config/settings.py` — middlewares e integração django-prometheus
- `config/urls.py` — rotas de health e métricas
- `grafana/provisioning/*` — provisioning
- `grafana/dashboards/*` — dashboards
- `prometheus/prometheus.yml` — scrape configs
- `docs/API_STANDARDS.md` — padrões de API e endpoints de saúde/métricas
