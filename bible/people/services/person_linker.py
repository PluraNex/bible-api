"""
Populate the Person hub from existing domain models.

Sources:
1. Author (commentaries) — 242 records → Person with person_type="author"
2. CanonicalEntity PERSON/DEITY — when available → Person with person_type="biblical"
3. Overlap detection — when Author and Entity represent the same person → person_type="mixed"

Usage:
    python manage.py bible people populate
    python manage.py bible people status
"""

import logging
import time
from dataclasses import dataclass, field

from django.db import transaction
from django.utils.text import slugify

from bible.people.models import Person, PersonType

logger = logging.getLogger(__name__)


@dataclass
class LinkResult:
    persons_created: int = 0
    persons_updated: int = 0
    authors_linked: int = 0
    entities_linked: int = 0
    mixed_found: int = 0
    errors: list = field(default_factory=list)
    duration_seconds: float = 0.0


def _make_unique_slug(base_name: str, exclude_pk: int | None = None) -> str:
    """Generate a unique slug, appending suffix if needed."""
    base = slugify(base_name)[:110]
    slug = base
    counter = 1
    qs = Person.objects.filter(slug=slug)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    while qs.exists():
        slug = f"{base}-{counter}"
        counter += 1
        qs = Person.objects.filter(slug=slug)
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
    return slug


class PersonLinker:
    """Populate and link Person hub records."""

    def populate_from_authors(self, update_existing: bool = False) -> LinkResult:
        """Create Person records from all Author records."""
        from bible.commentaries.models import Author

        result = LinkResult()
        start = time.time()

        authors = Author.objects.select_related("person").all()
        logger.info(f"Populating Person from {authors.count()} authors")

        for author in authors:
            try:
                self._link_author(author, update_existing, result)
            except Exception as e:
                result.errors.append(f"Author '{author.name}': {e}")
                logger.exception(f"Error linking author '{author.name}'")

        result.duration_seconds = time.time() - start
        return result

    @transaction.atomic
    def _link_author(self, author, update_existing: bool, result: LinkResult):
        """Create or update a Person for an Author."""
        # Already linked?
        if author.person and not update_existing:
            return

        if author.person and update_existing:
            # Update existing Person
            person = author.person
            person.canonical_name = author.name
            person.birth_year = str(author.birth_year) if author.birth_year else ""
            person.death_year = str(author.death_year) if author.death_year else ""
            person.description = (author.biography_summary or "")[:500]
            person.wikipedia_url = author.wikipedia_url or ""
            person.portrait_image = author.portrait_image or ""
            person.save()
            result.persons_updated += 1
            return

        # Create new Person
        person = Person.objects.create(
            canonical_name=author.name,
            slug=_make_unique_slug(author.name),
            person_type=PersonType.AUTHOR,
            birth_year=str(author.birth_year) if author.birth_year else "",
            death_year=str(author.death_year) if author.death_year else "",
            description=(author.biography_summary or "")[:500],
            wikipedia_url=author.wikipedia_url or "",
            portrait_image=author.portrait_image or "",
        )
        author.person = person
        author.save(update_fields=["person"])
        result.persons_created += 1
        result.authors_linked += 1

    def populate_from_entities(self, update_existing: bool = False) -> LinkResult:
        """Create Person records from CanonicalEntity PERSON/DEITY namespace."""
        from bible.entities.models import CanonicalEntity

        result = LinkResult()
        start = time.time()

        entities = (
            CanonicalEntity.objects
            .filter(namespace__in=["PERSON", "DEITY"])
            .select_related("person")
        )
        total = entities.count()

        if total == 0:
            logger.info("No PERSON/DEITY entities found — skipping entity linking")
            result.duration_seconds = time.time() - start
            return result

        logger.info(f"Populating Person from {total} PERSON/DEITY entities")

        for entity in entities:
            try:
                self._link_entity(entity, update_existing, result)
            except Exception as e:
                result.errors.append(f"Entity '{entity.primary_name}': {e}")
                logger.exception(f"Error linking entity '{entity.primary_name}'")

            if result.entities_linked % 1000 == 0 and result.entities_linked > 0:
                logger.info(f"  Linked {result.entities_linked}/{total} entities...")

        result.duration_seconds = time.time() - start
        return result

    @transaction.atomic
    def _link_entity(self, entity, update_existing: bool, result: LinkResult):
        """Create or update a Person for a CanonicalEntity."""
        if entity.person and not update_existing:
            return

        # Check if an Author-linked Person matches this entity (name similarity)
        matching_person = self._find_matching_author_person(entity)

        if matching_person:
            # This person is BOTH an author and a biblical entity
            entity.person = matching_person
            entity.save(update_fields=["person"])
            matching_person.person_type = PersonType.MIXED
            matching_person.save(update_fields=["person_type"])
            result.mixed_found += 1
            result.entities_linked += 1
            return

        if entity.person and update_existing:
            person = entity.person
            person.canonical_name = entity.primary_name
            person.birth_year = entity.birth_year or ""
            person.death_year = entity.death_year or ""
            person.description = (entity.description or "")[:500]
            person.wikipedia_url = entity.wikipedia_url or ""
            person.save()
            result.persons_updated += 1
            return

        # Create new Person
        person = Person.objects.create(
            canonical_name=entity.primary_name,
            slug=_make_unique_slug(entity.primary_name),
            person_type=PersonType.BIBLICAL,
            birth_year=entity.birth_year or "",
            death_year=entity.death_year or "",
            description=(entity.description or "")[:500],
            wikipedia_url=entity.wikipedia_url or "",
        )
        entity.person = person
        entity.save(update_fields=["person"])
        result.persons_created += 1
        result.entities_linked += 1

    def _find_matching_author_person(self, entity) -> Person | None:
        """Find an existing Author-linked Person that matches this entity."""
        name = entity.primary_name.lower().strip()

        # Try exact match on Person canonical_name
        match = (
            Person.objects
            .filter(
                canonical_name__iexact=entity.primary_name,
                person_type=PersonType.AUTHOR,
                author_profile__isnull=False,
            )
            .first()
        )
        if match:
            return match

        # Try matching on aliases if available
        for alias in entity.aliases.all():
            match = (
                Person.objects
                .filter(
                    canonical_name__iexact=alias.name,
                    person_type=PersonType.AUTHOR,
                    author_profile__isnull=False,
                )
                .first()
            )
            if match:
                return match

        return None

    def get_status(self) -> dict:
        """Get current Person hub status."""
        from bible.commentaries.models import Author

        total = Person.objects.count()
        by_type = {}
        for pt in PersonType:
            by_type[pt.value] = Person.objects.filter(person_type=pt.value).count()

        authors_linked = Author.objects.filter(person__isnull=False).count()
        authors_unlinked = Author.objects.filter(person__isnull=True).count()

        entity_info = {"linked": 0, "unlinked": 0}
        try:
            from bible.entities.models import CanonicalEntity
            entity_info["linked"] = CanonicalEntity.objects.filter(
                person__isnull=False, namespace__in=["PERSON", "DEITY"]
            ).count()
            entity_info["unlinked"] = CanonicalEntity.objects.filter(
                person__isnull=True, namespace__in=["PERSON", "DEITY"]
            ).count()
        except Exception:
            pass

        return {
            "total_persons": total,
            "by_type": by_type,
            "authors_linked": authors_linked,
            "authors_unlinked": authors_unlinked,
            "entities_linked": entity_info["linked"],
            "entities_unlinked": entity_info["unlinked"],
        }
