# Models
DEFAULT_ZERO = 0
MAX_VID_ID = 36
MAX_SNAP_ID = 32
MAX_CREATOR_ID = 32

# LLM
DATABASE_SCHEMA = '''
CREATE TABLE videos (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    creator_id VARCHAR(32) NOT NULL,  -- MD5 hash
    video_created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    views_count BIGINT NOT NULL DEFAULT 0,
    likes_count BIGINT NOT NULL DEFAULT 0,
    comments_count BIGINT NOT NULL DEFAULT 0,
    reports_count BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE video_snapshots (
    id VARCHAR(32) PRIMARY KEY,  -- MD5 hash
    video_id VARCHAR(36) NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    views_count BIGINT NOT NULL DEFAULT 0,
    likes_count BIGINT NOT NULL DEFAULT 0,
    comments_count BIGINT NOT NULL DEFAULT 0,
    reports_count BIGINT NOT NULL DEFAULT 0,
    delta_views_count BIGINT NOT NULL DEFAULT 0,
    delta_likes_count BIGINT NOT NULL DEFAULT 0,
    delta_comments_count BIGINT NOT NULL DEFAULT 0,
    delta_reports_count BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Indexes
CREATE INDEX idx_videos_creator_id ON videos(creator_id);
CREATE INDEX idx_videos_video_created_at ON videos(video_created_at);
CREATE INDEX idx_video_snapshots_video_id ON video_snapshots(video_id);
CREATE INDEX idx_video_snapshots_created_at ON video_snapshots(created_at);
CREATE INDEX idx_video_snapshots_video_created ON video_snapshots(video_id, created_at);
'''  # noqa: E501

EXAMPLES = '''
Question: "How many videos are there?"
SQL: SELECT COUNT(*) FROM videos
Question: "How many videos got more than 100000 views?"
SQL: SELECT COUNT(*) FROM videos WHERE views_count > 100000
Question: "How much did views grow on 2025-11-28?"
SQL: SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE DATE(created_at) = '2025-11-28'
Question: "How many videos received new views on 2025-11-27?"
SQL: SELECT COUNT(DISTINCT video_id) FROM video_snapshots WHERE DATE(created_at) = '2025-11-27' AND delta_views_count > 0
'''  # noqa: E501

RULES = '''
- Return ONLY the SQL query, nothing else
- The query must return a single number
- Use COALESCE(SUM(...), 0) or COALESCE(COUNT(...), 0) to handle NULL values
- For date filtering, use DATE(created_at) = 'YYYY-MM-DD' format
- creator_id and video_id are strings, use single quotes: 'abc123'
- Use table "videos" for final statistics (total views, likes, etc)
- Use table "video_snapshots" for growth/delta queries
- For "how many videos received views on date X": SELECT COUNT(DISTINCT video_id) FROM video_snapshots WHERE DATE(created_at) = 'X' AND delta_views_count > 0
- For "how much did views grow on date X": SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE DATE(created_at) = 'X'
- Never use JOIN unless explicitly required
- Only use tables listed in the schema
- Do not invent columns
'''  # noqa: E501
