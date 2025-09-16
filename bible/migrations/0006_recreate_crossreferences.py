# Generated manually to transform cross_references table structure

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("bible", "0005_add_blueprint_models"),
    ]

    operations = [
        # Drop existing CrossReference model and its constraints/indexes
        migrations.RemoveConstraint(
            model_name="crossreference",
            name="crossref_no_self_reference",
        ),
        migrations.RemoveConstraint(
            model_name="crossreference",
            name="crossref_unique_from_to_source",
        ),
        migrations.RemoveIndex(
            model_name="crossreference",
            name="cross_refer_relatio_d4f67f_idx",
        ),
        migrations.RemoveIndex(
            model_name="crossreference",
            name="cross_refer_to_vers_4c1d9a_idx",
        ),
        migrations.RemoveIndex(
            model_name="crossreference",
            name="cross_refer_from_ve_71f844_idx",
        ),
        migrations.DeleteModel(
            name="CrossReference",
        ),
        # Create new CrossReference model with blueprint structure
        migrations.CreateModel(
            name="CrossReference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_chapter", models.PositiveIntegerField()),
                ("from_verse", models.PositiveIntegerField()),
                ("to_chapter", models.PositiveIntegerField()),
                ("to_verse_start", models.PositiveIntegerField()),
                ("to_verse_end", models.PositiveIntegerField()),
                ("source", models.CharField(blank=True, help_text="Ex: TSK, OpenBible", max_length=120, null=True)),
                ("votes", models.PositiveIntegerField(default=0, help_text="Relevância da referência, se aplicável")),
                ("confidence", models.FloatField(default=1.0, help_text="Confiança na referência (0.0 a 1.0)")),
                (
                    "explanation",
                    models.TextField(blank=True, help_text="Nota explicativa sobre a referência", null=True),
                ),
                (
                    "from_book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="x_from", to="bible.canonicalbook"
                    ),
                ),
                (
                    "to_book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="x_to", to="bible.canonicalbook"
                    ),
                ),
            ],
            options={
                "db_table": "cross_references",
                "ordering": ["from_book", "from_chapter", "from_verse"],
            },
        ),
        migrations.AddIndex(
            model_name="crossreference",
            index=models.Index(fields=["from_book", "from_chapter", "from_verse"], name="cr_from_idx"),
        ),
        migrations.AddIndex(
            model_name="crossreference",
            index=models.Index(fields=["to_book", "to_chapter", "to_verse_start"], name="cr_to_idx"),
        ),
        migrations.AddConstraint(
            model_name="crossreference",
            constraint=models.UniqueConstraint(
                fields=[
                    "from_book",
                    "from_chapter",
                    "from_verse",
                    "to_book",
                    "to_chapter",
                    "to_verse_start",
                    "to_verse_end",
                    "source",
                ],
                name="uniq_crossref_full",
            ),
        ),
        migrations.AddConstraint(
            model_name="crossreference",
            constraint=models.CheckConstraint(
                check=models.Q(("to_verse_end__gte", models.F("to_verse_start"))), name="cr_to_end_gte_start"
            ),
        ),
        migrations.AddConstraint(
            model_name="crossreference",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("confidence__gte", 0.0)), models.Q(("confidence__lte", 1.0)), _connector="AND"
                ),
                name="cr_confidence_0_1",
            ),
        ),
    ]
