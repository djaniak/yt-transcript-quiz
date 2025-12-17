from youtube_transcript_api import YouTubeTranscriptApi
from pytube import Playlist
from typing import List, Dict, Optional
import re

def extract_video_id(url: str) -> Optional[str]:
    """Extracts video ID from a YouTube URL."""
    # Shortened URL
    match = re.search(r"youtu\.be\/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    
    # Standard URL
    match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
        
    return None

def get_transcript(video_id: str) -> str:
    """Fetches the transcript for a given video ID, preferring manual but falling back to auto-generated."""
    try:
        # YouTubeTranscriptApi must be instantiated to use .list_transcripts or .get_transcript 
        # (based on our debugging, though documentation usually says static, the local version behaves like this)
        # However, purely based on standard docs, it's static. But our debug showed `AttributeError` on static.
        # Wait, our debug `test_instantiation.py` showed:
        # "Instance has no get_transcript"
        # "Calling api.list(video_id)... Success list"
        # So we should use `api.list(video_id)` which returns a TranscriptList.
        
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        
        # logical preference: Manual English -> Manual Any -> Generated English -> Generated Any
        
        transcript = None
        
        # Try to find a manually created English transcript
        try:
             transcript = transcript_list.find_manually_created_transcript(['en'])
        except:
            pass
            
        # If no manual English, look for any manual
        if not transcript:
            try:
                # We can iterate to find the first manual, but strict logic usually prefers English.
                # Let's try to get *any* generated if manual fails.
                # Actually, let's just use the powerful .find_transcript method with a list of prefs
                # But .find_transcript searches for specific languages.
                pass
            except:
                pass

        # Simplification: Use the helper to find 'en' or auto-en
        # .find_transcript(['en']) will return manual or generated if we don't specify otherwise?
        # Actually .find_transcript(['en']) finds 'en'. 
        # If we want to accept generated, we might need to look specifically.
        
        if not transcript:
            try:
                 transcript = transcript_list.find_generated_transcript(['en'])
            except:
                pass
        
        # Valid fallback: any manual, then any generated
        if not transcript:
            # Iterating to find any manual?
            for t in transcript_list:
                if not t.is_generated:
                    transcript = t
                    break
        
        if not transcript:
            # Fallback to any generated (e.g. auto-translated or just the first one)
             for t in transcript_list:
                if t.is_generated:
                    transcript = t
                    break

        if not transcript:
            print(f"No suitable transcript found for {video_id}")
            return ""

        # Fetch the actual content
        fetched_transcript = transcript.fetch()
        
        # Combine all text parts
        full_text = " ".join([item.text for item in fetched_transcript])
        return full_text

    except Exception as e:
        print(f"Error fetching transcript for {video_id}: {e}")
        return ""

def get_playlist_videos(playlist_url: str) -> List[str]:
    """Returns a list of video IDs from a playlist."""
    try:
        playlist = Playlist(playlist_url)
        # Pytube's playlist.video_urls gives full URLs, we need IDs
        video_ids = []
        for url in playlist.video_urls:
            vid = extract_video_id(url)
            if vid:
                video_ids.append(vid)
        return video_ids
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return []
