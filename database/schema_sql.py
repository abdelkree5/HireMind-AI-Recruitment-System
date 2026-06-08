from __future__ import annotations


def build_schema_script(dialect: str) -> str:
    interview_turns_pk = (
        "BIGSERIAL PRIMARY KEY" if dialect == "postgresql" else "INTEGER PRIMARY KEY AUTOINCREMENT"
    )

    # pgvector extension — best-effort, non-fatal if unavailable
    _vector_ext = ""
    if dialect == "postgresql":
        _vector_ext = """
    DO $$ BEGIN
        CREATE EXTENSION IF NOT EXISTS vector;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'pgvector extension not available, skipping';
    END $$;
    """

    return f"""
    {_vector_ext}

    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL,
        company_name TEXT NOT NULL DEFAULT '',
        password_salt TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_login_at TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

    CREATE TABLE IF NOT EXISTS auth_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        revoked_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_auth_sessions_token_hash ON auth_sessions(token_hash);
    CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires_at ON auth_sessions(expires_at);

    CREATE TABLE IF NOT EXISTS posted_jobs (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        required_skills TEXT NOT NULL,
        responsibilities TEXT NOT NULL DEFAULT '[]',
        preferred_skills TEXT NOT NULL DEFAULT '[]',
        tools TEXT NOT NULL DEFAULT '[]',
        experience_level TEXT NOT NULL DEFAULT '',
        domain TEXT NOT NULL DEFAULT '',
        hiring_rules TEXT NOT NULL DEFAULT '{{}}',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS job_applications (
        id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL,
        candidate_name TEXT NOT NULL,
        candidate_headline TEXT NOT NULL,
        candidate_skills TEXT NOT NULL,
        match_score REAL NOT NULL,
        missing_skills TEXT NOT NULL,
        score_breakdown TEXT NOT NULL,
        feedback TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (job_id) REFERENCES posted_jobs(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_job_applications_job_id ON job_applications(job_id);
    CREATE INDEX IF NOT EXISTS idx_job_applications_match_score ON job_applications(match_score);
    CREATE INDEX IF NOT EXISTS idx_job_applications_created_at ON job_applications(created_at);

    CREATE TABLE IF NOT EXISTS interview_sessions (
        id TEXT PRIMARY KEY,
        application_id TEXT NOT NULL,
        job_id TEXT NOT NULL,
        candidate_name TEXT NOT NULL,
        status TEXT NOT NULL,
        total_questions INTEGER NOT NULL,
        current_question_index INTEGER NOT NULL,
        questions_json TEXT NOT NULL,
        candidate_profile_json TEXT NOT NULL DEFAULT '{{}}',
        answer_history_json TEXT NOT NULL DEFAULT '[]',
        difficulty_level TEXT NOT NULL DEFAULT 'medium',
        final_score REAL,
        final_recommendation TEXT,
        started_at TEXT NOT NULL,
        completed_at TEXT,
        FOREIGN KEY (application_id) REFERENCES job_applications(id) ON DELETE CASCADE,
        FOREIGN KEY (job_id) REFERENCES posted_jobs(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS interview_turns (
        id {interview_turns_pk},
        session_id TEXT NOT NULL,
        question_index INTEGER NOT NULL,
        question_text TEXT NOT NULL,
        candidate_answer TEXT NOT NULL,
        answer_score REAL NOT NULL,
        feedback TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_interview_sessions_application_id ON interview_sessions(application_id);
    CREATE INDEX IF NOT EXISTS idx_interview_turns_session_id ON interview_turns(session_id);

    CREATE TABLE IF NOT EXISTS recruiter_feedback (
        id TEXT PRIMARY KEY,
        application_id TEXT NOT NULL,
        candidate_id TEXT NOT NULL,
        job_id TEXT NOT NULL,
        ai_score REAL NOT NULL,
        candidate_rank INTEGER,
        recruiter_decision TEXT NOT NULL,
        is_accepted INTEGER NOT NULL DEFAULT 0,
        is_hired INTEGER NOT NULL DEFAULT 0,
        recruiter_notes TEXT DEFAULT '',
        rejection_reason TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        FOREIGN KEY (application_id) REFERENCES job_applications(id) ON DELETE CASCADE,
        FOREIGN KEY (job_id) REFERENCES posted_jobs(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_recruiter_feedback_application_id ON recruiter_feedback(application_id);
    CREATE INDEX IF NOT EXISTS idx_recruiter_feedback_job_id ON recruiter_feedback(job_id);

    CREATE TABLE IF NOT EXISTS recruiter_memory (
        id TEXT PRIMARY KEY,
        recruiter_id TEXT NOT NULL,
        preference_text TEXT NOT NULL,
        embedding vector(384),
        created_at TEXT NOT NULL,
        FOREIGN KEY (recruiter_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_recruiter_memory_recruiter_id ON recruiter_memory(recruiter_id);

    CREATE TABLE IF NOT EXISTS dynamic_skill_weights (
        job_id TEXT NOT NULL,
        skill_name TEXT NOT NULL,
        weight_offset REAL NOT NULL DEFAULT 0.0,
        rejection_count INTEGER NOT NULL DEFAULT 0,
        hire_count INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (job_id, skill_name)
    );

    CREATE TABLE IF NOT EXISTS agent_memory_stm (
        workflow_id TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL DEFAULT '{{}}',
        expires_at TEXT NOT NULL,
        PRIMARY KEY (workflow_id, key)
    );

    CREATE TABLE IF NOT EXISTS agent_memory_ltm (
        job_id TEXT NOT NULL,
        memory_type TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL DEFAULT '{{}}',
        updated_at TEXT NOT NULL,
        PRIMARY KEY (job_id, memory_type, key)
    );

    CREATE TABLE IF NOT EXISTS agent_episodes (
        id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL,
        candidate_id TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        event TEXT NOT NULL,
        outcome TEXT NOT NULL DEFAULT '{{}}',
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_agent_episodes_candidate ON agent_episodes(candidate_id);
    CREATE INDEX IF NOT EXISTS idx_agent_episodes_job ON agent_episodes(job_id);

    CREATE TABLE IF NOT EXISTS agent_traces (
        id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL,
        trace_id TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        task_type TEXT NOT NULL,
        input_summary TEXT NOT NULL DEFAULT '',
        output_summary TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'running',
        latency_ms REAL NOT NULL DEFAULT 0.0,
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_agent_traces_workflow ON agent_traces(workflow_id);
    CREATE INDEX IF NOT EXISTS idx_agent_traces_agent ON agent_traces(agent_name);

    CREATE TABLE IF NOT EXISTS agent_messages (
        id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL,
        sender_agent TEXT NOT NULL,
        receiver_agent TEXT NOT NULL,
        task_type TEXT NOT NULL,
        payload_json TEXT NOT NULL DEFAULT '{{}}',
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_agent_messages_workflow ON agent_messages(workflow_id);
    CREATE INDEX IF NOT EXISTS idx_agent_messages_receiver ON agent_messages(receiver_agent);

    CREATE TABLE IF NOT EXISTS domain_events (
        id TEXT PRIMARY KEY,
        workflow_id TEXT,
        event_type TEXT NOT NULL,
        aggregate_id TEXT NOT NULL,
        payload_json TEXT NOT NULL DEFAULT '{{}}',
        metadata_json TEXT NOT NULL DEFAULT '{{}}',
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_domain_events_workflow ON domain_events(workflow_id);
    CREATE INDEX IF NOT EXISTS idx_domain_events_type ON domain_events(event_type);

    -- ==========================================================
    -- AI Recruiting OS — Phase 1: Candidate AI Ecosystem
    -- ==========================================================

    CREATE TABLE IF NOT EXISTS career_assessments (
        id TEXT PRIMARY KEY,
        candidate_id TEXT NOT NULL,
        assessment_type TEXT NOT NULL,
        target_role TEXT NOT NULL DEFAULT '',
        result_json TEXT NOT NULL DEFAULT '{{}}',
        created_at TEXT NOT NULL,
        FOREIGN KEY (candidate_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_career_assessments_candidate ON career_assessments(candidate_id);
    CREATE INDEX IF NOT EXISTS idx_career_assessments_type ON career_assessments(assessment_type);

    CREATE TABLE IF NOT EXISTS generated_cvs (
        id TEXT PRIMARY KEY,
        candidate_id TEXT NOT NULL,
        format_type TEXT NOT NULL,
        input_sources_json TEXT NOT NULL DEFAULT '{{}}',
        output_content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (candidate_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_generated_cvs_candidate ON generated_cvs(candidate_id);

    -- ==========================================================
    -- AI Recruiting OS — Phase 2: Advanced Interview Intelligence
    -- ==========================================================

    CREATE TABLE IF NOT EXISTS coding_challenges (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        problem_json TEXT NOT NULL,
        submitted_code TEXT,
        evaluation_json TEXT NOT NULL DEFAULT '{{}}',
        complexity_analysis TEXT NOT NULL DEFAULT '',
        score REAL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_coding_challenges_session ON coding_challenges(session_id);

    CREATE TABLE IF NOT EXISTS behavioral_assessments (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        dimension TEXT NOT NULL,
        score REAL NOT NULL,
        evidence_json TEXT NOT NULL DEFAULT '{{}}',
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_behavioral_assessments_session ON behavioral_assessments(session_id);

    -- ==========================================================
    -- AI Recruiting OS — Phase 3: Recruiting Automation
    -- ==========================================================

    CREATE TABLE IF NOT EXISTS outreach_messages (
        id TEXT PRIMARY KEY,
        candidate_id TEXT NOT NULL,
        job_id TEXT NOT NULL,
        channel TEXT NOT NULL,
        message_content TEXT NOT NULL,
        sequence_position INTEGER NOT NULL DEFAULT 1,
        status TEXT NOT NULL DEFAULT 'draft',
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_outreach_messages_candidate ON outreach_messages(candidate_id);
    CREATE INDEX IF NOT EXISTS idx_outreach_messages_job ON outreach_messages(job_id);

    CREATE TABLE IF NOT EXISTS workflow_definitions (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        trigger_event TEXT NOT NULL,
        steps_json TEXT NOT NULL DEFAULT '[]',
        is_active INTEGER NOT NULL DEFAULT 1,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS workflow_executions (
        id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL,
        trigger_data_json TEXT NOT NULL DEFAULT '{{}}',
        status TEXT NOT NULL DEFAULT 'running',
        steps_completed INTEGER NOT NULL DEFAULT 0,
        result_json TEXT NOT NULL DEFAULT '{{}}',
        started_at TEXT NOT NULL,
        completed_at TEXT,
        FOREIGN KEY (workflow_id) REFERENCES workflow_definitions(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow ON workflow_executions(workflow_id);
    CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);

    -- ==========================================================
    -- AI Recruiting OS — Phase 4: Agentic Intelligence
    -- ==========================================================

    CREATE TABLE IF NOT EXISTS debate_sessions (
        id TEXT PRIMARY KEY,
        candidate_id TEXT NOT NULL,
        job_id TEXT NOT NULL,
        participants_json TEXT NOT NULL DEFAULT '[]',
        rounds_json TEXT NOT NULL DEFAULT '[]',
        consensus_json TEXT NOT NULL DEFAULT '{{}}',
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_debate_sessions_candidate ON debate_sessions(candidate_id);
    CREATE INDEX IF NOT EXISTS idx_debate_sessions_job ON debate_sessions(job_id);

    CREATE TABLE IF NOT EXISTS agent_reflections (
        id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        finding_type TEXT NOT NULL,
        description TEXT NOT NULL,
        severity TEXT NOT NULL DEFAULT 'low',
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_agent_reflections_workflow ON agent_reflections(workflow_id);

    -- ==========================================================
    -- AI Recruiting OS — Phase 5: Market Intelligence
    -- ==========================================================

    CREATE TABLE IF NOT EXISTS market_snapshots (
        id TEXT PRIMARY KEY,
        snapshot_type TEXT NOT NULL,
        data_json TEXT NOT NULL DEFAULT '{{}}',
        period TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_market_snapshots_type ON market_snapshots(snapshot_type);

    -- ==========================================================
    -- AI Recruiting OS — Phase 6: Analytics
    -- ==========================================================

    CREATE TABLE IF NOT EXISTS analytics_cache (
        id TEXT PRIMARY KEY,
        metric_type TEXT NOT NULL,
        scope TEXT NOT NULL DEFAULT 'global',
        scope_id TEXT NOT NULL DEFAULT '',
        value_json TEXT NOT NULL DEFAULT '{{}}',
        computed_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_analytics_cache_type ON analytics_cache(metric_type);

    -- ==========================================================
    -- AI Recruiting OS — Phase 7: Plugin Ecosystem
    -- ==========================================================

    CREATE TABLE IF NOT EXISTS installed_plugins (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        version TEXT NOT NULL,
        manifest_json TEXT NOT NULL DEFAULT '{{}}',
        is_active INTEGER NOT NULL DEFAULT 1,
        installed_at TEXT NOT NULL
    );
    """


def build_postgres_rollback_script() -> list[str]:
    return [
        # Phase 7
        "DROP TABLE IF EXISTS installed_plugins",
        # Phase 6
        "DROP TABLE IF EXISTS analytics_cache",
        # Phase 5
        "DROP TABLE IF EXISTS market_snapshots",
        # Phase 4
        "DROP TABLE IF EXISTS agent_reflections",
        "DROP TABLE IF EXISTS debate_sessions",
        # Phase 3
        "DROP TABLE IF EXISTS workflow_executions",
        "DROP TABLE IF EXISTS workflow_definitions",
        "DROP TABLE IF EXISTS outreach_messages",
        # Phase 2
        "DROP TABLE IF EXISTS behavioral_assessments",
        "DROP TABLE IF EXISTS coding_challenges",
        # Phase 1
        "DROP TABLE IF EXISTS generated_cvs",
        "DROP TABLE IF EXISTS career_assessments",
        # Original tables
        "DROP TABLE IF EXISTS domain_events",
        "DROP TABLE IF EXISTS agent_messages",
        "DROP TABLE IF EXISTS agent_traces",
        "DROP TABLE IF EXISTS agent_episodes",
        "DROP TABLE IF EXISTS agent_memory_ltm",
        "DROP TABLE IF EXISTS agent_memory_stm",
        "DROP TABLE IF EXISTS recruiter_memory",
        "DROP TABLE IF EXISTS dynamic_skill_weights",
        "DROP TABLE IF EXISTS recruiter_feedback",
        "DROP TABLE IF EXISTS interview_turns",
        "DROP TABLE IF EXISTS interview_sessions",
        "DROP TABLE IF EXISTS job_applications",
        "DROP TABLE IF EXISTS posted_jobs",
        "DROP TABLE IF EXISTS auth_sessions",
        "DROP TABLE IF EXISTS users",
    ]