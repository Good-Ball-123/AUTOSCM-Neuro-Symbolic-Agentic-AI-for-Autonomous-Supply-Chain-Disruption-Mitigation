# Functional Requirements (FR) Specification
**Project:** AUTOSCM - Neuro-Symbolic Multi-Agent System
**Document Version:** 1.0.0

Dokumen ini menjabarkan spesifikasi fungsional untuk ke-5 agen utama dan lapisan komputasi pada arsitektur AUTOSCM. Seluruh fungsi beroperasi di dalam topologi *State Graph* (LangGraph) dan bertukar data melalui *Shared Immutable State* di DynamoDB.

---

## FR-01: Ingestion Sentinel Agent (Data Ingestion)
Agen ini bertugas sebagai pintu gerbang (*entry point*) untuk semua telemetri logistik dari lapisan infrastruktur AWS.

*   **FR-1.1: Event Listener.** Agen harus menerima *payload* JSON telemetri yang di-rutekan melalui aturan AWS EventBridge dari AWS IoT Core.
*   **FR-1.2: Schema Validation.** Agen wajib memvalidasi *payload* menggunakan Pydantic v2. Jika *payload* cacat (misal: format stempel waktu salah), *event* di-drop ke *Dead Letter Queue* (DLQ).
*   **FR-1.3: Anomaly Detection.** Agen harus mendeteksi apakah deviasi pengiriman berada di luar batas toleransi menggunakan perhitungan deviasi statistik (*Z-score* / IQR) terhadap data historis vendor.
*   **FR-1.4: State Initialization.** Menulis objek `DisruptionEvent` yang telah tervalidasi ke AWS DynamoDB dan menghasilkan ID unik (`disruption_id`). Penulisan menggunakan *Optimistic Concurrency Control* (atribut `version = 1`).

**Acceptance Criteria:**
- *Payload* JSON yang tidak sesuai skema Pydantic langsung ditolak (HTTP 400 setara).
- Deteksi anomali selesai dalam waktu < 500 milidetik setelah *event* diterima dari EventBridge.

---

## FR-02: Risk Assessor Agent (Context & Scoring)
Agen ini menggunakan instans LLM (Claude 3.5 Sonnet / GPT-4o) murni untuk klasifikasi konteks, bukan komputasi numerik akhir.

*   **FR-2.1: Entity Extraction.** LLM mengekstrak konteks disrupsi: `supplier_id`, `affected_material`, `estimated_delay_hours`, dan `root_cause`.
*   **FR-2.2: Value-at-Risk (VaR) Calculation.** Agen menghitung skor komposit VaR (skala 0.0 hingga 1.0) berdasarkan:
    - *Lead-time variance* historis dari vendor.
    - Nilai finansial dari material yang tertunda.
    - Dampak pada *Critical Minimum Inventory* (CMI).
*   **FR-2.3: State Update.** Memperbarui *state* di DynamoDB dengan objek `RiskAssessmentPayload` (increment atribut `version`).

**Acceptance Criteria:**
- Skor VaR dihasilkan secara konsisten berformat `float` (0.0 - 1.0).
- Tidak ada manipulasi nilai numerik material oleh LLM di luar kalkulasi VaR.

---

## FR-03: SimPy Behavioral Twin Sandbox (Simulation)
Modul ini merupakan lapisan komputasi stokastik *pre-execution*.

*   **FR-3.1: Scenario Injection.** Menerima parameter kondisi saat ini (*current inventory*, *demand run-rate*) dan parameter disrupsi (*delay hours*).
*   **FR-3.2: Monte Carlo Execution.** Menjalankan simulasi *Discrete-Event* menggunakan SimPy dengan minimal N=500 iterasi untuk menangkap variabilitas stokastik.
*   **FR-3.3: Outcome Distribution.** Menghitung probabilitas tingkat stok pada P5, P50 (median), dan P95 selama 72 jam ke depan.
*   **FR-3.4: Feasibility Gate.** Jika distribusi P5 (skenario terburuk) menembus batas stok 0 (potensi *downtime* 100%), agen menandai skenario sebagai `CRITICAL_RISK`.

**Acceptance Criteria:**
- Eksekusi 500 iterasi Monte Carlo selesai dalam waktu < 3 detik (menggunakan vektorisasi NumPy jika perlu).
- Menghasilkan *feasibility score* deterministik.

---

## FR-04: Solver Dispatcher Agent (MILP Optimization)
Agen ini menghubungkan *state* dengan Google OR-Tools untuk menyelesaikan masalah optimisasi matematis.

*   **FR-4.1: Objective Formulation.** Agen menerjemahkan *state* saat ini menjadi fungsi objektif MILP yang meminimalkan: biaya *spot-freight*, penalti SLA, emisi karbon logistik, dan biaya *downtime*.
*   **FR-4.2: Hard Constraints Implementation.** Mengunci batasan matematis: kapasitas maksimum vendor alternatif (`Cap_s`) dan keseimbangan aliran inventori (`Inventory Flow Balance`).
*   **FR-4.3: Execution & Parsing.** Memanggil OR-Tools (GLOP/CP-SAT) dan mem-parsing hasil optimal (misal: rute baru, kuantitas vendor cadangan) kembali ke dalam JSON Pydantic skema `MitigationPlan`.
*   **FR-4.4: IIS Handling.** Jika *solver* merespons *INFEASIBLE*, agen menjalankan rutin *Irreducible Infeasible Subsystem* (IIS) untuk menemukan batasan yang berkonflik, melonggarkannya (misal: menurunkan buffer stock sementara), dan me-run ulang *solver*.

**Acceptance Criteria:**
- Tidak ada parameter formulasi (*variables*, *constraints*) yang dihalusinasikan oleh LLM.
- Menghasilkan output yang lolos validasi `strict=True` dari model Pydantic `MitigationPayload`.

---

## FR-05: Governance & Safety Auditor Agent (Decision Gateway)
Agen ini bertindak sebagai penjaga gerbang otonomi (*Sliding Autonomy Gate*).

*   **FR-5.1: Threshold Evaluation.** Membaca skor VaR dari *state* dan membandingkannya dengan `AUTONOMY_THRESHOLD` (standar: 0.35).
*   **FR-5.2: Autonomous Routing.** Jika `VaR < 0.35`, rute graf dialihkan langsung ke `SAP Executor Agent`.
*   **FR-5.3: Human-in-the-Loop Routing.** Jika `VaR >= 0.35` atau resolusi solver membutuhkan IIS *relaxation*, eksekusi dibekukan sementara.
*   **FR-5.4: Webhook Trigger.** Mengirim *payload* persetujuan via API ke *Human Approval Dashboard* (beserta notifikasi Slack/Teams webhook). Menunggu *callback* asinkron (Approve/Reject).

**Acceptance Criteria:**
- Sistem tidak pernah mengeksekusi skenario VaR tinggi secara otonom tanpa adanya *callback token* persetujuan dari *dashboard*.

---

## FR-06: SAP Executor Agent (ERP Action)
Lapisan terakhir yang melakukan mutasi data langsung ke sistem ERP.

*   **FR-6.1: Payload Formatting.** Mengubah `MitigationPayload` menjadi format JSON OData yang valid untuk SAP S/4HANA.
*   **FR-6.2: PO Creation.** Memanggil POST `/sap/opu/odata/sap/MM_PUR_PO_MAINT_SRV/PurchaseOrderSet` untuk menerbitkan pesanan darurat ke vendor pengganti.
*   **FR-6.3: PO Amendment.** Memanggil RFC `BAPI_PO_CHANGE` untuk mengurangi kuota pesanan dari vendor asli yang mengalami disrupsi.
*   **FR-6.4: Audit Trail.** Membaca respons HTTP dari SAP (Status 200/201). Menyimpan nomor *Purchase Order* SAP yang baru ke dalam DynamoDB dan menutup siklus *State Graph* sebagai `COMPLETED`.

**Acceptance Criteria:**
- Payload API ke SAP S/4HANA terkirim dengan otentikasi yang valid.
- Setiap mutasi ERP tercatat secara atomik di DynamoDB untuk kebutuhan audit.