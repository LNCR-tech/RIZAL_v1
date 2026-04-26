--
-- PostgreSQL database dump
--

\restrict FSBslmRZXcjopnPtEGoQEACy3AJ4p3euRFas1e4n28hI4DnrKLgVeWlYk6NtX2B

-- Dumped from database version 18.2
-- Dumped by pg_dump version 18.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
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
    'excused',
    'late'
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


--
-- Name: ssg_event_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.ssg_event_status AS ENUM (
    'pending',
    'approved',
    'rejected'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: attendances; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attendances (
    id integer NOT NULL,
    student_id integer,
    event_id integer,
    time_in timestamp with time zone NOT NULL,
    time_out timestamp with time zone,
    method character varying(50),
    status public.attendancestatus NOT NULL,
    verified_by integer,
    notes character varying(500),
    geo_distance_m double precision,
    geo_effective_distance_m double precision,
    geo_latitude double precision,
    geo_longitude double precision,
    geo_accuracy_m double precision,
    liveness_label character varying(32),
    liveness_score double precision,
    check_in_status character varying(16),
    check_out_status character varying(16)
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
    created_at timestamp with time zone DEFAULT now() NOT NULL
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
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_heartbeat timestamp with time zone,
    target_school_id integer NOT NULL
);


--
-- Name: clearance_deadlines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.clearance_deadlines (
    id integer NOT NULL,
    school_id integer NOT NULL,
    event_id integer NOT NULL,
    declared_by_user_id integer,
    target_governance_unit_id integer,
    deadline_at timestamp with time zone NOT NULL,
    status character varying(7) DEFAULT 'active'::character varying NOT NULL,
    warning_email_sent_at timestamp with time zone,
    warning_popup_sent_at timestamp with time zone,
    message text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: clearance_deadlines_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.clearance_deadlines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: clearance_deadlines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.clearance_deadlines_id_seq OWNED BY public.clearance_deadlines.id;


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
    updated_at timestamp with time zone DEFAULT now() NOT NULL
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
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    resolved_at timestamp with time zone
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
    created_at timestamp with time zone DEFAULT now() NOT NULL
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
    name character varying NOT NULL,
    school_id integer
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
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
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
-- Name: event_department_association; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_department_association (
    event_id integer NOT NULL,
    department_id integer NOT NULL
);


--
-- Name: event_program_association; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_program_association (
    event_id integer NOT NULL,
    program_id integer NOT NULL
);


--
-- Name: event_sanction_configs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_sanction_configs (
    id integer NOT NULL,
    school_id integer NOT NULL,
    event_id integer NOT NULL,
    sanctions_enabled boolean DEFAULT false NOT NULL,
    item_definitions_json json NOT NULL,
    created_by_user_id integer,
    updated_by_user_id integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: event_sanction_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.event_sanction_configs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: event_sanction_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.event_sanction_configs_id_seq OWNED BY public.event_sanction_configs.id;


--
-- Name: event_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_types (
    id integer NOT NULL,
    school_id integer,
    name character varying(100) NOT NULL,
    code character varying(50),
    description text,
    is_active boolean NOT NULL,
    sort_order integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: event_types_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.event_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: event_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.event_types_id_seq OWNED BY public.event_types.id;


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
    school_id integer NOT NULL,
    late_threshold_minutes integer DEFAULT 10 NOT NULL,
    geo_latitude double precision,
    geo_longitude double precision,
    geo_radius_m double precision,
    geo_required boolean DEFAULT false NOT NULL,
    geo_max_accuracy_m double precision,
    early_check_in_minutes integer NOT NULL,
    sign_out_grace_minutes integer NOT NULL,
    sign_out_override_until timestamp without time zone,
    present_until_override_at timestamp without time zone,
    late_until_override_at timestamp without time zone,
    sign_out_open_delay_minutes integer NOT NULL,
    event_type_id integer,
    created_by_user_id integer,
    create_idempotency_key character varying(128)
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
-- Name: faculty_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.faculty_profiles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    department_id integer,
    program_id integer
);


--
-- Name: faculty_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.faculty_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: faculty_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.faculty_profiles_id_seq OWNED BY public.faculty_profiles.id;


--
-- Name: governance_announcements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.governance_announcements (
    id integer NOT NULL,
    governance_unit_id integer NOT NULL,
    school_id integer NOT NULL,
    title character varying(255) NOT NULL,
    body text NOT NULL,
    status character varying(9) DEFAULT 'draft'::character varying NOT NULL,
    created_by_user_id integer,
    updated_by_user_id integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: governance_announcements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.governance_announcements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: governance_announcements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.governance_announcements_id_seq OWNED BY public.governance_announcements.id;


--
-- Name: governance_member_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.governance_member_permissions (
    id integer NOT NULL,
    governance_member_id integer NOT NULL,
    permission_id integer NOT NULL,
    granted_by_user_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: governance_member_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.governance_member_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: governance_member_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.governance_member_permissions_id_seq OWNED BY public.governance_member_permissions.id;


--
-- Name: governance_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.governance_members (
    id integer NOT NULL,
    governance_unit_id integer NOT NULL,
    user_id integer NOT NULL,
    position_title character varying(100),
    assigned_by_user_id integer,
    assigned_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


--
-- Name: governance_members_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.governance_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: governance_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.governance_members_id_seq OWNED BY public.governance_members.id;


--
-- Name: governance_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.governance_permissions (
    id integer NOT NULL,
    permission_code character varying(29) NOT NULL,
    permission_name character varying(100) NOT NULL,
    description text
);


--
-- Name: governance_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.governance_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: governance_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.governance_permissions_id_seq OWNED BY public.governance_permissions.id;


--
-- Name: governance_student_notes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.governance_student_notes (
    id integer NOT NULL,
    governance_unit_id integer NOT NULL,
    student_profile_id integer NOT NULL,
    school_id integer NOT NULL,
    tags json NOT NULL,
    notes text DEFAULT ''::text NOT NULL,
    created_by_user_id integer,
    updated_by_user_id integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: governance_student_notes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.governance_student_notes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: governance_student_notes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.governance_student_notes_id_seq OWNED BY public.governance_student_notes.id;


--
-- Name: governance_unit_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.governance_unit_permissions (
    id integer NOT NULL,
    governance_unit_id integer NOT NULL,
    permission_id integer NOT NULL,
    granted_by_user_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: governance_unit_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.governance_unit_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: governance_unit_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.governance_unit_permissions_id_seq OWNED BY public.governance_unit_permissions.id;


--
-- Name: governance_units; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.governance_units (
    id integer NOT NULL,
    unit_code character varying(50) NOT NULL,
    unit_name character varying(255) NOT NULL,
    unit_type character varying(3) NOT NULL,
    parent_unit_id integer,
    school_id integer NOT NULL,
    department_id integer,
    program_id integer,
    created_by_user_id integer,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    description text,
    event_default_early_check_in_minutes integer,
    event_default_late_threshold_minutes integer,
    event_default_sign_out_grace_minutes integer
);


--
-- Name: governance_units_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.governance_units_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: governance_units_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.governance_units_id_seq OWNED BY public.governance_units.id;


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
    created_at timestamp with time zone DEFAULT now() NOT NULL
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
    expires_at timestamp with time zone NOT NULL,
    consumed_at timestamp with time zone,
    ip_address character varying(64),
    user_agent character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


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
    created_at timestamp with time zone DEFAULT now() NOT NULL
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
-- Name: password_reset_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.password_reset_requests (
    id integer NOT NULL,
    user_id integer NOT NULL,
    school_id integer NOT NULL,
    requested_email character varying(255) NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    requested_at timestamp with time zone DEFAULT now() NOT NULL,
    resolved_at timestamp with time zone,
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
    name character varying NOT NULL,
    school_id integer
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
-- Name: sanction_compliance_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sanction_compliance_history (
    id integer NOT NULL,
    school_id integer NOT NULL,
    event_id integer,
    sanction_record_id integer,
    sanction_item_id integer,
    student_profile_id integer,
    complied_on date DEFAULT CURRENT_DATE NOT NULL,
    school_year character varying(20) NOT NULL,
    semester character varying(20) NOT NULL,
    complied_by_user_id integer,
    notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: sanction_compliance_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sanction_compliance_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sanction_compliance_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sanction_compliance_history_id_seq OWNED BY public.sanction_compliance_history.id;


--
-- Name: sanction_delegations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sanction_delegations (
    id integer NOT NULL,
    school_id integer NOT NULL,
    event_id integer NOT NULL,
    sanction_config_id integer,
    delegated_by_user_id integer,
    delegated_to_governance_unit_id integer NOT NULL,
    scope_type character varying(10) DEFAULT 'unit'::character varying NOT NULL,
    scope_json json,
    is_active boolean DEFAULT true NOT NULL,
    revoked_at timestamp with time zone,
    revoked_by_user_id integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: sanction_delegations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sanction_delegations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sanction_delegations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sanction_delegations_id_seq OWNED BY public.sanction_delegations.id;


--
-- Name: sanction_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sanction_items (
    id integer NOT NULL,
    sanction_record_id integer NOT NULL,
    item_code character varying(64),
    item_name character varying(255) NOT NULL,
    item_description text,
    status character varying(8) DEFAULT 'pending'::character varying NOT NULL,
    complied_at timestamp with time zone,
    compliance_notes text,
    metadata_json json,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: sanction_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sanction_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sanction_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sanction_items_id_seq OWNED BY public.sanction_items.id;


--
-- Name: sanction_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sanction_records (
    id integer NOT NULL,
    school_id integer NOT NULL,
    event_id integer NOT NULL,
    sanction_config_id integer,
    student_profile_id integer NOT NULL,
    attendance_id integer,
    delegated_governance_unit_id integer,
    status character varying(8) DEFAULT 'pending'::character varying NOT NULL,
    assigned_by_user_id integer,
    complied_at timestamp with time zone,
    notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: sanction_records_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sanction_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sanction_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sanction_records_id_seq OWNED BY public.sanction_records.id;


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
    created_at timestamp with time zone DEFAULT now() NOT NULL
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_by_user_id integer,
    event_default_early_check_in_minutes integer NOT NULL,
    event_default_late_threshold_minutes integer NOT NULL,
    event_default_sign_out_grace_minutes integer NOT NULL
);


--
-- Name: school_subscription_reminders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.school_subscription_reminders (
    id integer NOT NULL,
    school_id integer NOT NULL,
    reminder_type character varying(40) DEFAULT 'renewal_warning'::character varying NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    due_at timestamp with time zone NOT NULL,
    sent_at timestamp with time zone,
    error_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL
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
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
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
-- Name: ssg_announcements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ssg_announcements (
    id integer NOT NULL,
    school_id integer NOT NULL,
    title character varying(150) NOT NULL,
    message text NOT NULL,
    created_by integer,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: ssg_announcements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ssg_announcements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ssg_announcements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ssg_announcements_id_seq OWNED BY public.ssg_announcements.id;


--
-- Name: ssg_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ssg_events (
    id integer NOT NULL,
    school_id integer NOT NULL,
    title character varying(150) NOT NULL,
    description text,
    event_date timestamp without time zone NOT NULL,
    created_by integer,
    status public.ssg_event_status DEFAULT 'pending'::public.ssg_event_status NOT NULL,
    approved_by integer,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    approved_at timestamp without time zone,
    location character varying(200),
    notification_sent boolean DEFAULT false NOT NULL,
    start_time timestamp without time zone DEFAULT now() NOT NULL,
    end_time timestamp without time zone DEFAULT now() NOT NULL,
    late_threshold_minutes integer DEFAULT 10 NOT NULL
);


--
-- Name: ssg_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ssg_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ssg_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ssg_events_id_seq OWNED BY public.ssg_events.id;


--
-- Name: ssg_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ssg_permissions (
    id integer NOT NULL,
    permission_name character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: ssg_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ssg_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ssg_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ssg_permissions_id_seq OWNED BY public.ssg_permissions.id;


--
-- Name: ssg_role_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ssg_role_permissions (
    id integer NOT NULL,
    role_id integer NOT NULL,
    permission_id integer NOT NULL
);


--
-- Name: ssg_role_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ssg_role_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ssg_role_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ssg_role_permissions_id_seq OWNED BY public.ssg_role_permissions.id;


--
-- Name: ssg_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ssg_roles (
    id integer NOT NULL,
    school_id integer NOT NULL,
    role_name character varying(100) NOT NULL,
    max_members integer,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: ssg_roles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ssg_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ssg_roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ssg_roles_id_seq OWNED BY public.ssg_roles.id;


--
-- Name: ssg_user_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ssg_user_roles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    role_id integer NOT NULL,
    school_year character varying(20) NOT NULL,
    assigned_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: ssg_user_roles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ssg_user_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ssg_user_roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ssg_user_roles_id_seq OWNED BY public.ssg_user_roles.id;


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
    last_face_update timestamp with time zone,
    school_id integer NOT NULL,
    embedding_provider character varying(32),
    embedding_dtype character varying(16),
    embedding_dimension integer,
    embedding_normalized boolean NOT NULL
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
-- Name: user_app_preferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_app_preferences (
    user_id integer NOT NULL,
    dark_mode_enabled boolean DEFAULT false NOT NULL,
    font_size_percent integer DEFAULT 100 NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_roles (
    id integer NOT NULL,
    user_id integer,
    role_id integer
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
    created_at timestamp with time zone NOT NULL,
    school_id integer,
    must_change_password boolean DEFAULT true NOT NULL,
    should_prompt_password_change boolean NOT NULL,
    prefix character varying(20),
    suffix character varying(20)
);


--
-- Name: user_by_schools; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.user_by_schools AS
 SELECT s.id AS school_id,
    s.school_name,
    s.school_code,
    s.active_status,
    s.subscription_status,
    u.id AS user_id,
    u.email,
    u.first_name,
    u.middle_name,
    u.last_name,
    u.is_active AS user_active,
    u.created_at AS user_created_at,
    r.name AS role,
        CASE
            WHEN (sp.id IS NOT NULL) THEN true
            ELSE false
        END AS is_student,
    sp.student_id,
    sp.is_face_registered
   FROM ((((public.schools s
     LEFT JOIN public.users u ON ((s.id = u.school_id)))
     LEFT JOIN public.user_roles ur ON ((u.id = ur.user_id)))
     LEFT JOIN public.roles r ON ((ur.role_id = r.id)))
     LEFT JOIN public.student_profiles sp ON ((u.id = sp.user_id)))
  ORDER BY s.id, u.id;


--
-- Name: user_count_by_school; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.user_count_by_school AS
 SELECT s.id AS school_id,
    s.school_name,
    s.school_code,
    s.active_status,
    s.subscription_status,
    count(u.id) AS total_users,
    count(
        CASE
            WHEN ((r.name)::text = 'student'::text) THEN 1
            ELSE NULL::integer
        END) AS total_students,
    count(
        CASE
            WHEN ((r.name)::text = 'campus_admin'::text) THEN 1
            ELSE NULL::integer
        END) AS total_campus_admins,
    count(
        CASE
            WHEN ((r.name)::text = 'teacher'::text) THEN 1
            ELSE NULL::integer
        END) AS total_teachers,
    count(
        CASE
            WHEN (sp.is_face_registered = true) THEN 1
            ELSE NULL::integer
        END) AS students_with_face
   FROM ((((public.schools s
     LEFT JOIN public.users u ON ((s.id = u.school_id)))
     LEFT JOIN public.user_roles ur ON ((u.id = ur.user_id)))
     LEFT JOIN public.roles r ON ((ur.role_id = r.id)))
     LEFT JOIN public.student_profiles sp ON ((u.id = sp.user_id)))
  GROUP BY s.id, s.school_name, s.school_code, s.active_status, s.subscription_status
  ORDER BY s.id;


--
-- Name: user_face_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_face_profiles (
    user_id integer NOT NULL,
    face_encoding bytea NOT NULL,
    provider character varying(50) DEFAULT 'face_recognition'::character varying NOT NULL,
    reference_image_sha256 character varying(64),
    last_verified_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


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
    updated_at timestamp with time zone DEFAULT now() NOT NULL
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
    created_at timestamp with time zone DEFAULT now() NOT NULL
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
    updated_at timestamp with time zone DEFAULT now() NOT NULL
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
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_seen_at timestamp with time zone DEFAULT now() NOT NULL,
    revoked_at timestamp with time zone,
    expires_at timestamp with time zone NOT NULL
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
-- Name: attendances id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendances ALTER COLUMN id SET DEFAULT nextval('public.attendances_id_seq'::regclass);


--
-- Name: bulk_import_errors id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bulk_import_errors ALTER COLUMN id SET DEFAULT nextval('public.bulk_import_errors_id_seq'::regclass);


--
-- Name: clearance_deadlines id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clearance_deadlines ALTER COLUMN id SET DEFAULT nextval('public.clearance_deadlines_id_seq'::regclass);


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
-- Name: event_sanction_configs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_sanction_configs ALTER COLUMN id SET DEFAULT nextval('public.event_sanction_configs_id_seq'::regclass);


--
-- Name: event_types id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_types ALTER COLUMN id SET DEFAULT nextval('public.event_types_id_seq'::regclass);


--
-- Name: events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events ALTER COLUMN id SET DEFAULT nextval('public.events_id_seq'::regclass);


--
-- Name: faculty_profiles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_profiles ALTER COLUMN id SET DEFAULT nextval('public.faculty_profiles_id_seq'::regclass);


--
-- Name: governance_announcements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_announcements ALTER COLUMN id SET DEFAULT nextval('public.governance_announcements_id_seq'::regclass);


--
-- Name: governance_member_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_member_permissions ALTER COLUMN id SET DEFAULT nextval('public.governance_member_permissions_id_seq'::regclass);


--
-- Name: governance_members id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_members ALTER COLUMN id SET DEFAULT nextval('public.governance_members_id_seq'::regclass);


--
-- Name: governance_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_permissions ALTER COLUMN id SET DEFAULT nextval('public.governance_permissions_id_seq'::regclass);


--
-- Name: governance_student_notes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_student_notes ALTER COLUMN id SET DEFAULT nextval('public.governance_student_notes_id_seq'::regclass);


--
-- Name: governance_unit_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_unit_permissions ALTER COLUMN id SET DEFAULT nextval('public.governance_unit_permissions_id_seq'::regclass);


--
-- Name: governance_units id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_units ALTER COLUMN id SET DEFAULT nextval('public.governance_units_id_seq'::regclass);


--
-- Name: login_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_history ALTER COLUMN id SET DEFAULT nextval('public.login_history_id_seq'::regclass);


--
-- Name: notification_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_logs ALTER COLUMN id SET DEFAULT nextval('public.notification_logs_id_seq'::regclass);


--
-- Name: password_reset_requests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.password_reset_requests ALTER COLUMN id SET DEFAULT nextval('public.password_reset_requests_id_seq'::regclass);


--
-- Name: programs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.programs ALTER COLUMN id SET DEFAULT nextval('public.programs_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: sanction_compliance_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_compliance_history ALTER COLUMN id SET DEFAULT nextval('public.sanction_compliance_history_id_seq'::regclass);


--
-- Name: sanction_delegations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_delegations ALTER COLUMN id SET DEFAULT nextval('public.sanction_delegations_id_seq'::regclass);


--
-- Name: sanction_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_items ALTER COLUMN id SET DEFAULT nextval('public.sanction_items_id_seq'::regclass);


--
-- Name: sanction_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_records ALTER COLUMN id SET DEFAULT nextval('public.sanction_records_id_seq'::regclass);


--
-- Name: school_audit_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_audit_logs ALTER COLUMN id SET DEFAULT nextval('public.school_audit_logs_id_seq'::regclass);


--
-- Name: school_subscription_reminders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.school_subscription_reminders ALTER COLUMN id SET DEFAULT nextval('public.school_subscription_reminders_id_seq'::regclass);


--
-- Name: ssg_announcements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_announcements ALTER COLUMN id SET DEFAULT nextval('public.ssg_announcements_id_seq'::regclass);


--
-- Name: ssg_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_events ALTER COLUMN id SET DEFAULT nextval('public.ssg_events_id_seq'::regclass);


--
-- Name: ssg_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_permissions ALTER COLUMN id SET DEFAULT nextval('public.ssg_permissions_id_seq'::regclass);


--
-- Name: ssg_role_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_role_permissions ALTER COLUMN id SET DEFAULT nextval('public.ssg_role_permissions_id_seq'::regclass);


--
-- Name: ssg_roles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_roles ALTER COLUMN id SET DEFAULT nextval('public.ssg_roles_id_seq'::regclass);


--
-- Name: ssg_user_roles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_user_roles ALTER COLUMN id SET DEFAULT nextval('public.ssg_user_roles_id_seq'::regclass);


--
-- Name: student_profiles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles ALTER COLUMN id SET DEFAULT nextval('public.student_profiles_id_seq'::regclass);


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
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


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
-- Name: clearance_deadlines clearance_deadlines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clearance_deadlines
    ADD CONSTRAINT clearance_deadlines_pkey PRIMARY KEY (id);


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
-- Name: event_department_association event_department_association_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_department_association
    ADD CONSTRAINT event_department_association_pkey PRIMARY KEY (event_id, department_id);


--
-- Name: event_program_association event_program_association_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_program_association
    ADD CONSTRAINT event_program_association_pkey PRIMARY KEY (event_id, program_id);


--
-- Name: event_sanction_configs event_sanction_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_sanction_configs
    ADD CONSTRAINT event_sanction_configs_pkey PRIMARY KEY (id);


--
-- Name: event_types event_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_types
    ADD CONSTRAINT event_types_pkey PRIMARY KEY (id);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);


--
-- Name: faculty_profiles faculty_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_profiles
    ADD CONSTRAINT faculty_profiles_pkey PRIMARY KEY (id);


--
-- Name: governance_announcements governance_announcements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_announcements
    ADD CONSTRAINT governance_announcements_pkey PRIMARY KEY (id);


--
-- Name: governance_member_permissions governance_member_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_member_permissions
    ADD CONSTRAINT governance_member_permissions_pkey PRIMARY KEY (id);


--
-- Name: governance_members governance_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_members
    ADD CONSTRAINT governance_members_pkey PRIMARY KEY (id);


--
-- Name: governance_permissions governance_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_permissions
    ADD CONSTRAINT governance_permissions_pkey PRIMARY KEY (id);


--
-- Name: governance_student_notes governance_student_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_student_notes
    ADD CONSTRAINT governance_student_notes_pkey PRIMARY KEY (id);


--
-- Name: governance_unit_permissions governance_unit_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_unit_permissions
    ADD CONSTRAINT governance_unit_permissions_pkey PRIMARY KEY (id);


--
-- Name: governance_units governance_units_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_units
    ADD CONSTRAINT governance_units_pkey PRIMARY KEY (id);


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
-- Name: notification_logs notification_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_logs
    ADD CONSTRAINT notification_logs_pkey PRIMARY KEY (id);


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
-- Name: programs programs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.programs
    ADD CONSTRAINT programs_pkey PRIMARY KEY (id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: sanction_compliance_history sanction_compliance_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_compliance_history
    ADD CONSTRAINT sanction_compliance_history_pkey PRIMARY KEY (id);


--
-- Name: sanction_delegations sanction_delegations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_delegations
    ADD CONSTRAINT sanction_delegations_pkey PRIMARY KEY (id);


--
-- Name: sanction_items sanction_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_items
    ADD CONSTRAINT sanction_items_pkey PRIMARY KEY (id);


--
-- Name: sanction_records sanction_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_records
    ADD CONSTRAINT sanction_records_pkey PRIMARY KEY (id);


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
-- Name: ssg_announcements ssg_announcements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_announcements
    ADD CONSTRAINT ssg_announcements_pkey PRIMARY KEY (id);


--
-- Name: ssg_events ssg_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_events
    ADD CONSTRAINT ssg_events_pkey PRIMARY KEY (id);


--
-- Name: ssg_permissions ssg_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_permissions
    ADD CONSTRAINT ssg_permissions_pkey PRIMARY KEY (id);


--
-- Name: ssg_role_permissions ssg_role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_role_permissions
    ADD CONSTRAINT ssg_role_permissions_pkey PRIMARY KEY (id);


--
-- Name: ssg_roles ssg_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_roles
    ADD CONSTRAINT ssg_roles_pkey PRIMARY KEY (id);


--
-- Name: ssg_user_roles ssg_user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_user_roles
    ADD CONSTRAINT ssg_user_roles_pkey PRIMARY KEY (id);


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
-- Name: departments uq_departments_school_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT uq_departments_school_name UNIQUE (school_id, name);


--
-- Name: event_sanction_configs uq_event_sanction_configs_event_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_sanction_configs
    ADD CONSTRAINT uq_event_sanction_configs_event_id UNIQUE (event_id);


--
-- Name: event_types uq_event_types_school_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_types
    ADD CONSTRAINT uq_event_types_school_name UNIQUE (school_id, name);


--
-- Name: events uq_events_creator_idempotency_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT uq_events_creator_idempotency_key UNIQUE (created_by_user_id, create_idempotency_key);


--
-- Name: faculty_profiles uq_faculty_profiles_user_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_profiles
    ADD CONSTRAINT uq_faculty_profiles_user_id UNIQUE (user_id);


--
-- Name: governance_member_permissions uq_governance_member_permissions_member_permission; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_member_permissions
    ADD CONSTRAINT uq_governance_member_permissions_member_permission UNIQUE (governance_member_id, permission_id);


--
-- Name: governance_members uq_governance_members_unit_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_members
    ADD CONSTRAINT uq_governance_members_unit_user UNIQUE (governance_unit_id, user_id);


--
-- Name: governance_student_notes uq_governance_student_notes_unit_student; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_student_notes
    ADD CONSTRAINT uq_governance_student_notes_unit_student UNIQUE (governance_unit_id, student_profile_id);


--
-- Name: governance_unit_permissions uq_governance_unit_permissions_unit_permission; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_unit_permissions
    ADD CONSTRAINT uq_governance_unit_permissions_unit_permission UNIQUE (governance_unit_id, permission_id);


--
-- Name: governance_units uq_governance_units_school_unit_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_units
    ADD CONSTRAINT uq_governance_units_school_unit_code UNIQUE (school_id, unit_code);


--
-- Name: programs uq_programs_school_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.programs
    ADD CONSTRAINT uq_programs_school_name UNIQUE (school_id, name);


--
-- Name: sanction_delegations uq_sanction_delegations_event_governance_unit; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_delegations
    ADD CONSTRAINT uq_sanction_delegations_event_governance_unit UNIQUE (event_id, delegated_to_governance_unit_id);


--
-- Name: sanction_items uq_sanction_items_record_item_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_items
    ADD CONSTRAINT uq_sanction_items_record_item_code UNIQUE (sanction_record_id, item_code);


--
-- Name: sanction_records uq_sanction_records_event_student; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_records
    ADD CONSTRAINT uq_sanction_records_event_student UNIQUE (event_id, student_profile_id);


--
-- Name: ssg_role_permissions uq_ssg_role_permission; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_role_permissions
    ADD CONSTRAINT uq_ssg_role_permission UNIQUE (role_id, permission_id);


--
-- Name: ssg_roles uq_ssg_roles_school_role; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_roles
    ADD CONSTRAINT uq_ssg_roles_school_role UNIQUE (school_id, role_name);


--
-- Name: ssg_user_roles uq_ssg_user_role_year; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_user_roles
    ADD CONSTRAINT uq_ssg_user_role_year UNIQUE (user_id, role_id, school_year);


--
-- Name: student_profiles uq_student_profiles_school_student_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT uq_student_profiles_school_student_id UNIQUE (school_id, student_id);


--
-- Name: user_app_preferences user_app_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_app_preferences
    ADD CONSTRAINT user_app_preferences_pkey PRIMARY KEY (user_id);


--
-- Name: user_face_profiles user_face_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_face_profiles
    ADD CONSTRAINT user_face_profiles_pkey PRIMARY KEY (user_id);


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
-- Name: ix_clearance_deadlines_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clearance_deadlines_created_at ON public.clearance_deadlines USING btree (created_at);


--
-- Name: ix_clearance_deadlines_deadline_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clearance_deadlines_deadline_at ON public.clearance_deadlines USING btree (deadline_at);


--
-- Name: ix_clearance_deadlines_declared_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clearance_deadlines_declared_by_user_id ON public.clearance_deadlines USING btree (declared_by_user_id);


--
-- Name: ix_clearance_deadlines_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clearance_deadlines_event_id ON public.clearance_deadlines USING btree (event_id);


--
-- Name: ix_clearance_deadlines_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clearance_deadlines_id ON public.clearance_deadlines USING btree (id);


--
-- Name: ix_clearance_deadlines_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clearance_deadlines_school_id ON public.clearance_deadlines USING btree (school_id);


--
-- Name: ix_clearance_deadlines_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clearance_deadlines_status ON public.clearance_deadlines USING btree (status);


--
-- Name: ix_clearance_deadlines_target_governance_unit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clearance_deadlines_target_governance_unit_id ON public.clearance_deadlines USING btree (target_governance_unit_id);


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
-- Name: ix_departments_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_departments_school_id ON public.departments USING btree (school_id);


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
-- Name: ix_event_sanction_configs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_sanction_configs_created_at ON public.event_sanction_configs USING btree (created_at);


--
-- Name: ix_event_sanction_configs_created_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_sanction_configs_created_by_user_id ON public.event_sanction_configs USING btree (created_by_user_id);


--
-- Name: ix_event_sanction_configs_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_sanction_configs_event_id ON public.event_sanction_configs USING btree (event_id);


--
-- Name: ix_event_sanction_configs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_sanction_configs_id ON public.event_sanction_configs USING btree (id);


--
-- Name: ix_event_sanction_configs_sanctions_enabled; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_sanction_configs_sanctions_enabled ON public.event_sanction_configs USING btree (sanctions_enabled);


--
-- Name: ix_event_sanction_configs_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_sanction_configs_school_id ON public.event_sanction_configs USING btree (school_id);


--
-- Name: ix_event_sanction_configs_updated_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_sanction_configs_updated_by_user_id ON public.event_sanction_configs USING btree (updated_by_user_id);


--
-- Name: ix_event_types_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_types_id ON public.event_types USING btree (id);


--
-- Name: ix_event_types_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_types_school_id ON public.event_types USING btree (school_id);


--
-- Name: ix_events_created_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_events_created_by_user_id ON public.events USING btree (created_by_user_id);


--
-- Name: ix_events_event_type_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_events_event_type_id ON public.events USING btree (event_type_id);


--
-- Name: ix_events_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_events_id ON public.events USING btree (id);


--
-- Name: ix_events_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_events_school_id ON public.events USING btree (school_id);


--
-- Name: ix_faculty_profiles_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_profiles_department_id ON public.faculty_profiles USING btree (department_id);


--
-- Name: ix_faculty_profiles_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_profiles_id ON public.faculty_profiles USING btree (id);


--
-- Name: ix_faculty_profiles_program_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_profiles_program_id ON public.faculty_profiles USING btree (program_id);


--
-- Name: ix_faculty_profiles_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_profiles_user_id ON public.faculty_profiles USING btree (user_id);


--
-- Name: ix_governance_announcements_governance_unit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_announcements_governance_unit_id ON public.governance_announcements USING btree (governance_unit_id);


--
-- Name: ix_governance_announcements_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_announcements_school_id ON public.governance_announcements USING btree (school_id);


--
-- Name: ix_governance_announcements_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_announcements_status ON public.governance_announcements USING btree (status);


--
-- Name: ix_governance_member_permissions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_member_permissions_created_at ON public.governance_member_permissions USING btree (created_at);


--
-- Name: ix_governance_member_permissions_governance_member_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_member_permissions_governance_member_id ON public.governance_member_permissions USING btree (governance_member_id);


--
-- Name: ix_governance_member_permissions_granted_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_member_permissions_granted_by_user_id ON public.governance_member_permissions USING btree (granted_by_user_id);


--
-- Name: ix_governance_member_permissions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_member_permissions_id ON public.governance_member_permissions USING btree (id);


--
-- Name: ix_governance_member_permissions_permission_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_member_permissions_permission_id ON public.governance_member_permissions USING btree (permission_id);


--
-- Name: ix_governance_members_assigned_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_members_assigned_by_user_id ON public.governance_members USING btree (assigned_by_user_id);


--
-- Name: ix_governance_members_governance_unit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_members_governance_unit_id ON public.governance_members USING btree (governance_unit_id);


--
-- Name: ix_governance_members_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_members_id ON public.governance_members USING btree (id);


--
-- Name: ix_governance_members_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_members_is_active ON public.governance_members USING btree (is_active);


--
-- Name: ix_governance_members_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_members_user_id ON public.governance_members USING btree (user_id);


--
-- Name: ix_governance_permissions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_permissions_id ON public.governance_permissions USING btree (id);


--
-- Name: ix_governance_permissions_permission_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_governance_permissions_permission_code ON public.governance_permissions USING btree (permission_code);


--
-- Name: ix_governance_student_notes_governance_unit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_student_notes_governance_unit_id ON public.governance_student_notes USING btree (governance_unit_id);


--
-- Name: ix_governance_student_notes_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_student_notes_school_id ON public.governance_student_notes USING btree (school_id);


--
-- Name: ix_governance_student_notes_student_profile_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_student_notes_student_profile_id ON public.governance_student_notes USING btree (student_profile_id);


--
-- Name: ix_governance_unit_permissions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_unit_permissions_created_at ON public.governance_unit_permissions USING btree (created_at);


--
-- Name: ix_governance_unit_permissions_governance_unit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_unit_permissions_governance_unit_id ON public.governance_unit_permissions USING btree (governance_unit_id);


--
-- Name: ix_governance_unit_permissions_granted_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_unit_permissions_granted_by_user_id ON public.governance_unit_permissions USING btree (granted_by_user_id);


--
-- Name: ix_governance_unit_permissions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_unit_permissions_id ON public.governance_unit_permissions USING btree (id);


--
-- Name: ix_governance_unit_permissions_permission_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_unit_permissions_permission_id ON public.governance_unit_permissions USING btree (permission_id);


--
-- Name: ix_governance_units_created_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_units_created_by_user_id ON public.governance_units USING btree (created_by_user_id);


--
-- Name: ix_governance_units_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_units_department_id ON public.governance_units USING btree (department_id);


--
-- Name: ix_governance_units_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_units_id ON public.governance_units USING btree (id);


--
-- Name: ix_governance_units_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_units_is_active ON public.governance_units USING btree (is_active);


--
-- Name: ix_governance_units_parent_unit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_units_parent_unit_id ON public.governance_units USING btree (parent_unit_id);


--
-- Name: ix_governance_units_program_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_units_program_id ON public.governance_units USING btree (program_id);


--
-- Name: ix_governance_units_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_units_school_id ON public.governance_units USING btree (school_id);


--
-- Name: ix_governance_units_unit_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_units_unit_code ON public.governance_units USING btree (unit_code);


--
-- Name: ix_governance_units_unit_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_governance_units_unit_type ON public.governance_units USING btree (unit_type);


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
-- Name: ix_programs_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_programs_school_id ON public.programs USING btree (school_id);


--
-- Name: ix_roles_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);


--
-- Name: ix_sanction_compliance_history_complied_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_compliance_history_complied_by_user_id ON public.sanction_compliance_history USING btree (complied_by_user_id);


--
-- Name: ix_sanction_compliance_history_complied_on; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_compliance_history_complied_on ON public.sanction_compliance_history USING btree (complied_on);


--
-- Name: ix_sanction_compliance_history_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_compliance_history_created_at ON public.sanction_compliance_history USING btree (created_at);


--
-- Name: ix_sanction_compliance_history_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_compliance_history_event_id ON public.sanction_compliance_history USING btree (event_id);


--
-- Name: ix_sanction_compliance_history_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_compliance_history_id ON public.sanction_compliance_history USING btree (id);


--
-- Name: ix_sanction_compliance_history_sanction_item_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_compliance_history_sanction_item_id ON public.sanction_compliance_history USING btree (sanction_item_id);


--
-- Name: ix_sanction_compliance_history_sanction_record_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_compliance_history_sanction_record_id ON public.sanction_compliance_history USING btree (sanction_record_id);


--
-- Name: ix_sanction_compliance_history_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_compliance_history_school_id ON public.sanction_compliance_history USING btree (school_id);


--
-- Name: ix_sanction_compliance_history_school_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_compliance_history_school_year ON public.sanction_compliance_history USING btree (school_year);


--
-- Name: ix_sanction_compliance_history_semester; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_compliance_history_semester ON public.sanction_compliance_history USING btree (semester);


--
-- Name: ix_sanction_compliance_history_student_profile_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_compliance_history_student_profile_id ON public.sanction_compliance_history USING btree (student_profile_id);


--
-- Name: ix_sanction_delegations_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_delegations_created_at ON public.sanction_delegations USING btree (created_at);


--
-- Name: ix_sanction_delegations_delegated_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_delegations_delegated_by_user_id ON public.sanction_delegations USING btree (delegated_by_user_id);


--
-- Name: ix_sanction_delegations_delegated_to_governance_unit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_delegations_delegated_to_governance_unit_id ON public.sanction_delegations USING btree (delegated_to_governance_unit_id);


--
-- Name: ix_sanction_delegations_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_delegations_event_id ON public.sanction_delegations USING btree (event_id);


--
-- Name: ix_sanction_delegations_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_delegations_id ON public.sanction_delegations USING btree (id);


--
-- Name: ix_sanction_delegations_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_delegations_is_active ON public.sanction_delegations USING btree (is_active);


--
-- Name: ix_sanction_delegations_revoked_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_delegations_revoked_by_user_id ON public.sanction_delegations USING btree (revoked_by_user_id);


--
-- Name: ix_sanction_delegations_sanction_config_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_delegations_sanction_config_id ON public.sanction_delegations USING btree (sanction_config_id);


--
-- Name: ix_sanction_delegations_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_delegations_school_id ON public.sanction_delegations USING btree (school_id);


--
-- Name: ix_sanction_delegations_scope_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_delegations_scope_type ON public.sanction_delegations USING btree (scope_type);


--
-- Name: ix_sanction_items_complied_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_items_complied_at ON public.sanction_items USING btree (complied_at);


--
-- Name: ix_sanction_items_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_items_created_at ON public.sanction_items USING btree (created_at);


--
-- Name: ix_sanction_items_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_items_id ON public.sanction_items USING btree (id);


--
-- Name: ix_sanction_items_item_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_items_item_code ON public.sanction_items USING btree (item_code);


--
-- Name: ix_sanction_items_sanction_record_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_items_sanction_record_id ON public.sanction_items USING btree (sanction_record_id);


--
-- Name: ix_sanction_items_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_items_status ON public.sanction_items USING btree (status);


--
-- Name: ix_sanction_records_assigned_by_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_records_assigned_by_user_id ON public.sanction_records USING btree (assigned_by_user_id);


--
-- Name: ix_sanction_records_attendance_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_records_attendance_id ON public.sanction_records USING btree (attendance_id);


--
-- Name: ix_sanction_records_complied_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_records_complied_at ON public.sanction_records USING btree (complied_at);


--
-- Name: ix_sanction_records_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_records_created_at ON public.sanction_records USING btree (created_at);


--
-- Name: ix_sanction_records_delegated_governance_unit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_records_delegated_governance_unit_id ON public.sanction_records USING btree (delegated_governance_unit_id);


--
-- Name: ix_sanction_records_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_records_event_id ON public.sanction_records USING btree (event_id);


--
-- Name: ix_sanction_records_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_records_id ON public.sanction_records USING btree (id);


--
-- Name: ix_sanction_records_sanction_config_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_records_sanction_config_id ON public.sanction_records USING btree (sanction_config_id);


--
-- Name: ix_sanction_records_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_records_school_id ON public.sanction_records USING btree (school_id);


--
-- Name: ix_sanction_records_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_records_status ON public.sanction_records USING btree (status);


--
-- Name: ix_sanction_records_student_profile_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sanction_records_student_profile_id ON public.sanction_records USING btree (student_profile_id);


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
-- Name: ix_ssg_announcements_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ssg_announcements_school_id ON public.ssg_announcements USING btree (school_id);


--
-- Name: ix_ssg_events_event_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ssg_events_event_date ON public.ssg_events USING btree (event_date);


--
-- Name: ix_ssg_events_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ssg_events_school_id ON public.ssg_events USING btree (school_id);


--
-- Name: ix_ssg_events_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ssg_events_status ON public.ssg_events USING btree (status);


--
-- Name: ix_ssg_permissions_permission_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_ssg_permissions_permission_name ON public.ssg_permissions USING btree (permission_name);


--
-- Name: ix_ssg_role_permissions_permission_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ssg_role_permissions_permission_id ON public.ssg_role_permissions USING btree (permission_id);


--
-- Name: ix_ssg_role_permissions_role_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ssg_role_permissions_role_id ON public.ssg_role_permissions USING btree (role_id);


--
-- Name: ix_ssg_roles_school_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ssg_roles_school_id ON public.ssg_roles USING btree (school_id);


--
-- Name: ix_ssg_user_roles_role_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ssg_user_roles_role_id ON public.ssg_user_roles USING btree (role_id);


--
-- Name: ix_ssg_user_roles_school_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ssg_user_roles_school_year ON public.ssg_user_roles USING btree (school_year);


--
-- Name: ix_ssg_user_roles_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ssg_user_roles_user_id ON public.ssg_user_roles USING btree (user_id);


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
-- Name: uq_governance_units_single_ssg_per_school; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_governance_units_single_ssg_per_school ON public.governance_units USING btree (school_id) WHERE ((unit_type)::text = 'SSG'::text);


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
-- Name: clearance_deadlines clearance_deadlines_declared_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clearance_deadlines
    ADD CONSTRAINT clearance_deadlines_declared_by_user_id_fkey FOREIGN KEY (declared_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: clearance_deadlines clearance_deadlines_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clearance_deadlines
    ADD CONSTRAINT clearance_deadlines_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: clearance_deadlines clearance_deadlines_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clearance_deadlines
    ADD CONSTRAINT clearance_deadlines_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: clearance_deadlines clearance_deadlines_target_governance_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clearance_deadlines
    ADD CONSTRAINT clearance_deadlines_target_governance_unit_id_fkey FOREIGN KEY (target_governance_unit_id) REFERENCES public.governance_units(id) ON DELETE SET NULL;


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
-- Name: event_sanction_configs event_sanction_configs_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_sanction_configs
    ADD CONSTRAINT event_sanction_configs_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: event_sanction_configs event_sanction_configs_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_sanction_configs
    ADD CONSTRAINT event_sanction_configs_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: event_sanction_configs event_sanction_configs_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_sanction_configs
    ADD CONSTRAINT event_sanction_configs_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: event_sanction_configs event_sanction_configs_updated_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_sanction_configs
    ADD CONSTRAINT event_sanction_configs_updated_by_user_id_fkey FOREIGN KEY (updated_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: event_types event_types_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_types
    ADD CONSTRAINT event_types_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: faculty_profiles faculty_profiles_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_profiles
    ADD CONSTRAINT faculty_profiles_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: faculty_profiles faculty_profiles_program_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_profiles
    ADD CONSTRAINT faculty_profiles_program_id_fkey FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE SET NULL;


--
-- Name: faculty_profiles faculty_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_profiles
    ADD CONSTRAINT faculty_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: bulk_import_jobs fk_bulk_import_jobs_target_school_id_schools; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bulk_import_jobs
    ADD CONSTRAINT fk_bulk_import_jobs_target_school_id_schools FOREIGN KEY (target_school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: departments fk_departments_school_id_schools; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT fk_departments_school_id_schools FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: events fk_events_created_by_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT fk_events_created_by_user_id_users FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: events fk_events_event_type_id_event_types; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT fk_events_event_type_id_event_types FOREIGN KEY (event_type_id) REFERENCES public.event_types(id) ON DELETE SET NULL;


--
-- Name: events fk_events_school_id_schools; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT fk_events_school_id_schools FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: programs fk_programs_school_id_schools; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.programs
    ADD CONSTRAINT fk_programs_school_id_schools FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


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
-- Name: governance_announcements governance_announcements_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_announcements
    ADD CONSTRAINT governance_announcements_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: governance_announcements governance_announcements_governance_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_announcements
    ADD CONSTRAINT governance_announcements_governance_unit_id_fkey FOREIGN KEY (governance_unit_id) REFERENCES public.governance_units(id) ON DELETE CASCADE;


--
-- Name: governance_announcements governance_announcements_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_announcements
    ADD CONSTRAINT governance_announcements_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: governance_announcements governance_announcements_updated_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_announcements
    ADD CONSTRAINT governance_announcements_updated_by_user_id_fkey FOREIGN KEY (updated_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: governance_member_permissions governance_member_permissions_governance_member_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_member_permissions
    ADD CONSTRAINT governance_member_permissions_governance_member_id_fkey FOREIGN KEY (governance_member_id) REFERENCES public.governance_members(id) ON DELETE CASCADE;


--
-- Name: governance_member_permissions governance_member_permissions_granted_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_member_permissions
    ADD CONSTRAINT governance_member_permissions_granted_by_user_id_fkey FOREIGN KEY (granted_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: governance_member_permissions governance_member_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_member_permissions
    ADD CONSTRAINT governance_member_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.governance_permissions(id) ON DELETE CASCADE;


--
-- Name: governance_members governance_members_assigned_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_members
    ADD CONSTRAINT governance_members_assigned_by_user_id_fkey FOREIGN KEY (assigned_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: governance_members governance_members_governance_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_members
    ADD CONSTRAINT governance_members_governance_unit_id_fkey FOREIGN KEY (governance_unit_id) REFERENCES public.governance_units(id) ON DELETE CASCADE;


--
-- Name: governance_members governance_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_members
    ADD CONSTRAINT governance_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: governance_student_notes governance_student_notes_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_student_notes
    ADD CONSTRAINT governance_student_notes_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: governance_student_notes governance_student_notes_governance_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_student_notes
    ADD CONSTRAINT governance_student_notes_governance_unit_id_fkey FOREIGN KEY (governance_unit_id) REFERENCES public.governance_units(id) ON DELETE CASCADE;


--
-- Name: governance_student_notes governance_student_notes_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_student_notes
    ADD CONSTRAINT governance_student_notes_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: governance_student_notes governance_student_notes_student_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_student_notes
    ADD CONSTRAINT governance_student_notes_student_profile_id_fkey FOREIGN KEY (student_profile_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


--
-- Name: governance_student_notes governance_student_notes_updated_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_student_notes
    ADD CONSTRAINT governance_student_notes_updated_by_user_id_fkey FOREIGN KEY (updated_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: governance_unit_permissions governance_unit_permissions_governance_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_unit_permissions
    ADD CONSTRAINT governance_unit_permissions_governance_unit_id_fkey FOREIGN KEY (governance_unit_id) REFERENCES public.governance_units(id) ON DELETE CASCADE;


--
-- Name: governance_unit_permissions governance_unit_permissions_granted_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_unit_permissions
    ADD CONSTRAINT governance_unit_permissions_granted_by_user_id_fkey FOREIGN KEY (granted_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: governance_unit_permissions governance_unit_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_unit_permissions
    ADD CONSTRAINT governance_unit_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.governance_permissions(id) ON DELETE CASCADE;


--
-- Name: governance_units governance_units_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_units
    ADD CONSTRAINT governance_units_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: governance_units governance_units_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_units
    ADD CONSTRAINT governance_units_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: governance_units governance_units_parent_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_units
    ADD CONSTRAINT governance_units_parent_unit_id_fkey FOREIGN KEY (parent_unit_id) REFERENCES public.governance_units(id) ON DELETE SET NULL;


--
-- Name: governance_units governance_units_program_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_units
    ADD CONSTRAINT governance_units_program_id_fkey FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE SET NULL;


--
-- Name: governance_units governance_units_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.governance_units
    ADD CONSTRAINT governance_units_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


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
-- Name: sanction_compliance_history sanction_compliance_history_complied_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_compliance_history
    ADD CONSTRAINT sanction_compliance_history_complied_by_user_id_fkey FOREIGN KEY (complied_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: sanction_compliance_history sanction_compliance_history_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_compliance_history
    ADD CONSTRAINT sanction_compliance_history_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE SET NULL;


--
-- Name: sanction_compliance_history sanction_compliance_history_sanction_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_compliance_history
    ADD CONSTRAINT sanction_compliance_history_sanction_item_id_fkey FOREIGN KEY (sanction_item_id) REFERENCES public.sanction_items(id) ON DELETE SET NULL;


--
-- Name: sanction_compliance_history sanction_compliance_history_sanction_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_compliance_history
    ADD CONSTRAINT sanction_compliance_history_sanction_record_id_fkey FOREIGN KEY (sanction_record_id) REFERENCES public.sanction_records(id) ON DELETE SET NULL;


--
-- Name: sanction_compliance_history sanction_compliance_history_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_compliance_history
    ADD CONSTRAINT sanction_compliance_history_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: sanction_compliance_history sanction_compliance_history_student_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_compliance_history
    ADD CONSTRAINT sanction_compliance_history_student_profile_id_fkey FOREIGN KEY (student_profile_id) REFERENCES public.student_profiles(id) ON DELETE SET NULL;


--
-- Name: sanction_delegations sanction_delegations_delegated_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_delegations
    ADD CONSTRAINT sanction_delegations_delegated_by_user_id_fkey FOREIGN KEY (delegated_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: sanction_delegations sanction_delegations_delegated_to_governance_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_delegations
    ADD CONSTRAINT sanction_delegations_delegated_to_governance_unit_id_fkey FOREIGN KEY (delegated_to_governance_unit_id) REFERENCES public.governance_units(id) ON DELETE CASCADE;


--
-- Name: sanction_delegations sanction_delegations_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_delegations
    ADD CONSTRAINT sanction_delegations_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: sanction_delegations sanction_delegations_revoked_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_delegations
    ADD CONSTRAINT sanction_delegations_revoked_by_user_id_fkey FOREIGN KEY (revoked_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: sanction_delegations sanction_delegations_sanction_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_delegations
    ADD CONSTRAINT sanction_delegations_sanction_config_id_fkey FOREIGN KEY (sanction_config_id) REFERENCES public.event_sanction_configs(id) ON DELETE SET NULL;


--
-- Name: sanction_delegations sanction_delegations_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_delegations
    ADD CONSTRAINT sanction_delegations_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: sanction_items sanction_items_sanction_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_items
    ADD CONSTRAINT sanction_items_sanction_record_id_fkey FOREIGN KEY (sanction_record_id) REFERENCES public.sanction_records(id) ON DELETE CASCADE;


--
-- Name: sanction_records sanction_records_assigned_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_records
    ADD CONSTRAINT sanction_records_assigned_by_user_id_fkey FOREIGN KEY (assigned_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: sanction_records sanction_records_attendance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_records
    ADD CONSTRAINT sanction_records_attendance_id_fkey FOREIGN KEY (attendance_id) REFERENCES public.attendances(id) ON DELETE SET NULL;


--
-- Name: sanction_records sanction_records_delegated_governance_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_records
    ADD CONSTRAINT sanction_records_delegated_governance_unit_id_fkey FOREIGN KEY (delegated_governance_unit_id) REFERENCES public.governance_units(id) ON DELETE SET NULL;


--
-- Name: sanction_records sanction_records_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_records
    ADD CONSTRAINT sanction_records_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE CASCADE;


--
-- Name: sanction_records sanction_records_sanction_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_records
    ADD CONSTRAINT sanction_records_sanction_config_id_fkey FOREIGN KEY (sanction_config_id) REFERENCES public.event_sanction_configs(id) ON DELETE SET NULL;


--
-- Name: sanction_records sanction_records_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_records
    ADD CONSTRAINT sanction_records_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: sanction_records sanction_records_student_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sanction_records
    ADD CONSTRAINT sanction_records_student_profile_id_fkey FOREIGN KEY (student_profile_id) REFERENCES public.student_profiles(id) ON DELETE CASCADE;


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
-- Name: ssg_announcements ssg_announcements_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_announcements
    ADD CONSTRAINT ssg_announcements_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: ssg_announcements ssg_announcements_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_announcements
    ADD CONSTRAINT ssg_announcements_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: ssg_events ssg_events_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_events
    ADD CONSTRAINT ssg_events_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: ssg_events ssg_events_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_events
    ADD CONSTRAINT ssg_events_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: ssg_events ssg_events_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_events
    ADD CONSTRAINT ssg_events_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: ssg_role_permissions ssg_role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_role_permissions
    ADD CONSTRAINT ssg_role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.ssg_permissions(id) ON DELETE CASCADE;


--
-- Name: ssg_role_permissions ssg_role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_role_permissions
    ADD CONSTRAINT ssg_role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.ssg_roles(id) ON DELETE CASCADE;


--
-- Name: ssg_roles ssg_roles_school_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_roles
    ADD CONSTRAINT ssg_roles_school_id_fkey FOREIGN KEY (school_id) REFERENCES public.schools(id) ON DELETE CASCADE;


--
-- Name: ssg_user_roles ssg_user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_user_roles
    ADD CONSTRAINT ssg_user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.ssg_roles(id) ON DELETE CASCADE;


--
-- Name: ssg_user_roles ssg_user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssg_user_roles
    ADD CONSTRAINT ssg_user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


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
-- Name: user_app_preferences user_app_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_app_preferences
    ADD CONSTRAINT user_app_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_face_profiles user_face_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_face_profiles
    ADD CONSTRAINT user_face_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


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

\unrestrict FSBslmRZXcjopnPtEGoQEACy3AJ4p3euRFas1e4n28hI4DnrKLgVeWlYk6NtX2B

