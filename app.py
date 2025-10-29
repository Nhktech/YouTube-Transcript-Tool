import streamlit as st
import re
import importlib
import sys

st.set_page_config(page_title="YouTube Transcript Tool", layout="centered")
st.title("🎬 YouTube Transcript Tool (Debug Version)")
st.markdown("Fetch YouTube transcripts or upload audio when captions are missing.")

def extract_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})", url)
    return match.group(1) if match else None

# Import the API safely
try:
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
    from youtube_transcript_api.formatters import TextFormatter
    st.info("✅ youtube_transcript_api imported successfully.")
except Exception as e:
    st.error("❌ Failed to import youtube_transcript_api. Check your requirements.txt file.")
    st.stop()

url = st.text_input("Enter YouTube Video URL:")

if url:
    video_id = extract_video_id(url)
    if not video_id:
        st.error("Invalid YouTube URL or ID.")
    else:
        transcript = None
        try:
            if hasattr(YouTubeTranscriptApi, "get_transcript"):
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
            else:
                api = YouTubeTranscriptApi()
                transcript_list = api.list_transcripts(video_id)
                transcript = transcript_list.find_transcript(["en"]).fetch()

            if transcript:
                formatter = TextFormatter()
                text_transcript = formatter.format_transcript(transcript)
                st.success("✅ Transcript fetched successfully!")
                st.text_area("Transcript:", text_transcript, height=400)
                st.download_button("Download Transcript", text_transcript, file_name="transcript.txt")
        except (TranscriptsDisabled, NoTranscriptFound):
            st.warning("Transcript not available. Please upload audio instead.")
        except VideoUnavailable:
            st.error("Video unavailable or restricted.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

st.markdown("---")
st.subheader("🎧 Upload Audio File Instead")
uploaded_audio = st.file_uploader("Upload MP3/WAV", type=["mp3", "wav"])
if uploaded_audio:
    st.info("✅ Audio uploaded. Speech-to-text integration coming soon!")
