from django.urls import path

from .views import RagEvalSimpleView

app_name = "rag"

urlpatterns = [
    path("eval-simple/", RagEvalSimpleView.as_view(), name="eval_simple"),
]
