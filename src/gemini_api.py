import google.generativeai as genai
import logging
from google.api_core.exceptions import ResourceExhausted
from typing import Tuple
from src.utils import get_conf
from src.youtube_auth import get_authenticated_service
from youtube_transcript_api import YouTubeTranscriptApi


logger = logging.getLogger('faria_logger')

def setup_gemini_api():
    with open(get_conf('Paths', 'gemini_api_key'), 'r') as file:
        key = file.read()
        genai.configure(api_key=key)
        return genai.GenerativeModel('gemini-1.5-pro')


def get_video_details(video_id: str) -> Tuple[str, str]:
    request = get_authenticated_service().videos().list(part="snippet", id=video_id)
    response = request.execute()

    if not response['items']:
        raise ValueError(f"No video found with ID: {video_id}")

    video_info = response['items'][0]['snippet']
    title = video_info['title']
    description = video_info['description']

    return title, description


def get_youtube_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, ['it', 'en'])
        text = " ".join([item.text for item in transcript.snippets])
        return text
    except Exception as e:
        logger.error(f"Error getting transcript: {e}")
        return None


def summarize_text(text):
    logger.info("summarize_text")
    try:
        setup_gemini_api()
        model = genai.GenerativeModel("gemini-1.5-pro")
        prompt = f"""
            What follows is the transcript of a YouTube video, I want you to summarize it.
            Based on this summary I will decide if I want to watch the video or not.
            The summary should a least have a title, the list of tags, bullet points and a 
            brief conclusion where you add the "watch this video if" part explaining who and why should watch the video.
            Prefer short sentences over longer paragraphs, space out the text and use bullet points if possible.

            Transcript: {text}
            """
        response = model.generate_content(prompt)
        logger.info("summarize_text finished")
        return response.text
    except ResourceExhausted as e:
        logger.error(f"Quota exceeded")
        return None
    except Exception as e:
        logger.error(f"Error in summarize_text: {e}")
        return None

def extended_summarize_text(text):
    logger.info("extended_summarize_text")
    try:
        setup_gemini_api()
        model = genai.GenerativeModel("gemini-1.5-pro")
        prompt = f"""
            What follows is the transcript of a YouTube video, I want you to explain it in more detail.
            I do not want to read the whole transcript, but I want to know what the video is about 
            and get the most out of it with a 10 minute read at most.

            Transcript: {text}
            """
        response = model.generate_content(prompt)
        logger.info("extended_summarize_text finished")
        return response.text
    except ResourceExhausted as e:
        logger.error(f"Quota exceeded")
        return None
    except Exception as e:
        logger.error(f"Error in extended_summarize_text: {e}")
        return None
