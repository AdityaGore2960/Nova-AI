"""
Nova-AI — SQLAlchemy ORM Models
Database: PostgreSQL 16 + PostGIS 3.4
ORM: SQLAlchemy 2.x (async-compatible, declarative)
"""

import enum
import uuid
from datetime import date, datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import expression
from sqlalchemy.types import Enum as SAEnum


# ---------------------------------------------------------------------------
# Base & Enums
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class DatasetType(str, enum.Enum):
    satellite_imagery = "satellite_imagery"
    geological_map = "geological_map"
    geochemistry = "geochemistry"
    geophysics = "geophysics"
    dem = "dem"
    other = "other"


class DatasetStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class LayerType(str, enum.Enum):
    lithology = "lithology"
    fault = "fault"
    fold = "fold"
    alteration = "alteration"
    mineralization = "mineralization"
    contact = "contact"
    structure = "structure"
    other = "other"


class JobStatus(str, enum.Enum):
    pending = "pending"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ModelType(str, enum.Enum):
    cnn = "cnn"
    xgboost = "xgboost"
    random_forest = "random_forest"
    ensemble = "ensemble"
    svm = "svm"
    other = "other"


class ModelStatus(str, enum.Enum):
    training = "training"
    staging = "staging"
    production = "production"
    archived = "archived"
    failed = "failed"


class ReportStatus(str, enum.Enum):
    draft = "draft"
    generating = "generating"
    ready = "ready"
    failed = "failed"


class ReportFormat(str, enum.Enum):
    pdf = "pdf"
    geotiff = "geotiff"
    geojson = "geojson"
    csv = "csv"
    xlsx = "xlsx"


class MineralType(str, enum.Enum):
    gold = "gold"
    copper = "copper"
    silver = "silver"
    zinc = "zinc"
    lead = "lead"
    nickel = "nickel"
    uranium = "uranium"
    other = "other"


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------

class TimestampMixin:
    created_at = Column(
        "created_at",
        type_=sqlalchemy_utcnow(),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        "updated_at",
        type_=sqlalchemy_utcnow(),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


def sqlalchemy_utcnow():
    from sqlalchemy import DateTime
    from sqlalchemy.types import TypeDecorator
    import sqlalchemy

    class TZDateTime(TypeDecorator):
        impl = sqlalchemy.DateTime
        cache_ok = True

        def process_bind_param(self, value, dialect):
            return value

        def process_result_value(self, value, dialect):
            return value

    return TZDateTime(timezone=True)


# ---------------------------------------------------------------------------
# Core Tables
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole, name="user_role"), nullable=False, default=UserRole.analyst)
    status = Column(SAEnum(UserStatus, name="user_status"), nullable=False, default=UserStatus.active)
    avatar_url = Column(Text)
    organization = Column(String(255))
    last_login_at = Column(sqlalchemy_utcnow())
    created_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now())
    updated_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    owned_projects = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id")
    project_memberships = relationship("ProjectMember", back_populates="user")
    submitted_jobs = relationship("AnalysisJob", back_populates="submitter")
    reports = relationship("Report", back_populates="creator")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    target_mineral = Column(SAEnum(MineralType, name="mineral_type"), nullable=False, default=MineralType.gold)
    bbox = Column(Geometry("POLYGON", srid=4326))
    country = Column(String(100))
    region = Column(String(100))
    is_archived = Column(Boolean, nullable=False, default=False)
    metadata = Column(JSONB, nullable=False, server_default=expression.text("'{}'::jsonb"))
    created_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now())
    updated_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="owned_projects", foreign_keys=[owner_id])
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("AnalysisJob", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="project", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="project")

    __table_args__ = (
        Index("idx_projects_bbox", "bbox", postgresql_using="gist"),
    )


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(SAEnum(UserRole, name="user_role"), nullable=False, default=UserRole.viewer)
    invited_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now())

    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    data_type = Column(SAEnum(DatasetType, name="dataset_type"), nullable=False)
    status = Column(SAEnum(DatasetStatus, name="dataset_status"), nullable=False, default=DatasetStatus.pending)
    file_path = Column(Text, nullable=False)
    file_size_bytes = Column(BigInteger)
    file_format = Column(String(50))
    crs_epsg = Column(Integer)
    resolution_m = Column(Float)
    band_count = Column(Integer)
    bbox = Column(Geometry("POLYGON", srid=4326))
    acquisition_date = Column(Date)
    source = Column(String(255))
    metadata = Column(JSONB, nullable=False, server_default=expression.text("'{}'::jsonb"))
    created_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now())
    updated_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="datasets")
    geological_layers = relationship("GeologicalLayer", back_populates="dataset", cascade="all, delete-orphan")
    geochemistry_samples = relationship("GeochemistrySample", back_populates="dataset", cascade="all, delete-orphan")
    geophysics_observations = relationship("GeophysicsObservation", back_populates="dataset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_datasets_bbox", "bbox", postgresql_using="gist"),
        Index("idx_datasets_metadata", "metadata", postgresql_using="gin"),
    )


# ---------------------------------------------------------------------------
# Geological Layers
# ---------------------------------------------------------------------------

class GeologicalLayer(Base):
    __tablename__ = "geological_layers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    layer_type = Column(SAEnum(LayerType, name="layer_type"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    geometry = Column(Geometry("GEOMETRY", srid=4326), nullable=False)
    attributes = Column(JSONB, nullable=False, server_default=expression.text("'{}'::jsonb"))
    source = Column(String(255))
    confidence_score = Column(Float, CheckConstraint("confidence_score BETWEEN 0 AND 1"))
    created_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now())

    dataset = relationship("Dataset", back_populates="geological_layers")

    __table_args__ = (
        Index("idx_geo_layers_geom", "geometry", postgresql_using="gist"),
        Index("idx_geo_layers_attrs", "attributes", postgresql_using="gin"),
    )


class GeochemistrySample(Base):
    __tablename__ = "geochemistry_samples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    sample_id = Column(String(100))
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    depth_m = Column(Float)
    elements = Column(JSONB, nullable=False, server_default=expression.text("'{}'::jsonb"))
    sample_type = Column(String(50))
    collected_at = Column(Date)
    created_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now())

    dataset = relationship("Dataset", back_populates="geochemistry_samples")

    __table_args__ = (
        Index("idx_geochem_location", "location", postgresql_using="gist"),
        Index("idx_geochem_elements", "elements", postgresql_using="gin"),
    )


class GeophysicsObservation(Base):
    __tablename__ = "geophysics_observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    magnetic_nT = Column(Float)
    gravity_mGal = Column(Float)
    radiometric_K = Column(Float)
    radiometric_U = Column(Float)
    radiometric_Th = Column(Float)
    em_conductivity = Column(Float)
    attributes = Column(JSONB, nullable=False, server_default=expression.text("'{}'::jsonb"))
    observed_at = Column(Date)
    created_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now())

    dataset = relationship("Dataset", back_populates="geophysics_observations")

    __table_args__ = (
        Index("idx_geophys_location", "location", postgresql_using="gist"),
    )


# ---------------------------------------------------------------------------
# ML Models & Predictions
# ---------------------------------------------------------------------------

class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    model_type = Column(SAEnum(ModelType, name="model_type"), nullable=False)
    status = Column(SAEnum(ModelStatus, name="model_status"), nullable=False, default=ModelStatus.training)
    artifact_path = Column(Text, nullable=False)
    onnx_path = Column(Text)
    target_mineral = Column(SAEnum(MineralType, name="mineral_type"))
    hyperparameters = Column(JSONB, nullable=False, server_default=expression.text("'{}'::jsonb"))
    metrics = Column(JSONB, nullable=False, server_default=expression.text("'{}'::jsonb"))
    feature_names = Column(ARRAY(Text))
    trained_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    training_job_id = Column(UUID(as_uuid=True))
    notes = Column(Text)
    created_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now())
    updated_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now(), onupdate=func.now())

    jobs = relationship("AnalysisJob", back_populates="model")
    predictions = relationship("Prediction", back_populates="model")
    outputs = relationship("ModelOutput", back_populates="model")

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_name_version"),
        Index("idx_model_metrics", "metrics", postgresql_using="gin"),
    )


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    model_id = Column(UUID(as_uuid=True), ForeignKey("model_registry.id", ondelete="SET NULL"))
    job_name = Column(String(255))
    status = Column(SAEnum(JobStatus, name="job_status"), nullable=False, default=JobStatus.pending)
    parameters = Column(JSONB, nullable=False, server_default=expression.text("'{}'::jsonb"))
    dataset_ids = Column(ARRAY(UUID(as_uuid=True)))
    celery_task_id = Column(String(255))
    progress_pct = Column(SmallInteger, default=0)
    error_message = Column(Text)
    started_at = Column(sqlalchemy_utcnow())
    completed_at = Column(sqlalchemy_utcnow())
    created_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now())

    project = relationship("Project", back_populates="jobs")
    submitter = relationship("User", back_populates="submitted_jobs")
    model = relationship("ModelRegistry", back_populates="jobs")
    predictions = relationship("Prediction", back_populates="job", cascade="all, delete-orphan")
    outputs = relationship("ModelOutput", back_populates="job", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="job")

    __table_args__ = (
        Index("idx_jobs_created", "created_at", postgresql_ops={"created_at": "DESC"}),
        CheckConstraint("progress_pct BETWEEN 0 AND 100", name="ck_progress_range"),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    model_id = Column(UUID(as_uuid=True), ForeignKey("model_registry.id", ondelete="SET NULL"))
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=False)
    probability = Column(Float, nullable=False)
    confidence_lower = Column(Float)
    confidence_upper = Column(Float)
    risk_class = Column(String(20))
    created_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now())

    job = relationship("AnalysisJob", back_populates="predictions")
    project = relationship("Project", back_populates="predictions")
    model = relationship("ModelRegistry", back_populates="predictions")
    features = relationship("PredictionFeature", back_populates="prediction", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_predictions_geom", "geometry", postgresql_using="gist"),
        Index("idx_predictions_probability", "probability", postgresql_ops={"probability": "DESC"}),
        CheckConstraint("probability BETWEEN 0 AND 1", name="ck_probability_range"),
    )


class PredictionFeature(Base):
    __tablename__ = "prediction_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False)
    feature_values = Column(JSONB, nullable=False, server_default=expression.text("'{}'::jsonb"))
    shap_values = Column(JSONB, nullable=False, server_default=expression.text("'{}'::jsonb"))
    shap_base_value = Column(Float)
    created_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now())

    prediction = relationship("Prediction", back_populates="features")

    __table_args__ = (
        Index("idx_pred_features_shap", "shap_values", postgresql_using="gin"),
        Index("idx_pred_features_vals", "feature_values", postgresql_using="gin"),
    )


class ModelOutput(Base):
    __tablename__ = "model_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    model_id = Column(UUID(as_uuid=True), ForeignKey("model_registry.id", ondelete="SET NULL"))
    output_type = Column(String(100), nullable=False)
    file_path = Column(Text, nullable=False)
    file_format = Column(String(50))
    bbox = Column(Geometry("POLYGON", srid=4326))
    summary_stats = Column(JSONB, nullable=False, server_default=expression.text("'{}'::jsonb"))
    crs_epsg = Column(Integer, default=4326)
    resolution_m = Column(Float)
    created_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now())

    job = relationship("AnalysisJob", back_populates="outputs")
    model = relationship("ModelRegistry", back_populates="outputs")

    __table_args__ = (
        Index("idx_outputs_bbox", "bbox", postgresql_using="gist"),
    )


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("analysis_jobs.id", ondelete="SET NULL"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SAEnum(ReportStatus, name="report_status"), nullable=False, default=ReportStatus.draft)
    format = Column(SAEnum(ReportFormat, name="report_format"), nullable=False, default=ReportFormat.pdf)
    file_path = Column(Text)
    config = Column(JSONB, nullable=False, server_default=expression.text("'{}'::jsonb"))
    created_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now())
    updated_at = Column(sqlalchemy_utcnow(), nullable=False, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="reports")
    job = relationship("AnalysisJob", back_populates="reports")
    creator = relationship("User", back_populates="reports")
