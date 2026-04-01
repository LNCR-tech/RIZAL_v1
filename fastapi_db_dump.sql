--
-- PostgreSQL database dump
--

\restrict q1D5eiG7G60kN5QlwGs8TfrDQp7YHzr4dq99DOLiBN8zUa4a1uvBN0Zv1yPdxDv

-- Dumped from database version 15.16 (Debian 15.16-1.pgdg13+1)
-- Dumped by pg_dump version 15.16 (Debian 15.16-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE IF EXISTS fastapi_db;
--
-- Name: fastapi_db; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE fastapi_db WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


\unrestrict q1D5eiG7G60kN5QlwGs8TfrDQp7YHzr4dq99DOLiBN8zUa4a1uvBN0Zv1yPdxDv
\connect fastapi_db
\restrict q1D5eiG7G60kN5QlwGs8TfrDQp7YHzr4dq99DOLiBN8zUa4a1uvBN0Zv1yPdxDv

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: attendancestatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.attendancestatus AS ENUM (
    'present',
    'absent',
    'excused'
);


--
-- Name: eventstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.eventstatus AS ENUM (
    'UPCOMING',
    'ONGOING',
    'COMPLETED',
    'CANCELLED'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_logs (
    id integer NOT NULL,
    user_id integer NOT NULL,
    role character varying(100) NOT NULL,
    message text NOT NULL,
    tool_called character varying(100),
    success boolean NOT NULL,
    "timestamp" timestamp without time zone NOT NULL
);


--
-- Name: ai_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ai_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ai_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ai_logs_id_seq OWNED BY public.ai_logs.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: anomaly_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.anomaly_logs (
    id integer NOT NULL,
    event_id integer,
    user_id integer,
    anomaly_type character varying(64) NOT NULL,
    severity character varying(16) NOT NULL,
    confidence double precision NOT NULL,
    details json NOT NULL,
    detected_at timestamp without time zone NOT NULL,
    is_resolved boolean NOT NULL
);


--
-- Name: anomaly_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.anomaly_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: anomaly_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.anomaly_logs_id_seq OWNED BY public.anomaly_logs.id;


--
-- Name: attendance_predictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attendance_predictions (
    id integer NOT NULL,
    student_id integer NOT NULL,
    event_id integer NOT NULL,
    attendance_probability double precision NOT NULL,
    confidence double precision NOT NULL,
    risk_level character varying(16) NOT NULL,
    model_version character varying(64) NOT NULL,
    generated_at timestamp without time zone NOT NULL
);


--
-- Name: attendance_predictions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.attendance_predictions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: attendance_predictions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.attendance_predictions_id_seq OWNED BY public.attendance_predictions.id;


--
-- Name: attendances; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attendances (
    id integer NOT NULL,
    student_id integer,
    event_id integer,
    time_in timestamp without time zone NOT NULL,
    time_out timestamp without time zone,
    method character varying(50),
    status public.attendancestatus NOT NULL,
    verified_by integer,
    notes character varying(500)
);


--
-- Name: attendances_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.attendances_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: attendances_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.attendances_id_seq OWNED BY public.attendances.id;


--
-- Name: bulk_import_errors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bulk_import_errors (
    id integer NOT NULL,
    job_id character varying(36) NOT NULL,
    row_number integer NOT NULL,
    error_message text NOT NULL,
    row_data json,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: bulk_import_errors_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bulk_import_errors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bulk_import_errors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bulk_import_errors_id_seq OWNED BY public.bulk_import_errors.id;


--
-- Name: bulk_import_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bulk_import_jobs (
    id character varying(36) NOT NULL,
    created_by_user_id integer,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    original_filename character varying(255) NOT NULL,
    stored_file_path character varying(1024) NOT NULL,
    failed_report_path character varying(1024),
    total_rows integer DEFAULT 0 NOT NULL,
    processed_rows integer DEFAULT 0 NOT NULL,
    success_count integer DEFAULT 0 NOT NULL,
    failed_count integer DEFAULT 0 NOT NULL,
    eta_seconds integer,
    error_summary text,
    is_rate_limited boolean DEFAULT false NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    last_heartbeat timestamp without time zone,
    target_school_id integer NOT NULL
);


--
-- Name: data_governance_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_governance_settings (
    school_id integer NOT NULL,
    attendance_retention_days integer DEFAULT 1095 NOT NULL,
    audit_log_retention_days integer DEFAULT 3650 NOT NULL,
    import_file_retention_days integer DEFAULT 180 NOT NULL,
    auto_delete_enabled boolean DEFAULT false NOT NULL,
    updated_by_user_id integer,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: data_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_requests (
    id integer NOT NULL,
    school_id integer NOT NULL,
    requested_by_user_id integer,
    target_user_id integer,
    request_type character varying(20) NOT NULL,
    scope character varying(50) DEFAULT 'user_data'::character varying NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    reason text,
    details_json json,
    output_path character varying(1024),
    handled_by_user_id integer,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    resolved_at timestamp without time zone
);


--
-- Name: data_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: data_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_requests_id_seq OWNED BY public.data_requests.id;


--
-- Name: data_retention_run_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_retention_run_logs (
    id integer NOT NULL,
    school_id integer NOT NULL,
    dry_run boolean DEFAULT true NOT NULL,
    status character varying(20) DEFAULT 'completed'::character varying NOT NULL,
    summary text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: data_retention_run_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_retention_run_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: data_retention_run_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_retention_run_logs_id_seq OWNED BY public.data_retention_run_logs.id;


--
-- Name: departments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.departments (
    id integer NOT NULL,
    name character varying NOT NULL
);


--
-- Name: departments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.departments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: departments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.departments_id_seq OWNED BY public.departments.id;


--
-- Name: email_delivery_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.email_delivery_logs (
    id integer NOT NULL,
    job_id character varying(36),
    user_id integer,
    email character varying(255) NOT NULL,
    status character varying(20) NOT NULL,
    error_message text,
    retry_count integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: email_delivery_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.email_delivery_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: email_delivery_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.email_delivery_logs_id_seq OWNED BY public.email_delivery_logs.id;


--
-- Name: event_consumption_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_consumption_logs (
    id integer NOT NULL,
    event_id character varying(36) NOT NULL,
    event_type character varying(120) NOT NULL,
    consumer_name character varying(120) NOT NULL,
    status character varying(24) NOT NULL,
    error_message text,
    retry_count integer NOT NULL,
    processed_at timestamp without time zone NOT NULL
);


--
-- Name: event_consumption_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.event_consumption_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: event_consumption_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.event_consumption_logs_id_seq OWNED BY public.event_consumption_logs.id;


--
-- Name: event_department_association; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_department_association (
    event_id integer NOT NULL,
    department_id integer NOT NULL
);


--
-- Name: event_flags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_flags (
    id integer NOT NULL,
    event_id integer NOT NULL,
    reason character varying(255) NOT NULL,
    flagged_at timestamp without time zone NOT NULL,
    active boolean NOT NULL
);


--
-- Name: event_flags_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.event_flags_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: event_flags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.event_flags_id_seq OWNED BY public.event_flags.id;


--
-- Name: event_predictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_predictions (
    id integer NOT NULL,
    event_id integer NOT NULL,
    expected_attendance_count integer NOT NULL,
    expected_turnout_pct double precision NOT NULL,
    underperform_probability double precision NOT NULL,
    risk_level character varying(16) NOT NULL,
    model_version character varying(64) NOT NULL,
    generated_at timestamp without time zone NOT NULL
);


--
-- Name: event_predictions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.event_predictions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: event_predictions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.event_predictions_id_seq OWNED BY public.event_predictions.id;


--
-- Name: event_program_association; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_program_association (
    event_id integer NOT NULL,
    program_id integer NOT NULL
);


--
-- Name: event_ssg_association; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_ssg_association (
    event_id integer NOT NULL,
    ssg_profile_id integer NOT NULL
);


--
-- Name: events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.events (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    location character varying(200),
    start_datetime timestamp without time zone NOT NULL,
    end_datetime timestamp without time zone NOT NULL,
    status public.eventstatus NOT NULL,
    school_id integer NOT NULL
);


--
-- Name: events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.events_id_seq OWNED BY public.events.id;


--
-- Name: login_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.login_history (
    id integer NOT NULL,
    user_id integer,
    school_id integer,
    email_attempted character varying(255) NOT NULL,
    success boolean DEFAULT false NOT NULL,
    auth_method character varying(30) DEFAULT 'password'::character varying NOT NULL,
    failure_reason character varying(255),
    ip_address character varying(64),
    user_agent character varying(500),
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: login_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.login_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: login_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.login_history_id_seq OWNED BY public.login_history.id;


--
-- Name: mfa_challenges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mfa_challenges (
    id character varying(36) NOT NULL,
    user_id integer NOT NULL,
    code_hash character varying(255) NOT NULL,
    channel character varying(20) DEFAULT 'email'::character varying NOT NULL,
    attempts integer DEFAULT 0 NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    consumed_at timestamp without time zone,
    ip_address character varying(64),
    user_agent character varying(500),
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: model_metadata; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_metadata (
    id integer NOT NULL,
    model_name character varying(120) NOT NULL,
    model_version character varying(64) NOT NULL,
    trained_at timestamp without time zone NOT NULL,
    metrics json NOT NULL,
    feature_schema json NOT NULL,
    notes text
);


--
-- Name: model_metadata_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_metadata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_metadata_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.model_metadata_id_seq OWNED BY public.model_metadata.id;


--
-- Name: notification_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notification_logs (
    id integer NOT NULL,
    school_id integer,
    user_id integer,
    category character varying(50) NOT NULL,
    channel character varying(20) DEFAULT 'email'::character varying NOT NULL,
    status character varying(20) DEFAULT 'queued'::character varying NOT NULL,
    subject character varying(255) NOT NULL,
    message text NOT NULL,
    error_message text,
    metadata_json json,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: notification_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.notification_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: notification_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.notification_logs_id_seq OWNED BY public.notification_logs.id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    user_id integer,
    message character varying(1000) NOT NULL,
    is_read boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: outbox_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.outbox_events (
    id character varying(36) NOT NULL,
    event_type character varying(120) NOT NULL,
    source_service character varying(120) NOT NULL,
    payload json NOT NULL,
    status character varying(24) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    published_at timestamp without time zone,
    retry_count integer NOT NULL,
    last_error text
);


--
-- Name: password_reset_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.password_reset_requests (
    id integer NOT NULL,
    user_id integer NOT NULL,
    school_id integer NOT NULL,
    requested_email character varying(255) NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    requested_at timestamp without time zone DEFAULT now() NOT NULL,
    resolved_at timestamp without time zone,
    reviewed_by_user_id integer
);


--
-- Name: password_reset_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.password_reset_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: password_reset_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.password_reset_requests_id_seq OWNED BY public.password_reset_requests.id;


--
-- Name: program_department_association; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.program_department_association (
    program_id integer NOT NULL,
    department_id integer NOT NULL
);


--
-- Name: programs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.programs (
    id integer NOT NULL,
    name character varying NOT NULL
);


--
-- Name: programs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.programs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: programs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.programs_id_seq OWNED BY public.programs.id;


--
-- Name: recommendation_cache; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recommendation_cache (
    id integer NOT NULL,
    student_id integer NOT NULL,
    recommendations json NOT NULL,
    generated_at timestamp without time zone NOT NULL,
    expires_at timestamp without time zone NOT NULL
);


--
-- Name: recommendation_cache_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.recommendation_cache_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: recommendation_cache_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.recommendation_cache_id_seq OWNED BY public.recommendation_cache.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    name character varying(50) NOT NULL
);


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: school_audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.school_audit_logs (
    id integer NOT NULL,
    school_id integer NOT NULL,
    actor_user_id integer,
    action character varying(100) NOT NULL,
    status character varying(30) DEFAULT 'success'::character varying NOT NULL,
    details text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: school_audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.school_audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: school_audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.school_audit_logs_id_seq OWNED BY public.school_audit_logs.id;


--
-- Name: school_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.school_settings (
    school_id integer NOT NULL,
    primary_color character varying(7) DEFAULT '#162F65'::character varying NOT NULL,
    secondary_color character varying(7) DEFAULT '#2C5F9E'::character varying NOT NULL,
    accent_color character varying(7) DEFAULT '#4A90E2'::character varying NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_by_user_id integer
);


--
-- Name: school_subscription_reminders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.school_subscription_reminders (
    id integer NOT NULL,
    school_id integer NOT NULL,
    reminder_type character varying(40) DEFAULT 'renewal_warning'::character varying NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    due_at timestamp without time zone NOT NULL,
    sent_at timestamp without time zone,
    error_message text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: school_subscription_reminders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.school_subscription_reminders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: school_subscription_reminders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.school_subscription_reminders_id_seq OWNED BY public.school_subscription_reminders.id;


--
-- Name: school_subscription_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.school_subscription_settings (
    school_id integer NOT NULL,
    plan_name character varying(50) DEFAULT 'free'::character varying NOT NULL,
    user_limit integer DEFAULT 500 NOT NULL,
    event_limit_monthly integer DEFAULT 100 NOT NULL,
    import_limit_monthly integer DEFAULT 10 NOT NULL,
    renewal_date date,
    auto_renew boolean DEFAULT false NOT NULL,
    reminder_days_before integer DEFAULT 14 NOT NULL,
    updated_by_user_id integer,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: schools; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schools (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    address character varying(500) NOT NULL,
    logo_url character varying(1000),
    subscription_plan character varying(100) DEFAULT 'free'::character varying NOT NULL,
    subscription_start date DEFAULT CURRENT_DATE NOT NULL,
    subscription_end date,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    school_name character varying(255) NOT NULL,
    school_code character varying(50),
    primary_color character varying(7) DEFAULT '#162F65'::character varying NOT NULL,
    secondary_color character varying(7),
    subscription_status character varying(30) DEFAULT 'trial'::character varying NOT NULL,
    active_status boolean DEFAULT true NOT NULL
);


--
-- Name: schools_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.schools ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.schools_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: security_alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.security_alerts (
    id integer NOT NULL,
    anomaly_log_id integer NOT NULL,
    event_id integer,
    severity character varying(16) NOT NULL,
    message character varying(255) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    acknowledged boolean NOT NULL
);


--
-- Name: security_alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.security_alerts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: security_alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.security_alerts_id_seq OWNED BY public.security_alerts.id;


--
-- Name: ssg_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ssg_profiles (
    id integer NOT NULL,
    user_id integer,
    "position" character varying(100)
);


--
-- Name: ssg_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ssg_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ssg_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ssg_profiles_id_seq OWNED BY public.ssg_profiles.id;


--
-- Name: student_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_profiles (
    id integer NOT NULL,
    user_id integer,
    student_id character varying(50),
    department_id integer,
    program_id integer,
    year_level integer NOT NULL,
    face_encoding bytea,
    is_face_registered boolean,
    face_image_url character varying(500),
    registration_complete boolean,
    section character varying(50),
    rfid_tag character varying(100),
    last_face_update timestamp without time zone,
    school_id integer NOT NULL
);


--
-- Name: student_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.student_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: student_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.student_profiles_id_seq OWNED BY public.student_profiles.id;


--
-- Name: student_risk_scores; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_risk_scores (
    id integer NOT NULL,
    student_id integer NOT NULL,
    risk_score integer NOT NULL,
    risk_level character varying(16) NOT NULL,
    recommendation character varying(255) NOT NULL,
    factors json NOT NULL,
    generated_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: student_risk_scores_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.student_risk_scores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: student_risk_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.student_risk_scores_id_seq OWNED BY public.student_risk_scores.id;


--
-- Name: user_notification_preferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_notification_preferences (
    user_id integer NOT NULL,
    email_enabled boolean DEFAULT true NOT NULL,
    sms_enabled boolean DEFAULT false NOT NULL,
    sms_number character varying(40),
    notify_missed_events boolean DEFAULT true NOT NULL,
    notify_low_attendance boolean DEFAULT true NOT NULL,
    notify_account_security boolean DEFAULT true NOT NULL,
    notify_subscription boolean DEFAULT true NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: user_privacy_consents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_privacy_consents (
    id integer NOT NULL,
    user_id integer NOT NULL,
    school_id integer NOT NULL,
    consent_type character varying(50) NOT NULL,
    consent_granted boolean DEFAULT true NOT NULL,
    consent_version character varying(20) DEFAULT 'v1'::character varying NOT NULL,
    source character varying(50) DEFAULT 'web'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: user_privacy_consents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_privacy_consents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_privacy_consents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_privacy_consents_id_seq OWNED BY public.user_privacy_consents.id;


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_roles (
    id integer NOT NULL,
    user_id integer,
    role_id integer
);


--
-- Name: user_roles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_roles_id_seq OWNED BY public.user_roles.id;


--
-- Name: user_security_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_security_settings (
    user_id integer NOT NULL,
    mfa_enabled boolean DEFAULT false NOT NULL,
    trusted_device_days integer DEFAULT 14 NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: user_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_sessions (
    id character varying(36) NOT NULL,
    user_id integer NOT NULL,
    token_jti character varying(64) NOT NULL,
    ip_address character varying(64),
    user_agent character varying(500),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    last_seen_at timestamp without time zone DEFAULT now() NOT NULL,
    revoked_at timestamp without time zone,
    expires_at timestamp without time zone NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    first_name character varying(100),
    middle_name character varying(100),
    last_name character varying(100),
    is_active boolean,
    created_at timestamp without time zone NOT NULL,
    approval_status character varying(30) DEFAULT 'approved'::character varying NOT NULL,
    requested_roles character varying(200),
    requested_ssg_position character varying(100),
    school_id integer,
    must_change_password boolean DEFAULT true NOT NULL
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: ai_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_logs ALTER COLUMN id SET DEFAULT nextval('public.ai_logs_id_seq'::regclass);


--
-- Name: anomaly_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_logs ALTER COLUMN id SET DEFAULT nextval('public.anomaly_logs_id_seq'::regclass);


--
-- Name: attendance_predictions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_predictions ALTER COLUMN id SET DEFAULT nextval('public.attendance_predictions_id_seq'::regclass);


--
-- Name: attendances id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendances ALTER COLUMN id SET DEFAULT nextval('public.attendances_id_seq'::regclass);


--
-- Name: bulk_import_errors id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bulk_import_errors ALTER COLUMN id SET DEFAULT nextval('public.bulk_import_errors_id_seq'::regclass);


--
-- Name: data_requests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_requests ALTER COLUMN id SET DEFAULT nextval('public.data_requests_id_seq'::regclass);


--
-- Name: data_retention_run_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_retention_run_logs ALTER COLUMN id SET DEFAULT nextval('public.data_retention_run_logs_id_seq'::regclass);


--
-- Name: departments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments ALTER COLUMN id SET DEFAULT nextval('public.departments_id_seq'::regclass);


--
-- Name: email_delivery_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_delivery_logs ALTER COLUMN id SET DEFAULT nextval('public.email_delivery_logs_id_seq'::regclass);


--
-- Name: event_consumption_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_consumption_logs ALTER COLUMN id SET DEFAULT nextval('public.event_consumption_logs_id_seq'::regclass);


--
-- Name: event_flags id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_flags ALTER COLUMN id SET DEFAULT nextval('public.event_flags_id_seq'::regclass);


--
-- Name: event_predictions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_predictions ALTER COLUMN id SET DEFAULT nextval('public.event_predictions_id_seq'::regclass);


--
-- Name: events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events ALTER COLUMN id SET DEFAULT nextval('public.events_id_seq'::regclass);


--
-- Name: login_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_history ALTER COLUMN id SET DEFAULT nextval('public.login_history_id_seq'::regclass);


--
-- Name: model_metadata id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_metadata ALTER COLUMN id SET DEFAULT nextval('public.model_metadata_id_seq'::regclass);


--
-- Name: notification_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_logs ALTER COLUMN id SET DEFAULT nextval('public.notification_logs_id_seq'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: password_reset_requests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.password_reset_requests ALTER COLUMN id SET DEFAULT nextval('public.password_reset_requests_id_seq'::regclass);


--
-- Name: programs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.programs ALTER COLUMN id SET DEFAULT nextval('public.programs_id_seq'::regclass);


--
-- Name: recommendation_cache id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recommendation_cache ALTER COLUMN id SET DEFAULT nextval('public.recommendation_cache_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: school_audit_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_audit_logs ALTER COLUMN id SET DEFAULT nextval('public.school_audit_logs_id_seq'::regclass);


--
-- Name: school_subscription_reminders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_subscription_reminders ALTER COLUMN id SET DEFAULT nextval('public.school_subscription_reminders_id_seq'::regclass);


--
-- Name: security_alerts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.security_alerts ALTER COLUMN id SET DEFAULT nextval('public.security_alerts_id_seq'::regclass);


--
-- Name: ssg_profiles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_profiles ALTER COLUMN id SET DEFAULT nextval('public.ssg_profiles_id_seq'::regclass);


--
-- Name: student_profiles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles ALTER COLUMN id SET DEFAULT nextval('public.student_profiles_id_seq'::regclass);


--
-- Name: student_risk_scores id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_risk_scores ALTER COLUMN id SET DEFAULT nextval('public.student_risk_scores_id_seq'::regclass);


--
-- Name: user_privacy_consents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_privacy_consents ALTER COLUMN id SET DEFAULT nextval('public.user_privacy_consents_id_seq'::regclass);


--
-- Name: user_roles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles ALTER COLUMN id SET DEFAULT nextval('public.user_roles_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: ai_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ai_logs (id, user_id, role, message, tool_called, success, "timestamp") FROM stdin;
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
d4f6a8b0c2e4
\.


--
-- Data for Name: anomaly_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.anomaly_logs (id, event_id, user_id, anomaly_type, severity, confidence, details, detected_at, is_resolved) FROM stdin;
\.


--
-- Data for Name: attendance_predictions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.attendance_predictions (id, student_id, event_id, attendance_probability, confidence, risk_level, model_version, generated_at) FROM stdin;
\.


--
-- Data for Name: attendances; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.attendances (id, student_id, event_id, time_in, time_out, method, status, verified_by, notes) FROM stdin;
1	182	3	2026-03-06 12:12:39.34847	\N	manual	present	\N	E2E seeded attendance
2	182	4	2026-03-06 12:12:39.34847	\N	manual	absent	\N	E2E seeded attendance
3	182	5	2026-03-06 12:12:39.34847	\N	manual	absent	\N	E2E seeded attendance
\.


--
-- Data for Name: bulk_import_errors; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.bulk_import_errors (id, job_id, row_number, error_message, row_data, created_at) FROM stdin;
4	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	2	Department does not exist; Course does not exist	{"Student_ID": "2026-0001", "Email": "lancer.decin@gmail.com", "Last Name": "Navarro", "First Name": "Isabella", "Middle Name": "Diaz", "Department": "Engineering", "Course": "Computer Engineering"}	2026-03-05 06:18:14.259253
5	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	3	duplicate Email in uploaded file; Department does not exist; Course does not exist	{"Student_ID": "2026-0002", "Email": "lancer.decin@gmail.com", "Last Name": "Villanueva", "First Name": "Ariana", "Middle Name": "Fernandez", "Department": "Business", "Course": "Marketing"}	2026-03-05 06:18:14.259256
6	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	4	duplicate Email in uploaded file; Department does not exist; Course does not exist	{"Student_ID": "2026-0003", "Email": "lancer.decin@gmail.com", "Last Name": "Aquino", "First Name": "Carla", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.259257
7	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	5	duplicate Email in uploaded file; Department does not exist; Course does not exist	{"Student_ID": "2026-0004", "Email": "lancer.decin@gmail.com", "Last Name": "Reyes", "First Name": "Nathan", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.259257
8	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	6	Department does not exist; Course does not exist	{"Student_ID": "2026-0005", "Email": "liam.gonzales5@school.edu", "Last Name": "Gonzales", "First Name": "Liam", "Middle Name": "Diaz", "Department": "Arts and Sciences", "Course": "Psychology"}	2026-03-05 06:18:14.259257
9	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	7	Department does not exist; Course does not exist	{"Student_ID": "2026-0006", "Email": "ella.ramos6@school.edu", "Last Name": "Ramos", "First Name": "Ella", "Middle Name": "Morales", "Department": "Arts and Sciences", "Course": "Psychology"}	2026-03-05 06:18:14.259258
10	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	8	Department does not exist; Course does not exist	{"Student_ID": "2026-0007", "Email": "john.santos7@school.edu", "Last Name": "Santos", "First Name": "John", "Middle Name": "Martinez", "Department": "Arts and Sciences", "Course": "Psychology"}	2026-03-05 06:18:14.259258
11	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	9	Department does not exist; Course does not exist	{"Student_ID": "2026-0008", "Email": "ella.navarro8@school.edu", "Last Name": "Navarro", "First Name": "Ella", "Middle Name": "Santiago", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.259258
12	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	10	Department does not exist; Course does not exist	{"Student_ID": "2026-0009", "Email": "carla.gonzales9@school.edu", "Last Name": "Gonzales", "First Name": "Carla", "Middle Name": "Domingo", "Department": "Engineering", "Course": "Civil Engineering"}	2026-03-05 06:18:14.259259
13	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	11	Department does not exist; Course does not exist	{"Student_ID": "2026-0010", "Email": "nathan.navarro10@school.edu", "Last Name": "Navarro", "First Name": "Nathan", "Middle Name": "Domingo", "Department": "Arts and Sciences", "Course": "Political Science"}	2026-03-05 06:18:14.259259
14	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	12	Department does not exist; Course does not exist	{"Student_ID": "2026-0011", "Email": "kyle.villanueva11@school.edu", "Last Name": "Villanueva", "First Name": "Kyle", "Middle Name": "Fernandez", "Department": "Business", "Course": "Marketing"}	2026-03-05 06:18:14.259259
15	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	13	Department does not exist; Course does not exist	{"Student_ID": "2026-0012", "Email": "kyle.aquino12@school.edu", "Last Name": "Aquino", "First Name": "Kyle", "Middle Name": "Fernandez", "Department": "Engineering", "Course": "Civil Engineering"}	2026-03-05 06:18:14.259259
16	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	14	Department does not exist; Course does not exist	{"Student_ID": "2026-0013", "Email": "daniel.ramos13@school.edu", "Last Name": "Ramos", "First Name": "Daniel", "Middle Name": "Castillo", "Department": "Arts and Sciences", "Course": "Communication"}	2026-03-05 06:18:14.25926
17	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	15	Department does not exist; Course does not exist	{"Student_ID": "2026-0014", "Email": "isabella.reyes14@school.edu", "Last Name": "Reyes", "First Name": "Isabella", "Middle Name": "Castillo", "Department": "Engineering", "Course": "Computer Engineering"}	2026-03-05 06:18:14.25926
18	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	16	Department does not exist; Course does not exist	{"Student_ID": "2026-0015", "Email": "bianca.ramos15@school.edu", "Last Name": "Ramos", "First Name": "Bianca", "Middle Name": "Diaz", "Department": "Arts and Sciences", "Course": "Psychology"}	2026-03-05 06:18:14.25926
19	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	17	Department does not exist; Course does not exist	{"Student_ID": "2026-0016", "Email": "chloe.navarro16@school.edu", "Last Name": "Navarro", "First Name": "Chloe", "Middle Name": "Lopez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.25926
20	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	18	Department does not exist; Course does not exist	{"Student_ID": "2026-0017", "Email": "nathan.delacruz17@school.edu", "Last Name": "Dela Cruz", "First Name": "Nathan", "Middle Name": "Santiago", "Department": "Engineering", "Course": "Civil Engineering"}	2026-03-05 06:18:14.259261
21	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	19	Department does not exist; Course does not exist	{"Student_ID": "2026-0018", "Email": "daniel.mendoza18@school.edu", "Last Name": "Mendoza", "First Name": "Daniel", "Middle Name": "Domingo", "Department": "Engineering", "Course": "Civil Engineering"}	2026-03-05 06:18:14.259261
22	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	20	Department does not exist; Course does not exist	{"Student_ID": "2026-0019", "Email": "angela.reyes19@school.edu", "Last Name": "Reyes", "First Name": "Angela", "Middle Name": "Domingo", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.259261
23	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	21	Department does not exist; Course does not exist	{"Student_ID": "2026-0020", "Email": "ariana.mendoza20@school.edu", "Last Name": "Mendoza", "First Name": "Ariana", "Middle Name": "Rivera", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.259261
120	db0e9921-06e2-418e-ba73-3d5986e86dbd	95	Course does not exist	{"Student_ID": "2026-0094", "Email": "isabella.navarro94@school.edu", "Last Name": "Navarro", "First Name": "Isabella", "Middle Name": "Santiago", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309327
121	a2049bf9-bd83-46d8-947d-221349ba7404	5	duplicate Email in uploaded file	{"Student_ID": "2026-0004", "Email": "lancer.decin@gmail.com", "Last Name": "Reyes", "First Name": "Nathan", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Technology"}	2026-03-05 12:46:14.847403
122	a2049bf9-bd83-46d8-947d-221349ba7404	9	Course does not exist	{"Student_ID": "2026-0008", "Email": "ella.navarro8@school.edu", "Last Name": "Navarro", "First Name": "Ella", "Middle Name": "Santiago", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.847407
123	a2049bf9-bd83-46d8-947d-221349ba7404	17	Course does not exist	{"Student_ID": "2026-0016", "Email": "chloe.navarro16@school.edu", "Last Name": "Navarro", "First Name": "Chloe", "Middle Name": "Lopez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.847408
24	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	22	Department does not exist; Course does not exist	{"Student_ID": "2026-0021", "Email": "john.mendoza21@school.edu", "Last Name": "Mendoza", "First Name": "John", "Middle Name": "Santiago", "Department": "Arts and Sciences", "Course": "Political Science"}	2026-03-05 06:18:14.259261
25	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	23	Department does not exist; Course does not exist	{"Student_ID": "2026-0022", "Email": "kyle.castro22@school.edu", "Last Name": "Castro", "First Name": "Kyle", "Middle Name": "Perez", "Department": "Business", "Course": "Business Administration"}	2026-03-05 06:18:14.259262
26	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	24	Department does not exist; Course does not exist	{"Student_ID": "2026-0023", "Email": "isabella.santos23@school.edu", "Last Name": "Santos", "First Name": "Isabella", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.259262
27	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	25	Department does not exist; Course does not exist	{"Student_ID": "2026-0024", "Email": "liam.aquino24@school.edu", "Last Name": "Aquino", "First Name": "Liam", "Middle Name": "Domingo", "Department": "Business", "Course": "Business Administration"}	2026-03-05 06:18:14.259262
28	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	26	Department does not exist; Course does not exist	{"Student_ID": "2026-0025", "Email": "daniel.navarro25@school.edu", "Last Name": "Navarro", "First Name": "Daniel", "Middle Name": "Santiago", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.259262
29	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	27	Department does not exist; Course does not exist	{"Student_ID": "2026-0026", "Email": "john.mendoza26@school.edu", "Last Name": "Mendoza", "First Name": "John", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.259263
30	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	28	Department does not exist; Course does not exist	{"Student_ID": "2026-0027", "Email": "daniel.mendoza27@school.edu", "Last Name": "Mendoza", "First Name": "Daniel", "Middle Name": "Morales", "Department": "Engineering", "Course": "Electrical Engineering"}	2026-03-05 06:18:14.259263
31	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	29	Department does not exist; Course does not exist	{"Student_ID": "2026-0028", "Email": "ella.delacruz28@school.edu", "Last Name": "Dela Cruz", "First Name": "Ella", "Middle Name": "Lopez", "Department": "Engineering", "Course": "Electrical Engineering"}	2026-03-05 06:18:14.259263
32	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	30	Department does not exist; Course does not exist	{"Student_ID": "2026-0029", "Email": "nathan.torres29@school.edu", "Last Name": "Torres", "First Name": "Nathan", "Middle Name": "Rivera", "Department": "Arts and Sciences", "Course": "Communication"}	2026-03-05 06:18:14.259263
33	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	31	Department does not exist; Course does not exist	{"Student_ID": "2026-0030", "Email": "daniel.ramos30@school.edu", "Last Name": "Ramos", "First Name": "Daniel", "Middle Name": "Rivera", "Department": "Arts and Sciences", "Course": "Psychology"}	2026-03-05 06:18:14.259264
34	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	32	Department does not exist; Course does not exist	{"Student_ID": "2026-0031", "Email": "ethan.garcia31@school.edu", "Last Name": "Garcia", "First Name": "Ethan", "Middle Name": "Martinez", "Department": "Arts and Sciences", "Course": "Political Science"}	2026-03-05 06:18:14.259264
35	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	33	Department does not exist; Course does not exist	{"Student_ID": "2026-0032", "Email": "liam.reyes32@school.edu", "Last Name": "Reyes", "First Name": "Liam", "Middle Name": "Lopez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.259264
36	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	34	Department does not exist; Course does not exist	{"Student_ID": "2026-0033", "Email": "carla.delacruz33@school.edu", "Last Name": "Dela Cruz", "First Name": "Carla", "Middle Name": "Santiago", "Department": "Engineering", "Course": "Electrical Engineering"}	2026-03-05 06:18:14.259264
37	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	35	Department does not exist; Course does not exist	{"Student_ID": "2026-0034", "Email": "sofia.delacruz34@school.edu", "Last Name": "Dela Cruz", "First Name": "Sofia", "Middle Name": "Domingo", "Department": "Arts and Sciences", "Course": "Communication"}	2026-03-05 06:18:14.259264
38	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	36	Department does not exist; Course does not exist	{"Student_ID": "2026-0035", "Email": "ethan.torres35@school.edu", "Last Name": "Torres", "First Name": "Ethan", "Middle Name": "Fernandez", "Department": "Arts and Sciences", "Course": "Political Science"}	2026-03-05 06:18:14.259265
39	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	37	Department does not exist; Course does not exist	{"Student_ID": "2026-0036", "Email": "daniel.garcia36@school.edu", "Last Name": "Garcia", "First Name": "Daniel", "Middle Name": "Lopez", "Department": "Engineering", "Course": "Electrical Engineering"}	2026-03-05 06:18:14.259265
40	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	38	Department does not exist; Course does not exist	{"Student_ID": "2026-0037", "Email": "joshua.torres37@school.edu", "Last Name": "Torres", "First Name": "Joshua", "Middle Name": "Diaz", "Department": "Arts and Sciences", "Course": "Political Science"}	2026-03-05 06:18:14.259265
41	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	39	Department does not exist; Course does not exist	{"Student_ID": "2026-0038", "Email": "ariana.gonzales38@school.edu", "Last Name": "Gonzales", "First Name": "Ariana", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.259265
42	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	40	Department does not exist; Course does not exist	{"Student_ID": "2026-0039", "Email": "chloe.aquino39@school.edu", "Last Name": "Aquino", "First Name": "Chloe", "Middle Name": "Diaz", "Department": "Business", "Course": "Business Administration"}	2026-03-05 06:18:14.259266
43	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	41	Department does not exist; Course does not exist	{"Student_ID": "2026-0040", "Email": "ella.villanueva40@school.edu", "Last Name": "Villanueva", "First Name": "Ella", "Middle Name": "Domingo", "Department": "Business", "Course": "Marketing"}	2026-03-05 06:18:14.259266
44	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	42	Department does not exist; Course does not exist	{"Student_ID": "2026-0041", "Email": "nathan.delacruz41@school.edu", "Last Name": "Dela Cruz", "First Name": "Nathan", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.259266
45	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	43	Department does not exist; Course does not exist	{"Student_ID": "2026-0042", "Email": "ella.reyes42@school.edu", "Last Name": "Reyes", "First Name": "Ella", "Middle Name": "Diaz", "Department": "Business", "Course": "Marketing"}	2026-03-05 06:18:14.259266
46	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	44	Department does not exist; Course does not exist	{"Student_ID": "2026-0043", "Email": "nathan.gonzales43@school.edu", "Last Name": "Gonzales", "First Name": "Nathan", "Middle Name": "Perez", "Department": "Engineering", "Course": "Civil Engineering"}	2026-03-05 06:18:14.259267
47	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	45	Department does not exist; Course does not exist	{"Student_ID": "2026-0044", "Email": "ella.villanueva44@school.edu", "Last Name": "Villanueva", "First Name": "Ella", "Middle Name": "Fernandez", "Department": "Arts and Sciences", "Course": "Psychology"}	2026-03-05 06:18:14.259267
48	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	46	Department does not exist; Course does not exist	{"Student_ID": "2026-0045", "Email": "kyle.santos45@school.edu", "Last Name": "Santos", "First Name": "Kyle", "Middle Name": "Castillo", "Department": "Engineering", "Course": "Computer Engineering"}	2026-03-05 06:18:14.259267
49	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	47	Department does not exist; Course does not exist	{"Student_ID": "2026-0046", "Email": "john.reyes46@school.edu", "Last Name": "Reyes", "First Name": "John", "Middle Name": "Diaz", "Department": "Engineering", "Course": "Civil Engineering"}	2026-03-05 06:18:14.259267
50	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	48	Department does not exist; Course does not exist	{"Student_ID": "2026-0047", "Email": "isabella.castro47@school.edu", "Last Name": "Castro", "First Name": "Isabella", "Middle Name": "Castillo", "Department": "Business", "Course": "Business Administration"}	2026-03-05 06:18:14.259268
51	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	49	Department does not exist; Course does not exist	{"Student_ID": "2026-0048", "Email": "liam.castro48@school.edu", "Last Name": "Castro", "First Name": "Liam", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.259268
52	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	50	Department does not exist; Course does not exist	{"Student_ID": "2026-0049", "Email": "john.ramos49@school.edu", "Last Name": "Ramos", "First Name": "John", "Middle Name": "Santiago", "Department": "Engineering", "Course": "Civil Engineering"}	2026-03-05 06:18:14.259268
53	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	51	Department does not exist; Course does not exist	{"Student_ID": "2026-0050", "Email": "ariana.torres50@school.edu", "Last Name": "Torres", "First Name": "Ariana", "Middle Name": "Martinez", "Department": "Arts and Sciences", "Course": "Psychology"}	2026-03-05 06:18:14.259268
54	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	52	Department does not exist; Course does not exist	{"Student_ID": "2026-0051", "Email": "maria.garcia51@school.edu", "Last Name": "Garcia", "First Name": "Maria", "Middle Name": "Martinez", "Department": "Arts and Sciences", "Course": "Communication"}	2026-03-05 06:18:14.259268
55	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	53	Department does not exist; Course does not exist	{"Student_ID": "2026-0052", "Email": "daniel.navarro52@school.edu", "Last Name": "Navarro", "First Name": "Daniel", "Middle Name": "Santiago", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.259269
56	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	54	Department does not exist; Course does not exist	{"Student_ID": "2026-0053", "Email": "ella.castro53@school.edu", "Last Name": "Castro", "First Name": "Ella", "Middle Name": "Castillo", "Department": "Business", "Course": "Business Administration"}	2026-03-05 06:18:14.259269
57	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	55	Department does not exist; Course does not exist	{"Student_ID": "2026-0054", "Email": "angela.flores54@school.edu", "Last Name": "Flores", "First Name": "Angela", "Middle Name": "Lopez", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.259269
58	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	56	Department does not exist; Course does not exist	{"Student_ID": "2026-0055", "Email": "angela.villanueva55@school.edu", "Last Name": "Villanueva", "First Name": "Angela", "Middle Name": "Lopez", "Department": "Business", "Course": "Marketing"}	2026-03-05 06:18:14.259269
59	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	57	Department does not exist; Course does not exist	{"Student_ID": "2026-0056", "Email": "jose.navarro56@school.edu", "Last Name": "Navarro", "First Name": "Jose", "Middle Name": "Rivera", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.25927
60	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	58	Department does not exist; Course does not exist	{"Student_ID": "2026-0057", "Email": "chloe.castro57@school.edu", "Last Name": "Castro", "First Name": "Chloe", "Middle Name": "Domingo", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.25927
61	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	59	Department does not exist; Course does not exist	{"Student_ID": "2026-0058", "Email": "ariana.mendoza58@school.edu", "Last Name": "Mendoza", "First Name": "Ariana", "Middle Name": "Martinez", "Department": "Arts and Sciences", "Course": "Political Science"}	2026-03-05 06:18:14.25927
62	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	60	Department does not exist; Course does not exist	{"Student_ID": "2026-0059", "Email": "nathan.mendoza59@school.edu", "Last Name": "Mendoza", "First Name": "Nathan", "Middle Name": "Morales", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.25927
63	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	61	Department does not exist; Course does not exist	{"Student_ID": "2026-0060", "Email": "chloe.garcia60@school.edu", "Last Name": "Garcia", "First Name": "Chloe", "Middle Name": "Domingo", "Department": "Business", "Course": "Marketing"}	2026-03-05 06:18:14.259271
64	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	62	Department does not exist; Course does not exist	{"Student_ID": "2026-0061", "Email": "miguel.aquino61@school.edu", "Last Name": "Aquino", "First Name": "Miguel", "Middle Name": "Martinez", "Department": "Engineering", "Course": "Electrical Engineering"}	2026-03-05 06:18:14.259271
65	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	63	Department does not exist; Course does not exist	{"Student_ID": "2026-0062", "Email": "maria.santos62@school.edu", "Last Name": "Santos", "First Name": "Maria", "Middle Name": "Domingo", "Department": "Business", "Course": "Business Administration"}	2026-03-05 06:18:14.259271
66	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	64	Department does not exist; Course does not exist	{"Student_ID": "2026-0063", "Email": "bianca.santos63@school.edu", "Last Name": "Santos", "First Name": "Bianca", "Middle Name": "Castillo", "Department": "Arts and Sciences", "Course": "Communication"}	2026-03-05 06:18:14.259271
67	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	65	Department does not exist; Course does not exist	{"Student_ID": "2026-0064", "Email": "miguel.torres64@school.edu", "Last Name": "Torres", "First Name": "Miguel", "Middle Name": "Domingo", "Department": "Arts and Sciences", "Course": "Psychology"}	2026-03-05 06:18:14.259272
68	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	66	Department does not exist; Course does not exist	{"Student_ID": "2026-0065", "Email": "liam.reyes65@school.edu", "Last Name": "Reyes", "First Name": "Liam", "Middle Name": "Morales", "Department": "Engineering", "Course": "Civil Engineering"}	2026-03-05 06:18:14.259272
69	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	67	Department does not exist; Course does not exist	{"Student_ID": "2026-0066", "Email": "john.garcia66@school.edu", "Last Name": "Garcia", "First Name": "John", "Middle Name": "Domingo", "Department": "Arts and Sciences", "Course": "Psychology"}	2026-03-05 06:18:14.259272
70	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	68	Department does not exist; Course does not exist	{"Student_ID": "2026-0067", "Email": "bianca.castro67@school.edu", "Last Name": "Castro", "First Name": "Bianca", "Middle Name": "Domingo", "Department": "Arts and Sciences", "Course": "Psychology"}	2026-03-05 06:18:14.259272
71	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	69	Department does not exist; Course does not exist	{"Student_ID": "2026-0068", "Email": "angela.villanueva68@school.edu", "Last Name": "Villanueva", "First Name": "Angela", "Middle Name": "Fernandez", "Department": "Business", "Course": "Business Administration"}	2026-03-05 06:18:14.259273
72	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	70	Department does not exist; Course does not exist	{"Student_ID": "2026-0069", "Email": "sofia.castro69@school.edu", "Last Name": "Castro", "First Name": "Sofia", "Middle Name": "Domingo", "Department": "Engineering", "Course": "Civil Engineering"}	2026-03-05 06:18:14.259273
73	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	71	Department does not exist; Course does not exist	{"Student_ID": "2026-0070", "Email": "sofia.flores70@school.edu", "Last Name": "Flores", "First Name": "Sofia", "Middle Name": "Domingo", "Department": "Business", "Course": "Business Administration"}	2026-03-05 06:18:14.259273
74	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	72	Department does not exist; Course does not exist	{"Student_ID": "2026-0071", "Email": "noah.castro71@school.edu", "Last Name": "Castro", "First Name": "Noah", "Middle Name": "Lopez", "Department": "Arts and Sciences", "Course": "Psychology"}	2026-03-05 06:18:14.259274
75	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	73	Department does not exist; Course does not exist	{"Student_ID": "2026-0072", "Email": "ethan.aquino72@school.edu", "Last Name": "Aquino", "First Name": "Ethan", "Middle Name": "Rivera", "Department": "Engineering", "Course": "Civil Engineering"}	2026-03-05 06:18:14.259274
76	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	74	Department does not exist; Course does not exist	{"Student_ID": "2026-0073", "Email": "liam.castro73@school.edu", "Last Name": "Castro", "First Name": "Liam", "Middle Name": "Diaz", "Department": "Engineering", "Course": "Civil Engineering"}	2026-03-05 06:18:14.259274
77	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	75	Department does not exist; Course does not exist	{"Student_ID": "2026-0074", "Email": "chloe.reyes74@school.edu", "Last Name": "Reyes", "First Name": "Chloe", "Middle Name": "Morales", "Department": "Arts and Sciences", "Course": "Psychology"}	2026-03-05 06:18:14.259274
78	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	76	Department does not exist; Course does not exist	{"Student_ID": "2026-0075", "Email": "bianca.castro75@school.edu", "Last Name": "Castro", "First Name": "Bianca", "Middle Name": "Domingo", "Department": "Engineering", "Course": "Civil Engineering"}	2026-03-05 06:18:14.259275
79	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	77	Department does not exist; Course does not exist	{"Student_ID": "2026-0076", "Email": "kyle.reyes76@school.edu", "Last Name": "Reyes", "First Name": "Kyle", "Middle Name": "Santiago", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.259275
80	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	78	Department does not exist; Course does not exist	{"Student_ID": "2026-0077", "Email": "isabella.navarro77@school.edu", "Last Name": "Navarro", "First Name": "Isabella", "Middle Name": "Fernandez", "Department": "Engineering", "Course": "Computer Engineering"}	2026-03-05 06:18:14.259275
81	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	79	Department does not exist; Course does not exist	{"Student_ID": "2026-0078", "Email": "ariana.mendoza78@school.edu", "Last Name": "Mendoza", "First Name": "Ariana", "Middle Name": "Diaz", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.259276
82	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	80	Department does not exist; Course does not exist	{"Student_ID": "2026-0079", "Email": "isabella.gonzales79@school.edu", "Last Name": "Gonzales", "First Name": "Isabella", "Middle Name": "Lopez", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.259276
83	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	81	Department does not exist; Course does not exist	{"Student_ID": "2026-0080", "Email": "john.castro80@school.edu", "Last Name": "Castro", "First Name": "John", "Middle Name": "Domingo", "Department": "Engineering", "Course": "Computer Engineering"}	2026-03-05 06:18:14.259276
84	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	82	Department does not exist; Course does not exist	{"Student_ID": "2026-0081", "Email": "kyle.mendoza81@school.edu", "Last Name": "Mendoza", "First Name": "Kyle", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.259276
85	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	83	Department does not exist; Course does not exist	{"Student_ID": "2026-0082", "Email": "ariana.ramos82@school.edu", "Last Name": "Ramos", "First Name": "Ariana", "Middle Name": "Domingo", "Department": "Engineering", "Course": "Electrical Engineering"}	2026-03-05 06:18:14.259277
86	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	84	Department does not exist; Course does not exist	{"Student_ID": "2026-0083", "Email": "miguel.santos83@school.edu", "Last Name": "Santos", "First Name": "Miguel", "Middle Name": "Perez", "Department": "Business", "Course": "Marketing"}	2026-03-05 06:18:14.259277
87	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	85	Department does not exist; Course does not exist	{"Student_ID": "2026-0084", "Email": "jose.aquino84@school.edu", "Last Name": "Aquino", "First Name": "Jose", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.259277
88	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	86	Department does not exist; Course does not exist	{"Student_ID": "2026-0085", "Email": "ariana.santos85@school.edu", "Last Name": "Santos", "First Name": "Ariana", "Middle Name": "Diaz", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.259277
89	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	87	Department does not exist; Course does not exist	{"Student_ID": "2026-0086", "Email": "liam.gonzales86@school.edu", "Last Name": "Gonzales", "First Name": "Liam", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.259278
90	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	88	Department does not exist; Course does not exist	{"Student_ID": "2026-0087", "Email": "carla.mendoza87@school.edu", "Last Name": "Mendoza", "First Name": "Carla", "Middle Name": "Santiago", "Department": "Arts and Sciences", "Course": "Psychology"}	2026-03-05 06:18:14.259278
91	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	89	Department does not exist; Course does not exist	{"Student_ID": "2026-0088", "Email": "daniel.reyes88@school.edu", "Last Name": "Reyes", "First Name": "Daniel", "Middle Name": "Martinez", "Department": "Engineering", "Course": "Computer Engineering"}	2026-03-05 06:18:14.259278
92	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	90	Department does not exist; Course does not exist	{"Student_ID": "2026-0089", "Email": "carla.mendoza89@school.edu", "Last Name": "Mendoza", "First Name": "Carla", "Middle Name": "Castillo", "Department": "Engineering", "Course": "Electrical Engineering"}	2026-03-05 06:18:14.259278
93	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	91	Department does not exist; Course does not exist	{"Student_ID": "2026-0090", "Email": "liam.torres90@school.edu", "Last Name": "Torres", "First Name": "Liam", "Middle Name": "Domingo", "Department": "Engineering", "Course": "Computer Engineering"}	2026-03-05 06:18:14.259278
94	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	92	Department does not exist; Course does not exist	{"Student_ID": "2026-0091", "Email": "mark.garcia91@school.edu", "Last Name": "Garcia", "First Name": "Mark", "Middle Name": "Lopez", "Department": "Business", "Course": "Finance"}	2026-03-05 06:18:14.259279
95	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	93	Department does not exist; Course does not exist	{"Student_ID": "2026-0092", "Email": "joshua.mendoza92@school.edu", "Last Name": "Mendoza", "First Name": "Joshua", "Middle Name": "Diaz", "Department": "Engineering", "Course": "Electrical Engineering"}	2026-03-05 06:18:14.259279
96	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	94	Department does not exist; Course does not exist	{"Student_ID": "2026-0093", "Email": "miguel.reyes93@school.edu", "Last Name": "Reyes", "First Name": "Miguel", "Middle Name": "Diaz", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.259279
97	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	95	Department does not exist; Course does not exist	{"Student_ID": "2026-0094", "Email": "isabella.navarro94@school.edu", "Last Name": "Navarro", "First Name": "Isabella", "Middle Name": "Santiago", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:18:14.259279
98	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	96	Department does not exist; Course does not exist	{"Student_ID": "2026-0095", "Email": "noah.villanueva95@school.edu", "Last Name": "Villanueva", "First Name": "Noah", "Middle Name": "Castillo", "Department": "Arts and Sciences", "Course": "Political Science"}	2026-03-05 06:18:14.25928
99	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	97	Department does not exist; Course does not exist	{"Student_ID": "2026-0096", "Email": "maria.garcia96@school.edu", "Last Name": "Garcia", "First Name": "Maria", "Middle Name": "Castillo", "Department": "Arts and Sciences", "Course": "Communication"}	2026-03-05 06:18:14.25928
100	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	98	Department does not exist; Course does not exist	{"Student_ID": "2026-0097", "Email": "chloe.castro97@school.edu", "Last Name": "Castro", "First Name": "Chloe", "Middle Name": "Fernandez", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.25928
101	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	99	Department does not exist; Course does not exist	{"Student_ID": "2026-0098", "Email": "mark.flores98@school.edu", "Last Name": "Flores", "First Name": "Mark", "Middle Name": "Diaz", "Department": "Engineering", "Course": "Electrical Engineering"}	2026-03-05 06:18:14.25928
102	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	100	Department does not exist; Course does not exist	{"Student_ID": "2026-0099", "Email": "liam.castro99@school.edu", "Last Name": "Castro", "First Name": "Liam", "Middle Name": "Perez", "Department": "Business", "Course": "Business Administration"}	2026-03-05 06:18:14.259281
103	a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	101	Department does not exist; Course does not exist	{"Student_ID": "2026-0100", "Email": "noah.aquino100@school.edu", "Last Name": "Aquino", "First Name": "Noah", "Middle Name": "Santiago", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:18:14.259281
104	db0e9921-06e2-418e-ba73-3d5986e86dbd	3	duplicate Email in uploaded file	{"Student_ID": "2026-0002", "Email": "lancer.decin@gmail.com", "Last Name": "Villanueva", "First Name": "Ariana", "Middle Name": "Fernandez", "Department": "Business", "Course": "Marketing"}	2026-03-05 06:25:00.30932
105	db0e9921-06e2-418e-ba73-3d5986e86dbd	4	duplicate Email in uploaded file	{"Student_ID": "2026-0003", "Email": "lancer.decin@gmail.com", "Last Name": "Aquino", "First Name": "Carla", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:25:00.309323
106	db0e9921-06e2-418e-ba73-3d5986e86dbd	5	duplicate Email in uploaded file	{"Student_ID": "2026-0004", "Email": "lancer.decin@gmail.com", "Last Name": "Reyes", "First Name": "Nathan", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Technology"}	2026-03-05 06:25:00.309323
107	db0e9921-06e2-418e-ba73-3d5986e86dbd	9	Course does not exist	{"Student_ID": "2026-0008", "Email": "ella.navarro8@school.edu", "Last Name": "Navarro", "First Name": "Ella", "Middle Name": "Santiago", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309324
108	db0e9921-06e2-418e-ba73-3d5986e86dbd	17	Course does not exist	{"Student_ID": "2026-0016", "Email": "chloe.navarro16@school.edu", "Last Name": "Navarro", "First Name": "Chloe", "Middle Name": "Lopez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309324
109	db0e9921-06e2-418e-ba73-3d5986e86dbd	21	Course does not exist	{"Student_ID": "2026-0020", "Email": "ariana.mendoza20@school.edu", "Last Name": "Mendoza", "First Name": "Ariana", "Middle Name": "Rivera", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309324
110	db0e9921-06e2-418e-ba73-3d5986e86dbd	24	Course does not exist	{"Student_ID": "2026-0023", "Email": "isabella.santos23@school.edu", "Last Name": "Santos", "First Name": "Isabella", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309324
111	db0e9921-06e2-418e-ba73-3d5986e86dbd	27	Course does not exist	{"Student_ID": "2026-0026", "Email": "john.mendoza26@school.edu", "Last Name": "Mendoza", "First Name": "John", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309325
112	db0e9921-06e2-418e-ba73-3d5986e86dbd	33	Course does not exist	{"Student_ID": "2026-0032", "Email": "liam.reyes32@school.edu", "Last Name": "Reyes", "First Name": "Liam", "Middle Name": "Lopez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309325
113	db0e9921-06e2-418e-ba73-3d5986e86dbd	42	Course does not exist	{"Student_ID": "2026-0041", "Email": "nathan.delacruz41@school.edu", "Last Name": "Dela Cruz", "First Name": "Nathan", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309325
114	db0e9921-06e2-418e-ba73-3d5986e86dbd	49	Course does not exist	{"Student_ID": "2026-0048", "Email": "liam.castro48@school.edu", "Last Name": "Castro", "First Name": "Liam", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309325
115	db0e9921-06e2-418e-ba73-3d5986e86dbd	53	Course does not exist	{"Student_ID": "2026-0052", "Email": "daniel.navarro52@school.edu", "Last Name": "Navarro", "First Name": "Daniel", "Middle Name": "Santiago", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309326
116	db0e9921-06e2-418e-ba73-3d5986e86dbd	58	Course does not exist	{"Student_ID": "2026-0057", "Email": "chloe.castro57@school.edu", "Last Name": "Castro", "First Name": "Chloe", "Middle Name": "Domingo", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309326
117	db0e9921-06e2-418e-ba73-3d5986e86dbd	79	Course does not exist	{"Student_ID": "2026-0078", "Email": "ariana.mendoza78@school.edu", "Last Name": "Mendoza", "First Name": "Ariana", "Middle Name": "Diaz", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309326
118	db0e9921-06e2-418e-ba73-3d5986e86dbd	85	Course does not exist	{"Student_ID": "2026-0084", "Email": "jose.aquino84@school.edu", "Last Name": "Aquino", "First Name": "Jose", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309326
119	db0e9921-06e2-418e-ba73-3d5986e86dbd	87	Course does not exist	{"Student_ID": "2026-0086", "Email": "liam.gonzales86@school.edu", "Last Name": "Gonzales", "First Name": "Liam", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 06:25:00.309327
124	a2049bf9-bd83-46d8-947d-221349ba7404	21	Course does not exist	{"Student_ID": "2026-0020", "Email": "ariana.mendoza20@school.edu", "Last Name": "Mendoza", "First Name": "Ariana", "Middle Name": "Rivera", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.847409
125	a2049bf9-bd83-46d8-947d-221349ba7404	24	Course does not exist	{"Student_ID": "2026-0023", "Email": "isabella.santos23@school.edu", "Last Name": "Santos", "First Name": "Isabella", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.84741
126	a2049bf9-bd83-46d8-947d-221349ba7404	27	Course does not exist	{"Student_ID": "2026-0026", "Email": "john.mendoza26@school.edu", "Last Name": "Mendoza", "First Name": "John", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.847411
127	a2049bf9-bd83-46d8-947d-221349ba7404	33	Course does not exist	{"Student_ID": "2026-0032", "Email": "liam.reyes32@school.edu", "Last Name": "Reyes", "First Name": "Liam", "Middle Name": "Lopez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.847411
128	a2049bf9-bd83-46d8-947d-221349ba7404	42	Course does not exist	{"Student_ID": "2026-0041", "Email": "nathan.delacruz41@school.edu", "Last Name": "Dela Cruz", "First Name": "Nathan", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.847412
129	a2049bf9-bd83-46d8-947d-221349ba7404	49	Course does not exist	{"Student_ID": "2026-0048", "Email": "liam.castro48@school.edu", "Last Name": "Castro", "First Name": "Liam", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.847412
130	a2049bf9-bd83-46d8-947d-221349ba7404	53	Course does not exist	{"Student_ID": "2026-0052", "Email": "daniel.navarro52@school.edu", "Last Name": "Navarro", "First Name": "Daniel", "Middle Name": "Santiago", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.847413
131	a2049bf9-bd83-46d8-947d-221349ba7404	58	Course does not exist	{"Student_ID": "2026-0057", "Email": "chloe.castro57@school.edu", "Last Name": "Castro", "First Name": "Chloe", "Middle Name": "Domingo", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.847414
132	a2049bf9-bd83-46d8-947d-221349ba7404	79	Course does not exist	{"Student_ID": "2026-0078", "Email": "ariana.mendoza78@school.edu", "Last Name": "Mendoza", "First Name": "Ariana", "Middle Name": "Diaz", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.847415
133	a2049bf9-bd83-46d8-947d-221349ba7404	85	Course does not exist	{"Student_ID": "2026-0084", "Email": "jose.aquino84@school.edu", "Last Name": "Aquino", "First Name": "Jose", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.847415
134	a2049bf9-bd83-46d8-947d-221349ba7404	87	Course does not exist	{"Student_ID": "2026-0086", "Email": "liam.gonzales86@school.edu", "Last Name": "Gonzales", "First Name": "Liam", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.847416
135	a2049bf9-bd83-46d8-947d-221349ba7404	95	Course does not exist	{"Student_ID": "2026-0094", "Email": "isabella.navarro94@school.edu", "Last Name": "Navarro", "First Name": "Isabella", "Middle Name": "Santiago", "Department": "IT", "Course": "Information Systems"}	2026-03-05 12:46:14.847416
136	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	8	Course does not exist	{"Student_ID": "2026-0007", "Email": "chloe.navarro7@school.edu", "Last Name": "Navarro", "First Name": "Chloe", "Middle Name": "Rivera", "Department": "IT", "Course": "Information Systems"}	2026-03-05 13:18:39.18366
137	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	15	Course does not exist	{"Student_ID": "2026-0014", "Email": "miguel.delacruz14@school.edu", "Last Name": "Dela Cruz", "First Name": "Miguel", "Middle Name": "Martinez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 13:18:39.183664
138	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	28	Course does not exist	{"Student_ID": "2026-0027", "Email": "isabella.mendoza27@school.edu", "Last Name": "Mendoza", "First Name": "Isabella", "Middle Name": "Domingo", "Department": "IT", "Course": "Information Systems"}	2026-03-05 13:18:39.183664
139	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	29	Course does not exist	{"Student_ID": "2026-0028", "Email": "nathan.garcia28@school.edu", "Last Name": "Garcia", "First Name": "Nathan", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 13:18:39.183664
140	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	35	Course does not exist	{"Student_ID": "2026-0034", "Email": "kyle.gonzales34@school.edu", "Last Name": "Gonzales", "First Name": "Kyle", "Middle Name": "Castillo", "Department": "IT", "Course": "Information Systems"}	2026-03-05 13:18:39.183664
141	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	64	Course does not exist	{"Student_ID": "2026-0063", "Email": "bianca.castro63@school.edu", "Last Name": "Castro", "First Name": "Bianca", "Middle Name": "Perez", "Department": "IT", "Course": "Information Systems"}	2026-03-05 13:18:39.183665
142	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	68	Course does not exist	{"Student_ID": "2026-0067", "Email": "bianca.castro67@school.edu", "Last Name": "Castro", "First Name": "Bianca", "Middle Name": "Castillo", "Department": "IT", "Course": "Information Systems"}	2026-03-05 13:18:39.183665
143	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	70	Course does not exist	{"Student_ID": "2026-0069", "Email": "carla.delacruz69@school.edu", "Last Name": "Dela Cruz", "First Name": "Carla", "Middle Name": "Domingo", "Department": "IT", "Course": "Information Systems"}	2026-03-05 13:18:39.183666
144	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	83	Course does not exist	{"Student_ID": "2026-0082", "Email": "jose.flores82@school.edu", "Last Name": "Flores", "First Name": "Jose", "Middle Name": "Diaz", "Department": "IT", "Course": "Information Systems"}	2026-03-05 13:18:39.183666
145	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	84	Course does not exist	{"Student_ID": "2026-0083", "Email": "nathan.gonzales83@school.edu", "Last Name": "Gonzales", "First Name": "Nathan", "Middle Name": "Morales", "Department": "IT", "Course": "Information Systems"}	2026-03-05 13:18:39.183666
146	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	85	Course does not exist	{"Student_ID": "2026-0084", "Email": "jose.santos84@school.edu", "Last Name": "Santos", "First Name": "Jose", "Middle Name": "Rivera", "Department": "IT", "Course": "Information Systems"}	2026-03-05 13:18:39.183666
147	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	87	Course does not exist	{"Student_ID": "2026-0086", "Email": "ethan.delacruz86@school.edu", "Last Name": "Dela Cruz", "First Name": "Ethan", "Middle Name": "Diaz", "Department": "IT", "Course": "Information Systems"}	2026-03-05 13:18:39.183667
148	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	9	Email already exists	{"Student_ID": "2026-0008", "Email": "lancerrr0505@gmail.com", "Last Name": "Santos", "First Name": "Carla", "Middle Name": "Rivera", "Department": "Engineering", "Course": "Civil Engineering"}	2026-03-05 13:18:39.183667
149	c7ac08d9-fee4-45a4-bccf-6df86e1b7e90	2	Last Name is required; First Name is required; Middle Name is required; invalid email format; Department does not exist; Course does not exist	{"Student_ID": "STU-E2E-001", "Email": "invalid-email", "Last Name": "", "First Name": "", "Middle Name": "", "Department": "Nonexistent Dept", "Course": "Nonexistent Course"}	2026-03-06 12:15:50.715519
150	c7ac08d9-fee4-45a4-bccf-6df86e1b7e90	3	Student_ID is required; invalid email format; duplicate Email in uploaded file; Department does not exist; Course does not exist	{"Student_ID": "", "Email": "invalid-email", "Last Name": "Doe", "First Name": "Jane", "Middle Name": "A", "Department": "Nonexistent Dept", "Course": "Nonexistent Course"}	2026-03-06 12:15:50.715522
151	659af01e-b34d-46b9-9127-315f59317cf4	2	Last Name is required; First Name is required; Middle Name is required; invalid email format; Department does not exist; Course does not exist	{"Student_ID": "STU-E2E-001", "Email": "invalid-email", "Last Name": "", "First Name": "", "Middle Name": "", "Department": "Nonexistent Dept", "Course": "Nonexistent Course"}	2026-03-06 12:15:51.816656
152	659af01e-b34d-46b9-9127-315f59317cf4	3	Student_ID is required; invalid email format; duplicate Email in uploaded file; Department does not exist; Course does not exist	{"Student_ID": "", "Email": "invalid-email", "Last Name": "Doe", "First Name": "Jane", "Middle Name": "A", "Department": "Nonexistent Dept", "Course": "Nonexistent Course"}	2026-03-06 12:15:51.816659
153	41ab3881-d2e6-4fee-b333-778f3934be00	2	Last Name is required; First Name is required; Middle Name is required; invalid email format; Department does not exist; Course does not exist	{"Student_ID": "STU-E2E-001", "Email": "invalid-email", "Last Name": "", "First Name": "", "Middle Name": "", "Department": "Nonexistent Dept", "Course": "Nonexistent Course"}	2026-03-06 12:52:58.61981
154	41ab3881-d2e6-4fee-b333-778f3934be00	3	Student_ID is required; invalid email format; duplicate Email in uploaded file; Department does not exist; Course does not exist	{"Student_ID": "", "Email": "invalid-email", "Last Name": "Doe", "First Name": "Jane", "Middle Name": "A", "Department": "Nonexistent Dept", "Course": "Nonexistent Course"}	2026-03-06 12:52:58.619815
155	adf2b984-7955-46d2-90fa-a4f1337bf367	2	Last Name is required; First Name is required; Middle Name is required; invalid email format; Department does not exist; Course does not exist	{"Student_ID": "STU-E2E-001", "Email": "invalid-email", "Last Name": "", "First Name": "", "Middle Name": "", "Department": "Nonexistent Dept", "Course": "Nonexistent Course"}	2026-03-06 12:52:59.665349
156	adf2b984-7955-46d2-90fa-a4f1337bf367	3	Student_ID is required; invalid email format; duplicate Email in uploaded file; Department does not exist; Course does not exist	{"Student_ID": "", "Email": "invalid-email", "Last Name": "Doe", "First Name": "Jane", "Middle Name": "A", "Department": "Nonexistent Dept", "Course": "Nonexistent Course"}	2026-03-06 12:52:59.665353
\.


--
-- Data for Name: bulk_import_jobs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.bulk_import_jobs (id, created_by_user_id, status, original_filename, stored_file_path, failed_report_path, total_rows, processed_rows, success_count, failed_count, eta_seconds, error_summary, is_rate_limited, started_at, completed_at, created_at, updated_at, last_heartbeat, target_school_id) FROM stdin;
a41d6af4-2a41-4ca7-9e1d-e9581503e9a1	100	completed	student_samples.xlsx	/tmp/valid8_imports/uploads/a41d6af4-2a41-4ca7-9e1d-e9581503e9a1.xlsx	/tmp/valid8_imports/reports/a41d6af4-2a41-4ca7-9e1d-e9581503e9a1_failed_rows.xlsx	100	100	0	100	0	\N	f	2026-03-05 06:18:14.073504	2026-03-05 06:18:14.310669	2026-03-05 06:18:12.924625	2026-03-05 06:18:14.312014	2026-03-05 06:18:14.310671	4
db0e9921-06e2-418e-ba73-3d5986e86dbd	100	completed	student_samples.xlsx	/tmp/valid8_imports/uploads/db0e9921-06e2-418e-ba73-3d5986e86dbd.xlsx	/tmp/valid8_imports/reports/db0e9921-06e2-418e-ba73-3d5986e86dbd_failed_rows.xlsx	100	100	83	17	0	\N	f	2026-03-05 06:24:40.266395	2026-03-05 06:25:00.389553	2026-03-05 06:24:39.707628	2026-03-05 06:25:00.391875	2026-03-05 06:25:00.389555	4
659af01e-b34d-46b9-9127-315f59317cf4	362	completed	retry_e2e_import_invalid.xlsx	/tmp/valid8_imports/uploads/659af01e-b34d-46b9-9127-315f59317cf4.xlsx	/tmp/valid8_imports/reports/659af01e-b34d-46b9-9127-315f59317cf4_failed_rows.xlsx	2	2	0	2	0	\N	f	2026-03-06 12:15:51.792649	2026-03-06 12:15:51.840554	2026-03-06 12:15:51.7683	2026-03-06 12:15:51.841893	2026-03-06 12:15:51.840556	4
adb3d243-da76-4ed9-9139-9835708ee59a	\N	completed	test_import_lancer.xlsx	/tmp/valid8_imports/uploads/adb3d243-da76-4ed9-9139-9835708ee59a.xlsx	\N	1	1	1	0	0	\N	f	2026-03-05 09:40:14.22485	2026-03-05 09:40:14.859138	2026-03-05 09:40:12.552594	2026-03-05 09:40:14.861258	2026-03-05 09:40:14.85914	4
a2049bf9-bd83-46d8-947d-221349ba7404	100	completed	student_samples.xlsx	/tmp/valid8_imports/uploads/a2049bf9-bd83-46d8-947d-221349ba7404.xlsx	/tmp/valid8_imports/reports/a2049bf9-bd83-46d8-947d-221349ba7404_failed_rows.xlsx	100	100	85	15	0	\N	f	2026-03-05 12:45:43.394707	2026-03-05 12:46:15.017836	2026-03-05 12:45:40.750803	2026-03-05 12:46:15.022457	2026-03-05 12:46:15.017841	4
4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	272	completed	student_samples_abc.xlsx	/tmp/valid8_imports/uploads/4bbccbfb-8f1f-43e5-8f76-7a196885c7e5.xlsx	/tmp/valid8_imports/reports/4bbccbfb-8f1f-43e5-8f76-7a196885c7e5_failed_rows.xlsx	100	100	87	13	0	\N	f	2026-03-05 13:18:15.495133	2026-03-05 13:18:39.312286	2026-03-05 13:18:14.231033	2026-03-05 13:18:39.31576	2026-03-05 13:18:39.312289	5
c7ac08d9-fee4-45a4-bccf-6df86e1b7e90	362	completed	e2e_import_invalid.xlsx	/tmp/valid8_imports/uploads/c7ac08d9-fee4-45a4-bccf-6df86e1b7e90.xlsx	/tmp/valid8_imports/reports/c7ac08d9-fee4-45a4-bccf-6df86e1b7e90_failed_rows.xlsx	2	2	0	2	0	\N	f	2026-03-06 12:15:50.53862	2026-03-06 12:15:50.771892	2026-03-06 12:15:48.854491	2026-03-06 12:15:50.773836	2026-03-06 12:15:50.771895	4
41ab3881-d2e6-4fee-b333-778f3934be00	362	completed	e2e_import_invalid.xlsx	/tmp/valid8_imports/uploads/41ab3881-d2e6-4fee-b333-778f3934be00.xlsx	/tmp/valid8_imports/reports/41ab3881-d2e6-4fee-b333-778f3934be00_failed_rows.xlsx	2	2	0	2	0	\N	f	2026-03-06 12:52:58.145369	2026-03-06 12:52:58.689018	2026-03-06 12:52:57.203359	2026-03-06 12:52:58.690601	2026-03-06 12:52:58.68902	4
adf2b984-7955-46d2-90fa-a4f1337bf367	362	completed	retry_e2e_import_invalid.xlsx	/tmp/valid8_imports/uploads/adf2b984-7955-46d2-90fa-a4f1337bf367.xlsx	/tmp/valid8_imports/reports/adf2b984-7955-46d2-90fa-a4f1337bf367_failed_rows.xlsx	2	2	0	2	0	\N	f	2026-03-06 12:52:59.588754	2026-03-06 12:52:59.687931	2026-03-06 12:52:59.567369	2026-03-06 12:52:59.689648	2026-03-06 12:52:59.687933	4
\.


--
-- Data for Name: data_governance_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.data_governance_settings (school_id, attendance_retention_days, audit_log_retention_days, import_file_retention_days, auto_delete_enabled, updated_by_user_id, updated_at) FROM stdin;
3	1095	3650	180	f	\N	2026-03-06 12:03:04.441248
5	1095	3650	180	f	\N	2026-03-06 12:03:04.441248
4	365	365	30	t	362	2026-03-06 12:53:00.341456
\.


--
-- Data for Name: data_requests; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.data_requests (id, school_id, requested_by_user_id, target_user_id, request_type, scope, status, reason, details_json, output_path, handled_by_user_id, created_at, resolved_at) FROM stdin;
1	4	362	362	export	user_data	completed	E2E export request	{"scope": "self", "review_note": "E2E approve export"}	/tmp/valid8_imports/governance_exports/data_request_1.json	362	2026-03-06 12:17:34.322551	2026-03-06 12:17:34.38859
2	4	362	363	delete	user_data	completed	E2E delete request	{"scope": "user_data", "review_note": "E2E approve delete"}	\N	362	2026-03-06 12:17:34.433712	2026-03-06 12:17:34.456819
3	4	362	362	export	user_data	completed	E2E export	{"scope": "self", "review_note": "E2E approve export"}	/tmp/valid8_imports/governance_exports/data_request_3.json	362	2026-03-06 12:53:00.112215	2026-03-06 12:53:00.186671
4	4	362	363	delete	user_data	completed	E2E delete	{"scope": "user_data", "review_note": "E2E approve delete"}	\N	362	2026-03-06 12:53:00.220774	2026-03-06 12:53:00.247044
\.


--
-- Data for Name: data_retention_run_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.data_retention_run_logs (id, school_id, dry_run, status, summary, created_at) FROM stdin;
1	4	t	completed	audit_logs=0, import_jobs=0, notifications=0, dry_run=True	2026-03-06 12:17:34.507272
2	4	f	completed	audit_logs=0, import_jobs=0, notifications=0, dry_run=False	2026-03-06 12:17:34.659224
3	4	t	completed	audit_logs=0, import_jobs=0, notifications=0, dry_run=True	2026-03-06 12:53:00.293179
4	4	f	completed	audit_logs=0, import_jobs=0, notifications=0, dry_run=False	2026-03-06 12:53:00.38125
\.


--
-- Data for Name: departments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.departments (id, name) FROM stdin;
5	Arts and Sciences
6	Business
7	Engineering
8	IT
\.


--
-- Data for Name: email_delivery_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.email_delivery_logs (id, job_id, user_id, email, status, error_message, retry_count, created_at, updated_at) FROM stdin;
181	adb3d243-da76-4ed9-9139-9835708ee59a	\N	lancer.decin@gmail.com	sent	\N	0	2026-03-05 09:40:16.06503	2026-03-05 09:40:16.065034
182	a2049bf9-bd83-46d8-947d-221349ba7404	191	ella.ramos6@school.edu	sent	\N	0	2026-03-05 12:46:21.229977	2026-03-05 12:46:21.22999
183	a2049bf9-bd83-46d8-947d-221349ba7404	193	carla.gonzales9@school.edu	sent	\N	0	2026-03-05 12:46:21.341301	2026-03-05 12:46:21.34132
184	a2049bf9-bd83-46d8-947d-221349ba7404	190	liam.gonzales5@school.edu	sent	\N	0	2026-03-05 12:46:21.662328	2026-03-05 12:46:21.662341
185	a2049bf9-bd83-46d8-947d-221349ba7404	194	nathan.navarro10@school.edu	sent	\N	0	2026-03-05 12:46:21.877767	2026-03-05 12:46:21.877771
186	a2049bf9-bd83-46d8-947d-221349ba7404	192	john.santos7@school.edu	sent	\N	0	2026-03-05 12:46:22.064173	2026-03-05 12:46:22.064184
187	a2049bf9-bd83-46d8-947d-221349ba7404	189	francinepaalisbo@gmail.com	sent	\N	0	2026-03-05 12:46:22.640082	2026-03-05 12:46:22.640092
188	a2049bf9-bd83-46d8-947d-221349ba7404	188	lancerrr0505@gmail.com	sent	\N	0	2026-03-05 12:46:23.844981	2026-03-05 12:46:23.844994
189	a2049bf9-bd83-46d8-947d-221349ba7404	187	lancer.decin@gmail.com	sent	\N	0	2026-03-05 12:46:23.858664	2026-03-05 12:46:23.858678
190	a2049bf9-bd83-46d8-947d-221349ba7404	197	daniel.ramos13@school.edu	sent	\N	0	2026-03-05 12:46:25.214049	2026-03-05 12:46:25.214053
191	a2049bf9-bd83-46d8-947d-221349ba7404	195	kyle.villanueva11@school.edu	sent	\N	0	2026-03-05 12:46:25.88175	2026-03-05 12:46:25.881755
192	a2049bf9-bd83-46d8-947d-221349ba7404	200	nathan.delacruz17@school.edu	sent	\N	0	2026-03-05 12:46:26.188359	2026-03-05 12:46:26.188364
193	a2049bf9-bd83-46d8-947d-221349ba7404	196	kyle.aquino12@school.edu	sent	\N	0	2026-03-05 12:46:26.912168	2026-03-05 12:46:26.912174
194	a2049bf9-bd83-46d8-947d-221349ba7404	201	daniel.mendoza18@school.edu	sent	\N	0	2026-03-05 12:46:27.134753	2026-03-05 12:46:27.134756
195	a2049bf9-bd83-46d8-947d-221349ba7404	202	angela.reyes19@school.edu	sent	\N	0	2026-03-05 12:46:27.798806	2026-03-05 12:46:27.798814
196	a2049bf9-bd83-46d8-947d-221349ba7404	198	isabella.reyes14@school.edu	sent	\N	0	2026-03-05 12:46:28.070638	2026-03-05 12:46:28.07065
197	a2049bf9-bd83-46d8-947d-221349ba7404	199	bianca.ramos15@school.edu	sent	\N	0	2026-03-05 12:46:28.41938	2026-03-05 12:46:28.419383
198	a2049bf9-bd83-46d8-947d-221349ba7404	203	john.mendoza21@school.edu	sent	\N	0	2026-03-05 12:46:28.68854	2026-03-05 12:46:28.688544
199	a2049bf9-bd83-46d8-947d-221349ba7404	204	kyle.castro22@school.edu	sent	\N	0	2026-03-05 12:46:29.337447	2026-03-05 12:46:29.33745
200	a2049bf9-bd83-46d8-947d-221349ba7404	205	liam.aquino24@school.edu	sent	\N	0	2026-03-05 12:46:29.999108	2026-03-05 12:46:29.999113
201	a2049bf9-bd83-46d8-947d-221349ba7404	206	daniel.navarro25@school.edu	sent	\N	0	2026-03-05 12:46:30.059444	2026-03-05 12:46:30.059451
202	a2049bf9-bd83-46d8-947d-221349ba7404	207	daniel.mendoza27@school.edu	sent	\N	0	2026-03-05 12:46:30.509715	2026-03-05 12:46:30.509719
203	a2049bf9-bd83-46d8-947d-221349ba7404	209	nathan.torres29@school.edu	sent	\N	0	2026-03-05 12:46:31.365947	2026-03-05 12:46:31.365952
204	a2049bf9-bd83-46d8-947d-221349ba7404	210	daniel.ramos30@school.edu	sent	\N	0	2026-03-05 12:46:32.145857	2026-03-05 12:46:32.145865
205	a2049bf9-bd83-46d8-947d-221349ba7404	208	ella.delacruz28@school.edu	sent	\N	0	2026-03-05 12:46:32.382816	2026-03-05 12:46:32.38282
206	a2049bf9-bd83-46d8-947d-221349ba7404	211	ethan.garcia31@school.edu	sent	\N	0	2026-03-05 12:46:32.657969	2026-03-05 12:46:32.657974
207	a2049bf9-bd83-46d8-947d-221349ba7404	212	carla.delacruz33@school.edu	sent	\N	0	2026-03-05 12:46:33.063747	2026-03-05 12:46:33.06375
208	a2049bf9-bd83-46d8-947d-221349ba7404	214	ethan.torres35@school.edu	sent	\N	0	2026-03-05 12:46:33.256991	2026-03-05 12:46:33.256997
209	a2049bf9-bd83-46d8-947d-221349ba7404	213	sofia.delacruz34@school.edu	sent	\N	0	2026-03-05 12:46:33.428343	2026-03-05 12:46:33.428347
210	a2049bf9-bd83-46d8-947d-221349ba7404	215	daniel.garcia36@school.edu	sent	\N	0	2026-03-05 12:46:33.637616	2026-03-05 12:46:33.63762
211	a2049bf9-bd83-46d8-947d-221349ba7404	216	joshua.torres37@school.edu	sent	\N	0	2026-03-05 12:46:34.583639	2026-03-05 12:46:34.583642
212	a2049bf9-bd83-46d8-947d-221349ba7404	217	ariana.gonzales38@school.edu	sent	\N	0	2026-03-05 12:46:35.262204	2026-03-05 12:46:35.262208
213	a2049bf9-bd83-46d8-947d-221349ba7404	218	chloe.aquino39@school.edu	sent	\N	0	2026-03-05 12:46:35.555367	2026-03-05 12:46:35.555371
214	a2049bf9-bd83-46d8-947d-221349ba7404	220	ella.reyes42@school.edu	sent	\N	0	2026-03-05 12:46:36.117859	2026-03-05 12:46:36.117863
215	a2049bf9-bd83-46d8-947d-221349ba7404	221	nathan.gonzales43@school.edu	sent	\N	0	2026-03-05 12:46:36.444548	2026-03-05 12:46:36.444552
216	a2049bf9-bd83-46d8-947d-221349ba7404	219	ella.villanueva40@school.edu	sent	\N	0	2026-03-05 12:46:36.757123	2026-03-05 12:46:36.757126
217	a2049bf9-bd83-46d8-947d-221349ba7404	222	ella.villanueva44@school.edu	sent	\N	0	2026-03-05 12:46:36.89881	2026-03-05 12:46:36.898814
218	a2049bf9-bd83-46d8-947d-221349ba7404	223	kyle.santos45@school.edu	sent	\N	0	2026-03-05 12:46:37.017636	2026-03-05 12:46:37.01764
219	a2049bf9-bd83-46d8-947d-221349ba7404	224	john.reyes46@school.edu	sent	\N	0	2026-03-05 12:46:38.015916	2026-03-05 12:46:38.01592
220	a2049bf9-bd83-46d8-947d-221349ba7404	226	john.ramos49@school.edu	sent	\N	0	2026-03-05 12:46:38.575098	2026-03-05 12:46:38.575102
221	a2049bf9-bd83-46d8-947d-221349ba7404	225	isabella.castro47@school.edu	sent	\N	0	2026-03-05 12:46:38.835807	2026-03-05 12:46:38.83581
222	a2049bf9-bd83-46d8-947d-221349ba7404	227	ariana.torres50@school.edu	sent	\N	0	2026-03-05 12:46:39.402549	2026-03-05 12:46:39.402552
223	a2049bf9-bd83-46d8-947d-221349ba7404	228	maria.garcia51@school.edu	sent	\N	0	2026-03-05 12:46:39.830961	2026-03-05 12:46:39.83097
224	a2049bf9-bd83-46d8-947d-221349ba7404	231	angela.villanueva55@school.edu	sent	\N	0	2026-03-05 12:46:40.408669	2026-03-05 12:46:40.408678
225	a2049bf9-bd83-46d8-947d-221349ba7404	230	angela.flores54@school.edu	sent	\N	0	2026-03-05 12:46:40.72433	2026-03-05 12:46:40.724334
226	a2049bf9-bd83-46d8-947d-221349ba7404	229	ella.castro53@school.edu	sent	\N	0	2026-03-05 12:46:41.21571	2026-03-05 12:46:41.215716
227	a2049bf9-bd83-46d8-947d-221349ba7404	232	jose.navarro56@school.edu	sent	\N	0	2026-03-05 12:46:42.011293	2026-03-05 12:46:42.011298
228	a2049bf9-bd83-46d8-947d-221349ba7404	233	ariana.mendoza58@school.edu	sent	\N	0	2026-03-05 12:46:42.32348	2026-03-05 12:46:42.323484
229	a2049bf9-bd83-46d8-947d-221349ba7404	234	nathan.mendoza59@school.edu	sent	\N	0	2026-03-05 12:46:42.564001	2026-03-05 12:46:42.564017
230	a2049bf9-bd83-46d8-947d-221349ba7404	235	chloe.garcia60@school.edu	sent	\N	0	2026-03-05 12:46:43.000169	2026-03-05 12:46:43.000173
231	a2049bf9-bd83-46d8-947d-221349ba7404	236	miguel.aquino61@school.edu	sent	\N	0	2026-03-05 12:46:43.432331	2026-03-05 12:46:43.432336
232	a2049bf9-bd83-46d8-947d-221349ba7404	237	maria.santos62@school.edu	sent	\N	0	2026-03-05 12:46:44.305287	2026-03-05 12:46:44.305291
233	a2049bf9-bd83-46d8-947d-221349ba7404	238	bianca.santos63@school.edu	sent	\N	0	2026-03-05 12:46:44.475481	2026-03-05 12:46:44.475485
234	a2049bf9-bd83-46d8-947d-221349ba7404	239	miguel.torres64@school.edu	sent	\N	0	2026-03-05 12:46:44.898269	2026-03-05 12:46:44.898279
235	a2049bf9-bd83-46d8-947d-221349ba7404	241	john.garcia66@school.edu	sent	\N	0	2026-03-05 12:46:45.445926	2026-03-05 12:46:45.445932
236	a2049bf9-bd83-46d8-947d-221349ba7404	240	liam.reyes65@school.edu	sent	\N	0	2026-03-05 12:46:45.704308	2026-03-05 12:46:45.704312
237	a2049bf9-bd83-46d8-947d-221349ba7404	242	bianca.castro67@school.edu	sent	\N	0	2026-03-05 12:46:46.392916	2026-03-05 12:46:46.39292
238	a2049bf9-bd83-46d8-947d-221349ba7404	244	sofia.castro69@school.edu	sent	\N	0	2026-03-05 12:46:46.76297	2026-03-05 12:46:46.762974
239	a2049bf9-bd83-46d8-947d-221349ba7404	243	angela.villanueva68@school.edu	sent	\N	0	2026-03-05 12:46:46.986269	2026-03-05 12:46:46.986282
240	a2049bf9-bd83-46d8-947d-221349ba7404	245	sofia.flores70@school.edu	sent	\N	0	2026-03-05 12:46:47.909441	2026-03-05 12:46:47.909443
241	a2049bf9-bd83-46d8-947d-221349ba7404	246	noah.castro71@school.edu	sent	\N	0	2026-03-05 12:46:48.079126	2026-03-05 12:46:48.07914
242	a2049bf9-bd83-46d8-947d-221349ba7404	247	ethan.aquino72@school.edu	sent	\N	0	2026-03-05 12:46:48.630468	2026-03-05 12:46:48.630471
243	a2049bf9-bd83-46d8-947d-221349ba7404	249	chloe.reyes74@school.edu	sent	\N	0	2026-03-05 12:46:48.885075	2026-03-05 12:46:48.885079
244	a2049bf9-bd83-46d8-947d-221349ba7404	248	liam.castro73@school.edu	sent	\N	0	2026-03-05 12:46:49.186649	2026-03-05 12:46:49.186659
245	a2049bf9-bd83-46d8-947d-221349ba7404	250	bianca.castro75@school.edu	sent	\N	0	2026-03-05 12:46:49.712074	2026-03-05 12:46:49.712084
246	a2049bf9-bd83-46d8-947d-221349ba7404	251	kyle.reyes76@school.edu	sent	\N	0	2026-03-05 12:46:49.989576	2026-03-05 12:46:49.989585
247	a2049bf9-bd83-46d8-947d-221349ba7404	252	isabella.navarro77@school.edu	sent	\N	0	2026-03-05 12:46:50.647513	2026-03-05 12:46:50.647524
248	a2049bf9-bd83-46d8-947d-221349ba7404	253	isabella.gonzales79@school.edu	sent	\N	0	2026-03-05 12:46:51.59613	2026-03-05 12:46:51.596136
249	a2049bf9-bd83-46d8-947d-221349ba7404	254	john.castro80@school.edu	sent	\N	0	2026-03-05 12:46:51.825133	2026-03-05 12:46:51.825137
250	a2049bf9-bd83-46d8-947d-221349ba7404	255	kyle.mendoza81@school.edu	sent	\N	0	2026-03-05 12:46:52.332959	2026-03-05 12:46:52.332963
251	a2049bf9-bd83-46d8-947d-221349ba7404	256	ariana.ramos82@school.edu	sent	\N	0	2026-03-05 12:46:52.57281	2026-03-05 12:46:52.572814
252	a2049bf9-bd83-46d8-947d-221349ba7404	257	miguel.santos83@school.edu	sent	\N	0	2026-03-05 12:46:52.781032	2026-03-05 12:46:52.781037
253	a2049bf9-bd83-46d8-947d-221349ba7404	259	carla.mendoza87@school.edu	sent	\N	0	2026-03-05 12:46:53.369006	2026-03-05 12:46:53.369009
254	a2049bf9-bd83-46d8-947d-221349ba7404	258	ariana.santos85@school.edu	sent	\N	0	2026-03-05 12:46:53.48861	2026-03-05 12:46:53.488615
255	a2049bf9-bd83-46d8-947d-221349ba7404	260	daniel.reyes88@school.edu	sent	\N	0	2026-03-05 12:46:54.466662	2026-03-05 12:46:54.466676
256	a2049bf9-bd83-46d8-947d-221349ba7404	261	carla.mendoza89@school.edu	sent	\N	0	2026-03-05 12:46:54.916702	2026-03-05 12:46:54.916708
257	a2049bf9-bd83-46d8-947d-221349ba7404	262	liam.torres90@school.edu	sent	\N	0	2026-03-05 12:46:55.090447	2026-03-05 12:46:55.090459
258	a2049bf9-bd83-46d8-947d-221349ba7404	263	mark.garcia91@school.edu	sent	\N	0	2026-03-05 12:46:55.769219	2026-03-05 12:46:55.769223
259	a2049bf9-bd83-46d8-947d-221349ba7404	264	joshua.mendoza92@school.edu	sent	\N	0	2026-03-05 12:46:56.287221	2026-03-05 12:46:56.287225
260	a2049bf9-bd83-46d8-947d-221349ba7404	265	miguel.reyes93@school.edu	sent	\N	0	2026-03-05 12:46:56.426742	2026-03-05 12:46:56.426746
261	a2049bf9-bd83-46d8-947d-221349ba7404	266	noah.villanueva95@school.edu	sent	\N	0	2026-03-05 12:46:57.100223	2026-03-05 12:46:57.100232
262	a2049bf9-bd83-46d8-947d-221349ba7404	267	maria.garcia96@school.edu	sent	\N	0	2026-03-05 12:46:57.178822	2026-03-05 12:46:57.178825
263	a2049bf9-bd83-46d8-947d-221349ba7404	270	liam.castro99@school.edu	sent	\N	0	2026-03-05 12:46:58.331274	2026-03-05 12:46:58.33128
264	a2049bf9-bd83-46d8-947d-221349ba7404	269	mark.flores98@school.edu	sent	\N	0	2026-03-05 12:46:58.563446	2026-03-05 12:46:58.563455
265	a2049bf9-bd83-46d8-947d-221349ba7404	271	noah.aquino100@school.edu	sent	\N	0	2026-03-05 12:46:59.069238	2026-03-05 12:46:59.069242
266	a2049bf9-bd83-46d8-947d-221349ba7404	268	chloe.castro97@school.edu	sent	\N	0	2026-03-05 12:46:59.588424	2026-03-05 12:46:59.588427
267	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	276	bianca.navarro4@school.edu	sent	\N	0	2026-03-05 13:18:43.849857	2026-03-05 13:18:43.849867
268	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	274	noah.flores2@school.edu	sent	\N	0	2026-03-05 13:18:43.968647	2026-03-05 13:18:43.968654
269	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	279	ella.villanueva9@school.edu	sent	\N	0	2026-03-05 13:18:44.108244	2026-03-05 13:18:44.108252
270	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	280	chloe.ramos10@school.edu	sent	\N	0	2026-03-05 13:18:44.311971	2026-03-05 13:18:44.311973
271	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	278	ariana.delacruz6@school.edu	sent	\N	0	2026-03-05 13:18:44.599501	2026-03-05 13:18:44.599509
272	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	273	meekotan12@gmail.com	sent	\N	0	2026-03-05 13:18:44.794426	2026-03-05 13:18:44.79443
273	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	275	angela.navarro3@school.edu	sent	\N	0	2026-03-05 13:18:44.963323	2026-03-05 13:18:44.963327
274	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	277	jose.aquino5@school.edu	sent	\N	0	2026-03-05 13:18:45.149158	2026-03-05 13:18:45.149164
275	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	283	bianca.villanueva13@school.edu	sent	\N	0	2026-03-05 13:18:47.157744	2026-03-05 13:18:47.157747
276	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	282	sofia.flores12@school.edu	sent	\N	0	2026-03-05 13:18:47.621452	2026-03-05 13:18:47.621459
277	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	285	miguel.aquino16@school.edu	sent	\N	0	2026-03-05 13:18:47.790828	2026-03-05 13:18:47.79083
278	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	281	joshua.flores11@school.edu	sent	\N	0	2026-03-05 13:18:48.000893	2026-03-05 13:18:48.000899
279	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	286	carla.villanueva17@school.edu	sent	\N	0	2026-03-05 13:18:48.35848	2026-03-05 13:18:48.358483
280	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	284	ella.villanueva15@school.edu	sent	\N	0	2026-03-05 13:18:48.555933	2026-03-05 13:18:48.555936
281	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	288	carla.flores19@school.edu	sent	\N	0	2026-03-05 13:18:48.915293	2026-03-05 13:18:48.915297
282	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	287	carla.mendoza18@school.edu	sent	\N	0	2026-03-05 13:18:49.108625	2026-03-05 13:18:49.108631
283	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	289	liam.santos20@school.edu	sent	\N	0	2026-03-05 13:18:50.616704	2026-03-05 13:18:50.616706
284	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	291	noah.navarro22@school.edu	sent	\N	0	2026-03-05 13:18:50.889129	2026-03-05 13:18:50.889134
285	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	292	ariana.santos23@school.edu	sent	\N	0	2026-03-05 13:18:51.085098	2026-03-05 13:18:51.085113
286	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	290	noah.ramos21@school.edu	sent	\N	0	2026-03-05 13:18:51.351701	2026-03-05 13:18:51.351706
287	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	294	nathan.delacruz25@school.edu	sent	\N	0	2026-03-05 13:18:51.491998	2026-03-05 13:18:51.492005
288	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	293	daniel.navarro24@school.edu	sent	\N	0	2026-03-05 13:18:51.758293	2026-03-05 13:18:51.758331
289	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	296	miguel.delacruz29@school.edu	sent	\N	0	2026-03-05 13:18:52.401196	2026-03-05 13:18:52.401199
290	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	295	nathan.mendoza26@school.edu	sent	\N	0	2026-03-05 13:18:52.712867	2026-03-05 13:18:52.712872
291	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	297	noah.flores30@school.edu	sent	\N	0	2026-03-05 13:18:54.003336	2026-03-05 13:18:54.003338
292	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	298	chloe.mendoza31@school.edu	sent	\N	0	2026-03-05 13:18:54.41846	2026-03-05 13:18:54.418464
293	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	299	isabella.torres32@school.edu	sent	\N	0	2026-03-05 13:18:54.687506	2026-03-05 13:18:54.687516
294	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	300	mark.castro33@school.edu	sent	\N	0	2026-03-05 13:18:54.904952	2026-03-05 13:18:54.904955
295	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	302	carla.garcia36@school.edu	sent	\N	0	2026-03-05 13:18:55.305737	2026-03-05 13:18:55.30574
296	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	301	bianca.aquino35@school.edu	sent	\N	0	2026-03-05 13:18:55.537097	2026-03-05 13:18:55.537101
297	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	303	daniel.flores37@school.edu	sent	\N	0	2026-03-05 13:18:56.018035	2026-03-05 13:18:56.018045
298	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	304	daniel.garcia38@school.edu	sent	\N	0	2026-03-05 13:18:56.311329	2026-03-05 13:18:56.311331
299	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	305	angela.gonzales39@school.edu	sent	\N	0	2026-03-05 13:18:57.324928	2026-03-05 13:18:57.324932
300	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	306	nathan.villanueva40@school.edu	sent	\N	0	2026-03-05 13:18:57.973224	2026-03-05 13:18:57.973245
301	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	307	chloe.flores41@school.edu	sent	\N	0	2026-03-05 13:18:58.054926	2026-03-05 13:18:58.054929
302	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	309	isabella.torres43@school.edu	sent	\N	0	2026-03-05 13:18:58.324789	2026-03-05 13:18:58.324793
311	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	316	noah.torres50@school.edu	sent	\N	0	2026-03-05 13:19:02.316503	2026-03-05 13:19:02.316506
319	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	325	carla.ramos59@school.edu	sent	\N	0	2026-03-05 13:19:05.600856	2026-03-05 13:19:05.600858
325	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	333	kyle.santos70@school.edu	sent	\N	0	2026-03-05 13:19:10.26901	2026-03-05 13:19:10.269012
332	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	339	bianca.delacruz76@school.edu	sent	\N	0	2026-03-05 13:19:16.771588	2026-03-05 13:19:16.7716
338	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	346	bianca.delacruz87@school.edu	sent	\N	0	2026-03-05 13:19:22.130529	2026-03-05 13:19:22.130531
346	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	352	john.navarro93@school.edu	sent	\N	0	2026-03-05 13:19:28.607885	2026-03-05 13:19:28.607899
303	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	308	liam.santos42@school.edu	sent	\N	0	2026-03-05 13:18:58.51123	2026-03-05 13:18:58.511235
310	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	317	bianca.reyes51@school.edu	sent	\N	0	2026-03-05 13:19:02.139911	2026-03-05 13:19:02.139915
318	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	324	mark.mendoza58@school.edu	sent	\N	0	2026-03-05 13:19:05.395525	2026-03-05 13:19:05.395527
326	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	332	jose.delacruz68@school.edu	sent	\N	0	2026-03-05 13:19:10.630777	2026-03-05 13:19:10.630779
352	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	340	ethan.navarro77@school.edu	sent	\N	0	2026-03-05 13:19:40.04702	2026-03-05 13:19:40.047028
304	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	310	ariana.delacruz44@school.edu	sent	\N	0	2026-03-05 13:18:58.881625	2026-03-05 13:18:58.881628
313	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	318	bianca.torres52@school.edu	sent	\N	0	2026-03-05 13:19:02.863063	2026-03-05 13:19:02.863068
320	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	327	nathan.reyes61@school.edu	sent	\N	0	2026-03-05 13:19:06.270382	2026-03-05 13:19:06.270385
331	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	334	ethan.navarro71@school.edu	sent	\N	0	2026-03-05 13:19:14.063039	2026-03-05 13:19:14.063045
336	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	345	ariana.mendoza85@school.edu	sent	\N	0	2026-03-05 13:19:20.535162	2026-03-05 13:19:20.535164
343	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	350	angela.flores91@school.edu	sent	\N	0	2026-03-05 13:19:25.174202	2026-03-05 13:19:25.174215
348	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	357	sofia.reyes98@school.edu	sent	\N	0	2026-03-05 13:19:30.771434	2026-03-05 13:19:30.771436
354	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	356	miguel.santos97@school.edu	failed	Connection unexpectedly closed	1	2026-03-05 13:19:49.508687	2026-03-05 13:19:49.508691
305	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	311	nathan.garcia45@school.edu	sent	\N	0	2026-03-05 13:18:59.382918	2026-03-05 13:18:59.382923
312	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	319	isabella.navarro53@school.edu	sent	\N	0	2026-03-05 13:19:02.571105	2026-03-05 13:19:02.571113
321	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	326	bianca.garcia60@school.edu	sent	\N	0	2026-03-05 13:19:06.486641	2026-03-05 13:19:06.486642
327	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	335	carla.gonzales72@school.edu	sent	\N	0	2026-03-05 13:19:11.331206	2026-03-05 13:19:11.331208
340	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	341	carla.castro78@school.edu	sent	\N	0	2026-03-05 13:19:22.713508	2026-03-05 13:19:22.713511
350	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	354	nathan.gonzales95@school.edu	sent	\N	0	2026-03-05 13:19:35.418942	2026-03-05 13:19:35.418951
306	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	312	liam.garcia46@school.edu	sent	\N	0	2026-03-05 13:18:59.572543	2026-03-05 13:18:59.572546
314	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	320	ella.delacruz54@school.edu	sent	\N	0	2026-03-05 13:19:03.316322	2026-03-05 13:19:03.316327
322	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	328	joshua.flores62@school.edu	sent	\N	0	2026-03-05 13:19:07.745577	2026-03-05 13:19:07.74558
330	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	336	ella.castro73@school.edu	sent	\N	0	2026-03-05 13:19:13.923029	2026-03-05 13:19:13.923034
334	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	344	bianca.garcia81@school.edu	sent	\N	0	2026-03-05 13:19:19.25506	2026-03-05 13:19:19.255064
339	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	348	maria.flores89@school.edu	sent	\N	0	2026-03-05 13:19:22.271691	2026-03-05 13:19:22.271697
345	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	353	kyle.reyes94@school.edu	sent	\N	0	2026-03-05 13:19:27.70739	2026-03-05 13:19:27.707393
351	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	359	angela.santos100@school.edu	sent	\N	0	2026-03-05 13:19:37.43871	2026-03-05 13:19:37.438715
307	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	313	mark.reyes47@school.edu	sent	\N	0	2026-03-05 13:19:00.60709	2026-03-05 13:19:00.607093
315	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	321	joshua.ramos55@school.edu	sent	\N	0	2026-03-05 13:19:04.190038	2026-03-05 13:19:04.190058
323	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	329	daniel.gonzales64@school.edu	sent	\N	0	2026-03-05 13:19:08.930593	2026-03-05 13:19:08.930596
329	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	337	isabella.garcia74@school.edu	sent	\N	0	2026-03-05 13:19:13.217895	2026-03-05 13:19:13.217897
333	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	343	maria.delacruz80@school.edu	sent	\N	0	2026-03-05 13:19:17.015124	2026-03-05 13:19:17.015126
337	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	347	ethan.reyes88@school.edu	sent	\N	0	2026-03-05 13:19:21.499191	2026-03-05 13:19:21.499196
344	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	351	carla.santos92@school.edu	sent	\N	0	2026-03-05 13:19:25.332787	2026-03-05 13:19:25.33279
349	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	358	bianca.delacruz99@school.edu	sent	\N	0	2026-03-05 13:19:33.223842	2026-03-05 13:19:33.223845
308	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	315	ariana.villanueva49@school.edu	sent	\N	0	2026-03-05 13:19:01.06041	2026-03-05 13:19:01.060415
317	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	322	carla.garcia56@school.edu	sent	\N	0	2026-03-05 13:19:04.957102	2026-03-05 13:19:04.957106
324	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	331	sofia.delacruz66@school.edu	sent	\N	0	2026-03-05 13:19:10.118949	2026-03-05 13:19:10.118952
335	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	338	mark.flores75@school.edu	sent	\N	0	2026-03-05 13:19:19.450053	2026-03-05 13:19:19.450056
341	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	349	ariana.reyes90@school.edu	sent	\N	0	2026-03-05 13:19:23.237558	2026-03-05 13:19:23.23756
347	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	355	joshua.flores96@school.edu	sent	\N	0	2026-03-05 13:19:29.779248	2026-03-05 13:19:29.779251
309	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	314	john.santos48@school.edu	sent	\N	0	2026-03-05 13:19:01.53519	2026-03-05 13:19:01.535192
316	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	323	isabella.aquino57@school.edu	sent	\N	0	2026-03-05 13:19:04.782092	2026-03-05 13:19:04.782098
328	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	330	liam.aquino65@school.edu	sent	\N	0	2026-03-05 13:19:12.354855	2026-03-05 13:19:12.354858
342	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	342	angela.navarro79@school.edu	sent	\N	0	2026-03-05 13:19:23.645802	2026-03-05 13:19:23.645806
353	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	356	miguel.santos97@school.edu	failed	Connection unexpectedly closed	0	2026-03-05 13:19:46.529755	2026-03-05 13:19:46.529758
355	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	356	miguel.santos97@school.edu	failed	Connection unexpectedly closed	2	2026-03-05 13:19:53.507204	2026-03-05 13:19:53.507208
356	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	356	miguel.santos97@school.edu	failed	Connection unexpectedly closed	3	2026-03-05 13:20:00.49574	2026-03-05 13:20:00.495743
357	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	356	miguel.santos97@school.edu	failed	Connection unexpectedly closed	4	2026-03-05 13:20:02.062194	2026-03-05 13:20:02.062197
358	4bbccbfb-8f1f-43e5-8f76-7a196885c7e5	356	miguel.santos97@school.edu	failed	Connection unexpectedly closed	5	2026-03-05 13:20:15.972928	2026-03-05 13:20:15.972933
\.


--
-- Data for Name: event_consumption_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_consumption_logs (id, event_id, event_type, consumer_name, status, error_message, retry_count, processed_at) FROM stdin;
\.


--
-- Data for Name: event_department_association; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_department_association (event_id, department_id) FROM stdin;
\.


--
-- Data for Name: event_flags; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_flags (id, event_id, reason, flagged_at, active) FROM stdin;
\.


--
-- Data for Name: event_predictions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_predictions (id, event_id, expected_attendance_count, expected_turnout_pct, underperform_probability, risk_level, model_version, generated_at) FROM stdin;
\.


--
-- Data for Name: event_program_association; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_program_association (event_id, program_id) FROM stdin;
\.


--
-- Data for Name: event_ssg_association; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_ssg_association (event_id, ssg_profile_id) FROM stdin;
\.


--
-- Data for Name: events; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.events (id, name, location, start_datetime, end_datetime, status, school_id) FROM stdin;
3	E2E Notification Event 1-1772799159	E2E Hall	2026-03-05 12:12:39.34847	2026-03-05 14:12:39.34847	COMPLETED	4
4	E2E Notification Event 2-1772799159	E2E Hall	2026-03-04 12:12:39.34847	2026-03-04 14:12:39.34847	COMPLETED	4
5	E2E Notification Event 3-1772799159	E2E Hall	2026-03-03 12:12:39.34847	2026-03-03 14:12:39.34847	COMPLETED	4
\.


--
-- Data for Name: login_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.login_history (id, user_id, school_id, email_attempted, success, auth_method, failure_reason, ip_address, user_agent, created_at) FROM stdin;
1	1	\N	admin@university.edu	t	password_mfa_pending	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:10:47.929763
2	1	\N	admin@university.edu	t	password_mfa_pending	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:13:47.113377
3	1	\N	admin@university.edu	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:13:48.13824
4	362	4	e2e.schoolit@test.com	t	password_mfa_pending	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:13:51.907364
5	362	4	e2e.schoolit@test.com	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:13:52.196937
6	362	4	e2e.schoolit@test.com	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:13:52.505991
7	362	4	e2e.schoolit@test.com	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:14:30.329721
8	362	4	e2e.schoolit@test.com	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:15:48.305013
9	362	4	e2e.schoolit@test.com	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:16:01.117378
10	362	4	e2e.schoolit@test.com	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:17:24.203691
11	362	4	e2e.schoolit@test.com	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:23:16.406602
12	1	\N	admin@university.edu	t	password_mfa_pending	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:52:40.394376
13	362	4	e2e.schoolit@test.com	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:52:40.973722
14	362	4	e2e.schoolit@test.com	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:52:41.244418
15	273	5	meekotan12@gmail.com	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-06 13:03:31.378935
16	100	4	mu21@test.com	t	password_mfa_pending	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-06 13:06:17.253984
17	100	4	mu21@test.com	t	mfa	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-06 13:09:25.302368
18	362	4	e2e.schoolit@test.com	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 13:12:13.026199
19	362	4	e2e.schoolit@test.com	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 13:14:25.158869
20	100	4	mu21@test.com	t	password_mfa_pending	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 05:27:18.279903
21	100	4	mu21@test.com	t	mfa	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 05:27:47.282357
22	1	\N	admin@university.edu	t	password_mfa_pending	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 05:29:07.477556
23	1	\N	admin@university.edu	t	mfa	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 05:30:21.192911
24	273	5	meekotan12@gmail.com	t	password	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 05:33:40.427537
25	100	4	mu21@test.com	t	password_mfa_pending	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 06:33:25.709484
26	1	\N	admin@university.edu	t	password_mfa_pending	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 06:33:42.683656
\.


--
-- Data for Name: mfa_challenges; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.mfa_challenges (id, user_id, code_hash, channel, attempts, expires_at, consumed_at, ip_address, user_agent, created_at) FROM stdin;
1faa1a26-6d8b-4376-861e-7fcbf36ca9fd	1	cc8b542e2723af085fb7c2b972cf5870e6dd4a5894e76d5884a53ff9e1923479	email	0	2026-03-06 12:20:43.237539	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:10:43.247026
c85b39eb-cc0d-48b6-b0ce-c251d84f82ad	1	1f0ba29df1ec14edf7cc4c2412a40cfbf6bff1b7b0054c8eaccf6a6c3c3f034c	email	0	2026-03-06 12:23:43.5646	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:13:43.57536
b5801dae-64bc-4a93-9862-0aab48be294a	362	3e23f3eed1e4e778f4d9ad433e6dc7cc4db57ab850d88b03923931101a1ba425	email	0	2026-03-06 12:23:48.582924	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:13:48.583643
e2980c96-cd61-4439-876e-5da7539e4533	1	22614945004add466bc270456d9d75447fecd585424370bdc64fb6b6c7d141d3	email	0	2026-03-06 13:02:34.845648	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:52:34.870144
ae0bc40b-ed6d-4204-8b31-8d93fd713f7d	100	92f5474f138296b908e39043f5dfb741963d53edfc13633f1a1ada7f83d6626d	email	0	2026-03-06 13:16:10.581069	2026-03-06 13:09:25.167794	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-06 13:06:10.585488
fa9e3ca2-9aff-47b0-93f3-b6c8a623d1b9	100	93e37fc6a063586cfd0ab87c323eb35c8d77bdffa92c942c97a3bdc8a0493f02	email	0	2026-03-07 05:37:08.279858	2026-03-07 05:27:47.253569	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 05:27:08.34559
33c3c317-14ce-41c7-9c03-fc724d41002c	1	f8579292778b134111964c2c5c57e9c22a312ae7a35bbe17162749e39d924dd0	email	0	2026-03-07 05:39:03.1493	2026-03-07 05:30:21.15724	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 05:29:03.150728
4350737d-cb4b-4641-8903-c9dd6901d855	100	9a7b5d6929c0fa8e8e5c4473f967629233ef2cfec0e7e4b21c8916c939ad1448	email	0	2026-03-07 06:43:20.481566	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 06:33:20.520411
a6526801-e2bf-4f64-9a1a-1cd8bb7e7b85	1	8ef9882905cf9a243807cf2ee4e3a3c15fbd0ecea6b8c117893d05fb0eff906d	email	0	2026-03-07 06:43:38.946943	\N	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 06:33:38.947666
\.


--
-- Data for Name: model_metadata; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.model_metadata (id, model_name, model_version, trained_at, metrics, feature_schema, notes) FROM stdin;
\.


--
-- Data for Name: notification_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.notification_logs (id, school_id, user_id, category, channel, status, subject, message, error_message, metadata_json, created_at) FROM stdin;
1	4	362	test_notification	email	sent	VALID8 Test Notification	E2E notification test run	\N	{"triggered_by": 362, "channel_hint": "email"}	2026-03-06 12:14:34.653504
2	4	362	test_notification	sms	failed	VALID8 Test Notification	E2E notification test run	SMS provider not configured	{"triggered_by": 362, "channel_hint": "email"}	2026-03-06 12:14:34.675547
3	4	187	account_security	email	sent	E2E Security Alert	This is a test account security notification.	\N	{"triggered_by": 362}	2026-03-06 12:14:39.132514
4	4	100	subscription_renewal	email	sent	Subscription Renewal Reminder	Your school subscription renewal date is 2026-03-07 (1 day(s) remaining).	\N	{"renewal_date": "2026-03-07", "days_until_renewal": 1}	2026-03-06 12:17:31.351868
5	4	362	subscription_renewal	email	sent	Subscription Renewal Reminder	Your school subscription renewal date is 2026-03-07 (1 day(s) remaining).	\N	{"renewal_date": "2026-03-07", "days_until_renewal": 1}	2026-03-06 12:17:34.113941
6	4	362	subscription_renewal	sms	failed	Subscription Renewal Reminder	Your school subscription renewal date is 2026-03-07 (1 day(s) remaining).	SMS provider not configured	{"renewal_date": "2026-03-07", "days_until_renewal": 1}	2026-03-06 12:17:34.12249
7	4	187	missed_events	email	sent	Attendance Alert: Missed Events Detected	Hi Isabella,\n\nOur records show 2 missed event(s) in the last 14 days.\nPlease coordinate with your school office if this is incorrect.\n\nValid8 Attendance System	\N	{"absent_count": 2, "lookback_days": 14}	2026-03-06 12:23:20.698153
8	4	187	low_attendance	email	sent	Attendance Alert: Low Attendance Rate	Hi Isabella,\n\nYour attendance rate is currently 33.3% (1/3) which is below the threshold of 75.0%.\nPlease review your recent attendance records.\n\nValid8 Attendance System	\N	{"total_count": 3, "present_count": 1, "threshold_percent": 75.0, "attendance_percent": 33.33}	2026-03-06 12:23:24.230093
9	4	362	test_notification	email	sent	VALID8 Test Notification	E2E test	\N	{"triggered_by": 362, "channel_hint": "email"}	2026-03-06 12:52:45.529852
10	4	362	test_notification	sms	failed	VALID8 Test Notification	E2E test	SMS provider not configured	{"triggered_by": 362, "channel_hint": "email"}	2026-03-06 12:52:45.541101
11	4	187	missed_events	email	sent	Attendance Alert: Missed Events Detected	Hi Isabella,\n\nOur records show 2 missed event(s) in the last 14 days.\nPlease coordinate with your school office if this is incorrect.\n\nValid8 Attendance System	\N	{"absent_count": 2, "lookback_days": 14}	2026-03-06 12:52:49.085865
12	4	187	low_attendance	email	sent	Attendance Alert: Low Attendance Rate	Hi Isabella,\n\nYour attendance rate is currently 33.3% (1/3) which is below the threshold of 75.0%.\nPlease review your recent attendance records.\n\nValid8 Attendance System	\N	{"total_count": 3, "present_count": 1, "threshold_percent": 75.0, "attendance_percent": 33.33}	2026-03-06 12:52:53.060867
13	4	187	account_security	email	sent	E2E Security Alert	E2E security notification	\N	{"triggered_by": 362}	2026-03-06 12:52:56.784979
14	5	273	account_security	email	sent	New Login Detected	A new login to your VALID8 account was detected. If this wasn't you, reset your password immediately.	\N	{"event": "login"}	2026-03-06 13:03:37.20545
15	4	100	account_security	email	sent	MFA Login Completed	A multi-factor login was completed successfully on your VALID8 account.	\N	{"event": "mfa_login", "challenge_id": "ae0bc40b-ed6d-4204-8b31-8d93fd713f7d"}	2026-03-06 13:09:30.486934
16	4	100	account_security	email	sent	MFA Login Completed	A multi-factor login was completed successfully on your VALID8 account.	\N	{"event": "mfa_login", "challenge_id": "fa9e3ca2-9aff-47b0-93f3-b6c8a623d1b9"}	2026-03-07 05:27:59.44677
17	\N	1	account_security	email	sent	MFA Login Completed	A multi-factor login was completed successfully on your VALID8 account.	\N	{"event": "mfa_login", "challenge_id": "33c3c317-14ce-41c7-9c03-fc724d41002c"}	2026-03-07 05:30:26.205003
18	5	273	account_security	email	sent	New Login Detected	A new login to your VALID8 account was detected. If this wasn't you, reset your password immediately.	\N	{"event": "login"}	2026-03-07 05:33:46.41959
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.notifications (id, user_id, message, is_read, created_at) FROM stdin;
\.


--
-- Data for Name: outbox_events; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.outbox_events (id, event_type, source_service, payload, status, created_at, published_at, retry_count, last_error) FROM stdin;
\.


--
-- Data for Name: password_reset_requests; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.password_reset_requests (id, user_id, school_id, requested_email, status, requested_at, resolved_at, reviewed_by_user_id) FROM stdin;
\.


--
-- Data for Name: program_department_association; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.program_department_association (program_id, department_id) FROM stdin;
14	5
13	5
12	5
17	6
16	6
15	6
20	7
19	7
18	7
21	8
\.


--
-- Data for Name: programs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.programs (id, name) FROM stdin;
12	Communication
13	Political Science
14	Psychology
15	Business Administration
16	Finance
17	Marketing
18	Civil Engineering
19	Computer Engineering
20	Electrical Engineering
21	Information Technology
\.


--
-- Data for Name: recommendation_cache; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.recommendation_cache (id, student_id, recommendations, generated_at, expires_at) FROM stdin;
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.roles (id, name) FROM stdin;
1	student
2	ssg
3	event-organizer
4	admin
5	school_IT
\.


--
-- Data for Name: school_audit_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.school_audit_logs (id, school_id, actor_user_id, action, status, details, created_at) FROM stdin;
7	4	1	school_create_with_school_it	success	{"school_name": "Misamis University", "school_code": null, "school_it_user_id": 100, "school_it_email": "mu21@test.com"}	2026-03-05 06:13:51.8026
8	4	1	school_it_status_update	success	{"school_it_user_id": 100, "school_it_email": "mu21@test.com", "is_active": false}	2026-03-05 06:15:15.961151
9	4	1	school_it_status_update	success	{"school_it_user_id": 100, "school_it_email": "mu21@test.com", "is_active": true}	2026-03-05 06:15:17.551885
10	4	1	school_it_status_update	success	{"school_it_user_id": 100, "school_it_email": "mu21@test.com", "is_active": false}	2026-03-05 06:15:18.732378
11	4	1	school_it_status_update	success	{"school_it_user_id": 100, "school_it_email": "mu21@test.com", "is_active": true}	2026-03-05 06:15:19.420598
12	4	1	school_it_status_update	success	{"school_it_user_id": 100, "school_it_email": "mu21@test.com", "is_active": false}	2026-03-05 06:15:20.139292
13	4	1	school_it_status_update	success	{"school_it_user_id": 100, "school_it_email": "mu21@test.com", "is_active": true}	2026-03-05 06:15:20.845814
14	4	100	student_bulk_import_attempt	queued	{"job_id": "a41d6af4-2a41-4ca7-9e1d-e9581503e9a1", "filename": "student_samples.xlsx", "size_bytes": 13682}	2026-03-05 06:18:12.931029
15	4	100	student_bulk_import_result	success	{"job_id": "a41d6af4-2a41-4ca7-9e1d-e9581503e9a1", "total_rows": 100, "processed_rows": 100, "success_count": 0, "failed_count": 100, "failed_report_path": "/tmp/valid8_imports/reports/a41d6af4-2a41-4ca7-9e1d-e9581503e9a1_failed_rows.xlsx"}	2026-03-05 06:18:14.326458
16	4	100	student_bulk_import_attempt	queued	{"job_id": "db0e9921-06e2-418e-ba73-3d5986e86dbd", "filename": "student_samples.xlsx", "size_bytes": 13682}	2026-03-05 06:24:39.728768
17	4	100	student_bulk_import_result	success	{"job_id": "db0e9921-06e2-418e-ba73-3d5986e86dbd", "total_rows": 100, "processed_rows": 100, "success_count": 83, "failed_count": 17, "failed_report_path": "/tmp/valid8_imports/reports/db0e9921-06e2-418e-ba73-3d5986e86dbd_failed_rows.xlsx"}	2026-03-05 06:25:00.418864
18	4	\N	student_bulk_import_attempt	queued	{"job_id": "adb3d243-da76-4ed9-9139-9835708ee59a", "filename": "test_import_lancer.xlsx", "size_bytes": 4978}	2026-03-05 09:40:12.556984
19	4	\N	student_bulk_import_result	success	{"job_id": "adb3d243-da76-4ed9-9139-9835708ee59a", "total_rows": 1, "processed_rows": 1, "success_count": 1, "failed_count": 0, "failed_report_path": null}	2026-03-05 09:40:14.872024
20	4	100	student_bulk_import_attempt	queued	{"job_id": "a2049bf9-bd83-46d8-947d-221349ba7404", "filename": "student_samples.xlsx", "size_bytes": 13759}	2026-03-05 12:45:40.774826
21	4	100	student_bulk_import_result	success	{"job_id": "a2049bf9-bd83-46d8-947d-221349ba7404", "total_rows": 100, "processed_rows": 100, "success_count": 85, "failed_count": 15, "failed_report_path": "/tmp/valid8_imports/reports/a2049bf9-bd83-46d8-947d-221349ba7404_failed_rows.xlsx"}	2026-03-05 12:46:15.063107
22	5	1	school_create_with_school_it	success	{"school_name": "Andress Bonifacio College", "school_code": null, "school_it_user_id": 272, "school_it_email": "abcit@test.com"}	2026-03-05 13:10:33.649037
23	5	1	school_it_password_reset	success	{"school_it_user_id": 272, "school_it_email": "abcit@test.com"}	2026-03-05 13:11:18.915904
24	5	272	student_bulk_import_attempt	queued	{"job_id": "4bbccbfb-8f1f-43e5-8f76-7a196885c7e5", "filename": "student_samples_abc.xlsx", "size_bytes": 13708}	2026-03-05 13:18:14.277553
25	5	272	student_bulk_import_result	success	{"job_id": "4bbccbfb-8f1f-43e5-8f76-7a196885c7e5", "total_rows": 100, "processed_rows": 100, "success_count": 87, "failed_count": 13, "failed_report_path": "/tmp/valid8_imports/reports/4bbccbfb-8f1f-43e5-8f76-7a196885c7e5_failed_rows.xlsx"}	2026-03-05 13:18:39.360442
26	4	362	student_bulk_import_attempt	queued	{"job_id": "c7ac08d9-fee4-45a4-bccf-6df86e1b7e90", "filename": "e2e_import_invalid.xlsx", "size_bytes": 5009, "retried_from_job_id": null}	2026-03-06 12:15:48.862039
27	4	362	student_bulk_import_result	success	{"job_id": "c7ac08d9-fee4-45a4-bccf-6df86e1b7e90", "total_rows": 2, "processed_rows": 2, "success_count": 0, "failed_count": 2, "failed_report_path": "/tmp/valid8_imports/reports/c7ac08d9-fee4-45a4-bccf-6df86e1b7e90_failed_rows.xlsx"}	2026-03-06 12:15:50.787319
28	4	362	student_bulk_import_retry	queued	{"job_id": "659af01e-b34d-46b9-9127-315f59317cf4", "filename": "retry_e2e_import_invalid.xlsx", "size_bytes": 5004, "retried_from_job_id": "c7ac08d9-fee4-45a4-bccf-6df86e1b7e90"}	2026-03-06 12:15:51.770375
29	4	362	student_bulk_import_result	success	{"job_id": "659af01e-b34d-46b9-9127-315f59317cf4", "total_rows": 2, "processed_rows": 2, "success_count": 0, "failed_count": 2, "failed_report_path": "/tmp/valid8_imports/reports/659af01e-b34d-46b9-9127-315f59317cf4_failed_rows.xlsx"}	2026-03-06 12:15:51.846668
30	4	362	student_bulk_import_attempt	queued	{"job_id": "41ab3881-d2e6-4fee-b333-778f3934be00", "filename": "e2e_import_invalid.xlsx", "size_bytes": 5009, "retried_from_job_id": null}	2026-03-06 12:52:57.214652
31	4	362	student_bulk_import_result	success	{"job_id": "41ab3881-d2e6-4fee-b333-778f3934be00", "total_rows": 2, "processed_rows": 2, "success_count": 0, "failed_count": 2, "failed_report_path": "/tmp/valid8_imports/reports/41ab3881-d2e6-4fee-b333-778f3934be00_failed_rows.xlsx"}	2026-03-06 12:52:58.734242
32	4	362	student_bulk_import_retry	queued	{"job_id": "adf2b984-7955-46d2-90fa-a4f1337bf367", "filename": "retry_e2e_import_invalid.xlsx", "size_bytes": 5005, "retried_from_job_id": "41ab3881-d2e6-4fee-b333-778f3934be00"}	2026-03-06 12:52:59.570748
33	4	362	student_bulk_import_result	success	{"job_id": "adf2b984-7955-46d2-90fa-a4f1337bf367", "total_rows": 2, "processed_rows": 2, "success_count": 0, "failed_count": 2, "failed_report_path": "/tmp/valid8_imports/reports/adf2b984-7955-46d2-90fa-a4f1337bf367_failed_rows.xlsx"}	2026-03-06 12:52:59.699935
\.


--
-- Data for Name: school_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.school_settings (school_id, primary_color, secondary_color, accent_color, updated_at, updated_by_user_id) FROM stdin;
3	#162F65	#2C5F9E	#4A90E2	2026-03-05 06:12:01.649996	\N
4	#ffd500	#ffffff	#ffffff	2026-03-05 06:13:51.81089	1
5	#9e0000	#ffdd00	#ffdd00	2026-03-05 13:10:33.670378	1
\.


--
-- Data for Name: school_subscription_reminders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.school_subscription_reminders (id, school_id, reminder_type, status, due_at, sent_at, error_message, created_at) FROM stdin;
1	4	renewal_warning	sent	2026-03-06 12:17:24.643485	2026-03-06 12:17:34.124221	\N	2026-03-06 12:17:24.646213
\.


--
-- Data for Name: school_subscription_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.school_subscription_settings (school_id, plan_name, user_limit, event_limit_monthly, import_limit_monthly, renewal_date, auto_renew, reminder_days_before, updated_by_user_id, updated_at) FROM stdin;
3	free	500	100	10	\N	f	14	\N	2026-03-06 12:03:04.441248
5	free	500	100	10	\N	f	14	\N	2026-03-06 12:03:04.441248
4	enterprise	1200	300	40	2026-03-07	f	60	362	2026-03-06 12:17:24.569373
\.


--
-- Data for Name: schools; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.schools (id, name, address, logo_url, subscription_plan, subscription_start, subscription_end, created_at, updated_at, school_name, school_code, primary_color, secondary_color, subscription_status, active_status) FROM stdin;
3	Default School	Default Address	\N	free	2026-03-05	\N	2026-03-05 06:12:01.604946	2026-03-05 06:12:01.60495	Default School	\N	#162F65	#2C5F9E	trial	t
4	Misamis University	Misamis University Address	/media/school-logos/f8e19b6147b4487fbafa0c576690deed.jpg	free	2026-03-05	\N	2026-03-05 06:13:51.5426	2026-03-05 06:13:51.542606	Misamis University	\N	#ffd500	#ffffff	trial	t
5	Andress Bonifacio College	Andress Bonifacio College Address	/media/school-logos/4c9c4e1464a54514b5ccca7cf8b924aa.png	free	2026-03-05	\N	2026-03-05 13:10:33.067816	2026-03-05 13:10:33.067834	Andress Bonifacio College	\N	#9e0000	#ffdd00	trial	t
\.


--
-- Data for Name: security_alerts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.security_alerts (id, anomaly_log_id, event_id, severity, message, created_at, acknowledged) FROM stdin;
\.


--
-- Data for Name: ssg_profiles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ssg_profiles (id, user_id, "position") FROM stdin;
\.


--
-- Data for Name: student_profiles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.student_profiles (id, user_id, student_id, department_id, program_id, year_level, face_encoding, is_face_registered, face_image_url, registration_complete, section, rfid_tag, last_face_update, school_id) FROM stdin;
182	187	2026-0001	7	19	1	\N	f	\N	f	\N	\N	\N	4
183	188	2026-0002	6	17	1	\N	f	\N	f	\N	\N	\N	4
184	189	2026-0003	7	18	1	\N	f	\N	f	\N	\N	\N	4
185	190	2026-0005	5	14	1	\N	f	\N	f	\N	\N	\N	4
186	191	2026-0006	5	14	1	\N	f	\N	f	\N	\N	\N	4
187	192	2026-0007	5	14	1	\N	f	\N	f	\N	\N	\N	4
188	193	2026-0009	7	18	1	\N	f	\N	f	\N	\N	\N	4
189	194	2026-0010	5	13	1	\N	f	\N	f	\N	\N	\N	4
190	195	2026-0011	6	17	1	\N	f	\N	f	\N	\N	\N	4
191	196	2026-0012	7	18	1	\N	f	\N	f	\N	\N	\N	4
192	197	2026-0013	5	12	1	\N	f	\N	f	\N	\N	\N	4
193	198	2026-0014	7	19	1	\N	f	\N	f	\N	\N	\N	4
194	199	2026-0015	5	14	1	\N	f	\N	f	\N	\N	\N	4
195	200	2026-0017	7	18	1	\N	f	\N	f	\N	\N	\N	4
196	201	2026-0018	7	18	1	\N	f	\N	f	\N	\N	\N	4
197	202	2026-0019	8	21	1	\N	f	\N	f	\N	\N	\N	4
198	203	2026-0021	5	13	1	\N	f	\N	f	\N	\N	\N	4
199	204	2026-0022	6	15	1	\N	f	\N	f	\N	\N	\N	4
200	205	2026-0024	6	15	1	\N	f	\N	f	\N	\N	\N	4
201	206	2026-0025	8	21	1	\N	f	\N	f	\N	\N	\N	4
202	207	2026-0027	7	20	1	\N	f	\N	f	\N	\N	\N	4
203	208	2026-0028	7	20	1	\N	f	\N	f	\N	\N	\N	4
204	209	2026-0029	5	12	1	\N	f	\N	f	\N	\N	\N	4
205	210	2026-0030	5	14	1	\N	f	\N	f	\N	\N	\N	4
206	211	2026-0031	5	13	1	\N	f	\N	f	\N	\N	\N	4
207	212	2026-0033	7	20	1	\N	f	\N	f	\N	\N	\N	4
208	213	2026-0034	5	12	1	\N	f	\N	f	\N	\N	\N	4
209	214	2026-0035	5	13	1	\N	f	\N	f	\N	\N	\N	4
210	215	2026-0036	7	20	1	\N	f	\N	f	\N	\N	\N	4
211	216	2026-0037	5	13	1	\N	f	\N	f	\N	\N	\N	4
212	217	2026-0038	8	21	1	\N	f	\N	f	\N	\N	\N	4
213	218	2026-0039	6	15	1	\N	f	\N	f	\N	\N	\N	4
214	219	2026-0040	6	17	1	\N	f	\N	f	\N	\N	\N	4
215	220	2026-0042	6	17	1	\N	f	\N	f	\N	\N	\N	4
216	221	2026-0043	7	18	1	\N	f	\N	f	\N	\N	\N	4
217	222	2026-0044	5	14	1	\N	f	\N	f	\N	\N	\N	4
218	223	2026-0045	7	19	1	\N	f	\N	f	\N	\N	\N	4
219	224	2026-0046	7	18	1	\N	f	\N	f	\N	\N	\N	4
220	225	2026-0047	6	15	1	\N	f	\N	f	\N	\N	\N	4
221	226	2026-0049	7	18	1	\N	f	\N	f	\N	\N	\N	4
222	227	2026-0050	5	14	1	\N	f	\N	f	\N	\N	\N	4
223	228	2026-0051	5	12	1	\N	f	\N	f	\N	\N	\N	4
224	229	2026-0053	6	15	1	\N	f	\N	f	\N	\N	\N	4
225	230	2026-0054	8	21	1	\N	f	\N	f	\N	\N	\N	4
226	231	2026-0055	6	17	1	\N	f	\N	f	\N	\N	\N	4
227	232	2026-0056	8	21	1	\N	f	\N	f	\N	\N	\N	4
228	233	2026-0058	5	13	1	\N	f	\N	f	\N	\N	\N	4
229	234	2026-0059	8	21	1	\N	f	\N	f	\N	\N	\N	4
230	235	2026-0060	6	17	1	\N	f	\N	f	\N	\N	\N	4
231	236	2026-0061	7	20	1	\N	f	\N	f	\N	\N	\N	4
232	237	2026-0062	6	15	1	\N	f	\N	f	\N	\N	\N	4
233	238	2026-0063	5	12	1	\N	f	\N	f	\N	\N	\N	4
234	239	2026-0064	5	14	1	\N	f	\N	f	\N	\N	\N	4
235	240	2026-0065	7	18	1	\N	f	\N	f	\N	\N	\N	4
236	241	2026-0066	5	14	1	\N	f	\N	f	\N	\N	\N	4
237	242	2026-0067	5	14	1	\N	f	\N	f	\N	\N	\N	4
238	243	2026-0068	6	15	1	\N	f	\N	f	\N	\N	\N	4
239	244	2026-0069	7	18	1	\N	f	\N	f	\N	\N	\N	4
240	245	2026-0070	6	15	1	\N	f	\N	f	\N	\N	\N	4
241	246	2026-0071	5	14	1	\N	f	\N	f	\N	\N	\N	4
242	247	2026-0072	7	18	1	\N	f	\N	f	\N	\N	\N	4
243	248	2026-0073	7	18	1	\N	f	\N	f	\N	\N	\N	4
244	249	2026-0074	5	14	1	\N	f	\N	f	\N	\N	\N	4
245	250	2026-0075	7	18	1	\N	f	\N	f	\N	\N	\N	4
246	251	2026-0076	8	21	1	\N	f	\N	f	\N	\N	\N	4
247	252	2026-0077	7	19	1	\N	f	\N	f	\N	\N	\N	4
248	253	2026-0079	8	21	1	\N	f	\N	f	\N	\N	\N	4
249	254	2026-0080	7	19	1	\N	f	\N	f	\N	\N	\N	4
250	255	2026-0081	8	21	1	\N	f	\N	f	\N	\N	\N	4
251	256	2026-0082	7	20	1	\N	f	\N	f	\N	\N	\N	4
252	257	2026-0083	6	17	1	\N	f	\N	f	\N	\N	\N	4
253	258	2026-0085	8	21	1	\N	f	\N	f	\N	\N	\N	4
254	259	2026-0087	5	14	1	\N	f	\N	f	\N	\N	\N	4
255	260	2026-0088	7	19	1	\N	f	\N	f	\N	\N	\N	4
256	261	2026-0089	7	20	1	\N	f	\N	f	\N	\N	\N	4
257	262	2026-0090	7	19	1	\N	f	\N	f	\N	\N	\N	4
258	263	2026-0091	6	16	1	\N	f	\N	f	\N	\N	\N	4
259	264	2026-0092	7	20	1	\N	f	\N	f	\N	\N	\N	4
260	265	2026-0093	8	21	1	\N	f	\N	f	\N	\N	\N	4
261	266	2026-0095	5	13	1	\N	f	\N	f	\N	\N	\N	4
262	267	2026-0096	5	12	1	\N	f	\N	f	\N	\N	\N	4
263	268	2026-0097	8	21	1	\N	f	\N	f	\N	\N	\N	4
264	269	2026-0098	7	20	1	\N	f	\N	f	\N	\N	\N	4
265	270	2026-0099	6	15	1	\N	f	\N	f	\N	\N	\N	4
266	271	2026-0100	8	21	1	\N	f	\N	f	\N	\N	\N	4
267	273	2026-0001	7	18	1	\N	f	\N	f	\N	\N	\N	5
268	274	2026-0002	8	21	1	\N	f	\N	f	\N	\N	\N	5
269	275	2026-0003	6	16	1	\N	f	\N	f	\N	\N	\N	5
270	276	2026-0004	5	12	1	\N	f	\N	f	\N	\N	\N	5
271	277	2026-0005	6	17	1	\N	f	\N	f	\N	\N	\N	5
272	278	2026-0006	5	14	1	\N	f	\N	f	\N	\N	\N	5
273	279	2026-0009	8	21	1	\N	f	\N	f	\N	\N	\N	5
274	280	2026-0010	8	21	1	\N	f	\N	f	\N	\N	\N	5
275	281	2026-0011	5	14	1	\N	f	\N	f	\N	\N	\N	5
276	282	2026-0012	5	12	1	\N	f	\N	f	\N	\N	\N	5
277	283	2026-0013	5	12	1	\N	f	\N	f	\N	\N	\N	5
278	284	2026-0015	5	14	1	\N	f	\N	f	\N	\N	\N	5
279	285	2026-0016	6	15	1	\N	f	\N	f	\N	\N	\N	5
280	286	2026-0017	5	13	1	\N	f	\N	f	\N	\N	\N	5
281	287	2026-0018	5	12	1	\N	f	\N	f	\N	\N	\N	5
282	288	2026-0019	5	13	1	\N	f	\N	f	\N	\N	\N	5
283	289	2026-0020	5	13	1	\N	f	\N	f	\N	\N	\N	5
284	290	2026-0021	8	21	1	\N	f	\N	f	\N	\N	\N	5
285	291	2026-0022	7	20	1	\N	f	\N	f	\N	\N	\N	5
286	292	2026-0023	5	12	1	\N	f	\N	f	\N	\N	\N	5
287	293	2026-0024	5	13	1	\N	f	\N	f	\N	\N	\N	5
288	294	2026-0025	7	19	1	\N	f	\N	f	\N	\N	\N	5
289	295	2026-0026	5	13	1	\N	f	\N	f	\N	\N	\N	5
290	296	2026-0029	8	21	1	\N	f	\N	f	\N	\N	\N	5
291	297	2026-0030	6	15	1	\N	f	\N	f	\N	\N	\N	5
292	298	2026-0031	5	12	1	\N	f	\N	f	\N	\N	\N	5
293	299	2026-0032	5	14	1	\N	f	\N	f	\N	\N	\N	5
294	300	2026-0033	7	19	1	\N	f	\N	f	\N	\N	\N	5
295	301	2026-0035	6	15	1	\N	f	\N	f	\N	\N	\N	5
296	302	2026-0036	6	17	1	\N	f	\N	f	\N	\N	\N	5
297	303	2026-0037	7	20	1	\N	f	\N	f	\N	\N	\N	5
298	304	2026-0038	7	20	1	\N	f	\N	f	\N	\N	\N	5
299	305	2026-0039	7	20	1	\N	f	\N	f	\N	\N	\N	5
300	306	2026-0040	8	21	1	\N	f	\N	f	\N	\N	\N	5
301	307	2026-0041	6	16	1	\N	f	\N	f	\N	\N	\N	5
302	308	2026-0042	7	20	1	\N	f	\N	f	\N	\N	\N	5
303	309	2026-0043	6	17	1	\N	f	\N	f	\N	\N	\N	5
304	310	2026-0044	6	15	1	\N	f	\N	f	\N	\N	\N	5
305	311	2026-0045	8	21	1	\N	f	\N	f	\N	\N	\N	5
306	312	2026-0046	6	16	1	\N	f	\N	f	\N	\N	\N	5
307	313	2026-0047	5	13	1	\N	f	\N	f	\N	\N	\N	5
308	314	2026-0048	7	19	1	\N	f	\N	f	\N	\N	\N	5
309	315	2026-0049	8	21	1	\N	f	\N	f	\N	\N	\N	5
310	316	2026-0050	6	17	1	\N	f	\N	f	\N	\N	\N	5
311	317	2026-0051	6	17	1	\N	f	\N	f	\N	\N	\N	5
312	318	2026-0052	5	14	1	\N	f	\N	f	\N	\N	\N	5
313	319	2026-0053	6	15	1	\N	f	\N	f	\N	\N	\N	5
314	320	2026-0054	5	14	1	\N	f	\N	f	\N	\N	\N	5
315	321	2026-0055	6	16	1	\N	f	\N	f	\N	\N	\N	5
316	322	2026-0056	7	19	1	\N	f	\N	f	\N	\N	\N	5
317	323	2026-0057	7	19	1	\N	f	\N	f	\N	\N	\N	5
318	324	2026-0058	8	21	1	\N	f	\N	f	\N	\N	\N	5
319	325	2026-0059	7	20	1	\N	f	\N	f	\N	\N	\N	5
320	326	2026-0060	5	13	1	\N	f	\N	f	\N	\N	\N	5
321	327	2026-0061	5	14	1	\N	f	\N	f	\N	\N	\N	5
322	328	2026-0062	8	21	1	\N	f	\N	f	\N	\N	\N	5
323	329	2026-0064	5	13	1	\N	f	\N	f	\N	\N	\N	5
324	330	2026-0065	7	19	1	\N	f	\N	f	\N	\N	\N	5
325	331	2026-0066	6	15	1	\N	f	\N	f	\N	\N	\N	5
326	332	2026-0068	5	12	1	\N	f	\N	f	\N	\N	\N	5
327	333	2026-0070	5	12	1	\N	f	\N	f	\N	\N	\N	5
328	334	2026-0071	6	15	1	\N	f	\N	f	\N	\N	\N	5
329	335	2026-0072	7	20	1	\N	f	\N	f	\N	\N	\N	5
330	336	2026-0073	5	14	1	\N	f	\N	f	\N	\N	\N	5
331	337	2026-0074	7	19	1	\N	f	\N	f	\N	\N	\N	5
332	338	2026-0075	7	19	1	\N	f	\N	f	\N	\N	\N	5
333	339	2026-0076	7	19	1	\N	f	\N	f	\N	\N	\N	5
334	340	2026-0077	5	13	1	\N	f	\N	f	\N	\N	\N	5
335	341	2026-0078	6	17	1	\N	f	\N	f	\N	\N	\N	5
336	342	2026-0079	6	17	1	\N	f	\N	f	\N	\N	\N	5
337	343	2026-0080	8	21	1	\N	f	\N	f	\N	\N	\N	5
338	344	2026-0081	7	20	1	\N	f	\N	f	\N	\N	\N	5
339	345	2026-0085	5	14	1	\N	f	\N	f	\N	\N	\N	5
340	346	2026-0087	7	20	1	\N	f	\N	f	\N	\N	\N	5
341	347	2026-0088	6	16	1	\N	f	\N	f	\N	\N	\N	5
342	348	2026-0089	5	13	1	\N	f	\N	f	\N	\N	\N	5
343	349	2026-0090	6	16	1	\N	f	\N	f	\N	\N	\N	5
344	350	2026-0091	5	14	1	\N	f	\N	f	\N	\N	\N	5
345	351	2026-0092	7	20	1	\N	f	\N	f	\N	\N	\N	5
346	352	2026-0093	7	20	1	\N	f	\N	f	\N	\N	\N	5
347	353	2026-0094	7	19	1	\N	f	\N	f	\N	\N	\N	5
348	354	2026-0095	6	16	1	\N	f	\N	f	\N	\N	\N	5
349	355	2026-0096	8	21	1	\N	f	\N	f	\N	\N	\N	5
350	356	2026-0097	5	12	1	\N	f	\N	f	\N	\N	\N	5
351	357	2026-0098	8	21	1	\N	f	\N	f	\N	\N	\N	5
352	358	2026-0099	7	19	1	\N	f	\N	f	\N	\N	\N	5
353	359	2026-0100	7	18	1	\N	f	\N	f	\N	\N	\N	5
\.


--
-- Data for Name: student_risk_scores; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.student_risk_scores (id, student_id, risk_score, risk_level, recommendation, factors, generated_at, updated_at) FROM stdin;
\.


--
-- Data for Name: user_notification_preferences; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_notification_preferences (user_id, email_enabled, sms_enabled, sms_number, notify_missed_events, notify_low_attendance, notify_account_security, notify_subscription, updated_at) FROM stdin;
362	t	t	+15550001111	t	t	t	t	2026-03-06 12:14:30.775834
187	t	f	\N	t	t	t	t	2026-03-06 12:14:34.974826
100	t	f	\N	t	t	t	t	2026-03-06 12:17:27.675354
273	t	f	\N	t	t	t	t	2026-03-06 13:03:31.406212
1	t	f	\N	t	t	t	t	2026-03-07 05:30:21.228048
\.


--
-- Data for Name: user_privacy_consents; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_privacy_consents (id, user_id, school_id, consent_type, consent_granted, consent_version, source, created_at) FROM stdin;
1	362	4	privacy_policy	t	v2	web	2026-03-06 12:17:34.229668
2	362	4	privacy_policy	t	v2	web	2026-03-06 12:52:59.998139
\.


--
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_roles (id, user_id, role_id) FROM stdin;
1	1	4
100	100	5
187	187	1
188	188	1
189	189	1
190	190	1
191	191	1
192	192	1
193	193	1
194	194	1
195	195	1
196	196	1
197	197	1
198	198	1
199	199	1
200	200	1
201	201	1
202	202	1
203	203	1
204	204	1
205	205	1
206	206	1
207	207	1
208	208	1
209	209	1
210	210	1
211	211	1
212	212	1
213	213	1
214	214	1
215	215	1
216	216	1
217	217	1
218	218	1
219	219	1
220	220	1
221	221	1
222	222	1
223	223	1
224	224	1
225	225	1
226	226	1
227	227	1
228	228	1
229	229	1
230	230	1
231	231	1
232	232	1
233	233	1
234	234	1
235	235	1
236	236	1
237	237	1
238	238	1
239	239	1
240	240	1
241	241	1
242	242	1
243	243	1
244	244	1
245	245	1
246	246	1
247	247	1
248	248	1
249	249	1
250	250	1
251	251	1
252	252	1
253	253	1
254	254	1
255	255	1
256	256	1
257	257	1
258	258	1
259	259	1
260	260	1
261	261	1
262	262	1
263	263	1
264	264	1
265	265	1
266	266	1
267	267	1
268	268	1
269	269	1
270	270	1
271	271	1
272	272	5
273	273	1
274	274	1
275	275	1
276	276	1
277	277	1
278	278	1
279	279	1
280	280	1
281	281	1
282	282	1
283	283	1
284	284	1
285	285	1
286	286	1
287	287	1
288	288	1
289	289	1
290	290	1
291	291	1
292	292	1
293	293	1
294	294	1
295	295	1
296	296	1
297	297	1
298	298	1
299	299	1
300	300	1
301	301	1
302	302	1
303	303	1
304	304	1
305	305	1
306	306	1
307	307	1
308	308	1
309	309	1
310	310	1
311	311	1
312	312	1
313	313	1
314	314	1
315	315	1
316	316	1
317	317	1
318	318	1
319	319	1
320	320	1
321	321	1
322	322	1
323	323	1
324	324	1
325	325	1
326	326	1
327	327	1
328	328	1
329	329	1
330	330	1
331	331	1
332	332	1
333	333	1
334	334	1
335	335	1
336	336	1
337	337	1
338	338	1
339	339	1
340	340	1
341	341	1
342	342	1
343	343	1
344	344	1
345	345	1
346	346	1
347	347	1
348	348	1
349	349	1
350	350	1
351	351	1
352	352	1
353	353	1
354	354	1
355	355	1
356	356	1
357	357	1
358	358	1
359	359	1
362	362	5
363	363	1
\.


--
-- Data for Name: user_security_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_security_settings (user_id, mfa_enabled, trusted_device_days, updated_at) FROM stdin;
1	t	14	2026-03-06 12:10:43.175402
362	t	14	2026-03-06 12:52:41.414296
273	f	14	2026-03-06 13:03:31.310274
100	t	14	2026-03-06 13:06:10.556841
\.


--
-- Data for Name: user_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_sessions (id, user_id, token_jti, ip_address, user_agent, created_at, last_seen_at, revoked_at, expires_at) FROM stdin;
c8cb2b0d-ab0d-4648-a752-db1c0c525a93	1	eb3caac4-399f-4dc6-bfde-2ce0f4e076ad	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:13:48.107313	2026-03-06 12:13:48.107313	\N	2026-03-06 12:43:48.107313
b956d08f-a441-4b73-94d4-0e199e1b57aa	362	137487d8-faae-4170-9fa7-ab329a4b226d	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:13:52.194553	2026-03-06 12:13:52.194553	2026-03-06 12:13:52.947403	2026-03-06 12:43:52.194553
b645a65c-2fb2-4343-824d-0d9c237c06af	362	72d6a09e-c2ad-4d40-8286-8507836883a3	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:52:41.242368	2026-03-06 12:52:41.242368	\N	2026-03-06 13:22:41.242368
5f65f0d1-bca6-4a20-838c-ed59f79048dc	362	c1ee9a46-efbe-4c72-91f6-0eb83dcaacab	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:52:40.964606	2026-03-06 12:52:40.964606	2026-03-06 12:52:41.48774	2026-03-06 13:22:40.964606
799330b7-1103-46fd-bcb6-8cfa0ff67a73	362	131612e2-8427-4b60-b71a-e06dbec8c517	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:17:24.190757	2026-03-06 12:17:24.190757	2026-03-06 12:52:41.48774	2026-03-06 12:47:24.190757
afcbdfd5-ea6d-40cf-bd0a-b140b513306d	362	dd8509f7-3ada-46d4-8f71-ad19b9ccff24	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:23:16.351459	2026-03-06 12:23:16.351459	2026-03-06 12:52:41.48774	2026-03-06 12:53:16.351459
bf2f40e6-1310-48b0-b0df-4e6c121d386d	362	9b29fc24-854f-445a-9115-17b4378e7b1a	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:16:01.115316	2026-03-06 12:16:01.115316	2026-03-06 12:52:41.48774	2026-03-06 12:46:01.115316
c943985d-3adb-4ce8-ad7b-d15d6346c33e	362	e9d626c4-81a5-44de-9c95-76f2c8c7fdee	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:13:52.501716	2026-03-06 12:13:52.501716	2026-03-06 12:52:41.48774	2026-03-06 12:43:52.501716
ec3be028-6429-43b2-9ab3-6fff50bef90c	362	7ab700de-ace1-4149-9bb0-7ed2e8a6d91b	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:15:48.283223	2026-03-06 12:15:48.283223	2026-03-06 12:52:41.48774	2026-03-06 12:45:48.283223
fd136164-6f29-4d87-8539-bf928f969481	362	da09211f-6797-4c18-9339-4c31debe16bd	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 12:14:30.324303	2026-03-06 12:14:30.324303	2026-03-06 12:52:41.48774	2026-03-06 12:44:30.324303
8bea2376-27ae-432c-a031-55fbc0b123d7	273	7354d3bc-1501-488a-84f1-154ca0e0fb26	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-06 13:03:31.339182	2026-03-06 13:03:31.339182	\N	2026-03-06 13:33:31.339182
cc2f5b02-86e2-4850-b1b1-bd6bf4cc301c	100	b549c05f-42c6-4857-956e-8e6e2b11bd8b	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-06 13:09:25.283672	2026-03-06 13:09:25.283672	\N	2026-03-06 13:39:25.283672
5bd6003f-6950-432f-8510-93dad20d8947	362	1152fb13-d2a9-4c80-91bd-fb8ddc988c93	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 13:12:12.830379	2026-03-06 13:12:12.830379	\N	2026-03-06 13:42:12.830379
991817ae-78bc-42a5-a27f-bf76615f15ae	362	1f145193-1811-4813-9924-60b8103a6f91	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26200; en-US) PowerShell/7.5.4	2026-03-06 13:14:25.044899	2026-03-06 13:14:25.044899	\N	2026-03-06 13:44:25.044899
ebc7d6a6-48f4-4c47-9e1f-4ae2aed27ac2	100	5437e721-4f47-48cb-aa0e-85ea0d41d022	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 05:27:47.267109	2026-03-07 05:27:47.267109	\N	2026-03-07 05:57:47.267109
04e1d519-29a9-4da2-b710-607aec7767c0	1	c4302507-6cef-45f3-bd53-e8be44718c77	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 05:30:21.179469	2026-03-07 05:30:21.179469	\N	2026-03-07 06:00:21.179469
5c25f95f-ae72-4669-8c7b-3dcd5cb60c92	273	f67eb9eb-a950-4b97-8d2a-9b91793af6e3	172.18.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0	2026-03-07 05:33:40.411917	2026-03-07 05:33:40.411917	\N	2026-03-07 06:03:40.411917
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, email, password_hash, first_name, middle_name, last_name, is_active, created_at, approval_status, requested_roles, requested_ssg_position, school_id, must_change_password) FROM stdin;
188	lancerrr0505@gmail.com	$2b$12$TWwIRk9toZpnklNV1uNjnOn3MlvqQ/DBsGFaPflo3m.nAz5/v.EW.	Ariana	Fernandez	Villanueva	t	2026-03-05 12:46:14.11596	approved	\N	\N	4	f
187	lancer.decin@gmail.com	$2b$12$yAWMzrJ3r05axUSL.LQBw.NcgQY.xaTIdjHss8ZhJN901Ha5nQ1Na	Isabella	Diaz	Navarro	t	2026-03-05 12:46:14.115957	approved	\N	\N	4	t
100	mu21@test.com	$2b$12$oQdptH0oheOm8M0VAaiZJOIYonUrAqKTd0.ymb9XCI9OIlORUth8i	muIT	muIT	muIT	t	2026-03-05 06:13:51.78785	approved	\N	\N	4	f
189	francinepaalisbo@gmail.com	$2b$12$9bkzqZ1r6IvZcN4ow3xsxu/O1nnZunqF2oyHBl3hY9b3/8miwQpWS	Francine Nicole	Constancio	Paalisbo	t	2026-03-05 12:46:14.115961	approved	\N	\N	4	t
190	liam.gonzales5@school.edu	$2b$12$gW3pR0RLHuDplsMhfTKmq.Na9rW2zO/F245jAP3B9YrbQvWsopg8O	Liam	Diaz	Gonzales	t	2026-03-05 12:46:14.115961	approved	\N	\N	4	t
191	ella.ramos6@school.edu	$2b$12$/HbdXpDZr6p2upiiaoX.neIM6Q/.p2d68Mncr2o3yVQ.aUU6I7FeW	Ella	Morales	Ramos	t	2026-03-05 12:46:14.115961	approved	\N	\N	4	t
192	john.santos7@school.edu	$2b$12$wBK8XspqRoncyE.Pil52cusBSXUPtB4mHummFu5w1FEsY2IQoxI.m	John	Martinez	Santos	t	2026-03-05 12:46:14.115962	approved	\N	\N	4	t
193	carla.gonzales9@school.edu	$2b$12$mx1JhqyWr5R8VkFc/rLOpuPzrmxPfsIeQeIU6VuL67pFxKkLHijTS	Carla	Domingo	Gonzales	t	2026-03-05 12:46:14.115962	approved	\N	\N	4	t
194	nathan.navarro10@school.edu	$2b$12$/IU1bf//4QJxqdXG5PTwGudXFriflhjgkGGFjP/wIFWd/XgTc.eOe	Nathan	Domingo	Navarro	t	2026-03-05 12:46:14.115963	approved	\N	\N	4	t
195	kyle.villanueva11@school.edu	$2b$12$7JjKqq9AfX8nw.0JRAN24OlDlzP7XOKCi6uQFSPPNuaghYa6Yvgv.	Kyle	Fernandez	Villanueva	t	2026-03-05 12:46:14.115963	approved	\N	\N	4	t
196	kyle.aquino12@school.edu	$2b$12$H3kGN69d3T1cOm45U0UFtuTv1n2FNE8eJr58r9K2b/9rqiQ6MyN3S	Kyle	Fernandez	Aquino	t	2026-03-05 12:46:14.115963	approved	\N	\N	4	t
197	daniel.ramos13@school.edu	$2b$12$/B/qbDfEhlvtepGYv.OAcOkszbcWeXh68k7bLCsXd1Nta50jqnyLS	Daniel	Castillo	Ramos	t	2026-03-05 12:46:14.115963	approved	\N	\N	4	t
198	isabella.reyes14@school.edu	$2b$12$jJzy4w7ervRj.Us/swJbuOvrz7am.r8H3MVxuFJ/qnLrMJtyLh4Mu	Isabella	Castillo	Reyes	t	2026-03-05 12:46:14.115964	approved	\N	\N	4	t
199	bianca.ramos15@school.edu	$2b$12$3tz.AKBWtq5oEHydnJcfq.1sLYly4fmxq9Vew1YLIkxobCzRSpqEq	Bianca	Diaz	Ramos	t	2026-03-05 12:46:14.115964	approved	\N	\N	4	t
200	nathan.delacruz17@school.edu	$2b$12$JknELt0GgP0FR7spMkfbw.i1B3jkUxyCcUcCOM8ntham211JQXm4G	Nathan	Santiago	Dela Cruz	t	2026-03-05 12:46:14.115964	approved	\N	\N	4	t
201	daniel.mendoza18@school.edu	$2b$12$nkcDnIMpaIg1N0PB9cUzbuMw.eTdbAQcT1rI3ttMFUb8yXy4nSrEW	Daniel	Domingo	Mendoza	t	2026-03-05 12:46:14.115965	approved	\N	\N	4	t
202	angela.reyes19@school.edu	$2b$12$i8QSkaLik9nU3Qa1zg8NTOQEZSsy0PnZsXRtSgf4Q.S1S/iXx1H0C	Angela	Domingo	Reyes	t	2026-03-05 12:46:14.115965	approved	\N	\N	4	t
203	john.mendoza21@school.edu	$2b$12$boyVc.eLO/Ae98tqK4k.CenDfN42fID4hxEho8VD.qIpZRYGPDG3K	John	Santiago	Mendoza	t	2026-03-05 12:46:14.115965	approved	\N	\N	4	t
204	kyle.castro22@school.edu	$2b$12$kb8x5rAe8BYnsAIDYSBAa.DVFbfHa9wcAlyhDD.putJL1fjwGLrlO	Kyle	Perez	Castro	t	2026-03-05 12:46:14.115966	approved	\N	\N	4	t
205	liam.aquino24@school.edu	$2b$12$y4j5c9veS0LxXMgB/MrQ2O/RAV0c8IYmGac7y1Zb.CCcXSMMSNu9K	Liam	Domingo	Aquino	t	2026-03-05 12:46:14.115966	approved	\N	\N	4	t
206	daniel.navarro25@school.edu	$2b$12$5ZiBLN0sg1zf0GZ7/WQYVe/f3KShzkF5vdm6P2Ebr30ParvxYwO.O	Daniel	Santiago	Navarro	t	2026-03-05 12:46:14.115966	approved	\N	\N	4	t
207	daniel.mendoza27@school.edu	$2b$12$T1NlgwzhW4KzSPr4PoKomuU9i0.4m0Lgi26vHnSfdx70R/fG7SF3m	Daniel	Morales	Mendoza	t	2026-03-05 12:46:14.115966	approved	\N	\N	4	t
208	ella.delacruz28@school.edu	$2b$12$nFWa8wp5C3avq5EIqdykIu029Yzhq6iORTeMF9waQnyIt8a5Y4DXS	Ella	Lopez	Dela Cruz	t	2026-03-05 12:46:14.115967	approved	\N	\N	4	t
209	nathan.torres29@school.edu	$2b$12$KkMy3VSDP8BTPgQhY1fqkO5ncmzi5qs8laFozbOLOSd1IpMZ/bw9m	Nathan	Rivera	Torres	t	2026-03-05 12:46:14.115967	approved	\N	\N	4	t
210	daniel.ramos30@school.edu	$2b$12$26grkIQGNcmZonxZ8toNPe88Ip9lwTWhUS5m36rwbE3XGpPuqd5N6	Daniel	Rivera	Ramos	t	2026-03-05 12:46:14.115967	approved	\N	\N	4	t
211	ethan.garcia31@school.edu	$2b$12$GVrXQYUFFIuEJtDdvRoNE.3uZRpbzlmhR2YgPLJblSnXoXm2fxmtS	Ethan	Martinez	Garcia	t	2026-03-05 12:46:14.115967	approved	\N	\N	4	t
212	carla.delacruz33@school.edu	$2b$12$8Fbj/u9xQdonT4.DaY0xs.xeeUaKRRMWtHDVqGhJADC1iwucuXMhm	Carla	Santiago	Dela Cruz	t	2026-03-05 12:46:14.115968	approved	\N	\N	4	t
213	sofia.delacruz34@school.edu	$2b$12$1hDIp2fbfDKVbZD5VmELM.DfLItpUttd4iqlD4nV5TN9njNqBPtKS	Sofia	Domingo	Dela Cruz	t	2026-03-05 12:46:14.115968	approved	\N	\N	4	t
214	ethan.torres35@school.edu	$2b$12$ePisBGxxyPBIjifEqXlCfupYEK/qyNrQFArobtNkmKIO5dFo7ihSm	Ethan	Fernandez	Torres	t	2026-03-05 12:46:14.115968	approved	\N	\N	4	t
215	daniel.garcia36@school.edu	$2b$12$Z2pvHJs7pnKzmBqX4i0vuO.wJzc7UrKES7jKQkwEoFjHQzdY3Qef2	Daniel	Lopez	Garcia	t	2026-03-05 12:46:14.115969	approved	\N	\N	4	t
216	joshua.torres37@school.edu	$2b$12$IjUPvS1xKkH7k5ngx2G9Fukqzt3URbYXMVpNgkHl7gxnIN5VqTMj6	Joshua	Diaz	Torres	t	2026-03-05 12:46:14.115969	approved	\N	\N	4	t
217	ariana.gonzales38@school.edu	$2b$12$UfhLrIEabrdHn3Mq/JY83.yf4Xnj3a/EoM/Mb2N9jGrMLQkEROFsW	Ariana	Martinez	Gonzales	t	2026-03-05 12:46:14.115969	approved	\N	\N	4	t
218	chloe.aquino39@school.edu	$2b$12$0nblBdq7DR0bkinEwbtRduLJJ3hhw0WEY5UZRXn7dX285JZwajD0G	Chloe	Diaz	Aquino	t	2026-03-05 12:46:14.115969	approved	\N	\N	4	t
219	ella.villanueva40@school.edu	$2b$12$HM8CL92qKcBZ.hEpNomlkePoF730z3My68SawhLDDwsZ/cnOEjVgS	Ella	Domingo	Villanueva	t	2026-03-05 12:46:14.11597	approved	\N	\N	4	t
220	ella.reyes42@school.edu	$2b$12$q6nAPZ8AiAbSD5XxI0cbIOHlpcWardIBO0L.nmBKpsuAkAoZ74Boe	Ella	Diaz	Reyes	t	2026-03-05 12:46:14.11597	approved	\N	\N	4	t
221	nathan.gonzales43@school.edu	$2b$12$wfuUsRp.vGttT7rgkof.pOMLpg9IHEpp28OZncDep8BuX9iWFsKPi	Nathan	Perez	Gonzales	t	2026-03-05 12:46:14.11597	approved	\N	\N	4	t
1	admin@university.edu	$2b$12$3C8/fvZ5AViE6GCxFKMJC.yYRZiEekh/qve2h37urOqX1zQavXjW6	System	\N	Administrator	t	2026-02-19 03:28:06.91049	approved	\N	\N	\N	f
222	ella.villanueva44@school.edu	$2b$12$30IzBC6Or2xVikXBV8NRT.p32B0JJRI5AOCBl9eBbDR7SneM2mXMu	Ella	Fernandez	Villanueva	t	2026-03-05 12:46:14.11597	approved	\N	\N	4	t
223	kyle.santos45@school.edu	$2b$12$4QKWF9PZu0BZRLKfaZqgU.3Z929s0rbEzDsoEsLvmWxNJ5RA6gbDO	Kyle	Castillo	Santos	t	2026-03-05 12:46:14.115971	approved	\N	\N	4	t
224	john.reyes46@school.edu	$2b$12$RUpbp2JDYdcGAk1dRP/14eNH7te4SvZOUjN3Shc/KReX0Gc7AFXGy	John	Diaz	Reyes	t	2026-03-05 12:46:14.115971	approved	\N	\N	4	t
225	isabella.castro47@school.edu	$2b$12$BYytKsnbH.Mpx/ihIxsSV./.Zzs2id4alAer9GN8EGT7SIf.VLpWC	Isabella	Castillo	Castro	t	2026-03-05 12:46:14.115971	approved	\N	\N	4	t
226	john.ramos49@school.edu	$2b$12$UyKT/piyzzCkLYAf/jH/e.O8W4MchBhajKPQlKz/fF7C.VmK43R8y	John	Santiago	Ramos	t	2026-03-05 12:46:14.115971	approved	\N	\N	4	t
227	ariana.torres50@school.edu	$2b$12$UfLigtA8hHSv3ThLgeGFcurl2LQQ/5lPIuBgyWCnmQXv5Q5i42gW6	Ariana	Martinez	Torres	t	2026-03-05 12:46:14.115972	approved	\N	\N	4	t
228	maria.garcia51@school.edu	$2b$12$Xkl7LXB6zlbt8iEhzI6ogOqvDtY24y82KPzTo2a85QxGF5Ed8XrVa	Maria	Martinez	Garcia	t	2026-03-05 12:46:14.115972	approved	\N	\N	4	t
229	ella.castro53@school.edu	$2b$12$An6Ebrm0yC0E.qFfA7rYC.QzibRCb6q.3GWpMtcAW4/dnoNWoXGFu	Ella	Castillo	Castro	t	2026-03-05 12:46:14.115972	approved	\N	\N	4	t
230	angela.flores54@school.edu	$2b$12$b5yUGQz7vkK9HFb9m3KZM.183jpQzZTKWMURCZUq9noqKEoh3mNoW	Angela	Lopez	Flores	t	2026-03-05 12:46:14.115972	approved	\N	\N	4	t
231	angela.villanueva55@school.edu	$2b$12$lajJIHxDTz4S6cHYAgxK/eELmcNmnVsOzF4D7KIap.0tsE2O5B9lO	Angela	Lopez	Villanueva	t	2026-03-05 12:46:14.115973	approved	\N	\N	4	t
232	jose.navarro56@school.edu	$2b$12$hZIDi6CE5RFkoVZFx7RROuDZCuCyqRFeu579gBOJUCrNc1yRXaS9G	Jose	Rivera	Navarro	t	2026-03-05 12:46:14.115973	approved	\N	\N	4	t
233	ariana.mendoza58@school.edu	$2b$12$CBQZ5J9daSoN2ZugqfNQROKN1Xyo8rOOyni0fH0n6dYElOX3hlCpG	Ariana	Martinez	Mendoza	t	2026-03-05 12:46:14.115973	approved	\N	\N	4	t
234	nathan.mendoza59@school.edu	$2b$12$Vata/ucO2zr/bqwJC0LkYOqgDIzmL/YWz0nkAvP5/Xya5u2Z4td/6	Nathan	Morales	Mendoza	t	2026-03-05 12:46:14.115973	approved	\N	\N	4	t
235	chloe.garcia60@school.edu	$2b$12$m3zpSC8EGXa6XeXsfiX6pOY8.xCQZYDtmKyQU86PKpywtKQ3vRJ4m	Chloe	Domingo	Garcia	t	2026-03-05 12:46:14.115974	approved	\N	\N	4	t
236	miguel.aquino61@school.edu	$2b$12$OJXpMY5mE8bB7Kdu6KTNZuog7g5bEv4/6rPCXd8glW7lIpp18MKci	Miguel	Martinez	Aquino	t	2026-03-05 12:46:14.115974	approved	\N	\N	4	t
237	maria.santos62@school.edu	$2b$12$OnRz.duNdy3YBIXBl5aBpe/6Hx7vR3bGnjFUeaL3oUMfVMq6JUX9C	Maria	Domingo	Santos	t	2026-03-05 12:46:14.115974	approved	\N	\N	4	t
238	bianca.santos63@school.edu	$2b$12$k9HNTMo9Yv6U4xiBj7qqoept9sRzYOqj/QfkcYrp2Ih2B0b47.ejW	Bianca	Castillo	Santos	t	2026-03-05 12:46:14.115975	approved	\N	\N	4	t
239	miguel.torres64@school.edu	$2b$12$XGnTaAfMa5jlRNe235Upeu.g678fWfFeqqt15Mz./OlbW7TlcWVlK	Miguel	Domingo	Torres	t	2026-03-05 12:46:14.115975	approved	\N	\N	4	t
240	liam.reyes65@school.edu	$2b$12$8BaJhFuqJpgZ43ZtdRLSp.Jf619GOV.1DIepmknAqDn71p2ivrQ0K	Liam	Morales	Reyes	t	2026-03-05 12:46:14.115975	approved	\N	\N	4	t
241	john.garcia66@school.edu	$2b$12$pgfjXXsSk3d9Mb.PtH58mexv4URnljw5E5Ea3RuKxyCBGdeHHTAKu	John	Domingo	Garcia	t	2026-03-05 12:46:14.115975	approved	\N	\N	4	t
242	bianca.castro67@school.edu	$2b$12$ZNSUjey/RYVeTWuHphlzjuq3Rnu1UNmd0Y2/ISdLn2LdzubCje7aG	Bianca	Domingo	Castro	t	2026-03-05 12:46:14.115976	approved	\N	\N	4	t
243	angela.villanueva68@school.edu	$2b$12$zDKpnEMIRkKmFteMcHvpv.Wra.WVZog9KpUkW99IrWIXHofvbB6sa	Angela	Fernandez	Villanueva	t	2026-03-05 12:46:14.115976	approved	\N	\N	4	t
244	sofia.castro69@school.edu	$2b$12$F/BNO/YTzDcaEMLGMLewwekubPCSnznjIlFUvqXdTubGQ/MD4PzA.	Sofia	Domingo	Castro	t	2026-03-05 12:46:14.115976	approved	\N	\N	4	t
245	sofia.flores70@school.edu	$2b$12$KPoN5zA5H4na02JpUInuMerj1309uNDXY2McaJcvfFLBiTFHCW1W6	Sofia	Domingo	Flores	t	2026-03-05 12:46:14.115976	approved	\N	\N	4	t
246	noah.castro71@school.edu	$2b$12$Yc2Dx7Y.QYCoXKLpfBaveuBvHgZzL28.bXaNuuw1XEPE44/GIkSkS	Noah	Lopez	Castro	t	2026-03-05 12:46:14.115977	approved	\N	\N	4	t
247	ethan.aquino72@school.edu	$2b$12$OzKL0nWkKSv.4emRMm6T2uEpNHDrjZJ8izoSNA/Jy6M72ZJ0gIO8e	Ethan	Rivera	Aquino	t	2026-03-05 12:46:14.115977	approved	\N	\N	4	t
248	liam.castro73@school.edu	$2b$12$VHGUGNm54i0ioODkN4ty6uzsgHNRCPYRgtmWLGiHmbGcKnD7PvIWm	Liam	Diaz	Castro	t	2026-03-05 12:46:14.115977	approved	\N	\N	4	t
249	chloe.reyes74@school.edu	$2b$12$E1Q2VUo65XQUERx/0oEaLuBzTTq7uZBU3A/5TK2Qjrq9wHDdRQdC.	Chloe	Morales	Reyes	t	2026-03-05 12:46:14.115977	approved	\N	\N	4	t
250	bianca.castro75@school.edu	$2b$12$Ze.xUsZgKL9absvbLxWPcOeDxFgwTCgXjNwsb2K4Jh3aUOy3V0.yq	Bianca	Domingo	Castro	t	2026-03-05 12:46:14.115978	approved	\N	\N	4	t
251	kyle.reyes76@school.edu	$2b$12$JUopJoDfj3TJh8UdFPeGt.Y2d.hvu/slc5xW3cdB0mAS4/Si7UcGy	Kyle	Santiago	Reyes	t	2026-03-05 12:46:14.115978	approved	\N	\N	4	t
252	isabella.navarro77@school.edu	$2b$12$I5badLPSj6DkURNFHGKYd.uUTUYx05NiD.op8qxXejJqOUDMKWvKi	Isabella	Fernandez	Navarro	t	2026-03-05 12:46:14.115978	approved	\N	\N	4	t
253	isabella.gonzales79@school.edu	$2b$12$nBiXwP5YR/ngd8qfWHPeMOf8coXWqEEENsC9nACOkl7k3AqHuoDOe	Isabella	Lopez	Gonzales	t	2026-03-05 12:46:14.115978	approved	\N	\N	4	t
254	john.castro80@school.edu	$2b$12$q8XfgFIXZM/vxHPpPF/Ak.sAjwwA/w4EMzCOZ1U6wqZymXBz/Eca2	John	Domingo	Castro	t	2026-03-05 12:46:14.115979	approved	\N	\N	4	t
255	kyle.mendoza81@school.edu	$2b$12$3U7m0GaV085/T7RzfYsPLeipn.GWGPz44n4y4VuARUbLrD4jS.p8K	Kyle	Martinez	Mendoza	t	2026-03-05 12:46:14.115979	approved	\N	\N	4	t
256	ariana.ramos82@school.edu	$2b$12$a2.l1uJiWwkw6.J.HWeRougEJlq2SBqzHHa/Nr7p5NzTjoYT4dO4C	Ariana	Domingo	Ramos	t	2026-03-05 12:46:14.115979	approved	\N	\N	4	t
257	miguel.santos83@school.edu	$2b$12$7nEk1Du/26Fuw0E9crQ6/.HQfx7StcLjxjPNOE/roJUTlji1x3JGW	Miguel	Perez	Santos	t	2026-03-05 12:46:14.115979	approved	\N	\N	4	t
258	ariana.santos85@school.edu	$2b$12$v5fcZ.sxhjDSlKOdIbL3mO7bprNH3HlWkJ8T/hs1liCJKR31ZxYe.	Ariana	Diaz	Santos	t	2026-03-05 12:46:14.11598	approved	\N	\N	4	t
259	carla.mendoza87@school.edu	$2b$12$LnhrdWWA44KstWgk4DyUieCoI3FNwGTotnTtXI4HVR/qRqeZ1Yhf.	Carla	Santiago	Mendoza	t	2026-03-05 12:46:14.11598	approved	\N	\N	4	t
260	daniel.reyes88@school.edu	$2b$12$v3fCe9gJyAlxJVGUcWgQnOsKPZM9zvIxYxg9E8HN/QVt.qf5CJ0Xe	Daniel	Martinez	Reyes	t	2026-03-05 12:46:14.11598	approved	\N	\N	4	t
261	carla.mendoza89@school.edu	$2b$12$mlff.u0/ULAWEMAiDtHT/OmiFgjRabqzOnwKvl6FADhjOHGjBK/6O	Carla	Castillo	Mendoza	t	2026-03-05 12:46:14.11598	approved	\N	\N	4	t
262	liam.torres90@school.edu	$2b$12$7YuwpFdxh/NSuRtsxteIuue6ArDWS9ZfIOctxvIR0kfign0cwiyyu	Liam	Domingo	Torres	t	2026-03-05 12:46:14.115981	approved	\N	\N	4	t
263	mark.garcia91@school.edu	$2b$12$uKqYfcIG5iK2e5tdb9/cFejjGtGKHQ/TA37LdoI6HjYkfiOeKqPkW	Mark	Lopez	Garcia	t	2026-03-05 12:46:14.115981	approved	\N	\N	4	t
264	joshua.mendoza92@school.edu	$2b$12$NLuTcYmwz74p8MLMgMUVm.pp047G36mYJEWT7P1J9f1uFJsFfkZ2m	Joshua	Diaz	Mendoza	t	2026-03-05 12:46:14.115981	approved	\N	\N	4	t
265	miguel.reyes93@school.edu	$2b$12$eo8Mk/uZ109Y/8WmNZxmWeA7aszg8kJ.vB5BdkKUPFZkUWZ2bIVg.	Miguel	Diaz	Reyes	t	2026-03-05 12:46:14.115981	approved	\N	\N	4	t
266	noah.villanueva95@school.edu	$2b$12$NGCP/ctK2a6iIE.Wtya8auuntBkPe8e8iCFo5U80JSjNXJN7auT1y	Noah	Castillo	Villanueva	t	2026-03-05 12:46:14.115982	approved	\N	\N	4	t
267	maria.garcia96@school.edu	$2b$12$zsdy88Lc4rOJcdhCvrTV/OZK/2qahXwkAPDYMoEECHQ1Octh.U2Sy	Maria	Castillo	Garcia	t	2026-03-05 12:46:14.115982	approved	\N	\N	4	t
268	chloe.castro97@school.edu	$2b$12$8s9BYDDthI5fdtFhqrcQduvQDcqDk.3fADcMxupejVz6lqr1UGBDu	Chloe	Fernandez	Castro	t	2026-03-05 12:46:14.115982	approved	\N	\N	4	t
269	mark.flores98@school.edu	$2b$12$xaRhVO9zCD2EjYqMLlQVgupmiY0pBHQFHisf7YEqfPeuhdJULtRPC	Mark	Diaz	Flores	t	2026-03-05 12:46:14.115982	approved	\N	\N	4	t
270	liam.castro99@school.edu	$2b$12$.fhuFR5s8v9Dzx353VIone9QviHGw//z12JUMC5i2E8wuhq/RNiNe	Liam	Perez	Castro	t	2026-03-05 12:46:14.115982	approved	\N	\N	4	t
271	noah.aquino100@school.edu	$2b$12$eq86lbADDPIvQG8FE/DeNu/4cWHoNg5WzGmxs.xk.KLz2ApbP5rzi	Noah	Santiago	Aquino	t	2026-03-05 12:46:14.115983	approved	\N	\N	4	t
273	meekotan12@gmail.com	$2b$12$fJTIW9ETpQg.lgJJwkUm7Oqw9BCIbZrNe0u.9PYEN6iTtS.cebh9q	Kyle	Rivera	Flores	t	2026-03-05 13:18:38.862894	approved	\N	\N	5	f
272	abcit@test.com	$2b$12$pD9jvCuWaGu/xvHkEmKCG.2xATZYjTK8ozQd4P8f2BTie9VQWdM6.	abcIT	abcIT	abcIT	t	2026-03-05 13:10:33.564415	approved	\N	\N	5	f
274	noah.flores2@school.edu	$2b$12$UPHT7p5QuLJWuB77Sh7wueJy6uVzKHid3t1FYYCOfSQBAaaT9Aklm	Noah	Castillo	Flores	t	2026-03-05 13:18:38.862898	approved	\N	\N	5	t
275	angela.navarro3@school.edu	$2b$12$xInTOvZRxZWlixUgXQxWgu25E2saFJxNnRchVbhUZ1qqPccXG.Dvm	Angela	Martinez	Navarro	t	2026-03-05 13:18:38.862898	approved	\N	\N	5	t
276	bianca.navarro4@school.edu	$2b$12$U7YPnKAtQb3jxKwYOXcN..b/fs75b/cdHG2WZGD9.o6OZj.TYrOZe	Bianca	Diaz	Navarro	t	2026-03-05 13:18:38.862898	approved	\N	\N	5	t
277	jose.aquino5@school.edu	$2b$12$tj8exlxMXG5q/UAW8W0iX.lMqFwguYkkL0UylMBqvz8gV.L3xnKEy	Jose	Lopez	Aquino	t	2026-03-05 13:18:38.862899	approved	\N	\N	5	t
278	ariana.delacruz6@school.edu	$2b$12$9ScC0wVl/YoFsk0Af7yl2.fMcOzyyc/8fwQInbeESMsxvys2g7kAy	Ariana	Fernandez	Dela Cruz	t	2026-03-05 13:18:38.862899	approved	\N	\N	5	t
279	ella.villanueva9@school.edu	$2b$12$rfZ3HFTafKBFIhEWzYgiNuPKfM8hekXdXNjUnwKhGD9SL4R1RBXDe	Ella	Fernandez	Villanueva	t	2026-03-05 13:18:38.862899	approved	\N	\N	5	t
280	chloe.ramos10@school.edu	$2b$12$J27JGNiD1pZsJnHsWFErgOUY37MVCdJpx03kiUmjsDAbuqJ5a9y2y	Chloe	Santiago	Ramos	t	2026-03-05 13:18:38.8629	approved	\N	\N	5	t
281	joshua.flores11@school.edu	$2b$12$hW0xGrhR04AnxCtvF3PT2ehrQJO67NAmzc5ZpEiE8Vdt6W9fVdQdi	Joshua	Rivera	Flores	t	2026-03-05 13:18:38.8629	approved	\N	\N	5	t
282	sofia.flores12@school.edu	$2b$12$Tw6RQjrLWrCCbOKCyk5rVOaam7KS8tJsUdIBhwqcHzXJpBE7xUoEm	Sofia	Lopez	Flores	t	2026-03-05 13:18:38.8629	approved	\N	\N	5	t
283	bianca.villanueva13@school.edu	$2b$12$yJt.xmRUcYPrNvR9h0OdFO7JP5AEL7eOStxCp5odV2XES3.gOIeYS	Bianca	Castillo	Villanueva	t	2026-03-05 13:18:38.8629	approved	\N	\N	5	t
284	ella.villanueva15@school.edu	$2b$12$BtLwV0fT1pdGnZpRp6LHte0H7nb43Qrv7smNKW7Y0fXS2Z9AXrlKO	Ella	Castillo	Villanueva	t	2026-03-05 13:18:38.862901	approved	\N	\N	5	t
285	miguel.aquino16@school.edu	$2b$12$OxgKJB206pKXJPVuWWhcyu4/woxsC14Q8hCy2ovrjJr369TLGVsyi	Miguel	Lopez	Aquino	t	2026-03-05 13:18:38.862901	approved	\N	\N	5	t
286	carla.villanueva17@school.edu	$2b$12$63e9wxx56ruGbIFbs1Rh4efKj9HtASP7FgdryQT6VuU46H.qCWTxe	Carla	Morales	Villanueva	t	2026-03-05 13:18:38.862901	approved	\N	\N	5	t
287	carla.mendoza18@school.edu	$2b$12$ULzgL3wzS7lA/GO9SoYWx.MD1ATXxrE.tdCeeqDNVX9j35DmOU9cO	Carla	Morales	Mendoza	t	2026-03-05 13:18:38.862901	approved	\N	\N	5	t
288	carla.flores19@school.edu	$2b$12$ahToVuu4b9o5HDso6l7uaerbLQq0F4OBDjPtLWGSGC3i08PkTjqEW	Carla	Rivera	Flores	t	2026-03-05 13:18:38.862902	approved	\N	\N	5	t
289	liam.santos20@school.edu	$2b$12$UuKmcF1cZyrvkRQrBiAKqeghpVq1ZBZcgn2PbM9188ZuPA.RqGYf.	Liam	Lopez	Santos	t	2026-03-05 13:18:38.862902	approved	\N	\N	5	t
290	noah.ramos21@school.edu	$2b$12$8jjQQb9IkHS.go6dUiO3O.uftJe5jzOtTzLx792/xZcGz28EMK5eO	Noah	Santiago	Ramos	t	2026-03-05 13:18:38.862902	approved	\N	\N	5	t
291	noah.navarro22@school.edu	$2b$12$i8sDfKoIpkngyjSYrTHQ3.2cFj6cg.sOnPWp2u1/2J7EIa9VVTTL.	Noah	Lopez	Navarro	t	2026-03-05 13:18:38.862902	approved	\N	\N	5	t
292	ariana.santos23@school.edu	$2b$12$EsM7SnQgXPKd.m173L0qVeCEUEG.HUR3Kuh3113tffHerFpXz8Gg2	Ariana	Diaz	Santos	t	2026-03-05 13:18:38.862902	approved	\N	\N	5	t
293	daniel.navarro24@school.edu	$2b$12$hi/ujfB3QAxmFj35GTY5OODo4vNq5G8zErLfVVJwQxN.PnvQQwkZ6	Daniel	Santiago	Navarro	t	2026-03-05 13:18:38.862903	approved	\N	\N	5	t
294	nathan.delacruz25@school.edu	$2b$12$Li1bC2tn2j.oNdtqYgRve.JzmuooGc1m.j0uZa6clsZWJsmXWAg.W	Nathan	Martinez	Dela Cruz	t	2026-03-05 13:18:38.862903	approved	\N	\N	5	t
295	nathan.mendoza26@school.edu	$2b$12$z0vVrsxTqzf4IIbM0csFMOKHJNa1Egg9x6oSDenQ1B1mfCcKUxEXa	Nathan	Domingo	Mendoza	t	2026-03-05 13:18:38.862903	approved	\N	\N	5	t
296	miguel.delacruz29@school.edu	$2b$12$Y5h3dFVgQmuKkMXiGzL2Kuaz33GOGFPl03ZKDP63Dvee1wWPqUlP.	Miguel	Rivera	Dela Cruz	t	2026-03-05 13:18:38.862903	approved	\N	\N	5	t
297	noah.flores30@school.edu	$2b$12$ISCmrnKCqEaQNpy4Y2V8vO319mlNdxYxDHjVb1BCy3rcXqi6fSEVy	Noah	Castillo	Flores	t	2026-03-05 13:18:38.862903	approved	\N	\N	5	t
298	chloe.mendoza31@school.edu	$2b$12$GiSSzUgKpEbH6bs7C5qYLOw09WNI3iB9zOIp1jAhg21MvWNIiMnoa	Chloe	Rivera	Mendoza	t	2026-03-05 13:18:38.862904	approved	\N	\N	5	t
299	isabella.torres32@school.edu	$2b$12$wekK7VzzELE7xjyUYxJyreozo4U6A2YmGu93T1ybtG7yaY2ZXgxsm	Isabella	Martinez	Torres	t	2026-03-05 13:18:38.862904	approved	\N	\N	5	t
300	mark.castro33@school.edu	$2b$12$KFH.XKoz.rUHOE20Iw8APOIb0pPDulLElYa6p6DtnRLwZN6lA7eMy	Mark	Diaz	Castro	t	2026-03-05 13:18:38.862904	approved	\N	\N	5	t
301	bianca.aquino35@school.edu	$2b$12$SwspWD3N8EKZ7/y42b/lIeIXBzqX3vBYfb3z4J53R4FA/foVDa86C	Bianca	Diaz	Aquino	t	2026-03-05 13:18:38.862904	approved	\N	\N	5	t
302	carla.garcia36@school.edu	$2b$12$o3A0z.DFDv7LwjnQBwsbn.pRy8/V3bwJphnISQyo66N6hXqQNmNAa	Carla	Rivera	Garcia	t	2026-03-05 13:18:38.862905	approved	\N	\N	5	t
303	daniel.flores37@school.edu	$2b$12$jMoSvVYpegvr.iGEK6kVueuI0Zv/JYdfRJsvr4wTUrmVEWcOn3AVG	Daniel	Morales	Flores	t	2026-03-05 13:18:38.862905	approved	\N	\N	5	t
304	daniel.garcia38@school.edu	$2b$12$SE0kG8c9dfY8kC393BXS1um7GDaED1HIO361V9AZXBzLynbHlm4d6	Daniel	Diaz	Garcia	t	2026-03-05 13:18:38.862905	approved	\N	\N	5	t
305	angela.gonzales39@school.edu	$2b$12$crRrSJFWLbnDnUyKu9S4/.OJ7SC7pcSJgBBmWmZWSPLFYV5BWhkli	Angela	Domingo	Gonzales	t	2026-03-05 13:18:38.862905	approved	\N	\N	5	t
306	nathan.villanueva40@school.edu	$2b$12$I7fW0L5GFTOfGudotR1uYeSUxlPkH32tkVMODFgC7VxHlC9i8CceO	Nathan	Morales	Villanueva	t	2026-03-05 13:18:38.862906	approved	\N	\N	5	t
307	chloe.flores41@school.edu	$2b$12$AHIW5al5k/BnmbVrZrm8JecNco7NF9Rsd7htThgFbYPS46ON/z/c.	Chloe	Diaz	Flores	t	2026-03-05 13:18:38.862906	approved	\N	\N	5	t
308	liam.santos42@school.edu	$2b$12$yUa.ddVT/AYILox.6Z3MouzFLe5CdLCBRIvzPg43c4BcU43zn4bxi	Liam	Domingo	Santos	t	2026-03-05 13:18:38.862906	approved	\N	\N	5	t
309	isabella.torres43@school.edu	$2b$12$vKw4dtTWJ/5DdDrGy/nFIuZCH/HBtJYbu1qNaBxwzaN1jCUyRFm4y	Isabella	Rivera	Torres	t	2026-03-05 13:18:38.862906	approved	\N	\N	5	t
310	ariana.delacruz44@school.edu	$2b$12$qajfdAiF89vg9004TKaY7.P1Vlg2qgIBtvqs/slwCvVfoQv4A9h0K	Ariana	Perez	Dela Cruz	t	2026-03-05 13:18:38.862906	approved	\N	\N	5	t
311	nathan.garcia45@school.edu	$2b$12$1jq0axaBLA4veI6Cw4blKeUL.nH8ecdimfAku.Gs77u7ahzXtPwXe	Nathan	Perez	Garcia	t	2026-03-05 13:18:38.862907	approved	\N	\N	5	t
312	liam.garcia46@school.edu	$2b$12$7mxwJUGU0rv0Mt.6z87K1eHtVon1gd4epUFObD5xkGQo2DvXy3tAC	Liam	Domingo	Garcia	t	2026-03-05 13:18:38.862907	approved	\N	\N	5	t
313	mark.reyes47@school.edu	$2b$12$COrBTq0/RVPnuH0kEH5aOOlWwLs/ijEE7ENhUa2j1Hp/qK2qwae16	Mark	Rivera	Reyes	t	2026-03-05 13:18:38.862907	approved	\N	\N	5	t
314	john.santos48@school.edu	$2b$12$BSeq.B7.fX3W4DuAo0pL0O3R2BH5Ek2Ze21xL9sGy/gLnZU1Q5xRO	John	Fernandez	Santos	t	2026-03-05 13:18:38.862907	approved	\N	\N	5	t
315	ariana.villanueva49@school.edu	$2b$12$v.oVac0NBqbGhrJVmOsM7Ob2kYF2v5qYbb5woWGDdAPIAi3owCYoy	Ariana	Martinez	Villanueva	t	2026-03-05 13:18:38.862908	approved	\N	\N	5	t
316	noah.torres50@school.edu	$2b$12$Uva9Gly9vwJS7fbhBU5yFuUir7yG8iLWCyqBD1D89a4YyUbtiG7dm	Noah	Morales	Torres	t	2026-03-05 13:18:38.862908	approved	\N	\N	5	t
317	bianca.reyes51@school.edu	$2b$12$T8Hhd0Ad.LVzl3f7R.y19e6cNW2dAa7Ligyd/XcgZ7kYVND8bnpFG	Bianca	Lopez	Reyes	t	2026-03-05 13:18:38.862908	approved	\N	\N	5	t
318	bianca.torres52@school.edu	$2b$12$YTr2dg8O5DCxNP/3dxfXmuIu3.x8VMJzlmNqtjsOmibjdrJWRcnq6	Bianca	Martinez	Torres	t	2026-03-05 13:18:38.862908	approved	\N	\N	5	t
319	isabella.navarro53@school.edu	$2b$12$LPO9W06zbzyymiPK74jv3e3cy9uUwikmpE.xRmtc4TwuaCGfl9azu	Isabella	Perez	Navarro	t	2026-03-05 13:18:38.862909	approved	\N	\N	5	t
320	ella.delacruz54@school.edu	$2b$12$X11p23sYsvXJOCceHqB0J.viwdRnAME.zhN9TY.AQO6f6i61m/JgG	Ella	Fernandez	Dela Cruz	t	2026-03-05 13:18:38.862909	approved	\N	\N	5	t
321	joshua.ramos55@school.edu	$2b$12$DNRIedgt4p7TSqclRles/uM040SSXbHzRINuGeSkWGUVNYaSAukJy	Joshua	Castillo	Ramos	t	2026-03-05 13:18:38.862909	approved	\N	\N	5	t
322	carla.garcia56@school.edu	$2b$12$fMmbZvPBw/Z68jwjRun.s.32906fUhY2Cx5e5OrbXDeiY27NiVU8a	Carla	Martinez	Garcia	t	2026-03-05 13:18:38.862909	approved	\N	\N	5	t
323	isabella.aquino57@school.edu	$2b$12$hpG.Y6vvad6.jQrDQeV4b.vW6XGMq5kityXdm5qIOmzFb8ScqxEJW	Isabella	Morales	Aquino	t	2026-03-05 13:18:38.862909	approved	\N	\N	5	t
324	mark.mendoza58@school.edu	$2b$12$9e6XTJqXLfufQFfItPBn1eL8V7VU1KRb2RTGbXS0uWLtA6YbwM4hi	Mark	Fernandez	Mendoza	t	2026-03-05 13:18:38.86291	approved	\N	\N	5	t
325	carla.ramos59@school.edu	$2b$12$AJGwL7JIDAfdEwR53SusbuQGEJYT3VgT6wHhy9446fgh1as/QCwEK	Carla	Santiago	Ramos	t	2026-03-05 13:18:38.86291	approved	\N	\N	5	t
326	bianca.garcia60@school.edu	$2b$12$0xogo8/HrhTAk5NBPDPWY.EMn7VuHlw2F8qzAHo2yYZ0ML1tlkpkS	Bianca	Santiago	Garcia	t	2026-03-05 13:18:38.86291	approved	\N	\N	5	t
327	nathan.reyes61@school.edu	$2b$12$5OgzemVVwNXSxk6s4zv4P.0dIgC1hAVhitVW1grT3gT/GeKn1ExaS	Nathan	Rivera	Reyes	t	2026-03-05 13:18:38.86291	approved	\N	\N	5	t
328	joshua.flores62@school.edu	$2b$12$yRnEyTJ9RC2gphBXCrIaueV32bfA8UQomxYhTltRq4L9Rg0OX13nW	Joshua	Lopez	Flores	t	2026-03-05 13:18:38.86291	approved	\N	\N	5	t
329	daniel.gonzales64@school.edu	$2b$12$BWwmSDFrxVbDz.F0bT3vSeuEHrdg2ssJXG.IXdWfK3AAZe5rvFwIe	Daniel	Rivera	Gonzales	t	2026-03-05 13:18:38.862911	approved	\N	\N	5	t
330	liam.aquino65@school.edu	$2b$12$Fj.uf6dGaBNfZj1EzP5DgeiByCjWHsIDI9Tdvxd1EVgCsuyzwnLUi	Liam	Perez	Aquino	t	2026-03-05 13:18:38.862911	approved	\N	\N	5	t
331	sofia.delacruz66@school.edu	$2b$12$K/TCZ1DTsPlgzF1Tfu4M4uJWt3pwaISv8h9WI4xbrRI1xnpbK7XJa	Sofia	Castillo	Dela Cruz	t	2026-03-05 13:18:38.862911	approved	\N	\N	5	t
332	jose.delacruz68@school.edu	$2b$12$55ozorIWmVRaMDooo0KqCOHnCc8DAu6aJsuOebjKhfMrjPeB4X7Fq	Jose	Diaz	Dela Cruz	t	2026-03-05 13:18:38.862911	approved	\N	\N	5	t
333	kyle.santos70@school.edu	$2b$12$g4D0blNWfW5X/y5r73JUtuPXtghAoUJw7kVVMyJhPtvyt1YzgEMRS	Kyle	Santiago	Santos	t	2026-03-05 13:18:38.862911	approved	\N	\N	5	t
334	ethan.navarro71@school.edu	$2b$12$7K6EunWmrc9owP3iOUI5DOcaHJEKnbtP48u/6Ce/hUGPi8bos5q7G	Ethan	Morales	Navarro	t	2026-03-05 13:18:38.862912	approved	\N	\N	5	t
335	carla.gonzales72@school.edu	$2b$12$LEpAd3zPLsxPHbEIy4vQluV8bDbPIRwIil4QU.szY574YVzeWj23G	Carla	Santiago	Gonzales	t	2026-03-05 13:18:38.862912	approved	\N	\N	5	t
336	ella.castro73@school.edu	$2b$12$KhwijUjKBDxS8rgUmy0PMuRxTglpip4xDGjCJVhkVHauWctj56DKq	Ella	Diaz	Castro	t	2026-03-05 13:18:38.862912	approved	\N	\N	5	t
337	isabella.garcia74@school.edu	$2b$12$RaZ6xL4GRDLVsRuKT/3/a.0KuWQL0XKhMLM5R8eTpKEt9JcPlGg7y	Isabella	Diaz	Garcia	t	2026-03-05 13:18:38.862912	approved	\N	\N	5	t
338	mark.flores75@school.edu	$2b$12$uNVpQpg.DwStrXIGQ93KxuLd1voKGHLOk3ZZpuqf8oYqfFHjpH.xy	Mark	Domingo	Flores	t	2026-03-05 13:18:38.862912	approved	\N	\N	5	t
339	bianca.delacruz76@school.edu	$2b$12$flU/Lqp.TXDxStVE0SMGruII/XiF2rCVtVlR8vPBCD5qVRCbQQ0B2	Bianca	Santiago	Dela Cruz	t	2026-03-05 13:18:38.862913	approved	\N	\N	5	t
340	ethan.navarro77@school.edu	$2b$12$sq5aVzcvKHfYWPmDWcFfv.69KaixUE3T8VdbkJLorgNeZegTdcTo2	Ethan	Castillo	Navarro	t	2026-03-05 13:18:38.862913	approved	\N	\N	5	t
341	carla.castro78@school.edu	$2b$12$r3Z5y1oW0iYbbJHNQKgYhumTSzqTYx4oHU649PG1s0lQzDuE2Dyqa	Carla	Santiago	Castro	t	2026-03-05 13:18:38.862913	approved	\N	\N	5	t
342	angela.navarro79@school.edu	$2b$12$xZ11rDu/P9E3s8X5hBU3eeJCatlTPv/sDCOwj57BgLw.5d9zsoofK	Angela	Santiago	Navarro	t	2026-03-05 13:18:38.862913	approved	\N	\N	5	t
343	maria.delacruz80@school.edu	$2b$12$A7t1johSVYubPGJ/bwJHVuvsZqSdBFbbKkqjX3reE.OUdG82QkIey	Maria	Rivera	Dela Cruz	t	2026-03-05 13:18:38.862913	approved	\N	\N	5	t
344	bianca.garcia81@school.edu	$2b$12$JEbDvvKj0MT7.OPc4qa9febBTzTGfSZCB6o54Tb1QaV/ybDcEeszy	Bianca	Rivera	Garcia	t	2026-03-05 13:18:38.862913	approved	\N	\N	5	t
345	ariana.mendoza85@school.edu	$2b$12$EFytEV7KmjNNA5misztXku7SrCsUPx5T0mYL3TKXGh4uTZ8CKRGMa	Ariana	Fernandez	Mendoza	t	2026-03-05 13:18:38.862914	approved	\N	\N	5	t
346	bianca.delacruz87@school.edu	$2b$12$DUi8gMQxvkAOkPFhniFfWekX8cK.UU0giqpZdXHNPBNJdjD4o5Iya	Bianca	Castillo	Dela Cruz	t	2026-03-05 13:18:38.862914	approved	\N	\N	5	t
347	ethan.reyes88@school.edu	$2b$12$ZFq0t6MN1laQgKfZHZlVLONIYuKzvN/Wd3pkJ5G2uy7qbxMjtbbSm	Ethan	Castillo	Reyes	t	2026-03-05 13:18:38.862914	approved	\N	\N	5	t
348	maria.flores89@school.edu	$2b$12$e9V8b9J0geSKR7q3Hh/qhOcnpxlRhVDamm9chTMUlpcWvf.nBbw72	Maria	Fernandez	Flores	t	2026-03-05 13:18:38.862914	approved	\N	\N	5	t
349	ariana.reyes90@school.edu	$2b$12$2FC6X9m3G81AlXQFjhZCAeXjgNmD/2fw33Z3moek6.MQB/JM1faMe	Ariana	Castillo	Reyes	t	2026-03-05 13:18:38.862914	approved	\N	\N	5	t
350	angela.flores91@school.edu	$2b$12$NaEyBosUiICkOCbqdX8lvOZBXkT0aDVCpQ6VQMjwCLZpyRw/KWcJy	Angela	Martinez	Flores	t	2026-03-05 13:18:38.862915	approved	\N	\N	5	t
351	carla.santos92@school.edu	$2b$12$WhC9z/MOFdaq9S.rkPINjubwobA6e8lnAM.e0B9GFdLGmKAyG0FTm	Carla	Domingo	Santos	t	2026-03-05 13:18:38.862915	approved	\N	\N	5	t
352	john.navarro93@school.edu	$2b$12$UpMiXhTOYgyWabM45gSETuB6PxuxYu6ePok7vPheduVpU.mGvVlX2	John	Diaz	Navarro	t	2026-03-05 13:18:38.862915	approved	\N	\N	5	t
353	kyle.reyes94@school.edu	$2b$12$oxPdfxc07x8fKhJSGzcmy.NZtb4nw0464LRaT7Kh7S15jnbNFy/ka	Kyle	Rivera	Reyes	t	2026-03-05 13:18:38.862915	approved	\N	\N	5	t
354	nathan.gonzales95@school.edu	$2b$12$KrWC1XR21TXQYfCIuae.SOoCtAi3/ilbPcz65pQXPHv5tXZtxx1CG	Nathan	Morales	Gonzales	t	2026-03-05 13:18:38.862915	approved	\N	\N	5	t
355	joshua.flores96@school.edu	$2b$12$dskvBk91m/ZpTKHHpzq4B.RFZGF4UrKizszGeYdiiWU9X8wwoYTdW	Joshua	Santiago	Flores	t	2026-03-05 13:18:38.862916	approved	\N	\N	5	t
356	miguel.santos97@school.edu	$2b$12$In3/4m7cWMqx1K.vPGq2peeIpPkEChlLiUMM29z9/00kP82/q1lma	Miguel	Perez	Santos	t	2026-03-05 13:18:38.862916	approved	\N	\N	5	t
357	sofia.reyes98@school.edu	$2b$12$S0f/JwvKUsISq4T9bAkh2O2HkIUh2nQifd26fReYJ0spPnjYJZzEa	Sofia	Martinez	Reyes	t	2026-03-05 13:18:38.862916	approved	\N	\N	5	t
358	bianca.delacruz99@school.edu	$2b$12$X3KI015/ZKBqDDn4IGin/uhsCb33ohbzAZJvQzUJ3BQGk4EwW4LPC	Bianca	Domingo	Dela Cruz	t	2026-03-05 13:18:38.862916	approved	\N	\N	5	t
359	angela.santos100@school.edu	$2b$12$jgZDot48GNavQSsD1GPm.eL.TeFHSCFJQD1XC4S8PJvvTPyDzry42	Angela	Martinez	Santos	t	2026-03-05 13:18:38.862916	approved	\N	\N	5	t
362	e2e.schoolit@test.com	$2b$12$rm3EdNF5MYLx4qCNdgE1zerRzPS6qqx4ypKUJEa.LwVC1NGWj2w1i	E2E	\N	SchoolIT	t	2026-03-06 12:12:20.078847	approved	\N	\N	4	f
363	deleted_363_1772799454@deleted.example.com	$2b$12$YoPk27mtLXy9cB13YbATM.W6fkPbnc8EeWx2wQNyb2Yc8w85GMwWq	Delete	\N	Target	f	2026-03-06 12:16:34.160035	approved	\N	\N	4	f
\.


--
-- Name: ai_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ai_logs_id_seq', 1, false);


--
-- Name: anomaly_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.anomaly_logs_id_seq', 1, false);


--
-- Name: attendance_predictions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.attendance_predictions_id_seq', 1, false);


--
-- Name: attendances_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.attendances_id_seq', 3, true);


--
-- Name: bulk_import_errors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.bulk_import_errors_id_seq', 156, true);


--
-- Name: data_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.data_requests_id_seq', 4, true);


--
-- Name: data_retention_run_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.data_retention_run_logs_id_seq', 4, true);


--
-- Name: departments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.departments_id_seq', 8, true);


--
-- Name: email_delivery_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.email_delivery_logs_id_seq', 358, true);


--
-- Name: event_consumption_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.event_consumption_logs_id_seq', 1, false);


--
-- Name: event_flags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.event_flags_id_seq', 1, false);


--
-- Name: event_predictions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.event_predictions_id_seq', 1, false);


--
-- Name: events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.events_id_seq', 5, true);


--
-- Name: login_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.login_history_id_seq', 26, true);


--
-- Name: model_metadata_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_metadata_id_seq', 1, false);


--
-- Name: notification_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.notification_logs_id_seq', 18, true);


--
-- Name: notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.notifications_id_seq', 1, false);


--
-- Name: password_reset_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.password_reset_requests_id_seq', 1, true);


--
-- Name: programs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.programs_id_seq', 21, true);


--
-- Name: recommendation_cache_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.recommendation_cache_id_seq', 1, false);


--
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.roles_id_seq', 5, true);


--
-- Name: school_audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.school_audit_logs_id_seq', 33, true);


--
-- Name: school_subscription_reminders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.school_subscription_reminders_id_seq', 1, true);


--
-- Name: schools_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.schools_id_seq', 5, true);


--
-- Name: security_alerts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.security_alerts_id_seq', 1, false);


--
-- Name: ssg_profiles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ssg_profiles_id_seq', 1, false);


--
-- Name: student_profiles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.student_profiles_id_seq', 353, true);


--
-- Name: student_risk_scores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.student_risk_scores_id_seq', 1, false);


--
-- Name: user_privacy_consents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_privacy_consents_id_seq', 2, true);


--
-- Name: user_roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_roles_id_seq', 363, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 363, true);


--
-- Name: ai_logs ai_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_logs
    ADD CONSTRAINT ai_logs_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: anomaly_logs anomaly_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_logs
    ADD CONSTRAINT anomaly_logs_pkey PRIMARY KEY (id);


--
-- Name: attendance_predictions attendance_predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_predictions
    ADD CONSTRAINT attendance_predictions_pkey PRIMARY KEY (id);


--
-- Name: attendances attendances_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendances
    ADD CONSTRAINT attendances_pkey PRIMARY KEY (id);


--
-- Name: bulk_import_errors bulk_import_errors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bulk_import_errors
    ADD CONSTRAINT bulk_import_errors_pkey PRIMARY KEY (id);


--
-- Name: bulk_import_jobs bulk_import_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bulk_import_jobs
    ADD CONSTRAINT bulk_import_jobs_pkey PRIMARY KEY (id);


--
-- Name: data_governance_settings data_governance_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_governance_settings
    ADD CONSTRAINT data_governance_settings_pkey PRIMARY KEY (school_id);


--
-- Name: data_requests data_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_requests
    ADD CONSTRAINT data_requests_pkey PRIMARY KEY (id);


--
-- Name: data_retention_run_logs data_retention_run_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_retention_run_logs
    ADD CONSTRAINT data_retention_run_logs_pkey PRIMARY KEY (id);


--
-- Name: departments departments_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_name_key UNIQUE (name);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (id);


--
-- Name: email_delivery_logs email_delivery_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_delivery_logs
    ADD CONSTRAINT email_delivery_logs_pkey PRIMARY KEY (id);


--
-- Name: event_consumption_logs event_consumption_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_consumption_logs
    ADD CONSTRAINT event_consumption_logs_pkey PRIMARY KEY (id);


--
-- Name: event_department_association event_department_association_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_department_association
    ADD CONSTRAINT event_department_association_pkey PRIMARY KEY (event_id, department_id);


--
-- Name: event_flags event_flags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_flags
    ADD CONSTRAINT event_flags_pkey PRIMARY KEY (id);


--
-- Name: event_predictions event_predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_predictions
    ADD CONSTRAINT event_predictions_pkey PRIMARY KEY (id);


--
-- Name: event_program_association event_program_association_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_program_association
    ADD CONSTRAINT event_program_association_pkey PRIMARY KEY (event_id, program_id);


--
-- Name: event_ssg_association event_ssg_association_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_ssg_association
    ADD CONSTRAINT event_ssg_association_pkey PRIMARY KEY (event_id, ssg_profile_id);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);


--
-- Name: login_history login_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT login_history_pkey PRIMARY KEY (id);


--
-- Name: mfa_challenges mfa_challenges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mfa_challenges
    ADD CONSTRAINT mfa_challenges_pkey PRIMARY KEY (id);


--
-- Name: model_metadata model_metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_metadata
    ADD CONSTRAINT model_metadata_pkey PRIMARY KEY (id);


--
-- Name: notification_logs notification_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_logs
    ADD CONSTRAINT notification_logs_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: outbox_events outbox_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.outbox_events
    ADD CONSTRAINT outbox_events_pkey PRIMARY KEY (id);


--
-- Name: password_reset_requests password_reset_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.password_reset_requests
    ADD CONSTRAINT password_reset_requests_pkey PRIMARY KEY (id);


--
-- Name: program_department_association program_department_association_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.program_department_association
    ADD CONSTRAINT program_department_association_pkey PRIMARY KEY (program_id, department_id);


--
-- Name: programs programs_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.programs
    ADD CONSTRAINT programs_name_key UNIQUE (name);


--
-- Name: programs programs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.programs
    ADD CONSTRAINT programs_pkey PRIMARY KEY (id);


--
-- Name: recommendation_cache recommendation_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recommendation_cache
    ADD CONSTRAINT recommendation_cache_pkey PRIMARY KEY (id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: school_audit_logs school_audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_audit_logs
    ADD CONSTRAINT school_audit_logs_pkey PRIMARY KEY (id);


--
-- Name: school_settings school_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_settings
    ADD CONSTRAINT school_settings_pkey PRIMARY KEY (school_id);


--
-- Name: school_subscription_reminders school_subscription_reminders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_subscription_reminders
    ADD CONSTRAINT school_subscription_reminders_pkey PRIMARY KEY (id);


--
-- Name: school_subscription_settings school_subscription_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_subscription_settings
    ADD CONSTRAINT school_subscription_settings_pkey PRIMARY KEY (school_id);


--
-- Name: schools schools_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schools
    ADD CONSTRAINT schools_pkey PRIMARY KEY (id);


--
-- Name: security_alerts security_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.security_alerts
    ADD CONSTRAINT security_alerts_pkey PRIMARY KEY (id);


--
-- Name: ssg_profiles ssg_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_profiles
    ADD CONSTRAINT ssg_profiles_pkey PRIMARY KEY (id);


--
-- Name: student_profiles student_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_pkey PRIMARY KEY (id);


--
-- Name: student_profiles student_profiles_rfid_tag_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_rfid_tag_key UNIQUE (rfid_tag);


--
-- Name: student_risk_scores student_risk_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_risk_scores
    ADD CONSTRAINT student_risk_scores_pkey PRIMARY KEY (id);


--
-- Name: attendance_predictions uq_attendance_pred_student_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_predictions
    ADD CONSTRAINT uq_attendance_pred_student_event UNIQUE (student_id, event_id);


--
-- Name: student_profiles uq_student_profiles_school_student_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT uq_student_profiles_school_student_id UNIQUE (school_id, student_id);


--
-- Name: user_notification_preferences user_notification_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_notification_preferences
    ADD CONSTRAINT user_notification_preferences_pkey PRIMARY KEY (user_id);


--
-- Name: user_privacy_consents user_privacy_consents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_privacy_consents
    ADD CONSTRAINT user_privacy_consents_pkey PRIMARY KEY (id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);


--
-- Name: user_security_settings user_security_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_security_settings
    ADD CONSTRAINT user_security_settings_pkey PRIMARY KEY (user_id);


--
-- Name: user_sessions user_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_ai_logs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_logs_id ON public.ai_logs USING btree (id);


--
-- Name: ix_ai_logs_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_logs_role ON public.ai_logs USING btree (role);


--
-- Name: ix_ai_logs_success; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_logs_success ON public.ai_logs USING btree (success);


--
-- Name: ix_ai_logs_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_logs_timestamp ON public.ai_logs USING btree ("timestamp");


--
-- Name: ix_ai_logs_tool_called; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_logs_tool_called ON public.ai_logs USING btree (tool_called);


--
-- Name: ix_ai_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_logs_user_id ON public.ai_logs USING btree (user_id);


--
-- Name: ix_anomaly_logs_anomaly_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_anomaly_logs_anomaly_type ON public.anomaly_logs USING btree (anomaly_type);


--
-- Name: ix_anomaly_logs_detected_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_anomaly_logs_detected_at ON public.anomaly_logs USING btree (detected_at);


--
-- Name: ix_anomaly_logs_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_anomaly_logs_event_id ON public.anomaly_logs USING btree (event_id);


--
-- Name: ix_anomaly_logs_is_resolved; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_anomaly_logs_is_resolved ON public.anomaly_logs USING btree (is_resolved);


--
-- Name: ix_anomaly_logs_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_anomaly_logs_severity ON public.anomaly_logs USING btree (severity);


--
-- Name: ix_anomaly_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_anomaly_logs_user_id ON public.anomaly_logs USING btree (user_id);


--
-- Name: ix_attendance_predictions_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_attendance_predictions_event_id ON public.attendance_predictions USING btree (event_id);


--
-- Name: ix_attendance_predictions_generated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_attendance_predictions_generated_at ON public.attendance_predictions USING btree (generated_at);


--
-- Name: ix_attendance_predictions_risk_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_attendance_predictions_risk_level ON public.attendance_predictions USING btree (risk_level);


--
-- Name: ix_attendance_predictions_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_attendance_predictions_student_id ON public.attendance_predictions USING btree (student_id);


--
-- Name: ix_attendances_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_attendances_event_id ON public.attendances USING btree (event_id);


--
-- Name: ix_attendances_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_attendances_id ON public.attendances USING btree (id);


--
-- Name: ix_attendances_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_attendances_student_id ON public.attendances USING btree (student_id);


--
-- Name: ix_bulk_import_errors_job_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bulk_import_errors_job_id ON public.bulk_import_errors USING btree (job_id);


--
-- Name: ix_bulk_import_errors_job_row; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bulk_import_errors_job_row ON public.bulk_import_errors USING btree (job_id, row_number);


--
-- Name: ix_bulk_import_jobs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bulk_import_jobs_created_at ON public.bulk_import_jobs USING btree (created_at);


--
-- Name: ix_bulk_import_jobs_created_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bulk_import_jobs_created_by_user_id ON public.bulk_import_jobs USING btree (created_by_user_id);


--
-- Name: ix_bulk_import_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bulk_import_jobs_status ON public.bulk_import_jobs USING btree (status);


--
-- Name: ix_bulk_import_jobs_target_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bulk_import_jobs_target_school_id ON public.bulk_import_jobs USING btree (target_school_id);


--
-- Name: ix_data_requests_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_requests_created_at ON public.data_requests USING btree (created_at);


--
-- Name: ix_data_requests_request_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_requests_request_type ON public.data_requests USING btree (request_type);


--
-- Name: ix_data_requests_requested_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_requests_requested_by_user_id ON public.data_requests USING btree (requested_by_user_id);


--
-- Name: ix_data_requests_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_requests_school_id ON public.data_requests USING btree (school_id);


--
-- Name: ix_data_requests_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_requests_status ON public.data_requests USING btree (status);


--
-- Name: ix_data_requests_target_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_requests_target_user_id ON public.data_requests USING btree (target_user_id);


--
-- Name: ix_data_retention_run_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_retention_run_logs_created_at ON public.data_retention_run_logs USING btree (created_at);


--
-- Name: ix_data_retention_run_logs_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_retention_run_logs_school_id ON public.data_retention_run_logs USING btree (school_id);


--
-- Name: ix_departments_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_departments_id ON public.departments USING btree (id);


--
-- Name: ix_email_delivery_logs_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_delivery_logs_email ON public.email_delivery_logs USING btree (email);


--
-- Name: ix_email_delivery_logs_job_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_delivery_logs_job_id ON public.email_delivery_logs USING btree (job_id);


--
-- Name: ix_email_delivery_logs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_delivery_logs_status ON public.email_delivery_logs USING btree (status);


--
-- Name: ix_email_delivery_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_delivery_logs_user_id ON public.email_delivery_logs USING btree (user_id);


--
-- Name: ix_event_consumption_logs_consumer_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_consumption_logs_consumer_name ON public.event_consumption_logs USING btree (consumer_name);


--
-- Name: ix_event_consumption_logs_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_event_consumption_logs_event_id ON public.event_consumption_logs USING btree (event_id);


--
-- Name: ix_event_consumption_logs_event_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_consumption_logs_event_type ON public.event_consumption_logs USING btree (event_type);


--
-- Name: ix_event_consumption_logs_processed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_consumption_logs_processed_at ON public.event_consumption_logs USING btree (processed_at);


--
-- Name: ix_event_consumption_logs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_consumption_logs_status ON public.event_consumption_logs USING btree (status);


--
-- Name: ix_event_flags_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_flags_active ON public.event_flags USING btree (active);


--
-- Name: ix_event_flags_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_event_flags_event_id ON public.event_flags USING btree (event_id);


--
-- Name: ix_event_flags_flagged_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_flags_flagged_at ON public.event_flags USING btree (flagged_at);


--
-- Name: ix_event_predictions_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_event_predictions_event_id ON public.event_predictions USING btree (event_id);


--
-- Name: ix_event_predictions_generated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_predictions_generated_at ON public.event_predictions USING btree (generated_at);


--
-- Name: ix_event_predictions_risk_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_predictions_risk_level ON public.event_predictions USING btree (risk_level);


--
-- Name: ix_events_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_events_id ON public.events USING btree (id);


--
-- Name: ix_events_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_events_school_id ON public.events USING btree (school_id);


--
-- Name: ix_login_history_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_history_created_at ON public.login_history USING btree (created_at);


--
-- Name: ix_login_history_email_attempted; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_history_email_attempted ON public.login_history USING btree (email_attempted);


--
-- Name: ix_login_history_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_history_school_id ON public.login_history USING btree (school_id);


--
-- Name: ix_login_history_success; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_history_success ON public.login_history USING btree (success);


--
-- Name: ix_login_history_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_history_user_id ON public.login_history USING btree (user_id);


--
-- Name: ix_mfa_challenges_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mfa_challenges_created_at ON public.mfa_challenges USING btree (created_at);


--
-- Name: ix_mfa_challenges_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mfa_challenges_expires_at ON public.mfa_challenges USING btree (expires_at);


--
-- Name: ix_mfa_challenges_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mfa_challenges_user_id ON public.mfa_challenges USING btree (user_id);


--
-- Name: ix_model_metadata_model_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_model_metadata_model_name ON public.model_metadata USING btree (model_name);


--
-- Name: ix_model_metadata_trained_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_model_metadata_trained_at ON public.model_metadata USING btree (trained_at);


--
-- Name: ix_notification_logs_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notification_logs_category ON public.notification_logs USING btree (category);


--
-- Name: ix_notification_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notification_logs_created_at ON public.notification_logs USING btree (created_at);


--
-- Name: ix_notification_logs_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notification_logs_school_id ON public.notification_logs USING btree (school_id);


--
-- Name: ix_notification_logs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notification_logs_status ON public.notification_logs USING btree (status);


--
-- Name: ix_notification_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notification_logs_user_id ON public.notification_logs USING btree (user_id);


--
-- Name: ix_notifications_is_read; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_is_read ON public.notifications USING btree (is_read);


--
-- Name: ix_notifications_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_user_id ON public.notifications USING btree (user_id);


--
-- Name: ix_outbox_events_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_outbox_events_created_at ON public.outbox_events USING btree (created_at);


--
-- Name: ix_outbox_events_event_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_outbox_events_event_type ON public.outbox_events USING btree (event_type);


--
-- Name: ix_outbox_events_published_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_outbox_events_published_at ON public.outbox_events USING btree (published_at);


--
-- Name: ix_outbox_events_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_outbox_events_status ON public.outbox_events USING btree (status);


--
-- Name: ix_password_reset_requests_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_password_reset_requests_id ON public.password_reset_requests USING btree (id);


--
-- Name: ix_password_reset_requests_requested_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_password_reset_requests_requested_at ON public.password_reset_requests USING btree (requested_at);


--
-- Name: ix_password_reset_requests_requested_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_password_reset_requests_requested_email ON public.password_reset_requests USING btree (requested_email);


--
-- Name: ix_password_reset_requests_reviewed_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_password_reset_requests_reviewed_by_user_id ON public.password_reset_requests USING btree (reviewed_by_user_id);


--
-- Name: ix_password_reset_requests_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_password_reset_requests_school_id ON public.password_reset_requests USING btree (school_id);


--
-- Name: ix_password_reset_requests_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_password_reset_requests_status ON public.password_reset_requests USING btree (status);


--
-- Name: ix_password_reset_requests_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_password_reset_requests_user_id ON public.password_reset_requests USING btree (user_id);


--
-- Name: ix_programs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_programs_id ON public.programs USING btree (id);


--
-- Name: ix_recommendation_cache_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_recommendation_cache_expires_at ON public.recommendation_cache USING btree (expires_at);


--
-- Name: ix_recommendation_cache_generated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_recommendation_cache_generated_at ON public.recommendation_cache USING btree (generated_at);


--
-- Name: ix_recommendation_cache_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_recommendation_cache_student_id ON public.recommendation_cache USING btree (student_id);


--
-- Name: ix_roles_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);


--
-- Name: ix_school_audit_logs_actor_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_school_audit_logs_actor_user_id ON public.school_audit_logs USING btree (actor_user_id);


--
-- Name: ix_school_audit_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_school_audit_logs_created_at ON public.school_audit_logs USING btree (created_at);


--
-- Name: ix_school_audit_logs_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_school_audit_logs_school_id ON public.school_audit_logs USING btree (school_id);


--
-- Name: ix_school_subscription_reminders_due_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_school_subscription_reminders_due_at ON public.school_subscription_reminders USING btree (due_at);


--
-- Name: ix_school_subscription_reminders_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_school_subscription_reminders_school_id ON public.school_subscription_reminders USING btree (school_id);


--
-- Name: ix_school_subscription_reminders_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_school_subscription_reminders_status ON public.school_subscription_reminders USING btree (status);


--
-- Name: ix_schools_school_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_schools_school_code ON public.schools USING btree (school_code);


--
-- Name: ix_schools_school_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_schools_school_name ON public.schools USING btree (school_name);


--
-- Name: ix_security_alerts_acknowledged; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_security_alerts_acknowledged ON public.security_alerts USING btree (acknowledged);


--
-- Name: ix_security_alerts_anomaly_log_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_security_alerts_anomaly_log_id ON public.security_alerts USING btree (anomaly_log_id);


--
-- Name: ix_security_alerts_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_security_alerts_created_at ON public.security_alerts USING btree (created_at);


--
-- Name: ix_security_alerts_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_security_alerts_event_id ON public.security_alerts USING btree (event_id);


--
-- Name: ix_security_alerts_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_security_alerts_severity ON public.security_alerts USING btree (severity);


--
-- Name: ix_ssg_profiles_position; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ssg_profiles_position ON public.ssg_profiles USING btree ("position");


--
-- Name: ix_ssg_profiles_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_ssg_profiles_user_id ON public.ssg_profiles USING btree (user_id);


--
-- Name: ix_student_profiles_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_profiles_department_id ON public.student_profiles USING btree (department_id);


--
-- Name: ix_student_profiles_is_face_registered; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_profiles_is_face_registered ON public.student_profiles USING btree (is_face_registered);


--
-- Name: ix_student_profiles_program_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_profiles_program_id ON public.student_profiles USING btree (program_id);


--
-- Name: ix_student_profiles_registration_complete; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_profiles_registration_complete ON public.student_profiles USING btree (registration_complete);


--
-- Name: ix_student_profiles_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_profiles_school_id ON public.student_profiles USING btree (school_id);


--
-- Name: ix_student_profiles_school_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_profiles_school_student_id ON public.student_profiles USING btree (school_id, student_id);


--
-- Name: ix_student_profiles_section; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_profiles_section ON public.student_profiles USING btree (section);


--
-- Name: ix_student_profiles_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_profiles_student_id ON public.student_profiles USING btree (student_id);


--
-- Name: ix_student_profiles_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_student_profiles_user_id ON public.student_profiles USING btree (user_id);


--
-- Name: ix_student_risk_scores_generated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_risk_scores_generated_at ON public.student_risk_scores USING btree (generated_at);


--
-- Name: ix_student_risk_scores_risk_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_student_risk_scores_risk_level ON public.student_risk_scores USING btree (risk_level);


--
-- Name: ix_student_risk_scores_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_student_risk_scores_student_id ON public.student_risk_scores USING btree (student_id);


--
-- Name: ix_user_privacy_consents_consent_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_privacy_consents_consent_type ON public.user_privacy_consents USING btree (consent_type);


--
-- Name: ix_user_privacy_consents_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_privacy_consents_created_at ON public.user_privacy_consents USING btree (created_at);


--
-- Name: ix_user_privacy_consents_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_privacy_consents_school_id ON public.user_privacy_consents USING btree (school_id);


--
-- Name: ix_user_privacy_consents_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_privacy_consents_user_id ON public.user_privacy_consents USING btree (user_id);


--
-- Name: ix_user_roles_role_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_roles_role_id ON public.user_roles USING btree (role_id);


--
-- Name: ix_user_roles_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_roles_user_id ON public.user_roles USING btree (user_id);


--
-- Name: ix_user_sessions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_sessions_created_at ON public.user_sessions USING btree (created_at);


--
-- Name: ix_user_sessions_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_sessions_expires_at ON public.user_sessions USING btree (expires_at);


--
-- Name: ix_user_sessions_token_jti; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_user_sessions_token_jti ON public.user_sessions USING btree (token_jti);


--
-- Name: ix_user_sessions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_sessions_user_id ON public.user_sessions USING btree (user_id);


--
-- Name: ix_users_approval_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_approval_status ON public.users USING btree (approval_status);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_is_active ON public.users USING btree (is_active);


--
-- Name: ix_users_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_school_id ON public.users USING btree (school_id);


--
-- Name: ai_logs ai_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_logs
    ADD CONSTRAINT ai_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: anomaly_logs anomaly_logs_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_logs
    ADD CONSTRAINT anomaly_logs_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE SET NULL;


--
-- Name: anomaly_logs anomaly_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_logs
    ADD CONSTRAINT anomaly_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: attendance_predictions attendance_predictions_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_predictions
    ADD CONSTRAINT attendance_predictions_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: attendance_predictions attendance_predictions_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_predictions
    ADD CONSTRAINT attendance_predictions_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


--
-- Name: attendances attendances_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendances
    ADD CONSTRAINT attendances_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: attendances attendances_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendances
    ADD CONSTRAINT attendances_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


--
-- Name: attendances attendances_verified_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendances
    ADD CONSTRAINT attendances_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: bulk_import_errors bulk_import_errors_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bulk_import_errors
    ADD CONSTRAINT bulk_import_errors_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.bulk_import_jobs(id) ON DELETE CASCADE;


--
-- Name: bulk_import_jobs bulk_import_jobs_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bulk_import_jobs
    ADD CONSTRAINT bulk_import_jobs_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: data_governance_settings data_governance_settings_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_governance_settings
    ADD CONSTRAINT data_governance_settings_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: data_governance_settings data_governance_settings_updated_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_governance_settings
    ADD CONSTRAINT data_governance_settings_updated_by_user_id_fkey FOREIGN KEY (updated_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: data_requests data_requests_handled_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_requests
    ADD CONSTRAINT data_requests_handled_by_user_id_fkey FOREIGN KEY (handled_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: data_requests data_requests_requested_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_requests
    ADD CONSTRAINT data_requests_requested_by_user_id_fkey FOREIGN KEY (requested_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: data_requests data_requests_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_requests
    ADD CONSTRAINT data_requests_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: data_requests data_requests_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_requests
    ADD CONSTRAINT data_requests_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: data_retention_run_logs data_retention_run_logs_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_retention_run_logs
    ADD CONSTRAINT data_retention_run_logs_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: email_delivery_logs email_delivery_logs_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_delivery_logs
    ADD CONSTRAINT email_delivery_logs_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.bulk_import_jobs(id) ON DELETE SET NULL;


--
-- Name: email_delivery_logs email_delivery_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_delivery_logs
    ADD CONSTRAINT email_delivery_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: event_department_association event_department_association_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_department_association
    ADD CONSTRAINT event_department_association_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE CASCADE;


--
-- Name: event_department_association event_department_association_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_department_association
    ADD CONSTRAINT event_department_association_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: event_flags event_flags_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_flags
    ADD CONSTRAINT event_flags_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: event_predictions event_predictions_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_predictions
    ADD CONSTRAINT event_predictions_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: event_program_association event_program_association_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_program_association
    ADD CONSTRAINT event_program_association_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: event_program_association event_program_association_program_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_program_association
    ADD CONSTRAINT event_program_association_program_id_fkey FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE;


--
-- Name: event_ssg_association event_ssg_association_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_ssg_association
    ADD CONSTRAINT event_ssg_association_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id);


--
-- Name: event_ssg_association event_ssg_association_ssg_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_ssg_association
    ADD CONSTRAINT event_ssg_association_ssg_profile_id_fkey FOREIGN KEY (ssg_profile_id) REFERENCES public.ssg_profiles(id);


--
-- Name: bulk_import_jobs fk_bulk_import_jobs_target_school_id_schools; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bulk_import_jobs
    ADD CONSTRAINT fk_bulk_import_jobs_target_school_id_schools FOREIGN KEY (target_school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: events fk_events_school_id_schools; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT fk_events_school_id_schools FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: student_profiles fk_student_profiles_school_id_schools; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT fk_student_profiles_school_id_schools FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: users fk_users_school_id_schools; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_school_id_schools FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: login_history login_history_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT login_history_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE SET NULL;


--
-- Name: login_history login_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT login_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: mfa_challenges mfa_challenges_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mfa_challenges
    ADD CONSTRAINT mfa_challenges_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: notification_logs notification_logs_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_logs
    ADD CONSTRAINT notification_logs_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: notification_logs notification_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_logs
    ADD CONSTRAINT notification_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: password_reset_requests password_reset_requests_reviewed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.password_reset_requests
    ADD CONSTRAINT password_reset_requests_reviewed_by_user_id_fkey FOREIGN KEY (reviewed_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: password_reset_requests password_reset_requests_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.password_reset_requests
    ADD CONSTRAINT password_reset_requests_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: password_reset_requests password_reset_requests_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.password_reset_requests
    ADD CONSTRAINT password_reset_requests_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: program_department_association program_department_association_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.program_department_association
    ADD CONSTRAINT program_department_association_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE CASCADE;


--
-- Name: program_department_association program_department_association_program_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.program_department_association
    ADD CONSTRAINT program_department_association_program_id_fkey FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE;


--
-- Name: recommendation_cache recommendation_cache_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recommendation_cache
    ADD CONSTRAINT recommendation_cache_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


--
-- Name: school_audit_logs school_audit_logs_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_audit_logs
    ADD CONSTRAINT school_audit_logs_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: school_audit_logs school_audit_logs_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_audit_logs
    ADD CONSTRAINT school_audit_logs_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: school_settings school_settings_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_settings
    ADD CONSTRAINT school_settings_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: school_settings school_settings_updated_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_settings
    ADD CONSTRAINT school_settings_updated_by_user_id_fkey FOREIGN KEY (updated_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: school_subscription_reminders school_subscription_reminders_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_subscription_reminders
    ADD CONSTRAINT school_subscription_reminders_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: school_subscription_settings school_subscription_settings_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_subscription_settings
    ADD CONSTRAINT school_subscription_settings_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: school_subscription_settings school_subscription_settings_updated_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_subscription_settings
    ADD CONSTRAINT school_subscription_settings_updated_by_user_id_fkey FOREIGN KEY (updated_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: security_alerts security_alerts_anomaly_log_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.security_alerts
    ADD CONSTRAINT security_alerts_anomaly_log_id_fkey FOREIGN KEY (anomaly_log_id) REFERENCES public.anomaly_logs(id) ON DELETE CASCADE;


--
-- Name: security_alerts security_alerts_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.security_alerts
    ADD CONSTRAINT security_alerts_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE SET NULL;


--
-- Name: ssg_profiles ssg_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_profiles
    ADD CONSTRAINT ssg_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_profiles student_profiles_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE RESTRICT;


--
-- Name: student_profiles student_profiles_program_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_program_id_fkey FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE RESTRICT;


--
-- Name: student_profiles student_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: student_risk_scores student_risk_scores_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_risk_scores
    ADD CONSTRAINT student_risk_scores_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


--
-- Name: user_notification_preferences user_notification_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_notification_preferences
    ADD CONSTRAINT user_notification_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_privacy_consents user_privacy_consents_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_privacy_consents
    ADD CONSTRAINT user_privacy_consents_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: user_privacy_consents user_privacy_consents_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_privacy_consents
    ADD CONSTRAINT user_privacy_consents_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_security_settings user_security_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_security_settings
    ADD CONSTRAINT user_security_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_sessions user_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict q1D5eiG7G60kN5QlwGs8TfrDQp7YHzr4dq99DOLiBN8zUa4a1uvBN0Zv1yPdxDv

