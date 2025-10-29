import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from youtube_transcript_api.formatters import TextFormatter

st.set_page_config(page_title="YouTube Transcript Tool", page_icon="🎥", layout="centered")

st.title("🎬 YouTube Transcript Extractor")
st.markdown("Extract YouTube transcripts easily or upload audio if captions are not available.")

def extract_video_id(url):
    """Extract YouTube video ID from any valid URL."""
    import re
    pattern = r"(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

url = st.text_input("Enter YouTube Video URL:")

if url:
    video_id = extract_video_id(url)
    if not video_id:
        st.error("❌ Invalid YouTube URL.")
    else:
        try:
            # --- FIXED METHOD CALL ---
            api = YouTubeTranscriptApi()
            transcript = api.list_transcripts(video_id).find_transcript(['en']).fetch()
            
            formatter = TextFormatter()
            text_transcript = formatter.format_transcript(transcript)
            st.success("✅ Transcript fetched successfully!")
            st.text_area("Transcript:", text_transcript, height=400)
            st.download_button("Download Transcript", text_transcript, file_name="transcript.txt")

        except (TranscriptsDisabled, NoTranscriptFound):
            st.warning("⚠️ Transcript not available. Please upload an audio file below.")
        except VideoUnavailable:
            st.error("🚫 Video unavailable or restricted.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# --- AUDIO UPLOAD SECTION ---
st.markdown("---")
st.subheader("🎧 Upload Audio File Instead")

uploaded_audio = st.file_uploader("Upload MP3 or WAV", type=["mp3", "wav"])
if uploaded_audio:
    st.info("✅ Audio uploaded successfully. Speech-to-text feature will process this soon!")
