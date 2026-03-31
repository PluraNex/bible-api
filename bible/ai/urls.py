from django.urls import path

from . import views

app_name = "ai"

urlpatterns = [
    path("agents/", views.AgentListView.as_view(), name="ai_agents_list"),
    path("tools/", views.ToolListView.as_view(), name="ai_tools_list"),
    path("tools/<str:tool>/test/", views.ToolTestView.as_view(), name="ai_tool_test"),
    path(
        "agents/<str:name>/runs/",
        views.AgentRunCreateView.as_view(),
        name="ai_agent_run_create",
    ),
    path("runs/<int:run_id>/", views.AgentRunDetailView.as_view(), name="ai_run_detail"),
    path(
        "runs/<int:run_id>/approve/",
        views.AgentRunApproveView.as_view(),
        name="ai_run_approve",
    ),
    path(
        "runs/<int:run_id>/cancel/",
        views.AgentRunCancelView.as_view(),
        name="ai_run_cancel",
    ),
    # RAG endpoints
    path("rag/retrieve/", views.RagRetrieveView.as_view(), name="rag_retrieve"),
    path("rag/search/", views.RagSearchView.as_view(), name="rag_search"),
    path("rag/hybrid/", views.RagHybridSearchView.as_view(), name="rag_hybrid"),
    path("rag/similar/", views.RagSimilarView.as_view(), name="rag_similar"),
    path("rag/health/", views.RagHealthView.as_view(), name="rag_health"),
    path("rag/stats/", views.RagStatsView.as_view(), name="rag_stats"),
]
