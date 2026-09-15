# Product Requirements Document (PRD)
**Project Name:** AUTOSCM (Autonomous Supply Chain Disruption Orchestrator)
**Track:** Intelligent Supply Chain (Sokrates Agentic AI Hackathon 2026)
**Document Version:** 1.0.0
**Status:** In Development
**Date:** September 2026

---

## 1. Executive Summary
AUTOSCM adalah ekosistem *Neuro-Symbolic Multi-Agent* yang memitigasi disrupsi rantai pasok secara otonom (*closed-loop*). Sistem ini mengeliminasi latensi *human-in-the-loop* dengan menggabungkan penalaran *Large Language Models* (LLM) dengan *Discrete-Event Simulation* (DES) dan *Mixed-Integer Linear Programming* (MILP) *Solver*. Fokus utama produk ini adalah mendeteksi, mensimulasikan, mengoptimasi, dan mengeksekusi penyesuaian *Purchase Order* (PO) secara langsung ke sistem SAP S/4HANA dalam waktu kurang dari 120 detik (MTTM).

## 2. Problem Statement & Business Case
*   **Latency in Existing SOTA:** Platform SCM eksisting (seperti SAP IBP, AWS Supply Chain) mengandalkan integrasi *batch* dan heuristik statis, menjadikan produk-produk tersebut bertindak sebagai *passive observability layer*, bukan *active execution engine*.
*   **Human-in-the-Loop Bottleneck:** Eksekusi mitigasi saat ini membutuhkan tinjauan manual, menyebabkan *Mean Time to Mitigate* (MTTM) berkisar antara 4-8 jam. Pada skenario manufaktur *Just-in-Time* (JIT), latensi ini memicu *production line downtime* yang merugikan hingga miliaran rupiah per jam.
*   **LLM Hallucination Risk:** Upaya menggunakan LLM murni untuk penjadwalan rantai pasok rentan terhadap halusinasi angka dan format, membuatnya tidak layak untuk mengeksekusi mutasi API langsung ke sistem ERP.

## 3. Product Principles
1.  **Zero-Hallucination Execution:** LLM tidak diizinkan melakukan kalkulasi matematis atau menentukan rute. LLM murni beroperasi sebagai *reasoning layer* yang menyusun parameter untuk *deterministic solver*.
2.  **Pre-Execution Sandboxing:** Tidak ada mutasi *state* ERP tanpa verifikasi dampak. Setiap skenario mitigasi harus melewati pengujian *Monte Carlo* di *Behavioral Twin Sandbox*.
3.  **Strict Data Contracts:** Seluruh pertukaran data internal dan eksternal wajib tervalidasi skema statis (Pydantic v2 `strict=True`).
4.  **Value-at-Risk (VaR) Sliding Autonomy:** Otonomi eksekusi dikendalikan secara dinamis berdasarkan ambang batas skor VaR; memisahkan *Fully Autonomous Execution* dengan *Human Approval Gate*.

---

## 4. System Architecture Overview

Arsitektur AUTOSCM bertumpu pada topologi *State Graph* (LangGraph) dengan 5 agen terpisah yang saling berkomunikasi melalui *shared state* yang diamankan menggunakan *Optimistic Concurrency Control* (OCC) di AWS DynamoDB.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffffff', 'primaryBorderColor': '#000000', 'primaryTextColor': '#000000', 'lineColor': '#000000'}}}%%
graph LR
    AWS[AWS EventBridge] --> IA(Ingestion Agent)
    IA --> DB[(DynamoDB State)]
    DB --> RA(Risk Assessor)
    RA --> SD(Solver Dispatcher)
    SD --> SIM[SimPy Sandbox]
    SIM --> MILP[OR-Tools Solver]
    MILP --> GA(Governance Auditor)
    GA -->|VaR < Threshold| EX(SAP Executor)
    GA -->|VaR >= Threshold| UI[React Approval UI]
    UI -->|Approved| EX
    EX --> SAP[SAP S/4HANA]