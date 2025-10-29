import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import re

st.title("🎬 YouTube Transcript Generator")

url = st.text_input("Enter YouTube Video URL:")

def get_video_id(url):
    video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return video_id_match.group(1) if video_id_match else None

if url:
    try:
        video_id = get_video_id(url)
        if video_id:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            text = " ".join([t['text'] for t in transcript])
            st.text_area("Transcript:", text, height=300)
        else:
            st.error("Invalid YouTube URL.")
    except Exception:
        st.warning("Transcript not available. Please upload audio instead.")
        uploaded_file = st.file_uploader("Upload audio file")
        if uploaded_file:
            st.info("Audio received — (future version will process this).")
