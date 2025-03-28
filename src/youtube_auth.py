import logging
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from src.utils import get_conf


logger = logging.getLogger('faria_logger')


def get_authenticated_service():
    try:
        credentials = None
        auth_token_path = get_conf('Paths', 'auth_token')
        client_secret_path = get_conf('Paths', 'client_secret')

        # Token file stores the user's credentials from previously successful logins
        if os.path.exists(auth_token_path):
            with open(auth_token_path, 'rb') as token:
                credentials = pickle.load(token)

        # If credentials are invalid or don't exist, log in.
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except Exception as e:
                    # If refresh fails, force a new authorization flow
                    if "invalid_grant" in str(e) or "Token has been expired or revoked" in str(e):
                        logger.info("Refresh token expired or revoked. Starting new auth flow.")
                        credentials = None
                    else:
                        raise

            # If credentials still None, run the full auth flow
            if not credentials or not credentials.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secret_path,
                    ['https://www.googleapis.com/auth/youtube.readonly', 'https://www.googleapis.com/auth/youtube'])
                credentials = flow.run_local_server(port=8080)

            # Save the credentials for the next run
            with open(auth_token_path, 'wb') as token:
                pickle.dump(credentials, token)

        return build('youtube', 'v3', credentials=credentials)
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None