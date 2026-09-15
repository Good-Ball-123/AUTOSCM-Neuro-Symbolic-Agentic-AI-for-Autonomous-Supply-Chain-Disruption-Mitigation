# AUTOSCM 🌐
**Autonomous Supply Chain Disruption Orchestrator**

[![Hackathon](https://img.shields.io/badge/Event-Sokrates_Agentic_AI_Hackathon_2026-0f1117?style=flat-square)](#)
[![Track](https://img.shields.io/badge/Track-Intelligent_Supply_Chain-1a4fd6?style=flat-square)](#)
[![Tech Stack](https://img.shields.io/badge/Tech-LangGraph_%7C_OR--Tools_%7C_SimPy_%7C_SAP-success?style=flat-square)](#)

Dokumen ini merupakan Master Documentation untuk proyek **AUTOSCM**, sebuah ekosistem *Neuro-Symbolic Multi-Agent* yang dibangun untuk **Agentic AI Hackathon by Sokrates 2026** pada kategori **Intelligent Supply Chain**[cite: 1].

---

## 📑 Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Problem Statement & Business Case](#2-problem-statement--business-case)
3. [System Architecture (State Graph)](#3-system-architecture)
4. [Functional Requirements (FR)](#4-functional-requirements-fr)
5. [Data Contracts & Schemas (Pydantic)](#5-data-contracts--schemas-pydantic)
6. [Success Metrics (KPIs)](#6-success-metrics-kpis)

---

## 1. Executive Summary
AUTOSCM menggeser paradigma operasi rantai pasok dari *passive observability* menjadi *active self-healing execution*. Sistem ini memitigasi disrupsi logistik secara otonom (*closed-loop*) dengan menggabungkan penalaran *Large Language Models* (LLM), *Discrete-Event Simulation* (DES), dan *Mixed-Integer Linear Programming* (MILP) *Solver*. Fokus produk ini adalah mengeksekusi penyesuaian *Purchase Order* (PO) secara langsung ke sistem SAP S/4HANA dalam waktu kurang dari 120 detik (MTTM) sejak anomali terdeteksi oleh AWS IoT.

## 2. Problem Statement & Business Case
*   **Latency in Existing SOTA:** Platform SCM eksisting (SAP IBP, AWS Supply Chain) mengandalkan integrasi *batch* dan heuristik statis, sehingga masih bertindak sebagai alat bantu visual (*dashboard*), bukan agen pengeksekusi.
*   **Human-in-the-Loop Bottleneck:** Eksekusi mitigasi manual memakan waktu 4-8 jam. Pada skenario pabrik *Just-in-Time* (JIT), jeda ini berpotensi memicu *production line downtime* yang menelan kerugian miliaran rupiah per jam.
*   **LLM Hallucination Risk:** Model LLM murni rentan terhadap halusinasi angka. Praktik industri tidak mengizinkan LLM menebak kuantitas pemesanan atau rute pengiriman tanpa fondasi matematis yang deterministik.

---

## 3. System Architecture

Arsitektur AUTOSCM tidak berjalan secara linear, melainkan menggunakan topologi *State Graph* (via LangGraph) dengan 5 agen terpisah yang saling berkomunikasi melalui *shared state* di AWS DynamoDB (diamankan dengan *Optimistic Concurrency Control*).

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffffff', 'primaryBorderColor': '#000000', 'primaryTextColor': '#000000', 'lineColor': '#000000', 'textColor': '#000000', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#ffffff', 'mainBkg': '#ffffff', 'nodeBorder': '#000000', 'clusterBkg': '#ffffff', 'clusterBorder': '#000000', 'fontSize': '12px'}}}%%
graph TD
    %% ── Data Ingestion Layer ──
    EBR["AWS EventBridge\n(Rule-based routing)"]
    IOT["AWS IoT Core\n(MQTT telemetry stream)"]
    IOT -->|"event payload JSON"| EBR

    %% ── Agent 1: Ingestion Sentinel ──
    EBR --> ISA
    ISA["Ingestion Sentinel Agent\nSchema validation · Out-of-Distribution\nAnomaly detection (Z-score / IQR)"]
    ISA -->|"validated StateEvent"| DDB

    %% ── Shared State Store ──
    DDB[("DynamoDB\nOptimistic Locking\n(version attribute + ConditionExpression)")]

    %% ── Agent 2: Risk Assessor ──
    DDB --> RAA
    RAA["Risk Assessor Agent\nLLM: GPT-4o / Bedrock Claude 3.5\nProduces: VaR score · disruption_class"]
    RAA -->|"RiskAssessmentPayload (Pydantic v2)"| SDA

    %% ── Agent 3: Solver Dispatcher ──
    SDA["Solver Dispatcher Agent\nRoutes to SimPy Sandbox → MILP Solver"]
    SDA --> SIM
    SIM["SimPy Discrete-Event\nBehavioral Twin Sandbox\n(Monte Carlo N=500)"]
    SIM -->|"feasibility_score"| GRB
    GRB["OR-Tools / Gurobi\nMILP Solver\n(IIS detection on infeasible)"]
    GRB -->|"MitigationPlan (Pydantic v2)"| GSA

    %% ── Sliding Autonomy Gate ──
    GSA["Governance & Safety Auditor Agent\nVaR threshold · policy compliance check"]
    GSA -->|"VaR < threshold"| AUTO["Fully Autonomous Execution"]
    GSA -->|"VaR ≥ threshold"| HG["Human Approval Gate\n(SNS notification + UI)"]
    AUTO --> SEA
    HG -->|"approved"| SEA

    %% ── Agent 4: SAP Executor ──
    SEA["SAP Executor Agent\nOData: POST /PurchaseOrderSet\nBAPI: BAPI_PO_CHANGE\nSAP S/4HANA 2023+"]
    SEA -->|"Audit log → DynamoDB"| DDB