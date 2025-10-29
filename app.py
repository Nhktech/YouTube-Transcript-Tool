import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re

st.title("🎬 YouTube Transcript Generator")

url = st.text_input("Enter YouTube Video URL:")

def get_video_id(url):
    video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return video_id_match.group(1) if video_id_match else None

if url:
    video_id = get_video_id(url)
    if not video_id:
        st.error("Invalid YouTube URL.")
    else:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            text = " ".join([t['text'] for t in transcript])
            st.text_area("Transcript:", text, height=300)
        except TranscriptsDisabled:
            st.warning("❌ Transcript disabled for this video.")
        except NoTranscriptFound:
            st.warning("❌ No transcript found (maybe private or no captions).")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            st.info("Please upload audio instead.")
            uploaded_file = st.file_uploader("Upload audio file")
            if uploaded_file:
                st.info("Audio received — (future version will process this).")
