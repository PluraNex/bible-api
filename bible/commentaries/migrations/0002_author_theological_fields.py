"""Add theological fields to Author model.

New fields:
- death_location: where the author died
- orthodoxy_status: doctrinal status (orthodox, controversial, condemned, heterodox)
- recognized_by: which traditions recognize this author (JSONField)
- councils: ecumenical councils associated (JSONField)

Changed fields:
- author_type: expanded choices (added mystic, anonymous_work, collective_work, etc.)
- tradition: removed choices constraint, increased max_length to 200
- theological_school: removed choices constraint
- primary_hermeneutic: removed choices constraint, increased max_length to 100
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("commentaries", "0001_initial_models"),
    ]

    operations = [
        # New fields
        migrations.AddField(
            model_name="author",
            name="death_location",
            field=models.CharField(
                blank=True,
                default="",
                help_text="City/region of death",
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name="author",
            name="orthodoxy_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("orthodox", "Orthodox — universally accepted"),
                    ("controversial", "Controversial — debated across traditions"),
                    ("condemned_partially", "Condemned partially — some works condemned"),
                    ("heterodox", "Heterodox — rejected as heretical"),
                ],
                default="orthodox",
                help_text="Doctrinal status across Christian traditions",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="author",
            name="recognized_by",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Traditions that recognize/venerate this author",
            ),
        ),
        migrations.AddField(
            model_name="author",
            name="councils",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Ecumenical councils associated with this author",
            ),
        ),
        # Expand author_type choices
        migrations.AlterField(
            model_name="author",
            name="author_type",
            field=models.CharField(
                choices=[
                    ("biblical", "Biblical Author"),
                    ("apostolic_father", "Apostolic Father"),
                    ("church_father", "Church Father"),
                    ("desert_father", "Desert Father"),
                    ("medieval", "Medieval Theologian"),
                    ("scholastic", "Scholastic"),
                    ("reformation", "Reformation Era"),
                    ("puritan", "Puritan"),
                    ("mystic", "Mystic"),
                    ("modern_commentator", "Modern Commentator"),
                    ("contemporary", "Contemporary Scholar"),
                    ("post_reformation", "Post-Reformation"),
                    ("anonymous_work", "Anonymous Work"),
                    ("collective_work", "Collective Work"),
                    ("liturgical_text", "Liturgical Text"),
                    ("legendary", "Traditional/Legendary"),
                ],
                help_text="Primary category of author",
                max_length=30,
            ),
        ),
        # Remove choices constraint from tradition (too many variations)
        migrations.AlterField(
            model_name="author",
            name="tradition",
            field=models.CharField(
                blank=True,
                help_text="Theological/ecclesiastical tradition",
                max_length=200,
            ),
        ),
        # Remove choices constraint from theological_school
        migrations.AlterField(
            model_name="author",
            name="theological_school",
            field=models.CharField(
                blank=True,
                help_text="Theological school or approach",
                max_length=200,
            ),
        ),
        # Remove choices constraint from primary_hermeneutic, expand max_length
        migrations.AlterField(
            model_name="author",
            name="primary_hermeneutic",
            field=models.CharField(
                blank=True,
                help_text="Primary interpretive approach",
                max_length=100,
            ),
        ),
    ]
