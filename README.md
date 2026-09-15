# AUTOSCM: Autonomous Supply Chain Disruption Orchestrator

**Event:** Sokrates Agentic AI Hackathon 2026  
**Track:** Intelligent Supply Chain  
**Version:** 1.0.0-draft  

## 1. Overview
AUTOSCM is an enterprise-grade Neuro-Symbolic Multi-Agent System designed to transition supply chain operations from passive observability to active, self-healing execution. 

Built to address the critical latency in human-in-the-loop disruption mitigation, AUTOSCM autonomously ingests telemetry anomalies, simulates downstream production risks, formulates deterministic mathematical optimizations, and executes Purchase Order (PO) amendments directly into SAP S/4HANA. 

This architecture guarantees zero-hallucination execution by strictly isolating the Large Language Model (LLM) reasoning layer from the deterministic computational engines.

## 2. Core Architectural Principles
* **Zero-Hallucination Execution:** LLMs are restricted exclusively to orchestration and semantic routing. All numerical planning (freight cost, carbon penalty optimization, alternative routing) is solved deterministically by Google OR-Tools (MILP Solver).
* **Pre-Execution Sandboxing:** Before committing any transaction to the ERP state, a SimPy Discrete-Event Simulation runs a Monte Carlo behavioral twin to verify that the proposed mitigation prevents downstream stockouts.
* **Strict Data Contracts:** Cross-agent communication and SAP API payloads are aggressively validated using Pydantic v2 (`strict=True`).
* **Sliding Autonomy:** Execution is gated by a dynamic Value-at-Risk (VaR) score. Low-risk mitigations are executed autonomously; high-risk actions are routed to a Human Approval Gateway.

## 3. System Architecture Diagram

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffffff', 'primaryBorderColor': '#000000', 'primaryTextColor': '#000000', 'lineColor': '#000000', 'textColor': '#000000', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#ffffff', 'mainBkg': '#ffffff', 'nodeBorder': '#000000', 'clusterBkg': '#ffffff', 'clusterBorder': '#000000', 'fontSize': '12px'}}}%%
graph TD
    EBR["AWS EventBridge\n(Rule-based routing)"]
    IOT["AWS IoT Core\n(MQTT telemetry stream)"]
    IOT -->|"event payload JSON"| EBR

    EBR --> ISA
    ISA["Ingestion Sentinel Agent\nSchema validation & Anomaly detection"]
    ISA -->|"validated StateEvent"| DDB

    DDB[("DynamoDB\nOptimistic Locking (OCC)")]

    DDB --> RAA
    RAA["Risk Assessor Agent\nProduces: VaR score & disruption_class"]
    RAA -->|"RiskAssessmentPayload"| SDA

    SDA["Solver Dispatcher Agent\nRoutes to Sandbox & MILP Solver"]
    SDA --> SIM
    SIM["SimPy Discrete-Event\nBehavioral Twin Sandbox"]
    SIM -->|"feasibility_score"| GRB
    GRB["OR-Tools / Gurobi\nMILP Solver (IIS detection)"]
    GRB -->|"MitigationPlan"| GSA

    GSA["Governance & Safety Auditor Agent\nVaR threshold & compliance check"]
    GSA -->|"VaR < threshold"| AUTO["Fully Autonomous Execution"]
    GSA -->|"VaR >= threshold"| HG["Human Approval Gate"]
    AUTO --> SEA
    HG -->|"approved"| SEA

    SEA["SAP Executor Agent\nOData: POST /PurchaseOrderSet\nBAPI: BAPI_PO_CHANGE"]
    SEA -->|"Audit log"| DDB