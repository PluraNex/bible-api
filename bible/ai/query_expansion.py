"""
Query Expansion Module - Expansão de queries para melhor recall

Este módulo implementa técnicas de query expansion para busca bíblica:
1. Sinônimos teológicos - termos com significado similar no contexto bíblico
2. Variações morfológicas - diferentes formas da mesma palavra
3. Conceitos relacionados - termos que frequentemente co-ocorrem

Técnicas implementadas:
- Static Expansion: dicionário de sinônimos curado manualmente
- Stemming: redução a radicais para capturar variações
- Thesaurus: expansão baseada em tesauro teológico

Referências:
- https://nlp.stanford.edu/IR-book/html/htmledition/query-expansion-1.html
- Semantic Bible (theological thesaurus concepts)

Versão: 1.0.0
Data: Nov 2025
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


def normalize_accents(text: str) -> str:
    """Remove acentos de uma string para normalização."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ============================================================================
# DICIONÁRIO DE SINÔNIMOS TEOLÓGICOS
# ============================================================================
# Formato: termo_base -> [sinônimos ordenados por relevância]
# Os primeiros sinônimos são mais próximos semanticamente

THEOLOGICAL_SYNONYMS: dict[str, list[str]] = {
    # === EMOÇÕES E SENTIMENTOS ===
    "amor": ["caridade", "afeição", "ágape", "benevolência", "bondade", "ternura"],
    "ódio": ["ira", "raiva", "aversão", "inimizade", "hostilidade", "rancor", "malícia"],
    "odio": ["ira", "raiva", "aversão", "inimizade", "hostilidade", "rancor", "malícia"],  # sem acento
    "ira": ["ódio", "raiva", "fúria", "indignação", "cólera", "furor"],
    "medo": ["temor", "pavor", "terror", "receio", "angústia"],
    "temor": ["medo", "reverência", "respeito", "pavor"],
    "alegria": ["júbilo", "gozo", "regozijo", "contentamento", "felicidade", "exultação"],
    "tristeza": ["luto", "pesar", "dor", "aflição", "angústia", "sofrimento"],
    "paz": ["shalom", "tranquilidade", "sossego", "harmonia", "serenidade", "descanso"],
    "esperança": ["fé", "confiança", "expectativa", "aguardo"],
    "esperanca": ["fé", "confiança", "expectativa", "aguardo"],  # sem acento
    
    # === CONCEITOS TEOLÓGICOS CENTRAIS ===
    "salvação": ["redenção", "libertação", "resgate", "livramento", "socorro"],
    "salvacao": ["redenção", "libertação", "resgate", "livramento", "socorro"],  # sem acento
    "redenção": ["salvação", "resgate", "libertação", "expiação"],
    "redencao": ["salvação", "resgate", "libertação", "expiação"],  # sem acento
    "perdão": ["remissão", "absolvição", "misericórdia", "indulto", "clemência"],
    "perdao": ["remissão", "absolvição", "misericórdia", "indulto", "clemência"],  # sem acento
    "pecado": ["transgressão", "iniquidade", "culpa", "erro", "falta", "maldade"],
    "graça": ["favor", "benevolência", "misericórdia", "bondade", "clemência"],
    "graca": ["favor", "benevolência", "misericórdia", "bondade", "clemência"],  # sem acento
    "fé": ["crença", "confiança", "convicção", "certeza", "esperança"],
    "fe": ["crença", "confiança", "convicção", "certeza", "esperança"],  # sem acento
    "arrependimento": ["conversão", "contrição", "penitência", "mudança"],
    "justificação": ["absolvição", "declaração", "inocência"],
    "justificacao": ["absolvição", "declaração", "inocência"],  # sem acento
    "santificação": ["consagração", "purificação", "dedicação", "separação"],
    "glorificação": ["exaltação", "louvor", "adoração", "majestade"],
    
    # === ATRIBUTOS DIVINOS ===
    "onipotente": ["todo-poderoso", "soberano", "supremo", "poderoso"],
    "onisciente": ["sabe tudo", "conhecedor", "sábio"],
    "onipresente": ["presente", "imanente", "eterno"],
    "santo": ["puro", "sagrado", "consagrado", "imaculado", "perfeito"],
    "justo": ["reto", "íntegro", "correto", "equitativo", "imparcial"],
    "misericordioso": ["compassivo", "piedoso", "clemente", "bondoso", "gracioso"],
    "fiel": ["leal", "constante", "verdadeiro", "confiável", "firme"],
    
    # === TERMOS SOBRE DEUS ===
    "deus": ["senhor", "eterno", "altíssimo", "criador", "pai", "todo-poderoso"],
    "senhor": ["deus", "jeová", "yahweh", "adonai", "mestre"],
    "jesus": ["cristo", "messias", "salvador", "redentor", "cordeiro", "filho"],
    "cristo": ["jesus", "messias", "ungido", "salvador"],
    "messias": ["cristo", "jesus", "ungido", "libertador"],
    "espírito": ["espírito santo", "consolador", "parácleto", "sopro"],
    
    # === LUGARES E CONCEITOS ===
    "céu": ["paraíso", "glória", "morada", "reino", "eternidade"],
    "inferno": ["geena", "hades", "sheol", "abismo", "perdição", "condenação"],
    "reino": ["reinado", "domínio", "governo", "soberania", "majestade"],
    "igreja": ["assembleia", "congregação", "corpo", "noiva", "comunidade"],
    "templo": ["santuário", "tabernáculo", "casa", "morada"],
    
    # === AÇÕES E PRÁTICAS ===
    "orar": ["rogar", "suplicar", "interceder", "clamar", "pedir"],
    "oração": ["prece", "súplica", "intercessão", "clamor", "petição"],
    "adorar": ["louvar", "glorificar", "exaltar", "venerar", "cultuar"],
    "adoração": ["louvor", "culto", "veneração", "reverência"],
    "jejum": ["abstinência", "privação", "renúncia"],
    "batismo": ["imersão", "lavagem", "purificação", "iniciação"],
    "comunhão": ["ceia", "eucaristia", "partilha", "participação"],
    "pregação": ["proclamação", "anúncio", "evangelização", "testemunho"],
    
    # === VIRTUDES ===
    "humildade": ["mansidão", "modéstia", "simplicidade", "submissão"],
    "paciência": ["longanimidade", "perseverança", "tolerância", "constância"],
    "bondade": ["benignidade", "generosidade", "benevolência", "caridade"],
    "mansidão": ["humildade", "brandura", "docilidade", "gentileza"],
    "domínio próprio": ["temperança", "autocontrole", "moderação"],
    "sabedoria": ["prudência", "discernimento", "entendimento", "conhecimento"],
    
    # === VÍCIOS E MALES ===
    "orgulho": ["soberba", "arrogância", "vaidade", "presunção", "altivez"],
    "inveja": ["ciúme", "cobiça", "ganância", "avareza"],
    "cobiça": ["ganância", "avareza", "ambição", "desejo"],
    "mentira": ["falsidade", "engano", "fraude", "hipocrisia"],
    "idolatria": ["adoração falsa", "paganismo", "ídolos"],
    
    # === PESSOAS E CARGOS ===
    "profeta": ["vidente", "mensageiro", "porta-voz"],
    "apóstolo": ["enviado", "mensageiro", "missionário", "embaixador"],
    "sacerdote": ["levita", "ministro", "pastor", "presbítero"],
    "pastor": ["shepherd", "guia", "líder", "ancião", "presbítero"],
    "discípulo": ["seguidor", "aprendiz", "aluno", "servo"],
    "servo": ["escravo", "ministro", "mordomo", "criado"],
    
    # === EVENTOS E DOUTRINAS ===
    "ressurreição": ["ressuscitar", "levantar", "vida", "imortalidade"],
    "crucificação": ["cruz", "sacrifício", "morte", "expiação"],
    "ascensão": ["subida", "elevação", "exaltação"],
    "segunda vinda": ["parúsia", "retorno", "volta", "aparecimento"],
    "juízo": ["julgamento", "tribunal", "condenação", "sentença"],
    "aliança": ["pacto", "concerto", "promessa", "compromisso", "testamento"],
    "bênção": ["benção", "favor", "prosperidade", "graça"],
    "maldição": ["praga", "castigo", "condenação", "juízo"],
}

# Variações morfológicas comuns em português
MORPHOLOGICAL_VARIANTS: dict[str, list[str]] = {
    "amor": ["amar", "amou", "amado", "amando", "amei", "ama", "amem", "amamos"],
    "ódio": ["odiar", "odiou", "odiado", "odiando", "odiei", "odeia", "odeiam", "odiaram"],
    "perdão": ["perdoar", "perdoou", "perdoado", "perdoando", "perdoei", "perdoa", "perdoem"],
    "salvar": ["salvação", "salvador", "salvo", "salvou", "salvando", "salve", "salvos"],
    "pecado": ["pecar", "pecou", "pecador", "pecando", "pequei", "peca", "pecam", "pecados"],
    "orar": ["oração", "orou", "orando", "orei", "ora", "orem", "orações"],
    "crer": ["crença", "creu", "crendo", "cri", "crê", "creem", "creram", "fé"],
    "morrer": ["morte", "morreu", "morrendo", "morri", "morre", "morrem", "morto", "mortos"],
    "viver": ["vida", "viveu", "vivendo", "vivi", "vive", "vivem", "vivo", "vivos"],
    "nascer": ["nascimento", "nasceu", "nascendo", "nasci", "nasce", "nascem", "nascido"],
}


@dataclass
class ExpandedQuery:
    """Resultado da expansão de query."""
    
    original: str
    expanded_terms: list[str]
    synonyms_used: dict[str, list[str]]
    expansion_type: str
    
    def to_bm25_query(self) -> str:
        """Converte para formato OR para BM25."""
        all_terms = [self.original] + self.expanded_terms
        # Remover duplicatas mantendo ordem
        seen = set()
        unique = []
        for term in all_terms:
            if term.lower() not in seen:
                seen.add(term.lower())
                unique.append(term)
        return " | ".join(unique)
    
    def to_tsquery(self) -> str:
        """Converte para formato tsquery do PostgreSQL."""
        all_terms = [self.original] + self.expanded_terms
        seen = set()
        unique = []
        for term in all_terms:
            clean = re.sub(r"[^\w]", "", term.lower())
            if clean and clean not in seen:
                seen.add(clean)
                unique.append(clean)
        return " | ".join(unique)


def expand_query(
    query: str,
    *,
    max_synonyms_per_term: int = 3,
    include_morphological: bool = True,
    boost_original: bool = True,
) -> ExpandedQuery:
    """
    Expande uma query com sinônimos teológicos e variações.
    
    Args:
        query: Query original
        max_synonyms_per_term: Máximo de sinônimos por termo (default: 3)
        include_morphological: Incluir variações morfológicas (default: True)
        boost_original: Dar mais peso ao termo original (default: True)
    
    Returns:
        ExpandedQuery com termos expandidos
    
    Example:
        >>> expand_query("amor de Deus")
        ExpandedQuery(
            original="amor de Deus",
            expanded_terms=["caridade", "afeição", "ágape", "senhor", "eterno"],
            synonyms_used={"amor": ["caridade", "afeição", "ágape"], "deus": ["senhor", "eterno"]},
            expansion_type="theological_synonyms"
        )
    """
    # Tokenizar query
    words = _tokenize(query)
    
    expanded_terms: list[str] = []
    synonyms_used: dict[str, list[str]] = {}
    
    for word in words:
        word_lower = word.lower()
        word_normalized = normalize_accents(word_lower)
        
        # Buscar sinônimos teológicos (tentar com e sem acentos)
        syns = None
        lookup_key = word_lower
        if word_lower in THEOLOGICAL_SYNONYMS:
            syns = THEOLOGICAL_SYNONYMS[word_lower][:max_synonyms_per_term]
        elif word_normalized in THEOLOGICAL_SYNONYMS:
            syns = THEOLOGICAL_SYNONYMS[word_normalized][:max_synonyms_per_term]
            lookup_key = word_normalized
        
        if syns:
            expanded_terms.extend(syns)
            synonyms_used[lookup_key] = syns
        
        # Buscar variações morfológicas (tentar com e sem acentos)
        if include_morphological:
            variants = None
            if word_lower in MORPHOLOGICAL_VARIANTS:
                variants = MORPHOLOGICAL_VARIANTS[word_lower][:max_synonyms_per_term]
            elif word_normalized in MORPHOLOGICAL_VARIANTS:
                variants = MORPHOLOGICAL_VARIANTS[word_normalized][:max_synonyms_per_term]
            
            if variants:
                expanded_terms.extend(variants)
                if lookup_key not in synonyms_used:
                    synonyms_used[lookup_key] = []
                synonyms_used[lookup_key].extend(variants)
    
    # Determinar tipo de expansão
    expansion_type = "none"
    if synonyms_used:
        expansion_type = "theological_synonyms"
        if include_morphological:
            expansion_type = "theological_synonyms+morphological"
    
    return ExpandedQuery(
        original=query,
        expanded_terms=expanded_terms,
        synonyms_used=synonyms_used,
        expansion_type=expansion_type,
    )


def expand_query_for_bm25(query: str, **kwargs) -> str:
    """
    Expande query e retorna string formatada para BM25.
    
    Útil para uso direto na busca BM25 com operador OR.
    """
    expanded = expand_query(query, **kwargs)
    return expanded.to_tsquery()


def expand_query_for_embedding(
    query: str,
    *,
    strategy: str = "concatenate",
    max_synonyms: int = 2,
) -> str:
    """
    Expande query para gerar embedding mais rico.
    
    Estratégias:
    - "concatenate": Concatena sinônimos à query original
    - "replace": Substitui termos por sinônimos mais comuns
    - "augment": Adiciona contexto teológico
    
    Args:
        query: Query original
        strategy: Estratégia de expansão
        max_synonyms: Máximo de sinônimos a incluir
    
    Returns:
        Query expandida para embedding
    """
    expanded = expand_query(query, max_synonyms_per_term=max_synonyms)
    
    if strategy == "concatenate":
        # Adicionar sinônimos ao final
        all_terms = [query]
        for syns in expanded.synonyms_used.values():
            all_terms.extend(syns[:max_synonyms])
        return " ".join(all_terms)
    
    elif strategy == "replace":
        # Substituir por sinônimo mais comum
        result = query
        for word, syns in expanded.synonyms_used.items():
            if syns:
                # Usar primeiro sinônimo (mais relevante)
                result = re.sub(rf"\b{word}\b", f"{word} {syns[0]}", result, flags=re.IGNORECASE)
        return result
    
    elif strategy == "augment":
        # Adicionar contexto teológico
        context_terms = []
        for word, syns in expanded.synonyms_used.items():
            if syns:
                context_terms.append(syns[0])
        if context_terms:
            return f"{query} ({', '.join(context_terms)})"
        return query
    
    return query


def get_related_concepts(term: str, max_results: int = 5) -> list[str]:
    """
    Retorna conceitos relacionados a um termo.
    
    Útil para sugestões de busca e exploração temática.
    """
    term_lower = term.lower()
    
    related = []
    
    # Sinônimos diretos
    if term_lower in THEOLOGICAL_SYNONYMS:
        related.extend(THEOLOGICAL_SYNONYMS[term_lower][:max_results])
    
    # Termos que têm este como sinônimo (relação inversa)
    for key, syns in THEOLOGICAL_SYNONYMS.items():
        if term_lower in [s.lower() for s in syns]:
            if key not in related:
                related.append(key)
    
    return related[:max_results]


def _tokenize(text: str) -> list[str]:
    """Tokeniza texto removendo stopwords e pontuação."""
    # Stopwords em português
    stopwords = {
        "de", "da", "do", "das", "dos", "a", "o", "as", "os", "e", "ou",
        "um", "uma", "uns", "umas", "em", "no", "na", "nos", "nas",
        "por", "para", "com", "sem", "sob", "sobre", "entre", "que",
        "se", "ao", "aos", "à", "às", "pelo", "pela", "pelos", "pelas",
        "este", "esta", "esse", "essa", "aquele", "aquela", "isto", "isso",
        "aquilo", "meu", "minha", "seu", "sua", "nosso", "nossa",
    }
    
    # Remover pontuação e dividir
    clean = re.sub(r"[^\w\s]", " ", text.lower())
    words = [w.strip() for w in clean.split() if w.strip()]
    
    # Filtrar stopwords
    return [w for w in words if w not in stopwords]


def get_expansion_stats() -> dict[str, Any]:
    """Retorna estatísticas do dicionário de expansão."""
    total_terms = len(THEOLOGICAL_SYNONYMS)
    total_synonyms = sum(len(syns) for syns in THEOLOGICAL_SYNONYMS.values())
    morphological_terms = len(MORPHOLOGICAL_VARIANTS)
    
    # Categorias
    categories = {
        "emoções": ["amor", "ódio", "ira", "medo", "alegria", "tristeza", "paz"],
        "teologia": ["salvação", "redenção", "perdão", "pecado", "graça", "fé"],
        "divino": ["deus", "senhor", "jesus", "cristo", "espírito"],
        "práticas": ["orar", "adorar", "jejum", "batismo", "comunhão"],
        "virtudes": ["humildade", "paciência", "bondade", "mansidão", "sabedoria"],
    }
    
    return {
        "total_base_terms": total_terms,
        "total_synonyms": total_synonyms,
        "average_synonyms_per_term": round(total_synonyms / total_terms, 2) if total_terms else 0,
        "morphological_variants": morphological_terms,
        "categories": {cat: len([t for t in terms if t in THEOLOGICAL_SYNONYMS]) for cat, terms in categories.items()},
    }


# ============================================================================
# FUNÇÕES DE CONVENIÊNCIA PARA INTEGRAÇÃO
# ============================================================================

def expand_for_hybrid_search(
    query: str,
    alpha: float = 0.5,
) -> tuple[str, str, dict]:
    """
    Prepara query expandida para busca híbrida.
    
    Returns:
        Tuple de (query_bm25, query_embedding, metadata)
    """
    expanded = expand_query(query)
    
    # Para BM25: usar formato OR
    query_bm25 = expanded.to_tsquery()
    
    # Para embedding: concatenar com contexto
    query_embedding = expand_query_for_embedding(query, strategy="augment")
    
    metadata = {
        "original": query,
        "bm25_terms": query_bm25.split(" | "),
        "embedding_query": query_embedding,
        "synonyms_used": expanded.synonyms_used,
        "expansion_type": expanded.expansion_type,
    }
    
    return query_bm25, query_embedding, metadata
