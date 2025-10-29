import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from youtube_transcript_api.formatters import TextFormatter

st.set_page_config(page_title="YouTube Transcript Tool", page_icon="🎥", layout="centered")

st.title("🎬 YouTube Transcript Extractor")

st.markdown("Easily get transcripts from any YouTube video or upload audio instead.")

# Input field for YouTube URL
url = st.text_input("Enter YouTube Video URL:")

def extract_video_id(url):
    """Extract video ID from YouTube URL."""
    import re
    pattern = r"(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

if url:
    video_id = extract_video_id(url)
    if not video_id:
        st.error("Invalid YouTube URL. Please check and try again.")
    else:
        try:
            # Attempt to get transcript
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            formatter = TextFormatter()
            text_transcript = formatter.format_transcript(transcript)
            st.text_area("Transcript:", text_transcript, height=400)
            st.download_button("Download Transcript as TXT", text_transcript, file_name="transcript.txt")
        except (TranscriptsDisabled, NoTranscriptFound):
            st.warning("Transcript not available. Please upload audio instead.")
        except VideoUnavailable:
            st.error("Video unavailable or restricted.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

st.markdown("---")
st.subheader("🎧 Or Upload Audio File Instead")
uploaded_audio = st.file_uploader("Upload an MP3 or WAV file", type=["mp3", "wav"])

if uploaded_audio:
    st.info("✅ Audio file uploaded successfully! Speech-to-text feature coming soon.")
