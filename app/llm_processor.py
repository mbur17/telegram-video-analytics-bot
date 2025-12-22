import logging
import re

from ollama import AsyncClient
from sqlglot import exp, parse_one

from app.config import settings

logger = logging.getLogger(__name__)


# Database schema description for SQLCoder
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


class LLMProcessor:
    """Process natural language queries using Ollama + SQLCoder."""

    def __init__(self):
        self.model = settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL
        self.client = AsyncClient(host=self.base_url)
        logger.info(f'Using Ollama at {self.base_url} with model {self.model}')

    def _translate_russian_dates(self, query: str) -> str:
        months = {
            'января': '01', 'февраля': '02', 'марта': '03',
            'апреля': '04', 'мая': '05', 'июня': '06',
            'июля': '07', 'августа': '08', 'сентября': '09',
            'октября': '10', 'ноября': '11', 'декабря': '12'
        }
        result = query
        for ru_month, num in months.items():
            # Pattern: "28 ноября 2025" -> "2025-11-28"
            pattern = rf'(\d{{1,2}})\s+{ru_month}\s+(\d{{4}})'
            result = re.sub(pattern, r'\2-' + num + r'-\1', result)
        return result

    def _build_prompt(self, user_query: str) -> str:
        query_translated = self._translate_russian_dates(user_query)

        prompt = f'''
### Task
Generate a SQL query to answer the following question: `{query_translated}`
The question may be written in Russian.
First, mentally translate it to English, then generate SQL.

### Database Schema
{DATABASE_SCHEMA}

### Instructions
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

### Examples
Question: "How many videos are there?"
SQL: SELECT COUNT(*) FROM videos

Question: "How many videos got more than 100000 views?"
SQL: SELECT COUNT(*) FROM videos WHERE views_count > 100000

Question: "How much did views grow on 2025-11-28?"
SQL: SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE DATE(created_at) = '2025-11-28'

Question: "How many videos received new views on 2025-11-27?"
SQL: SELECT COUNT(DISTINCT video_id) FROM video_snapshots WHERE DATE(created_at) = '2025-11-27' AND delta_views_count > 0

### SQL Query
'''  # noqa: E501

        return prompt

    def _clean_sql_response(self, sql: str) -> str:
        # Remove markdown and llama tokens
        sql = re.sub(
            r'```(?:sql)?|</?s>', '', sql, flags=re.IGNORECASE
        ).strip()
        match = re.search(
            r'(SELECT\b.*?)(?:\n\s*[A-Z][a-z].*|$)',
            sql,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return ''
        cleaned = ' '.join(match.group(1).split())
        return cleaned.rstrip(';') + ';'

    def validate_sql(self, sql: str) -> bool:
        try:
            expr = parse_one(sql, read='postgres')
        except Exception:
            return False
        # Must be SELECT-like
        if not isinstance(expr, (exp.Select, exp.Subquery, exp.With)):
            return False
        # Only read-only operations
        forbidden = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Create,
            exp.Drop,
            exp.Alter,
            exp.Command,
        )
        for node in expr.walk():
            if isinstance(node, forbidden):
                return False
        return True

    async def text_to_sql(self, user_query: str) -> str:
        """Convert natural language query to SQL using Ollama + SQLCoder."""
        logger.info(f'Processing query: {user_query}')
        try:
            prompt = self._build_prompt(user_query)
            logger.info(f'Sending request to Ollama ({self.model})...')
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.1,
                    'top_p': 0.9,
                }
            )
            logger.warning('RAW LLM RESPONSE:\n%s', response)
            raw_text = response.get('response', '')
            sql = self._clean_sql_response(raw_text)
            logger.warning('CLEANED SQL:\n%s', sql)
            if not self.validate_sql(sql):
                raise ValueError('Generated SQL query failed validation')
            logger.info(f'Generated SQL: {sql}')
            return sql
        except Exception as e:
            logger.error(f'Error processing query: {e}', exc_info=True)
            raise


llm_processor = LLMProcessor()
