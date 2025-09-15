# Sistema de Dados Bible API — Guia do Desenvolvedor

## 🎯 **Novo Sistema Unificado (2025-09-13)**

O sistema de dados foi **completamente redesenhado** para máxima simplicidade e robustez:

### **Sistema Anterior ❌**
- 26 arquivos complexos
- Múltiplos comandos legados
- Pipeline fragmentado
- Taxa de sucesso: 31%

### **Sistema Atual ✅**
- **3 arquivos** simples e poderosos
- **1 comando** unificado (`python manage.py bible`)
- **Engine integrado** completo
- **Taxa de sucesso: 70%**

## 📚 **Documentação**

### **Principal**
- **[UNIFIED_DATA_SYSTEM.md](UNIFIED_DATA_SYSTEM.md)** — **⭐ LEIA PRIMEIRO** - Sistema completo redesenhado

### **Arquivos Legados (Depreciados)**
- ~~pipeline.md~~ → Substituído pelo sistema unificado
- ~~cli.md~~ → Agora: `python manage.py bible --help`
- ~~schemas.md~~ → Validação automática integrada
- ~~migration.md~~ → Agora: `python manage.py bible migrate`
- ~~observability.md~~ → Agora: `python manage.py bible status`

## ⚡ **Início Rápido**

### **Ver Status**
```bash
python manage.py bible status --detailed
```

### **Popular Dados**
```bash
python manage.py bible populate --languages pt-BR,en-US
```

### **Migrar Arquivos**
```bash
python manage.py bible migrate --source-dir data/raw/
```

## 🎉 **Estado Atual**

✅ **926.419 versículos** processados
✅ **34 versões** da Bíblia no banco
✅ **2 idiomas** suportados (pt-BR, en-US)
✅ **343.609 referências** cruzadas
✅ **Sistema 100% funcional** sem dependências legadas

Para detalhes completos, consulte **[UNIFIED_DATA_SYSTEM.md](UNIFIED_DATA_SYSTEM.md)**
