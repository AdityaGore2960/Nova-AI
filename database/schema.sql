-- =============================================================================
-- NEXUS-MIND: PostgreSQL + PostGIS Schema
-- Version: 1.0.0
-- Description: Production-grade normalized schema for AI mineral prospectivity
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS pg_trgm;        -- fuzzy text search
CREATE EXTENSION IF NOT EXISTS btree_gin;       -- GIN index support for composite

-- ---------------------------------------------------------------------------
-- Enumerations
-- ---------------------------------------------------------------------------
CREATE TYPE user_role AS ENUM ('admin', 'analyst', 'viewer');
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended');

CREATE TYPE dataset_type AS ENUM (
    'satellite_imagery',
    'geological_map',
    'geochemistry',
    'geophysics',
    'dem',                  -- Digital Elevation Model
    'other'
);
CREATE TYPE dataset_status AS ENUM ('pending', 'processing', 'ready', 'failed');

CREATE TYPE layer_type AS ENUM (
    'lithology',
    'fault',
    'fold',
    'alteration',
    'mineralization',
    'contact',
    'structure',
    'other'
);

CREATE TYPE job_status AS ENUM ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE model_type AS ENUM ('cnn', 'xgboost', 'random_forest', 'ensemble', 'svm', 'other');
CREATE TYPE model_status AS ENUM ('training', 'staging', 'production', 'archived', 'failed');

CREATE TYPE report_status AS ENUM ('draft', 'generating', 'ready', 'failed');
CREATE TYPE report_format AS ENUM ('pdf', 'geotiff', 'geojson', 'csv', 'xlsx');

CREATE TYPE mineral_type AS ENUM ('gold', 'copper', 'silver', 'zinc', 'lead', 'nickel', 'uranium', 'other');

-- ---------------------------------------------------------------------------
-- SCHEMA: Core
-- ---------------------------------------------------------------------------

-- users ----------------------------------------------------------------------
CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email               VARCHAR(255) NOT NULL UNIQUE,
    hashed_password     VARCHAR(255) NOT NULL,
    full_name           VARCHAR(255) NOT NULL,
    role                user_role NOT NULL DEFAULT 'analyst',
    status              user_status NOT NULL DEFAULT 'active',
    avatar_url          TEXT,
    organization        VARCHAR(255),
    last_login_at       TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audit fast lookup
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_role ON users (role);
CREATE INDEX idx_users_status ON users (status);

-- projects -------------------------------------------------------------------
CREATE TABLE projects (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id            UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    target_mineral      mineral_type NOT NULL DEFAULT 'gold',
    bbox                geometry(Polygon, 4326),   -- Area of Interest
    country             VARCHAR(100),
    region              VARCHAR(100),
    is_archived         BOOLEAN NOT NULL DEFAULT FALSE,
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_projects_owner ON projects (owner_id);
CREATE INDEX idx_projects_bbox ON projects USING GIST (bbox);
CREATE INDEX idx_projects_mineral ON projects (target_mineral);
CREATE INDEX idx_projects_archived ON projects (is_archived);

-- project_members ------------------------------------------------------------
CREATE TABLE project_members (
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role                user_role NOT NULL DEFAULT 'viewer',
    invited_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (project_id, user_id)
);

CREATE INDEX idx_proj_members_user ON project_members (user_id);

-- ---------------------------------------------------------------------------
-- SCHEMA: Datasets
-- ---------------------------------------------------------------------------

-- datasets -------------------------------------------------------------------
CREATE TABLE datasets (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    uploaded_by         UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    data_type           dataset_type NOT NULL,
    status              dataset_status NOT NULL DEFAULT 'pending',
    file_path           TEXT NOT NULL,          -- S3 URI
    file_size_bytes     BIGINT,
    file_format         VARCHAR(50),            -- GeoTIFF, Shapefile, GeoJSON, CSV
    crs_epsg            INTEGER,                -- Coordinate Reference System
    resolution_m        FLOAT,                  -- Spatial resolution in meters
    band_count          INTEGER,                -- For raster datasets
    bbox                geometry(Polygon, 4326),
    acquisition_date    DATE,
    source              VARCHAR(255),           -- Landsat-9, Sentinel-2, USGS, etc.
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_datasets_project ON datasets (project_id);
CREATE INDEX idx_datasets_type ON datasets (data_type);
CREATE INDEX idx_datasets_status ON datasets (status);
CREATE INDEX idx_datasets_bbox ON datasets USING GIST (bbox);
CREATE INDEX idx_datasets_metadata ON datasets USING GIN (metadata);

-- ---------------------------------------------------------------------------
-- SCHEMA: Geological Layers
-- ---------------------------------------------------------------------------

-- geological_layers ----------------------------------------------------------
-- Vector geometries (polygons, linestrings, points) from geological maps
CREATE TABLE geological_layers (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id          UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    layer_type          layer_type NOT NULL,
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    geometry            geometry(Geometry, 4326) NOT NULL,  -- accepts any geom type
    attributes          JSONB NOT NULL DEFAULT '{}',        -- lithology code, age, confidence
    source              VARCHAR(255),
    confidence_score    FLOAT CHECK (confidence_score BETWEEN 0 AND 1),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Spatial index is critical here — most queries are geospatial
CREATE INDEX idx_geo_layers_geom ON geological_layers USING GIST (geometry);
CREATE INDEX idx_geo_layers_project ON geological_layers (project_id);
CREATE INDEX idx_geo_layers_dataset ON geological_layers (dataset_id);
CREATE INDEX idx_geo_layers_type ON geological_layers (layer_type);
CREATE INDEX idx_geo_layers_attrs ON geological_layers USING GIN (attributes);

-- geochemistry_samples -------------------------------------------------------
CREATE TABLE geochemistry_samples (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id          UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    sample_id           VARCHAR(100),           -- lab sample identifier
    location            geometry(Point, 4326) NOT NULL,
    depth_m             FLOAT,
    elements            JSONB NOT NULL DEFAULT '{}',  -- {"Au_ppb": 0.32, "Cu_ppm": 12.4, ...}
    sample_type         VARCHAR(50),            -- soil, stream-sediment, rock-chip
    collected_at        DATE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_geochem_location ON geochemistry_samples USING GIST (location);
CREATE INDEX idx_geochem_project ON geochemistry_samples (project_id);
CREATE INDEX idx_geochem_dataset ON geochemistry_samples (dataset_id);
CREATE INDEX idx_geochem_elements ON geochemistry_samples USING GIN (elements);

-- geophysics_observations ----------------------------------------------------
CREATE TABLE geophysics_observations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id          UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    location            geometry(Point, 4326) NOT NULL,
    magnetic_nT         FLOAT,
    gravity_mGal        FLOAT,
    radiometric_K       FLOAT,
    radiometric_U       FLOAT,
    radiometric_Th      FLOAT,
    em_conductivity     FLOAT,
    attributes          JSONB NOT NULL DEFAULT '{}',
    observed_at         DATE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_geophys_location ON geophysics_observations USING GIST (location);
CREATE INDEX idx_geophys_project ON geophysics_observations (project_id);
CREATE INDEX idx_geophys_dataset ON geophysics_observations (dataset_id);

-- ---------------------------------------------------------------------------
-- SCHEMA: ML Models & Predictions
-- ---------------------------------------------------------------------------

-- model_registry -------------------------------------------------------------
CREATE TABLE model_registry (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(255) NOT NULL,
    version             VARCHAR(50) NOT NULL,          -- semver e.g. "2.3.1"
    model_type          model_type NOT NULL,
    status              model_status NOT NULL DEFAULT 'training',
    artifact_path       TEXT NOT NULL,                 -- S3 URI to serialized model
    onnx_path           TEXT,                          -- ONNX export path
    target_mineral      mineral_type,
    hyperparameters     JSONB NOT NULL DEFAULT '{}',
    metrics             JSONB NOT NULL DEFAULT '{}',   -- {"auc": 0.92, "f1": 0.88, "kappa": 0.81}
    feature_names       TEXT[],                        -- ordered list of input features
    trained_by          UUID REFERENCES users(id) ON DELETE SET NULL,
    training_job_id     UUID,                          -- links to analysis_jobs
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (name, version)
);

CREATE INDEX idx_model_status ON model_registry (status);
CREATE INDEX idx_model_type ON model_registry (model_type);
CREATE INDEX idx_model_mineral ON model_registry (target_mineral);
CREATE INDEX idx_model_metrics ON model_registry USING GIN (metrics);

-- analysis_jobs --------------------------------------------------------------
CREATE TABLE analysis_jobs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    submitted_by        UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    model_id            UUID REFERENCES model_registry(id) ON DELETE SET NULL,
    job_name            VARCHAR(255),
    status              job_status NOT NULL DEFAULT 'pending',
    parameters          JSONB NOT NULL DEFAULT '{}',   -- AOI, thresholds, model config
    dataset_ids         UUID[],                        -- input datasets used
    celery_task_id      VARCHAR(255),                  -- Celery async task id
    progress_pct        SMALLINT DEFAULT 0 CHECK (progress_pct BETWEEN 0 AND 100),
    error_message       TEXT,
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_project ON analysis_jobs (project_id);
CREATE INDEX idx_jobs_status ON analysis_jobs (status);
CREATE INDEX idx_jobs_submitted_by ON analysis_jobs (submitted_by);
CREATE INDEX idx_jobs_model ON analysis_jobs (model_id);
CREATE INDEX idx_jobs_created ON analysis_jobs (created_at DESC);

-- predictions ----------------------------------------------------------------
-- Row per spatial cell / polygon with probability score
CREATE TABLE predictions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id              UUID NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    model_id            UUID REFERENCES model_registry(id) ON DELETE SET NULL,
    geometry            geometry(Polygon, 4326) NOT NULL,  -- prediction cell
    probability         FLOAT NOT NULL CHECK (probability BETWEEN 0 AND 1),
    confidence_lower    FLOAT CHECK (confidence_lower BETWEEN 0 AND 1),
    confidence_upper    FLOAT CHECK (confidence_upper BETWEEN 0 AND 1),
    risk_class          VARCHAR(20),                       -- 'high', 'medium', 'low'
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Spatial + composite indexes — most queries filter by job + space
CREATE INDEX idx_predictions_geom ON predictions USING GIST (geometry);
CREATE INDEX idx_predictions_job ON predictions (job_id);
CREATE INDEX idx_predictions_project ON predictions (project_id);
CREATE INDEX idx_predictions_probability ON predictions (probability DESC);
CREATE INDEX idx_predictions_risk ON predictions (risk_class);

-- prediction_features --------------------------------------------------------
-- SHAP values & raw feature values per prediction cell
CREATE TABLE prediction_features (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prediction_id       UUID NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    feature_values      JSONB NOT NULL DEFAULT '{}',   -- {"au_ppb": 0.4, "ndvi": 0.71, ...}
    shap_values         JSONB NOT NULL DEFAULT '{}',   -- {"au_ppb": 0.12, "ndvi": -0.03, ...}
    shap_base_value     FLOAT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pred_features_pred ON prediction_features (prediction_id);
CREATE INDEX idx_pred_features_shap ON prediction_features USING GIN (shap_values);
CREATE INDEX idx_pred_features_vals ON prediction_features USING GIN (feature_values);

-- model_outputs --------------------------------------------------------------
-- Aggregate output artifacts per job (raster paths, summary stats)
CREATE TABLE model_outputs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id              UUID NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    model_id            UUID REFERENCES model_registry(id) ON DELETE SET NULL,
    output_type         VARCHAR(100) NOT NULL,          -- 'prospectivity_raster', 'shap_map', 'uncertainty_map'
    file_path           TEXT NOT NULL,                  -- S3 URI
    file_format         VARCHAR(50),                    -- GeoTIFF, PNG, GeoJSON
    bbox                geometry(Polygon, 4326),
    summary_stats       JSONB NOT NULL DEFAULT '{}',    -- {"mean": 0.42, "p90": 0.81, "max": 0.99}
    crs_epsg            INTEGER DEFAULT 4326,
    resolution_m        FLOAT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_outputs_job ON model_outputs (job_id);
CREATE INDEX idx_outputs_type ON model_outputs (output_type);
CREATE INDEX idx_outputs_bbox ON model_outputs USING GIST (bbox);

-- ---------------------------------------------------------------------------
-- SCHEMA: Reports
-- ---------------------------------------------------------------------------

-- reports --------------------------------------------------------------------
CREATE TABLE reports (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    job_id              UUID REFERENCES analysis_jobs(id) ON DELETE SET NULL,
    created_by          UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    status              report_status NOT NULL DEFAULT 'draft',
    format              report_format NOT NULL DEFAULT 'pdf',
    file_path           TEXT,                           -- S3 URI (available when ready)
    config              JSONB NOT NULL DEFAULT '{}',    -- sections, filters, map extent
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reports_project ON reports (project_id);
CREATE INDEX idx_reports_job ON reports (job_id);
CREATE INDEX idx_reports_created_by ON reports (created_by);
CREATE INDEX idx_reports_status ON reports (status);

-- ---------------------------------------------------------------------------
-- SCHEMA: Audit & System
-- ---------------------------------------------------------------------------

-- audit_log ------------------------------------------------------------------
CREATE TABLE audit_log (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             UUID REFERENCES users(id) ON DELETE SET NULL,
    action              VARCHAR(100) NOT NULL,          -- 'project.create', 'job.run', etc.
    resource_type       VARCHAR(100),
    resource_id         UUID,
    payload             JSONB,
    ip_address          INET,
    user_agent          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);  -- partition by month

-- Create initial partitions
CREATE TABLE audit_log_2026_01 PARTITION OF audit_log
    FOR VALUES FROM ('2026-01-01') TO ('2026-07-01');
CREATE TABLE audit_log_2026_07 PARTITION OF audit_log
    FOR VALUES FROM ('2026-07-01') TO ('2027-01-01');
CREATE TABLE audit_log_2027_01 PARTITION OF audit_log
    FOR VALUES FROM ('2027-01-01') TO ('2027-07-01');

CREATE INDEX idx_audit_user ON audit_log (user_id);
CREATE INDEX idx_audit_action ON audit_log (action);
CREATE INDEX idx_audit_resource ON audit_log (resource_type, resource_id);
CREATE INDEX idx_audit_created ON audit_log (created_at DESC);

-- ---------------------------------------------------------------------------
-- Auto-update updated_at trigger
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON datasets
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON model_registry
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ---------------------------------------------------------------------------
-- Views: convenience
-- ---------------------------------------------------------------------------

-- Active projects with member count
CREATE VIEW v_project_summary AS
SELECT
    p.id,
    p.name,
    p.target_mineral,
    p.country,
    p.is_archived,
    u.full_name          AS owner_name,
    COUNT(DISTINCT pm.user_id) AS member_count,
    COUNT(DISTINCT d.id)       AS dataset_count,
    COUNT(DISTINCT aj.id)      AS job_count,
    p.created_at
FROM projects p
JOIN users u ON u.id = p.owner_id
LEFT JOIN project_members pm ON pm.project_id = p.id
LEFT JOIN datasets d ON d.project_id = p.id
LEFT JOIN analysis_jobs aj ON aj.project_id = p.id
GROUP BY p.id, u.full_name;

-- High-probability prediction zones (>= 0.75)
CREATE VIEW v_high_probability_zones AS
SELECT
    pr.id,
    pr.project_id,
    pr.job_id,
    pr.geometry,
    pr.probability,
    pr.confidence_lower,
    pr.confidence_upper,
    pr.risk_class,
    ST_Area(pr.geometry::geography) / 1e6 AS area_km2,
    ST_Centroid(pr.geometry)              AS centroid
FROM predictions pr
WHERE pr.probability >= 0.75;
