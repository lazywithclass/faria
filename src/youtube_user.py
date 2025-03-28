from googleapiclient.errors import HttpError
from src.utils import get_conf


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


def get_subscription_feed(youtube):
    max_results_per_channel = get_conf('API', 'max_videos_to_fetch_per_channel')
    feed_videos = []
    channel_ids = get_subscriptions(youtube)

    for channel_id in channel_ids:
        try:
            channels_response = youtube.channels().list(
                part="contentDetails",
                id=channel_id,
                maxResults=max_results_per_channel
            ).execute()

            if not channels_response.get('items'):
                continue

            uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            playlist_response = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=max_results_per_channel
            ).execute()

            # Extract video IDs from playlist items
            video_ids = [item['snippet']['resourceId']['videoId']
                         for item in playlist_response.get('items', [])]

            if video_ids:
                # Get video details including duration
                videos_response = youtube.videos().list(
                    part="contentDetails",
                    id=','.join(video_ids)
                ).execute()

                # Create a mapping of video ID to duration
                durations = {item['id']: item['contentDetails']['duration']
                             for item in videos_response.get('items', [])}

                for item in playlist_response.get('items', []):
                    video_id = item['snippet']['resourceId']['videoId']
                    video_data = {
                        'id': video_id,
                        'title': item['snippet']['title'],
                        'channel': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt'],
                        'duration': _format_duration(durations.get(video_id, ''))
                    }
                    feed_videos.append(video_data)

        except Exception as e:
            print(f"Error fetching videos for channel {channel_id}: {e}")
            continue

    feed_videos.sort(key=lambda x: x['published_at'], reverse=True)

    print(f"Found {len(feed_videos)} videos in subscription feed")
    return feed_videos


def filter_watched_videos(feed_videos, watched_video_ids):
    unwatched_videos = []

    for video in feed_videos:
        if video['id'] not in watched_video_ids:
            unwatched_videos.append(video)

    print(f"Found {len(unwatched_videos)} unwatched videos out of {len(feed_videos)} total videos")
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