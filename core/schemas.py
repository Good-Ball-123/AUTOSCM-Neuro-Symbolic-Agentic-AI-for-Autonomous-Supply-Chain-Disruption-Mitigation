# core/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime

# ==========================================
# 1. INGESTION LAYER
# ==========================================
class DisruptionEvent(BaseModel):
    model_config = ConfigDict(strict=True)

    event_id: UUID = Field(..., description="UUID unik dari AWS EventBridge")
    timestamp: datetime = Field(..., description="Waktu deteksi anomali")
    supplier_id: str = Field(..., max_length=20)
    material_id: str = Field(..., max_length=40)
    delay_hours: int = Field(gt=0, description="Keterlambatan dalam hitungan jam bulat")
    reason: Literal["WEATHER", "PORT_CONGESTION", "CUSTOMS", "MANUFACTURING_DEFECT", "UNKNOWN"]

# ==========================================
# 2. RISK ASSESSOR LAYER
# ==========================================
class RiskAssessmentPayload(BaseModel):
    model_config = ConfigDict(strict=True)

    var_score: float = Field(ge=0.0, le=1.0, description="Value-at-Risk komposit (0.0 - 1.0)")
    critical_min_inventory: float = Field(gt=0.0, description="Batas stok pengaman sebelum downtime")
    estimated_downtime_risk_pct: float = Field(ge=0.0, le=1.0)
    disruption_class: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# ==========================================
# 3. SOLVER DISPATCHER LAYER (KONTRAK EKSEKUSI)
# ==========================================
class MitigationPayload(BaseModel):
    model_config = ConfigDict(strict=True)

    disruption_id: UUID
    target_supplier_id: str = Field(..., description="ID Vendor alternatif atau eksisting")
    order_qty: float = Field(gt=0.0, description="Kuantitas PO mitigasi")
    unit: Literal["KG", "PCS", "LTR"]
    required_delivery_date: datetime
    freight_mode: Literal["AIR", "SEA", "ROAD", "RAIL"]
    carbon_kg_co2: float = Field(ge=0.0, description="Estimasi penalti karbon")
    solver_status: Literal["OPTIMAL", "FEASIBLE", "IIS_RELAXED"]

# ==========================================
# 4. SAP EXECUTOR LAYER
# ==========================================
class SAPExecutionLog(BaseModel):
    model_config = ConfigDict(strict=True)

    mitigation_id: UUID
    execution_timestamp: datetime
    sap_po_number: str = Field(..., description="Nomor dokumen PO di SAP S/4HANA")
    bapi_status: Literal["CREATED", "AMENDED", "FAILED"]
    http_status_code: int = Field(ge=200, le=599)
    audit_notes: Optional[str] = None

# ==========================================
# 5. LANGGRAPH SHARED STATE
# ==========================================
class AUTOSCMState(BaseModel):
    model_config = ConfigDict(strict=True)

    version: int = Field(default=1, description="Token Optimistic Concurrency Control")
    current_node: str = Field(..., description="Agen yang sedang berjalan")
    status: Literal["PROCESSING", "PENDING_APPROVAL", "EXECUTED", "FAILED"]
    
    event: Optional[DisruptionEvent] = None
    risk: Optional[RiskAssessmentPayload] = None
    mitigation_plan: Optional[MitigationPayload] = None
    execution_log: Optional[SAPExecutionLog] = None

    def increment_version(self):
        self.version += 1