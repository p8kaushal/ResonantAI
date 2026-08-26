-- Enable Required PostgreSQL Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enum Definitions
CREATE TYPE user_role_type AS ENUM ('patient_user', 'caregiver', 'enterprise_admin', 'system_admin');
CREATE TYPE subscription_tier_type AS ENUM ('free_trial', 'individual_medical', 'enterprise_dei', 'developer_api');
CREATE TYPE impairment_severity_type AS ENUM ('mild', 'moderate', 'severe', 'profound');

-- 1. Profiles Table (Extends Supabase Auth users)
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role user_role_type NOT NULL DEFAULT 'patient_user',
    subscription_tier subscription_tier_type NOT NULL DEFAULT 'free_trial',
    impairment_severity impairment_severity_type DEFAULT 'moderate',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Voice Profiles Table (Stores Encrypted Voice Embeddings)
CREATE TABLE public.voice_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    profile_name TEXT NOT NULL DEFAULT 'Default Restored Voice',
    embedding_vector FLOAT8[] NOT NULL, -- 256-dimensional voice timbre vector
    calibration_sample_count INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Device Nodes Table (Tracks Registered Laptops/Desktops)
CREATE TABLE public.device_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    device_hardware_id TEXT NOT NULL UNIQUE,
    os_type TEXT NOT NULL, -- 'macOS' or 'Windows'
    cpu_architecture TEXT NOT NULL,
    onnx_execution_provider TEXT NOT NULL,
    app_version TEXT NOT NULL,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Session Telemetry Metrics Table (Anonymized Performance Data)
CREATE TABLE public.telemetry_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    device_id UUID REFERENCES public.device_nodes(id) ON DELETE SET NULL,
    session_duration_seconds INT NOT NULL,
    average_latency_ms NUMERIC(5,2) NOT NULL,
    estimated_wer_reduction NUMERIC(4,2) NOT NULL, -- e.g. 0.65 for 65% improvement
    total_audio_frames_processed BIGINT NOT NULL,
    dropped_frames_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Indexes for Query Performance
CREATE INDEX idx_voice_profiles_user_id ON public.voice_profiles(user_id);
CREATE INDEX idx_device_nodes_user_device ON public.device_nodes(user_id, device_hardware_id);
CREATE INDEX idx_telemetry_metrics_created_at ON public.telemetry_metrics(created_at DESC);

-- Enable Row Level Security (RLS) on All Tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.voice_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.device_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.telemetry_metrics ENABLE ROW LEVEL SECURITY;

-- Security RLS Policies

-- Profiles Policies
CREATE POLICY "Users can view their own profile."
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile."
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Voice Profiles Policies
CREATE POLICY "Users can view their own voice profiles."
    ON public.voice_profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own voice profiles."
    ON public.voice_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own voice profiles."
    ON public.voice_profiles FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own voice profiles."
    ON public.voice_profiles FOR DELETE
    USING (auth.uid() = user_id);

-- Device Nodes Policies
CREATE POLICY "Users can manage their device nodes."
    ON public.device_nodes FOR ALL
    USING (auth.uid() = user_id);

-- Telemetry Metrics Policies
CREATE POLICY "Users can insert telemetry metrics."
    ON public.telemetry_metrics FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own telemetry."
    ON public.telemetry_metrics FOR SELECT
    USING (auth.uid() = user_id);
