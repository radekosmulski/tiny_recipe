"""Predefined actions you can use in your project"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_actions.ipynb.

# %% auto 0
__all__ = ['html', 'test_url', 'recipe', 'result', 'test_video', 'sample_html', 'download', 'select', 'youtube_captions',
           'extract_video_ids', 'playlist_video_ids']

# %% ../nbs/01_actions.ipynb 2
from .core import list_actions, recipe_transform, Recipe, Recipes

from fastcore.test import *
import httpx

# %% ../nbs/01_actions.ipynb 3
@recipe_transform()
def download(url, timeout=30):
    "Download content from URL. Returns text content by default"
    import httpx
    try:
        response = httpx.get(url, timeout=float(timeout))
        response.raise_for_status()  # Raise error for bad status codes
        return response.text
    except httpx.HTTPError as e:
        raise ValueError(f"Failed to download from {url}: {str(e)}")

# %% ../nbs/01_actions.ipynb 5
@recipe_transform()
def select(html, css, first=True, text_only=False):
    "Select elements from HTML using CSS selector. Returns first match by default, or all matches if first=False. Use text_only=True to get only text content."
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.select(css)
    if not results:
        return None
    
    if text_only:
        if first:
            return results[0].get_text().strip()
        return [r.get_text().strip() for r in results]
    else:
        if first:
            return str(results[0])
        return [str(r) for r in results]

# Test basic selection
html = """
<div class="content">
    <h1>Title</h1>
    <p class="text">First paragraph</p>
    <p class="text">Second paragraph</p>
</div>
"""

# Test single element selection
test_eq(select(html, "h1"), "<h1>Title</h1>")

# Test multiple elements
test_eq(select(html, "p.text", first=True),
        '<p class="text">First paragraph</p>')

test_eq(select(html, "p.text", first=False), 
        ['<p class="text">First paragraph</p>', 
         '<p class="text">Second paragraph</p>'])

# Test multiple elements with text_only
test_eq(select(html, "p.text", first=False, text_only=True), 
        ['First paragraph', 'Second paragraph'])

# Test no matches
test_eq(select(html, "span"), None)

# Test in pipeline with download
test_url = "https://example.com"
recipe = Recipe(
    input=test_url,
    actions="download.select|css=h1"
)
result = recipe.run()
test_eq("Example Domain" in result, True)

# %% ../nbs/01_actions.ipynb 6
@recipe_transform()
def youtube_captions(video_id, timestamps="True"):
    """Get captions from a YouTube video.
    Args:
        video_id: YouTube video ID (e.g., 'abc123xyz' from 'youtube.com/watch?v=abc123xyz')
        timestamps: "True" or "False" string to include timestamps in output (default: "True")
    Returns:
        String with video captions, optionally with timestamps
    """
    from youtube_transcript_api import YouTubeTranscriptApi
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        if timestamps.lower() == "true":
            return '\n'.join(
                f"[{int(entry['start']//60)}:{int(entry['start']%60):02d}] {entry['text']}"
                for entry in transcript
            )
        return '\n'.join(entry['text'] for entry in transcript)
        
    except Exception as e:
        raise ValueError(f"Failed to get captions for video {video_id}: {str(e)}")

# Test cases
test_video = "FcugVUydSBY"  # MKBHD's 100 subscriber milestone video

# Test basic functionality
result = youtube_captions(test_video)
test_eq(len(result) > 0, True)

# %% ../nbs/01_actions.ipynb 9
@recipe_transform()
def extract_video_ids(html):
    """Extract YouTube video IDs from a playlist page.
    Returns list of video IDs from video-title links.
    """
    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(html, 'html.parser')
    # Find all video title links
    links = soup.select('a#video-title')
    
    # Extract video IDs from hrefs using regex
    video_ids = []
    for link in links:
        href = link.get('href', '')
        # Match v= parameter in URL
        if match := re.search(r'[?&]v=([^&]+)', href):
            video_ids.append(match.group(1))
    
    return video_ids

# Test with sample HTML
sample_html = """
<div id="meta">
    <h3>
        <a id="video-title" href="/watch?v=QqZUzkPcU7A&list=123&index=1">Video 1</a>
    </h3>
</div>
<div id="meta">
    <h3>
        <a id="video-title" href="/watch?v=ABC123xyz&list=123&index=2">Video 2</a>
    </h3>
</div>
"""

# Test basic extraction
test_eq(extract_video_ids(sample_html), 
        ['QqZUzkPcU7A', 'ABC123xyz'])

# Test empty page
test_eq(extract_video_ids('<div></div>'), [])

# Example usage in a recipe pipeline
recipe = Recipe(
    input="<playlist page html>",
    actions="extract_video_ids.youtube_captions"
)

# %% ../nbs/01_actions.ipynb 11
@recipe_transform()
def playlist_video_ids(playlist_url):
    """Extract video IDs from a YouTube playlist using pytube and create recipes for each video.
    Args:
        playlist_url: Full YouTube playlist URL
    Returns:
        Recipes object containing a recipe for each video
    """
    from pytube import Playlist
    try:
        playlist = Playlist(playlist_url)
        video_ids = [url.split('watch?v=')[1] for url in playlist.video_urls]
        # Create a recipe for each video ID
        return Recipes([Recipe(input=vid) for vid in video_ids])
    except Exception as e:
        raise ValueError(f"Failed to get video IDs from playlist {playlist_url}: {str(e)}")
