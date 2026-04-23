from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, Enum, JSON, Float, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    viewer = "viewer"


class ReportFormat(str, enum.Enum):
    pdf = "pdf"
    excel = "excel"
    powerpoint = "powerpoint"
    dashboard = "dashboard"


class ReportStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ReportFrequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    manual = "manual"


class IntegrationStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    error = "error"
    pending = "pending"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.manager)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    clients = relationship("Client", back_populates="owner", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    company = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    logo_url = Column(String(500))
    brand_color_primary = Column(String(7), default="#3B82F6")
    brand_color_secondary = Column(String(7), default="#1E40AF")
    is_active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="clients")
    integrations = relationship("Integration", back_populates="client", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="client", cascade="all, delete-orphan")
    kpis = relationship("CustomKPI", back_populates="client", cascade="all, delete-orphan")


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    platform = Column(String(100), nullable=False)
    display_name = Column(String(255))
    credentials = Column(Text)   # AES-256-GCM encrypted blob (base64)
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.pending)
    last_synced_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    config = Column(JSON)  # platform-specific config (account IDs etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (UniqueConstraint("client_id", "platform", name="uq_client_platform"),)

    client = relationship("Client", back_populates="integrations")
    metrics = relationship("Metric", back_populates="integration", cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    title = Column(String(255), nullable=False)
    frequency = Column(Enum(ReportFrequency), default=ReportFrequency.manual)
    format = Column(Enum(ReportFormat), default=ReportFormat.pdf)
    status = Column(Enum(ReportStatus), default=ReportStatus.pending)
    date_from = Column(DateTime(timezone=True))
    date_to = Column(DateTime(timezone=True))
    platforms = Column(JSON)  # list of platform names to include
    kpi_config = Column(JSON)  # which KPIs to show
    file_path = Column(String(500))
    file_url = Column(String(500))
    error_message = Column(Text)
    generated_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("Client", back_populates="reports")
    metrics = relationship("Metric", back_populates="report")


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=True)
    platform = Column(String(100), nullable=False)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float)
    metric_unit = Column(String(50))  # currency, percentage, count, etc.
    date = Column(DateTime(timezone=True), nullable=False)
    dimensions = Column(JSON)  # campaign, ad_set, ad, etc.
    raw_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    integration = relationship("Integration", back_populates="metrics")
    report = relationship("Report", back_populates="metrics")


class CustomKPI(Base):
    __tablename__ = "custom_kpis"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    formula = Column(Text)  # e.g., "spend / conversions"
    unit = Column(String(50))
    target_value = Column(Float)
    platforms = Column(JSON)  # which platforms this KPI applies to
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="kpis")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")
