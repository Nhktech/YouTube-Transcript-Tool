# app.py
import streamlit as st
import re
import os
import importlib
import traceback

st.set_page_config(page_title="YouTube Transcript Tool", page_icon="🎥", layout="centered")
st.title("🎬 YouTube Transcript Tool (Robust)")

st.markdown(
    "Shigar da YouTube URL domin a ƙoƙarta cire transcript. Idan baya nan, zaka iya ɗora audio. "
    "Wannan version tana gwadawa da hanyoyi daban-daban na `youtube_transcript_api` don hana errors."
)

# ---- detect local file that shadows the package ----
if os.path.exists("youtube_transcript_api.py"):
    st.error(
        "An gano `youtube_transcript_api.py` a cikin repo — wannan zai hana package na gaskiya aiki. "
        "Don Allah ka goge ko rename wannan file kafin ka deploy."
    )

# Try to import the library (best-effort)
yta = None
YTApi = None
exceptions = {}
try:
    yta = importlib.import_module("youtube_transcript_api")
    # try common names
    try:
        from youtube_transcript_api import (
            YouTubeTranscriptApi as YTApi,
            TranscriptsDisabled,
            NoTranscriptFound,
            VideoUnavailable,
        )
    except Exception:
        # fallback: sometimes module exposes these at different paths
        try:
            TranscriptsDisabled = getattr(yta, "TranscriptsDisabled", Exception)
            NoTranscriptFound = getattr(yta, "NoTranscriptFound", Exception)
            VideoUnavailable = getattr(yta, "VideoUnavailable", Exception)
            YTApi = getattr(yta, "YouTubeTranscriptApi", None)
        except Exception as e:
            exceptions["import_inner"] = str(e)
except Exception as e:
    exceptions["import_module"] = str(e)

# helper to extract video id
def extract_video_id(url):
    if not url:
        return None
    m = re.search(r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None

# universal fetch function with multiple fallbacks
def fetch_transcript_flexible(video_id, prefer_languages=None):
    """
    Try multiple ways to get transcript using different shapes of the library.
    Returns transcript (list of dicts with 'text','start','duration') or raises.
    """
    if not video_id:
        raise ValueError("No video id provided")

    # 1) If classmethod exists: YouTubeTranscriptApi.get_transcript
    try:
        if YTApi is not None and hasattr(YTApi, "get_transcript"):
            if prefer_languages:
                return YTApi.get_transcript(video_id, languages=prefer_languages)
            return YTApi.get_transcript(video_id)
    except Exception as e:
        # keep trying other options
        last_exc = e

    # 2) If class has list_transcripts (some versions expose it on class)
    try:
        if YTApi is not None and hasattr(YTApi, "list_transcripts"):
            ts_list = YTApi.list_transcripts(video_id)
            # ts_list might have find_transcript / find_generated_transcript
            if hasattr(ts_list, "find_transcript"):
                if prefer_languages:
                    tr = ts_list.find_transcript(prefer_languages)
                else:
                    # try to get any transcript (use first available)
                    try:
                        tr = ts_list.find_transcript(["en"])
                    except Exception:
                        tr = next(iter(ts_list._transcripts)) if hasattr(ts_list, "_transcripts") else None
                if tr:
                    if hasattr(tr, "fetch"):
                        return tr.fetch()
            # fallback: if ts_list itself can be fetched
            if hasattr(ts_list, "fetch"):
                return ts_list.fetch()
    except Exception as e:
        last_exc = e

    # 3) Module-level function: youtube_transcript_api.get_transcript
    try:
        if yta is not None and hasattr(yta, "get_transcript"):
            if prefer_languages:
                return yta.get_transcript(video_id, languages=prefer_languages)
            return yta.get_transcript(video_id)
    except Exception as e:
        last_exc = e

    # 4) Module may expose "fetch" or "fetch_transcript"
    try:
        for func_name in ("fetch", "fetch_transcript", "get_transcripts"):
            if yta is not None and hasattr(yta, func_name):
                func = getattr(yta, func_name)
                return func(video_id)
    except Exception as e:
        last_exc = e

    # 5) As a last attempt, try to introspect anything that looks like 'list' or 'transcript' and call it
    try:
        if yta is not None:
            for name in dir(yta):
                if "transcript" in name.lower() or "list" in name.lower():
                    attr = getattr(yta, name)
                    if callable(attr):
                        try:
                            res = attr(video_id)
                            # basic check if result looks like transcript
                            if isinstance(res, list) and res and isinstance(res[0], dict) and "text" in res[0]:
                                return res
                        except Exception:
                            continue
    except Exception:
        pass

    # If all attempts fail, raise a helpful error
    msg = "Unable to fetch transcript with installed youtube_transcript_api. "
    msg += "Please ensure you're using a compatible package (pip install youtube-transcript-api) "
    msg += "or remove conflicting local files. Last error: " + (str(last_exc) if 'last_exc' in locals() else "none")
    raise RuntimeError(msg)


# UI logic
url = st.text_input("Enter YouTube video URL or ID:")

if st.button("Get Transcript"):
    if not url:
        st.error("Please enter a YouTube URL or Video ID.")
    else:
        vid = extract_video_id(url) or (url if re.match(r"^[A-Za-z0-9_-]{11}$", url) else None)
        if not vid:
            st.error("Could not extract a valid YouTube video id. Check the URL/ID.")
        else:
            # if import failed, show message
            if YTApi is None and yta is None:
                st.error(
                    "youtube_transcript_api not importable in this environment. "
                    "Check requirements.txt contains 'youtube-transcript-api' and redeploy. "
                    f"Import errors: {exceptions}"
                )
            else:
                try:
                    # try fetching
                    transcript = fetch_transcript_flexible(vid, prefer_languages=["en"])
                    # format transcript to text
                    lines = []
                    for seg in transcript:
                        start = seg.get("start", 0)
                        text = seg.get("text", seg.get("value", "")).strip()
                        lines.append(f"[{int(start)}s] {text}")
                    output_text = "\n".join(lines)
                    st.success("Transcript fetched!")
                    st.text_area("Transcript", value=output_text, height=400)
                    st.download_button("Download TXT", data=output_text, file_name=f"{vid}_transcript.txt")
                except Exception as e:
                    st.warning("Transcript not available via youtube_transcript_api.")
                    st.info("Reason (debug): " + str(e))
                    # show stacktrace in logs for debugging (not shown to public)
                    st.write("If you need help, check your Streamlit logs or paste this message to me.")
                    # Offer audio upload fallback
                    st.markdown("---")
                    st.subheader("Upload audio file as fallback (MP3/WAV/M4A)")
                    uploaded = st.file_uploader("Upload audio file", type=["mp3", "wav", "m4a"])
                    if uploaded:
                        st.success("Audio uploaded — speech-to-text not implemented in this app, but you can download the file and process locally or add Whisper/OpenAI API integration.")
