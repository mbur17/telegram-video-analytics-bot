import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from app.db import db
from app.models import Video, VideoSnapshot

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_datetime(dt_str: str) -> datetime:
    formats = [
        '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError(f'Could not parse datetime: {dt_str}')


async def load_json_data(json_path: Path):
    logger.info(f'Loading data from {json_path}')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    videos_data = data.get('videos', data) if isinstance(data, dict) else data
    logger.info(f'Found {len(videos_data)} videos in JSON')
    db.init()
    async with db.session() as session:
        video_count = 0
        snapshot_count = 0
        for video_data in videos_data:
            video = Video(
                id=str(video_data['id']),
                creator_id=str(video_data['creator_id']),
                video_created_at=parse_datetime(
                    video_data['video_created_at']
                ),
                views_count=video_data.get('views_count', 0),
                likes_count=video_data.get('likes_count', 0),
                comments_count=video_data.get('comments_count', 0),
                reports_count=video_data.get('reports_count', 0),
                created_at=parse_datetime(video_data['created_at']),
                updated_at=parse_datetime(video_data['updated_at'])
            )
            session.add(video)
            video_count += 1
            for snapshot_data in video_data.get('snapshots', []):
                snapshot = VideoSnapshot(
                    id=str(snapshot_data['id']),
                    video_id=str(video_data['id']),
                    views_count=snapshot_data.get('views_count', 0),
                    likes_count=snapshot_data.get('likes_count', 0),
                    comments_count=snapshot_data.get('comments_count', 0),
                    reports_count=snapshot_data.get('reports_count', 0),
                    delta_views_count=snapshot_data.get(
                        'delta_views_count', 0
                    ),
                    delta_likes_count=snapshot_data.get(
                        'delta_likes_count', 0
                    ),
                    delta_comments_count=snapshot_data.get(
                        'delta_comments_count', 0
                    ),
                    delta_reports_count=snapshot_data.get(
                        'delta_reports_count', 0
                    ),
                    created_at=parse_datetime(snapshot_data['created_at']),
                    updated_at=parse_datetime(snapshot_data['updated_at'])
                )
                session.add(snapshot)
                snapshot_count += 1
        await session.commit()
        logger.info(
            f'Loaded {video_count} videos and {snapshot_count} snapshots'
        )
    await db.close()


async def main():
    json_path = Path('data/videos.json')

    if not json_path.exists():
        logger.error(f'JSON file not found: {json_path}')
        logger.info('Please place videos.json in the data/ directory')
        return

    try:
        await load_json_data(json_path)
        logger.info('Data loading completed successfully')
    except Exception as e:
        logger.error(f'Error loading data: {e}', exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
