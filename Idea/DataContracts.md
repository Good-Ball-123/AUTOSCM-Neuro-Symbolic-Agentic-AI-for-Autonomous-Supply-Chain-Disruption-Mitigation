# Data Contracts & Schemas Specification
**Project:** AUTOSCM - Neuro-Symbolic Multi-Agent System
**Document Version:** 1.0.0
**Framework:** Pydantic v2

Dokumen ini mendefinisikan skema data statis (*Data Contracts*) yang digunakan untuk memvalidasi *payload* input/output di seluruh *nodes* LangGraph. Skema ini dikonfigurasi dengan `ConfigDict(strict=True)` untuk secara mutlak menolak halusinasi tipe data dari LLM sebelum berinteraksi dengan API SAP S/4HANA atau *deterministic solver*.

---

## 1. Core Principles
1. **Strict Type Coercion Disable:** LLM sering kali mencoba memaksakan *string* ke *float* (misal: `"100.5"` alih-alih `100.5`). Mode `strict=True` pada Pydantic v2 akan melempar `ValidationError` secara instan, mencegah data kotor masuk ke *solver* atau *database*.
2. **Deterministic Enums:** Semua kategori kualitatif (seperti *freight mode*, status solver) wajib menggunakan `Literal` atau `Enum`.
3. **Immutability & Versioning:** Seluruh perubahan *state* ke DynamoDB membutuhkan inkrementasi atribut `version` untuk *Optimistic Concurrency Control* (OCC).

---

## 2. Python Dependencies
```python
from pydantic import BaseModel, Field, ConfigDict, UUID4, confloat, AwareDatetime
from typing import Optional, Literal, List
from datetime import datetime