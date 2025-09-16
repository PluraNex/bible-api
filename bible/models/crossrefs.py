from django.db import models
from django.db.models import F, Q

# A referência agora é para o livro canônico, não para um verso específico de uma versão
from .books import CanonicalBook


class CrossReference(models.Model):
    """
    Relação canônica e agnóstica à versão entre um trecho bíblico e outro.
    """

    # De
    from_book = models.ForeignKey(CanonicalBook, on_delete=models.CASCADE, related_name="x_from")
    from_chapter = models.PositiveIntegerField()
    from_verse = models.PositiveIntegerField()

    # Para (com suporte a intervalo de versículos)
    to_book = models.ForeignKey(CanonicalBook, on_delete=models.CASCADE, related_name="x_to")
    to_chapter = models.PositiveIntegerField()
    to_verse_start = models.PositiveIntegerField()
    to_verse_end = models.PositiveIntegerField()

    # Metadados da referência
    source = models.CharField(max_length=120, blank=True, default="", help_text="Ex: TSK, OpenBible")
    votes = models.PositiveIntegerField(default=0, help_text="Relevância da referência, se aplicável")

    # Campos adicionais do blueprint para futuras implementações
    confidence = models.FloatField(default=1.0, help_text="Confiança na referência (0.0 a 1.0)")
    explanation = models.TextField(blank=True, default="", help_text="Nota explicativa sobre a referência")

    class Meta:
        db_table = "cross_references"
        ordering = ["from_book", "from_chapter", "from_verse"]
        indexes = [
            models.Index(fields=["from_book", "from_chapter", "from_verse"], name="cr_from_idx"),
            models.Index(fields=["to_book", "to_chapter", "to_verse_start"], name="cr_to_idx"),
        ]
        constraints = [
            # Garante que uma referência de uma fonte específica seja única
            models.UniqueConstraint(
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
            # Garante que o intervalo de versículos de destino seja válido
            models.CheckConstraint(check=Q(to_verse_end__gte=F("to_verse_start")), name="cr_to_end_gte_start"),
            # Garante que a confiança esteja no intervalo correto
            models.CheckConstraint(check=Q(confidence__gte=0.0) & Q(confidence__lte=1.0), name="cr_confidence_0_1"),
        ]

    def __str__(self):
        to_range = f"{self.to_verse_start}"
        if self.to_verse_end > self.to_verse_start:
            to_range += f"-{self.to_verse_end}"

        return (
            f"{self.from_book.osis_code} {self.from_chapter}:{self.from_verse} → "
            f"{self.to_book.osis_code} {self.to_chapter}:{to_range}"
        )
