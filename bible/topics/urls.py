"""
URL configuration for Topics domain.
"""

from django.urls import path

from .views import (
    TopicAnchorVersesView,
    TopicAspectsView,
    TopicCrossReferencesView,
    TopicDefinitionsView,
    TopicDetailView,
    TopicListView,
    TopicRelatedView,
    TopicSearchView,
    TopicsByLetterView,
    TopicsByTypeView,
    TopicStatisticsView,
    TopicStudyView,
    TopicThemesView,
)
from .review_views import (
    TopicReviewListView,
    TopicReviewDetailView,
    TopicEntitiesView,
    TopicThemesView as TopicReviewThemesView,
    TopicValidateView,
    TopicBatchValidateView,
    TopicApproveCorrectionsView,
    TopicReviewReportView,
)

app_name = "topics"

urlpatterns = [
    # List and Search
    path("", TopicListView.as_view(), name="list"),
    path("search/", TopicSearchView.as_view(), name="search"),

    # Navigation by letter
    path("by-letter/<str:letter>/", TopicsByLetterView.as_view(), name="by-letter"),

    # Navigation by type
    path("by-type/<str:topic_type>/", TopicsByTypeView.as_view(), name="by-type"),

    # Phase 0 Review endpoints (JSON files) - MUST be before <slug:slug>/ routes
    path("review/", TopicReviewListView.as_view(), name="review-list"),
    path("review/report/", TopicReviewReportView.as_view(), name="review-report"),
    path("review/batch-validate/", TopicBatchValidateView.as_view(), name="review-batch-validate"),
    path("review/<str:topic_key>/", TopicReviewDetailView.as_view(), name="review-detail"),
    path("review/<str:topic_key>/entities/", TopicEntitiesView.as_view(), name="review-entities"),
    path("review/<str:topic_key>/themes/", TopicReviewThemesView.as_view(), name="review-themes"),
    path("review/<str:topic_key>/validate/", TopicValidateView.as_view(), name="review-validate"),
    path("review/<str:topic_key>/approve/", TopicApproveCorrectionsView.as_view(), name="review-approve"),

    # Topic detail and related endpoints (slug-based routes must be LAST)
    path("<slug:slug>/", TopicDetailView.as_view(), name="detail"),
    path("<slug:slug>/aspects/", TopicAspectsView.as_view(), name="aspects"),
    path("<slug:slug>/definitions/", TopicDefinitionsView.as_view(), name="definitions"),
    path("<slug:slug>/themes/", TopicThemesView.as_view(), name="themes"),
    path("<slug:slug>/cross-references/", TopicCrossReferencesView.as_view(), name="cross-references"),
    path("<slug:slug>/related/", TopicRelatedView.as_view(), name="related"),
    path("<slug:slug>/statistics/", TopicStatisticsView.as_view(), name="statistics"),
    path("<slug:slug>/anchor-verses/", TopicAnchorVersesView.as_view(), name="anchor-verses"),
    path("<slug:slug>/study/", TopicStudyView.as_view(), name="study"),
]
