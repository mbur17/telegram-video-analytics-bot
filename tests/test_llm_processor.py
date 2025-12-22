import pytest

from app.llm_processor import LLMProcessor


@pytest.fixture
def llm_processor():
    return LLMProcessor()


class TestSQLValidation:

    def test_valid_select_query(self, llm_processor):
        sql = 'SELECT COUNT(*) FROM videos;'
        assert llm_processor.validate_sql(sql) is True

    def test_select_with_where(self, llm_processor):
        sql = 'SELECT COUNT(*) FROM videos WHERE creator_id = \'abc123\';'
        assert llm_processor.validate_sql(sql) is True

    def test_select_with_join(self, llm_processor):
        sql = '''
        SELECT COUNT(DISTINCT vs.video_id)
        FROM video_snapshots vs
        JOIN videos v ON vs.video_id = v.id
        WHERE vs.delta_views_count > 0;
        '''
        assert llm_processor.validate_sql(sql) is True

    def test_reject_delete(self, llm_processor):
        sql = 'DELETE FROM videos WHERE id = \'123\';'
        assert llm_processor.validate_sql(sql) is False

    def test_reject_drop(self, llm_processor):
        sql = 'DROP TABLE videos;'
        assert llm_processor.validate_sql(sql) is False

    def test_reject_insert(self, llm_processor):
        sql = 'INSERT INTO videos (id) VALUES (\'123\');'
        assert llm_processor.validate_sql(sql) is False

    def test_reject_update(self, llm_processor):
        sql = 'UPDATE videos SET views_count = 0;'
        assert llm_processor.validate_sql(sql) is False

    def test_reject_create(self, llm_processor):
        sql = 'CREATE TABLE test (id INT);'
        assert llm_processor.validate_sql(sql) is False


class TestResponseCleaning:

    def test_clean_simple_sql(self, llm_processor):
        sql = 'SELECT COUNT(*) FROM videos'
        result = llm_processor._clean_sql_response(sql)
        assert result == 'SELECT COUNT(*) FROM videos;'

    def test_clean_sql_with_backticks(self, llm_processor):
        sql = '```sql\nSELECT COUNT(*) FROM videos\n```'
        result = llm_processor._clean_sql_response(sql)
        assert result == 'SELECT COUNT(*) FROM videos;'

    def test_clean_sql_with_semicolon(self, llm_processor):
        sql = 'SELECT COUNT(*) FROM videos;'
        result = llm_processor._clean_sql_response(sql)
        assert result == 'SELECT COUNT(*) FROM videos;'

    def test_clean_multiline_sql(self, llm_processor):
        sql = '''Here is the query:
        SELECT COUNT(*) FROM videos
        That's it.'''
        result = llm_processor._clean_sql_response(sql)
        assert result == 'SELECT COUNT(*) FROM videos;'

    def test_clean_llama_tokens(self, llm_processor):
        sql = '<s>SELECT COUNT(*) FROM videos</s>'
        result = llm_processor._clean_sql_response(sql)
        assert result == 'SELECT COUNT(*) FROM videos;'


class TestDateTranslation:

    def test_translate_november(self, llm_processor):
        query = 'Сколько видео вышло 28 ноября 2025?'
        result = llm_processor._translate_russian_dates(query)
        assert '2025-11-28' in result

    def test_translate_december(self, llm_processor):
        query = 'Видео от 15 декабря 2025'
        result = llm_processor._translate_russian_dates(query)
        assert '2025-12-15' in result

    def test_no_translation_needed(self, llm_processor):
        query = 'Сколько всего видео?'
        result = llm_processor._translate_russian_dates(query)
        assert result == query
