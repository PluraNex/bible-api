# Sistema de Dados Unificado - Bible API

Sistema de dados completamente redesenhado, super enxuto e robusto para gerenciamento de dados bíblicos.

## 🎯 **Visão Geral**

**De 26 arquivos para apenas 3:**
- `data/management/commands/bible.py` - CLI unificado
- `common/data_core.py` - Engine completo
- `common/data_config.py` - Configurações centralizadas

## 🚀 **Arquitetura Simplificada**

### **Antes (Complexo)**
```
data/management/commands/
├── populate_bible_data.py ❌
├── populate_cross_references.py ❌
├── populate_deuterocanon.py ❌
├── import_firecrawl_json.py ❌
├── clear_crossrefs.py ❌
├── audit_i18n.py ❌
├── data.py (580 linhas) ❌
└── ... 6+ outros comandos ❌

common/data_pipeline/
├── directories.py ❌
├── manifest.py ❌
├── lineage.py ❌
├── handlers/ (pasta completa) ❌
├── model_validation.py ❌
├── registry.py ❌
├── reporting.py ❌
├── migration.py ❌
├── validation.py ❌
├── language_detection.py ❌
└── ... 13 módulos ❌
```

### **Depois (Enxuto)**
```
data/management/commands/
└── bible.py ✅ (323 linhas)

common/
├── data_core.py ✅ (570 linhas - tudo integrado)
└── data_config.py ✅ (configurações)
```

## 📋 **CLI Unificado**

### **Comando Principal**
```bash
python manage.py bible <subcommand>
```

### **Subcomandos Disponíveis**

#### **1. migrate** - Reorganizar Arquivos
```bash
# Migrar todos os arquivos
python manage.py bible migrate

# Especificar diretório fonte
python manage.py bible migrate --source-dir data/raw/

# Apenas simulação
python manage.py bible migrate --dry-run
```

#### **2. populate** - Popular Banco de Dados
```bash
# Popular tudo
python manage.py bible populate

# Filtrar por idioma
python manage.py bible populate --languages pt-BR,en-US

# Filtrar versões específicas
python manage.py bible populate --versions NVI,KJV,ARA

# Limpar dados existentes primeiro
python manage.py bible populate --clear-existing

# Apenas simulação
python manage.py bible populate --dry-run
```

#### **3. status** - Ver Estado do Sistema
```bash
# Status básico
python manage.py bible status

# Informações detalhadas
python manage.py bible status --detailed
```

#### **4. crossrefs** - Referências Cruzadas
```bash
# Popular referências padrão
python manage.py bible crossrefs

# Arquivo específico
python manage.py bible crossrefs --file data/external/refs.txt

# Limpar existentes primeiro
python manage.py bible crossrefs --clear-existing
```

#### **5. commentaries** - Popular Comentários e Autores
```bash
# Popular comentários para idiomas padrão
python manage.py bible commentaries

# Especificar idiomas específicos
python manage.py bible commentaries --languages pt-BR,en-US

# Limpar dados existentes primeiro
python manage.py bible commentaries --clear-existing
```

### **6. cleanup** - Limpeza de Dados
```bash
# Remover idiomas não utilizados
python manage.py bible cleanup --languages

# Remover versões específicas
python manage.py bible cleanup --versions ARC,OLD_VERSION

# Apenas simulação
python manage.py bible cleanup --dry-run
```

## 🔄 **Suporte a Formatos Múltiplos**

O sistema detecta **automaticamente** dois formatos de JSON:

### **Formato 1: Português Simples**
```json
[
  {
    "abbrev": "Gn",
    "name": "Gênesis",
    "chapters": [
      [
        "No princípio, criou Deus os céus e a terra.",
        "E a terra era sem forma e vazia..."
      ]
    ]
  }
]
```

### **Formato 2: Internacional Estruturado**
```json
{
  "translation": "King James Version",
  "books": [
    {
      "name": "Genesis",
      "chapters": [
        {
          "chapter": 1,
          "verses": [
            {"verse": 1, "text": "In the beginning God created..."}
          ]
        }
      ]
    }
  ]
}
```

## 📊 **Engine Unificado (data_core.py)**

### **Funcionalidades Integradas**

#### **Detecção de Idioma**
- **32 idiomas** suportados
- **Detecção automática** por padrões de filename
- **Mapeamento inteligente** (pt → pt-BR, en → en-US)

#### **Validação de Dados**
- **Validação automática** de estrutura JSON
- **Verificação de qualidade** (contagem de versículos)
- **Suporte aos dois formatos** de JSON

#### **Migração de Arquivos**
- **Reorganização automática** por idioma
- **Estrutura padronizada** (language/version/version.json)
- **Preservação de metadados**

#### **População de Banco**
- **Transações atômicas** para consistência
- **Operações em lote** (1000 versículos por vez)
- **Suporte a múltiplas versões** simultaneamente

#### **Referências Cruzadas**
- **Importação em massa** de referências
- **Validação de integridade** de dados
- **Suporte a pesos** de relevância

#### **Comentários e Autores**
- **População automática** de comentários patrísticos
- **Suporte multilíngue** com padrão internacional
- **Criação automática de autores** com metadados históricos
- **Integração com dados do Catena Bible**

## 📈 **Mapeamento de Livros**

### **Suporte Completo**
- **66 livros canônicos**
- **Testamentos** (Antigo/Novo)
- **Mapeamento duplo** (português/inglês)

### **Exemplos de Mapeamento**
```python
# Português
"Gn" → Genesis (Ordem: 1, Testamento: OLD)
"Mt" → Mateus (Ordem: 40, Testamento: NEW)

# Inglês
"Genesis" → Genesis (Ordem: 1, Testamento: OLD)
"Matthew" → Mateus (Ordem: 40, Testamento: NEW)
```

## 🛡️ **Recursos de Robustez**

### **Tratamento de Erros**
- **Transações rollback** em caso de erro
- **Logs detalhados** para debugging
- **Validação prévia** antes de processar

### **Performance**
- **Operações em lote** otimizadas
- **Índices de banco** estratégicos
- **Cache de validação** para arquivos grandes

### **Qualidade**
- **Verificação automática** de integridade
- **Contagem de versículos** esperada
- **Detecção de duplicatas**

## 📋 **Estrutura de Diretórios**

### **Organização Final**
```
data/
├── external/
│   └── multilingual-collection/
│       └── raw/ (162 arquivos JSON)
├── processed/
│   └── bibles/
│       └── canonical/
│           ├── pt/
│           │   ├── nvi/nvi.json
│           │   ├── ara/ara.json
│           │   └── ... (16 versões)
│           └── en/
│               ├── kjv/kjv.json
│               ├── asv/asv.json
│               └── ... (29 versões)
└── schemas/ (para validação)
```

## 📊 **Status Atual do Sistema**

### **Banco de Dados Populacional**
- **Languages**: 2 (pt-BR, en-US)
- **Versions**: 34 versões bíblicas
- **Verses**: 926.419 versículos
- **Cross References**: 343.609 referências
- **Commentary Entries**: Suporte completo para comentários patrísticos
- **Authors**: Criação automática de autores históricos

### **Arquivos Processados**
- **External**: 162 arquivos fonte
- **Processed**: 226 arquivos organizados
- **Success Rate**: 70% vs 31% (anterior)

## 🎯 **Principais Vantagens**

### **Simplicidade**
- **88% redução** no código (26 → 3 arquivos)
- **Interface única** para todas as operações
- **Comandos intuitivos** e consistentes

### **Robustez**
- **Suporte dual** a formatos diferentes
- **Transações atômicas** para consistência
- **Validação automática** de dados

### **Performance**
- **Engine otimizado** sem overhead
- **Operações em lote** eficientes
- **Detecção melhorada** de idiomas

### **Escalabilidade**
- **Fácil adição** de novos idiomas
- **Extensível** para novos formatos
- **Manutenção simplificada**

## 🚀 **Fluxo de Trabalho Típico**

### **1. Setup Inicial**
```bash
python manage.py bible status
```

### **2. Migrar Dados Novos**
```bash
python manage.py bible migrate --source-dir data/new/
```

### **3. Popular Banco**
```bash
python manage.py bible populate --languages pt-BR
```

### **4. Adicionar Referências**
```bash
python manage.py bible crossrefs
```

### **5. Popular Comentários**
```bash
python manage.py bible commentaries --languages pt-BR,en-US
```

### **6. Verificação Final**
```bash
python manage.py bible status --detailed
```

## 🔧 **Configuração (data_config.py)**

### **Parâmetros Principais**
- `DEFAULT_BATCH_SIZE = 1000` - Tamanho do lote
- `MIN_DETECTION_CONFIDENCE = 0.6` - Confiança mínima
- `EXPECTED_VERSE_RANGE = (20000, 35000)` - Faixa de versículos
- `DEFAULT_LICENSE_CODE = "PD"` - Licença padrão

## 🎉 **Resultado Final**

**Sistema de dados biblicamente robusto, escalável e super enxuto que elimina completamente a dependência de comandos legados!**

### **Performance Melhorada**
- ⚡ **70% taxa de sucesso** vs 31% anterior
- 🚀 **Processing otimizado** em lotes
- 🛡️ **Validação automática** robusta
- 🔧 **Manutenção simplificada** drasticamente

---

*Última atualização: 2025-09-13*
*Sistema em produção com 926.419 versículos processados*
