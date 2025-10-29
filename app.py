# app.py  (paste this to GitHub)
import streamlit as st
import re
import importlib
import sys

st.set_page_config(page_title="YouTube Transcript Debugger", layout="centered")
st.title("🎬 YouTube Transcript Debugger")

st.markdown("""
This app attempts multiple ways to fetch transcripts using whatever `youtube_transcript_api`
is installed on the environment. It also shows debugging info to help find conflicts.
""")

url = st.text_input("Enter YouTube URL or video id:")

# helper to extract id
def extract_video_id(url_or_id: str):
    m = re.search(r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})", url_or_id or "")
    if m:
        return m.group(1)
    # maybe user entered just the id
    if re.match(r'^[A-Za-z0-9_-]{11}$', url_or_id or ""):
        return url_or_id
    return None

# Try to import the library and show where it comes from
try:
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
    from youtube_transcript_api.formatters import TextFormatter
    # find module file for debugging
    module_name = YouTubeTranscriptApi.__module__
    module_obj = importlib.import_module(module_name)
    module_file = getattr(module_obj, "__file__", None)
    st.info(f"Detected youtube_transcript_api module: {module_name}")
    if module_file:
        st.write(f"Module file: `{module_file}`")
    else:
        st.write("Module file info not available (built-in or namespace package).")
except Exception as imp_err:
    st.error("Could not import `youtube_transcript_api` properly.")
    st.write("Import error:", imp_err)
    st.write("Make sure `requirements.txt` contains `youtube-transcript-api` and there are no local files named `youtube_transcript_api.py` in your repo.")
    # stop further processing since import failed
    st.stop()

# If user entered URL / id, attempt fetch
if url:
    vid = extract_video_id(url)
    if not vid:
        st.error("Invalid YouTube URL or ID. Example valid: https://www.youtube.com/watch?v=VIDEOID")
    else:
        st.write(f"Using video id: `{vid}`")
        # Attempt method 1: class method get_transcript (most common)
        tried_methods = []
        transcript = None
        try:
            if hasattr(YouTubeTranscriptApi, "get_transcript"):
                tried_methods.append("YouTubeTranscriptApi.get_transcript")
                # some versions accept languages param, some not — try both
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(vid, languages=['en'])
                except TypeError:
                    transcript = YouTubeTranscriptApi.get_transcript(vid)
            # Method 2: module-level function list_transcripts (some versions)
            elif hasattr(YouTubeTranscriptApi, "list_transcripts"):
                tried_methods.append("YouTubeTranscriptApi.list_transcripts (call as function)")
                # call as function if available (some installs expose function instead of class)
                try:
                    transcripts_list = YouTubeTranscriptApi.list_transcripts(vid)
                    # transcripts_list may be TranscriptList object
                    try:
                        found = transcripts_list.find_transcript(['en'])
                    except Exception:
                        try:
                            found = transcripts_list.find_generated_transcript(['en'])
                        except Exception:
                            found = None
                    if found:
                        transcript = found.fetch()
                except Exception as e:
                    st.write("list_transcripts call error:", e)
            else:
                # last resort: try using module functions via importlib
                tried_methods.append("fallback importlib search")
                mod = importlib.import_module("youtube_transcript_api")
                if hasattr(mod, "YouTubeTranscriptApi") and hasattr(mod.YouTubeTranscriptApi, "get_transcript"):
                    tried_methods.append("module.YouTubeTranscriptApi.get_transcript")
                    transcript = mod.YouTubeTranscriptApi.get_transcript(vid)
        except TranscriptsDisabled:
            st.warning("Transcripts are disabled for this video.")
        except NoTranscriptFound:
            st.warning("No transcript found for this video.")
        except VideoUnavailable:
            st.error("Video unavailable or restricted.")
        except Exception as e:
            st.error("Unexpected error while attempting transcript fetch.")
            st.write("Error detail:", e)

        st.write("Tried methods:", tried_methods)

        if transcript:
            st.success("✅ Transcript fetched!")
            try:
                formatter = TextFormatter()
                text_transcript = formatter.format_transcript(transcript)
            except Exception:
                # if formatter fails, fallback to simple join
                try:
                    text_transcript = "\n".join([seg.get("text","") for seg in transcript])
                except Exception:
                    text_transcript = str(transcript)
            st.text_area("Transcript:", value=text_transcript, height=400)
            st.download_button("Download TXT", data=text_transcript, file_name=f"{vid}_transcript.txt")
        else:
            st.warning("Transcript not available via youtube_transcript_api.\n\nReason (debug): Unable to fetch transcript with installed youtube_transcript_api. Please ensure you're using a compatible package (pip install youtube-transcript-api) or remove conflicting local files.")
            st.info("If you need help, paste the above debug info and module file path to me or check Streamlit logs.")
            # show hint to user: list available transcripts via library if supported
            try:
                # try to get transcript list for extra debug
                if hasattr(YouTubeTranscriptApi, "list_transcripts"):
                    st.write("Attempting to list available transcripts (debug)...")
                    try:
                        ts = YouTubeTranscriptApi.list_transcripts(vid)
                        st.write("list_transcripts result:", ts)  # may be object representation
                    except Exception as e:
                        st.write("list_transcripts() error:", e)
            except Exception:
                pass

# Allow audio upload as fallback
st.markdown("---")
st.subheader("Upload audio if transcript is not available")
uploaded_audio = st.file_uploader("Upload MP3/WAV for transcription (backup)", type=["mp3","wav","m4a"])
if uploaded_audio:
    st.info("Audio uploaded. You can integrate Whisper / speech-to-text to process this file.")
    # Optional: write audio to /tmp and show path for manual processing
    try:
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_audio.name)
        tmp.write(uploaded_audio.read())
        tmp.flush()
        tmp.close()
        st.write("Saved audio to:", tmp.name)
    except Exception as e:
        st.write("Could not save uploaded file:", e)
