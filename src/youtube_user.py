import logging

from src.utils import get_conf


logger = logging.getLogger('faria_logger')
MAX_RESULTS_PER_PAGE = get_conf('API', 'max_results_per_page')

def get_subscriptions(youtube):
    channel_ids = []
    next_page_token = None

    while True:
        subscription_response = youtube.subscriptions().list(
            part='snippet',
            mine=True,
            maxResults=MAX_RESULTS_PER_PAGE,
            pageToken=next_page_token
        ).execute()

        for item in subscription_response['items']:
            channel_ids.append(item['snippet']['resourceId']['channelId'])

        next_page_token = subscription_response.get('nextPageToken')
        if not next_page_token:
            break

    return channel_ids


# TODO this should only get videos that are after the last uploaded for each channel
def get_subscription_feed(youtube, db=None):
    feed_videos = []
    channel_ids = get_subscriptions(youtube)

    # Get list of videos to exclude (watched or disliked)
    excluded_ids = []
    if db:
        excluded_ids = db.get_watched_video_ids() + db.get_disliked_video_ids()

    for channel_id in channel_ids:
        try:
            logger.info(f"Fetching videos for channel {channel_id}")
            # Get channel uploads playlist
            channels_response = youtube.channels().list(
                part="contentDetails",
                id=channel_id
            ).execute()

            if not channels_response.get('items'):
                continue

            uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            # Variables for pagination
            next_page_token = None
            channel_videos = []

            # Loop to get all videos from the playlist using pagination
            while True:
                # Get videos from playlist with date filter
                playlist_response = youtube.playlistItems().list(
                    part="snippet",
                    playlistId=uploads_playlist_id,
                    maxResults=50,  # Maximum allowed by API
                    pageToken=next_page_token
                ).execute()

                for item in playlist_response.get('items', []):
                    video_id = item['snippet']['resourceId']['videoId']
                    if video_id not in excluded_ids:
                        channel_videos.append({
                            'id': video_id,
                            'title': item['snippet']['title'],
                            'channel': item['snippet']['channelTitle'],
                            'published_at': item['snippet']['publishedAt'],
                            'duration': ''  # will be populated later
                        })

                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break

            if channel_videos:
                video_ids = [video['id'] for video in channel_videos]
                all_durations = {}

                for i in range(0, len(video_ids), 50):
                    batch = video_ids[i:i + 50]
                    videos_response = youtube.videos().list(
                        part="contentDetails",
                        id=','.join(batch)
                    ).execute()

                    batch_durations = {item['id']: item['contentDetails']['duration']
                                       for item in videos_response.get('items', [])}
                    all_durations.update(batch_durations)

                for video in channel_videos:
                    video['duration'] = _format_duration(all_durations.get(video['id'], ''))

                feed_videos.extend(channel_videos)

        except Exception as e:
            logger.error(f"Error fetching videos for channel {channel_id}: {e}")
            continue

    feed_videos.sort(key=lambda x: x['published_at'], reverse=True)
    return feed_videos


def filter_watched_videos(feed_videos, watched_video_ids):
    unwatched_videos = []
    for video in feed_videos:
        if video['id'] not in watched_video_ids:
            unwatched_videos.append(video)
    return unwatched_videos


def _format_duration(iso_duration):
    """Convert ISO 8601 duration format (PT#H#M#S) to human-readable MM:SS or HH:MM:SS"""
    if not iso_duration:
        return ""

    import re

    hours_match = re.search(r'(\d+)H', iso_duration)
    minutes_match = re.search(r'(\d+)M', iso_duration)
    seconds_match = re.search(r'(\d+)S', iso_duration)

    hours = int(hours_match.group(1)) if hours_match else 0
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    seconds = int(seconds_match.group(1)) if seconds_match else 0

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"