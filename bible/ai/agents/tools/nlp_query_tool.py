"""
NLP Query Processing Tool - Análise linguística avançada de queries.

Este tool usa NLP + IA para:
1. Tokenizar e limpar queries (remover stopwords)
2. Classificar tipo semântico (frase, conceito, referência)
3. Calcular estratégia de boost dinâmica
4. Cachear resultados para queries futuras

Integra com spaCy (NLP) e OpenAI (classificação semântica).

Autor: Bible API Team
Data: Novembro 2025
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SemanticType(str, Enum):
    """Tipos semânticos de query."""
    
    PHRASE = "phrase"           # Frase exata: "paz na terra"
    CONCEPT = "concept"         # Conceito abstrato: "justiça", "salvação"
    REFERENCE = "reference"     # Referência bíblica: "João 3:16"
    ENTITY = "entity"           # Entidade: "Jesus", "Davi", "Jerusalém"
    KEYWORD = "keyword"         # Palavra-chave única: "amor"
    QUESTION = "question"       # Pergunta: "quem é o Espírito Santo?"


@dataclass
class NLPAnalysis:
    """Resultado da análise NLP de uma query."""
    
    # Query original e processada
    query_original: str
    query_normalized: str
    
    # Tokens
    tokens_raw: list[str]           # ["paz", "na", "terra"]
    tokens_clean: list[str]         # ["paz", "terra"]
    tokens_lemma: list[str]         # ["paz", "terra"]
    stopwords_removed: list[str]    # ["na"]
    
    # Análise linguística
    pos_tags: dict[str, str]        # {"paz": "NOUN", "terra": "NOUN"}
    entities: list[dict] = field(default_factory=list)  # NER results
    
    # Classificação semântica
    semantic_type: SemanticType = SemanticType.KEYWORD
    semantic_confidence: float = 0.0
    
    # N-grams
    bigrams: list[str] = field(default_factory=list)
    trigrams: list[str] = field(default_factory=list)
    is_known_phrase: bool = False
    
    # Estratégia de boost
    boost_strategy: dict = field(default_factory=dict)
    
    # Metadados
    from_cache: bool = False
    processing_time_ms: float = 0.0
    
    def get_optimal_distance(self) -> int:
        """
        Calcula distância ideal para operador tsquery.
        
        Fórmula: número de stopwords removidas + 1
        
        Exemplos:
        - "paz na terra" → 2 stopwords → distância 2 (paz <2> terra)
        - "amor de Deus" → 1 stopword → distância 2 (amor <2> Deus)
        - "espírito santo" → 0 stopwords → distância 1 (<-> adjacente)
        """
        return len(self.stopwords_removed) + 1
    
    def to_tsquery(self) -> str:
        """
        Gera tsquery otimizado baseado na análise NLP.
        
        Usa distância dinâmica calculada pelos stopwords removidos.
        """
        if len(self.tokens_clean) < 2:
            return self.tokens_clean[0] if self.tokens_clean else ""
        
        distance = self.get_optimal_distance()
        
        # Para frases, usar operador de distância
        if self.semantic_type == SemanticType.PHRASE:
            phrase = f" <{distance}> ".join(self.tokens_clean)
            return f"({phrase})"
        
        # Para conceitos, usar OR
        return " | ".join(self.tokens_clean)
    
    def to_dict(self) -> dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "query_original": self.query_original,
            "query_normalized": self.query_normalized,
            "tokens_raw": self.tokens_raw,
            "tokens_clean": self.tokens_clean,
            "tokens_lemma": self.tokens_lemma,
            "stopwords_removed": self.stopwords_removed,
            "pos_tags": self.pos_tags,
            "entities": self.entities,
            "semantic_type": self.semantic_type.value,
            "semantic_confidence": self.semantic_confidence,
            "bigrams": self.bigrams,
            "trigrams": self.trigrams,
            "is_known_phrase": self.is_known_phrase,
            "boost_strategy": self.boost_strategy,
            "optimal_distance": self.get_optimal_distance(),
            "tsquery": self.to_tsquery(),
            "from_cache": self.from_cache,
            "processing_time_ms": self.processing_time_ms,
        }


# Stopwords em português (expandido para contexto bíblico)
PT_STOPWORDS = {
    # Artigos
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    # Preposições
    "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
    "por", "para", "com", "sem", "sob", "sobre", "entre", "até",
    "ao", "aos", "à", "às", "pelo", "pela", "pelos", "pelas",
    # Conjunções
    "e", "ou", "mas", "que", "se", "como", "quando", "porque",
    # Pronomes
    "eu", "tu", "ele", "ela", "nós", "vós", "eles", "elas",
    "me", "te", "se", "nos", "vos", "lhe", "lhes",
    "meu", "minha", "teu", "tua", "seu", "sua", "nosso", "nossa",
    # Verbos auxiliares
    "é", "são", "foi", "eram", "ser", "estar", "ter", "haver",
    # Outros
    "não", "sim", "já", "ainda", "também", "muito", "mais", "menos",
}

# Frases bíblicas conhecidas (para detecção de phrase search)
KNOWN_BIBLICAL_PHRASES = {
    "paz na terra",
    "gloria a deus",
    "amor ao proximo",
    "agua viva",
    "pao da vida",
    "luz do mundo",
    "bom pastor",
    "cordeiro de deus",
    "filho do homem",
    "reino dos ceus",
    "espirito santo",
    "vida eterna",
    "novo testamento",
    "antigo testamento",
    "dia do senhor",
    "palavra de deus",
    "casa do senhor",
    "terra prometida",
    "mar vermelho",
    "monte sinai",
    "jardim do eden",
    "arca da alianca",
    "tabuas da lei",
    "sermao da montanha",
    "ultima ceia",
    "ressurreicao dos mortos",
}


class NLPQueryTool:
    """
    Tool de análise NLP para queries de busca bíblica.
    
    Combina processamento linguístico (spaCy/NLTK) com
    classificação semântica (LLM) e Gazetteer de entidades
    bíblicas para otimizar buscas.
    
    Exemplo:
        tool = NLPQueryTool()
        analysis = tool.analyze("paz na terra")
        print(analysis.semantic_type)  # SemanticType.PHRASE
        print(analysis.tokens_clean)   # ["paz", "terra"]
        print(analysis.to_tsquery())   # "(paz <2> terra)"
    """
    
    # Caminho do Gazetteer
    GAZETTEER_PATH = "data/NLP/nlp_gazetteer/canonical_entities_v4_unified.json"
    
    def __init__(
        self,
        use_spacy: bool = True,
        use_llm_classification: bool = True,
        use_cache: bool = True,
        use_gazetteer: bool = True,
        spacy_model: str = "pt_core_news_sm",
    ):
        """
        Inicializa o tool.
        
        Args:
            use_spacy: Usar spaCy para análise linguística avançada
            use_llm_classification: Usar LLM para classificar tipo semântico
            use_cache: Cachear resultados no banco
            use_gazetteer: Usar gazetteer de entidades bíblicas
            spacy_model: Modelo spaCy a usar (sm, md, lg)
        """
        self.use_spacy = use_spacy
        self.use_llm_classification = use_llm_classification
        self.use_cache = use_cache
        self.use_gazetteer = use_gazetteer
        self.spacy_model = spacy_model
        
        self._nlp = None  # Lazy load spaCy
        self._gazetteer = None  # Lazy load gazetteer
    
    @property
    def nlp(self):
        """Carrega modelo spaCy sob demanda."""
        if self._nlp is None and self.use_spacy:
            try:
                import spacy
                self._nlp = spacy.load(self.spacy_model)
                logger.info(f"spaCy model loaded: {self.spacy_model}")
            except OSError:
                logger.warning(f"spaCy model {self.spacy_model} not found, using fallback")
                self._nlp = False  # Marca como tentado e falhou
            except ImportError:
                logger.warning("spaCy not installed, using fallback tokenization")
                self._nlp = False
        return self._nlp
    
    @property
    def gazetteer(self) -> dict:
        """Carrega gazetteer de entidades bíblicas sob demanda."""
        if self._gazetteer is None and self.use_gazetteer:
            try:
                import json
                from pathlib import Path
                
                # Tentar múltiplos caminhos
                possible_paths = [
                    Path(self.GAZETTEER_PATH),
                    Path(__file__).parent.parent.parent.parent.parent / "data/NLP/nlp_gazetteer/canonical_entities_v4_unified.json",
                    Path("/app/data/NLP/nlp_gazetteer/canonical_entities_v4_unified.json"),
                ]
                
                for path in possible_paths:
                    if path.exists():
                        with open(path, encoding="utf-8") as f:
                            self._gazetteer = json.load(f)
                        logger.info(f"Gazetteer loaded: {path}")
                        break
                
                if self._gazetteer is None:
                    logger.warning("Gazetteer not found, entity detection disabled")
                    self._gazetteer = {}
                    
            except Exception as e:
                logger.warning(f"Failed to load gazetteer: {e}")
                self._gazetteer = {}
        
        return self._gazetteer or {}
    
    def detect_entities(self, query: str) -> list[dict]:
        """
        Detecta entidades bíblicas na query usando o gazetteer.
        
        Args:
            query: Query normalizada
            
        Returns:
            Lista de entidades detectadas com boost e tipo
        """
        if not self.gazetteer:
            return []
        
        entities = []
        query_lower = query.lower()
        
        for namespace, items in self.gazetteer.items():
            # Pular metadados
            if namespace.startswith("_") or not isinstance(items, dict):
                continue
            
            for name, data in items.items():
                if not isinstance(data, dict):
                    continue
                    
                aliases = data.get("aliases", [name])
                if not isinstance(aliases, list):
                    aliases = [aliases]
                
                for alias in aliases:
                    alias_lower = alias.lower()
                    # Normalizar alias (remover acentos)
                    alias_normalized = self._normalize(alias_lower)
                    
                    if alias_normalized in query_lower or alias_lower in query_lower:
                        entities.append({
                            "text": alias,
                            "type": namespace,
                            "canonical_id": data.get("canonical_id", f"{namespace}:{name}"),
                            "boost": data.get("boost", 1.0),
                            "priority": data.get("priority", 50),
                            "description": data.get("description", ""),
                        })
                        break  # Não duplicar mesma entidade
        
        # Ordenar por boost (maior primeiro)
        return sorted(entities, key=lambda x: x["boost"], reverse=True)
    
    def _get_from_cache(self, query_normalized: str) -> NLPAnalysis | None:
        """Tenta obter análise do cache."""
        try:
            from bible.models import QueryNLPCache
            
            cached = QueryNLPCache.objects.filter(
                query_normalized=query_normalized
            ).first()
            
            if cached:
                cached.increment_usage()
                logger.debug(f"NLP Cache HIT: '{query_normalized}' (usage: {cached.usage_count})")
                return cached.to_nlp_analysis()
        except Exception as e:
            logger.warning(f"NLP Cache lookup failed: {e}")
        
        return None
    
    def _save_to_cache(self, analysis: NLPAnalysis) -> None:
        """Salva análise no cache."""
        try:
            from bible.models import QueryNLPCache
            
            # Usar update_or_create para evitar duplicatas
            QueryNLPCache.objects.update_or_create(
                query_normalized=analysis.query_normalized,
                defaults={
                    "query_original": analysis.query_original,
                    "semantic_type": analysis.semantic_type.value,
                    "semantic_confidence": analysis.semantic_confidence,
                    "tokens_raw": analysis.tokens_raw,
                    "tokens_clean": analysis.tokens_clean,
                    "tokens_lemma": analysis.tokens_lemma,
                    "stopwords_removed": analysis.stopwords_removed,
                    "entities": analysis.entities,
                    "boost_strategy": analysis.boost_strategy,
                    "tsquery_optimized": analysis.to_tsquery(),
                    "bigrams": analysis.bigrams,
                    "trigrams": analysis.trigrams,
                    "is_known_phrase": analysis.is_known_phrase,
                    "processing_time_ms": analysis.processing_time_ms,
                }
            )
            logger.debug(f"NLP Cache SAVE: '{analysis.query_normalized}'")
        except Exception as e:
            logger.warning(f"NLP Cache save failed: {e}")
    
    def analyze(self, query: str, use_cache: bool = True) -> NLPAnalysis:
        """
        Analisa uma query completa com NLP.
        
        Args:
            query: Query de busca
            use_cache: Se True, tenta usar cache antes de processar
            
        Returns:
            NLPAnalysis com todos os dados processados
        """
        import time
        start = time.time()
        
        query = query.strip()
        query_normalized = self._normalize(query)
        
        # Tentar cache primeiro
        if use_cache:
            cached = self._get_from_cache(query_normalized)
            if cached:
                return cached
        
        # 1. Tokenização
        if self.nlp:
            tokens_data = self._tokenize_spacy(query_normalized)
        else:
            tokens_data = self._tokenize_simple(query_normalized)
        
        # 2. Detectar entidades bíblicas usando gazetteer
        gazetteer_entities = self.detect_entities(query_normalized)
        
        # 3. Detectar tipo semântico
        semantic_type, confidence = self._classify_semantic_type(
            query_normalized,
            tokens_data["tokens_clean"],
            gazetteer_entities,
        )
        
        # 4. Detectar frases conhecidas
        is_known_phrase = self._is_known_phrase(query_normalized)
        if is_known_phrase:
            semantic_type = SemanticType.PHRASE
            confidence = max(confidence, 0.9)
        
        # Se encontrou entidade de alta prioridade, ajustar tipo
        if gazetteer_entities and gazetteer_entities[0]["boost"] >= 2.5:
            semantic_type = SemanticType.ENTITY
            confidence = max(confidence, 0.85)
        
        # 5. Gerar n-grams
        bigrams, trigrams = self._generate_ngrams(tokens_data["tokens_raw"])
        
        # 6. Calcular estratégia de boost (agora com entidades)
        boost_strategy = self._calculate_boost_strategy(
            semantic_type,
            tokens_data,
            is_known_phrase,
            gazetteer_entities,
        )
        
        processing_time = (time.time() - start) * 1000
        
        # Combinar entidades do spaCy com do gazetteer
        all_entities = tokens_data.get("entities", []) + gazetteer_entities
        
        analysis = NLPAnalysis(
            query_original=query,
            query_normalized=query_normalized,
            tokens_raw=tokens_data["tokens_raw"],
            tokens_clean=tokens_data["tokens_clean"],
            tokens_lemma=tokens_data["tokens_lemma"],
            stopwords_removed=tokens_data["stopwords_removed"],
            pos_tags=tokens_data["pos_tags"],
            entities=all_entities,
            semantic_type=semantic_type,
            semantic_confidence=confidence,
            bigrams=bigrams,
            trigrams=trigrams,
            is_known_phrase=is_known_phrase,
            boost_strategy=boost_strategy,
            from_cache=False,
            processing_time_ms=processing_time,
        )
        
        # Salvar no cache para uso futuro
        if use_cache:
            self._save_to_cache(analysis)
        
        return analysis
    
    def _normalize(self, text: str) -> str:
        """Normaliza texto: lowercase, remove acentos."""
        text = text.lower().strip()
        # Remove acentos
        nfkd = unicodedata.normalize("NFKD", text)
        return "".join(c for c in nfkd if not unicodedata.combining(c))
    
    def _tokenize_spacy(self, text: str) -> dict:
        """Tokeniza usando spaCy com análise completa."""
        doc = self.nlp(text)
        
        tokens_raw = []
        tokens_clean = []
        tokens_lemma = []
        stopwords_removed = []
        pos_tags = {}
        entities = []
        
        for token in doc:
            word = token.text.strip()
            if not word:
                continue
                
            tokens_raw.append(word)
            pos_tags[word] = token.pos_
            
            # Verificar se é stopword
            if word in PT_STOPWORDS or token.is_stop or len(word) <= 2:
                stopwords_removed.append(word)
            else:
                tokens_clean.append(word)
                tokens_lemma.append(token.lemma_)
        
        # Extrair entidades nomeadas
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            })
        
        return {
            "tokens_raw": tokens_raw,
            "tokens_clean": tokens_clean,
            "tokens_lemma": tokens_lemma,
            "stopwords_removed": stopwords_removed,
            "pos_tags": pos_tags,
            "entities": entities,
        }
    
    def _tokenize_simple(self, text: str) -> dict:
        """Tokenização simples sem spaCy."""
        # Remove pontuação
        text_clean = re.sub(r"[^\w\s]", " ", text)
        words = text_clean.split()
        
        tokens_raw = words
        tokens_clean = []
        stopwords_removed = []
        
        for word in words:
            if word in PT_STOPWORDS or len(word) <= 2:
                stopwords_removed.append(word)
            else:
                tokens_clean.append(word)
        
        return {
            "tokens_raw": tokens_raw,
            "tokens_clean": tokens_clean,
            "tokens_lemma": tokens_clean,  # Sem lematização
            "stopwords_removed": stopwords_removed,
            "pos_tags": {w: "UNKNOWN" for w in tokens_raw},
            "entities": [],
        }
    
    def _classify_semantic_type(
        self,
        query: str,
        tokens: list[str],
        entities: list[dict] | None = None,
    ) -> tuple[SemanticType, float]:
        """
        Classifica o tipo semântico da query.
        
        Usa heurísticas, entidades do gazetteer e opcionalmente LLM.
        """
        entities = entities or []
        
        # 1. Detectar referência bíblica (João 3:16)
        ref_pattern = r"\b(\d?\s*[a-z]+)\s+(\d+)[:\.](\d+)\b"
        if re.search(ref_pattern, query, re.IGNORECASE):
            return SemanticType.REFERENCE, 0.95
        
        # 2. Detectar entidade de alta prioridade do gazetteer
        if entities and entities[0]["boost"] >= 2.5:
            return SemanticType.ENTITY, 0.9
        
        # 3. Detectar pergunta
        question_words = {"quem", "qual", "como", "onde", "quando", "porque", "por que"}
        if query.endswith("?") or (tokens and tokens[0] in question_words):
            return SemanticType.QUESTION, 0.85
        
        # 4. Detectar frase (múltiplas palavras significativas)
        if len(tokens) >= 2:
            return SemanticType.PHRASE, 0.75
        
        # 5. Palavra única
        if len(tokens) == 1:
            # Conceitos abstratos conhecidos
            abstract_concepts = {
                "amor", "fe", "esperanca", "graca", "salvacao", "perdao",
                "justica", "misericordia", "santidade", "pecado", "arrependimento",
            }
            if tokens[0] in abstract_concepts:
                return SemanticType.CONCEPT, 0.8
            
            # Se é entidade do gazetteer (mesmo com boost menor)
            if entities:
                return SemanticType.ENTITY, 0.75
            
            return SemanticType.KEYWORD, 0.7
        
        return SemanticType.KEYWORD, 0.5
    
    def _is_known_phrase(self, query: str) -> bool:
        """Verifica se é uma frase bíblica conhecida."""
        return query in KNOWN_BIBLICAL_PHRASES
    
    def _generate_ngrams(self, tokens: list[str]) -> tuple[list[str], list[str]]:
        """Gera bigrams e trigrams."""
        bigrams = []
        trigrams = []
        
        for i in range(len(tokens) - 1):
            bigrams.append(f"{tokens[i]}_{tokens[i+1]}")
        
        for i in range(len(tokens) - 2):
            trigrams.append(f"{tokens[i]}_{tokens[i+1]}_{tokens[i+2]}")
        
        return bigrams, trigrams
    
    def _calculate_boost_strategy(
        self,
        semantic_type: SemanticType,
        tokens_data: dict,
        is_known_phrase: bool,
        entities: list[dict] | None = None,
    ) -> dict:
        """
        Calcula estratégia de boost otimizada.
        
        Baseado no tipo semântico, análise linguística e entidades detectadas.
        """
        stopwords_count = len(tokens_data["stopwords_removed"])
        tokens_count = len(tokens_data["tokens_clean"])
        entities = entities or []
        
        # Distância dinâmica: stopwords + 1
        distance = stopwords_count + 1
        
        strategy = {
            "distance": distance,
            "tsquery_operator": f"<{distance}>" if distance > 1 else "<->",
            "entities_detected": len(entities),
        }
        
        # Se tem entidades de alto boost, usar boost do gazetteer
        if entities:
            max_entity_boost = max(e["boost"] for e in entities)
            strategy["entity_boost"] = max_entity_boost
            strategy["entity_types"] = list(set(e["type"] for e in entities))
        
        if semantic_type == SemanticType.ENTITY:
            # Entidade bíblica detectada (pessoa, lugar, evento, etc)
            entity_boost = entities[0]["boost"] if entities else 2.0
            strategy.update({
                "method": "entity_boost",
                "use_like_boost": True,
                "like_boost_factor": entity_boost,
                "expand": False,  # Não expandir nomes próprios
                "alpha": 0.7,  # Bem textual para entidades
                "explanation": f"Entidade bíblica detectada: {entities[0]['type'] if entities else 'unknown'}",
            })
        
        elif semantic_type == SemanticType.PHRASE:
            strategy.update({
                "method": "phrase_boost",
                "use_like_boost": True,
                "like_boost_factor": 2.0,
                "expand": False if is_known_phrase else True,
                "alpha": 0.6,  # Mais textual
                "explanation": "Frase exata detectada, priorizando match textual",
            })
        
        elif semantic_type == SemanticType.CONCEPT:
            strategy.update({
                "method": "semantic_expand",
                "use_like_boost": False,
                "expand": True,
                "alpha": 0.4,  # Mais semântico
                "explanation": "Conceito abstrato, priorizando expansão semântica",
            })
        
        elif semantic_type == SemanticType.REFERENCE:
            strategy.update({
                "method": "exact_reference",
                "use_like_boost": True,
                "like_boost_factor": 3.0,
                "expand": False,
                "alpha": 0.8,  # Muito textual
                "explanation": "Referência bíblica, match exato",
            })
        
        elif semantic_type == SemanticType.QUESTION:
            strategy.update({
                "method": "semantic_qa",
                "use_like_boost": False,
                "expand": True,
                "alpha": 0.3,  # Muito semântico
                "explanation": "Pergunta, priorizando busca semântica",
            })
        
        else:  # KEYWORD
            strategy.update({
                "method": "balanced",
                "use_like_boost": tokens_count == 1,
                "like_boost_factor": 1.5,
                "expand": tokens_count == 1,
                "alpha": 0.5,
                "explanation": "Keyword genérica, abordagem balanceada",
            })
        
        return strategy


# Função de conveniência
def analyze_query(query: str, **kwargs) -> NLPAnalysis:
    """
    Analisa query com NLP.
    
    Exemplo:
        analysis = analyze_query("paz na terra")
        print(analysis.to_tsquery())  # "(paz <2> terra)"
    """
    tool = NLPQueryTool(**kwargs)
    return tool.analyze(query)
