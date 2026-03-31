"""Add evidence_score to Theme and grade to ThemeVerseLink.

These fields capture the validated research data from the TCC hybrid search experiments:
- evidence_score: Overall theme confidence (0-1) from multi-source validation
- grade: Discrete quality grade (1-3) from graded relevance assessment
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("themes", "0001_themes_enriched"),
    ]

    operations = [
        migrations.AddField(
            model_name="theme",
            name="evidence_score",
            field=models.FloatField(
                default=0.0,
                help_text="Evidence confidence score from multi-source validation (0-1)",
            ),
        ),
        migrations.AddField(
            model_name="themeverselink",
            name="grade",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Quality grade: 3=primary (3+ sources), 2=secondary (2 sources), 1=supporting (1 source)",
            ),
        ),
        migrations.AddIndex(
            model_name="themeverselink",
            index=models.Index(fields=["grade"], name="tvl_grade_idx"),
        ),
    ]
