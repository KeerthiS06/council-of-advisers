import time
import itertools
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

# Default configuration constants
DEFAULT_API_KEY = "AIzaSyCnbd9fpz7S_3830EGK8rZjI3ERTO__ZJA"
DEFAULT_CHANNEL_ID = "UCn0lK_IfpMItgdVfug6_WaQ"
DEFAULT_CHANNEL_NAME = "Buddha Motivation"

def get_all_channel_videos(api_key, channel_id):
    # Initialize the YouTube API client
    youtube = build('youtube', 'v3', developerKey=api_key)

    # STEP 1: Get the Channel's unique "Uploads" Playlist ID
    channel_response = youtube.channels().list(
        part='contentDetails',
        id=channel_id
    ).execute()

    # Extract the uploads playlist ID
    uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    video_links = []
    next_page_token = None
    sleep_cycle = itertools.cycle([2,3,4])

    # STEP 2: Loop through the playlist items to extract video IDs
    print("Fetching videos... This might take a moment for large channels.")
    while True:
        playlist_response = youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist_id,
            maxResults=50,  # 50 is the maximum allowed per request
            pageToken=next_page_token
        ).execute()

        # Parse the video links from the current page
        for item in playlist_response.get('items', []):
            video_id = item['snippet']['resourceId']['videoId']
            title = item['snippet']['title']
            url = f"https://www.youtube.com/watch?v={video_id}"
            video_links.append((title, url))

        # Check if there is another page of videos
        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break  # No more pages, exit loop

        sleep_secs = next(sleep_cycle)
        print(f"Sleeping {sleep_secs}s before next API call...")
        time.sleep(sleep_secs)

    return video_links

def extract_video_ids_from_list(videos):
    title_and_id=[]
    for title, url in videos.items():
        try:
            after_equals = url.split('v=')[1]
            video_id = after_equals.split('&')[0]

            title_and_id.append({
                "title": title,
                "video_id": video_id
            })
        except IndexError:
            print(f"Skipping invalid URL for '{title}': {url}")
            continue

    return title_and_id


def get_transcript_from_dict(title_and_id):
    # Extract title and id from the passed dictionary
    title = title_and_id.get('title', 'Unknown Title')
    video_id = title_and_id.get('video_id')

    # Safety check if video_id is missing
    if not video_id:
        return {
            "title": title,
            "transcript": "Error: Missing video_id"
        }

    try:
        yt_api = YouTubeTranscriptApi()
        transcript_obj = yt_api.fetch(video_id)

        # Converts it back into standard dictionaries
        raw_transcript = transcript_obj.to_raw_data()

        # Now entry['text'] will work perfectly
        full_text = " ".join([entry['text'] for entry in raw_transcript])
    except Exception as e:
        print(f"Error fetching transcript for '{title}': {e}")
        full_text = f"Error: Could not retrieve transcript ({e})"

    # Return the final dictionary with title and transcript
    return {
        "title": title,
        "transcript": full_text
    }



def save_all_transcripts_to_file(transcripts, output_dir=".", filename=DEFAULT_CHANNEL_NAME):
    """
    Saves a list of transcript dicts (each with 'title' and 'transcript' keys)
    into a single local file, separated by dividers.
    """
    import os

    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        for i, item in enumerate(transcripts, start=1):
            title = item.get("title", "Unknown Title")
            transcript = item.get("transcript", "")
            f.write(f"[{i}] Title: {title}\n\n")
            f.write(transcript)
            f.write("\n\n" + "=" * 80 + "\n\n")

    print(f"All transcripts saved to: {file_path}")
    return file_path


DEFAULT_TEST_VIDEO = {
    "title": "Test Video",
    "video_id": "5_3oAbuuYXQ"  # Replace with any valid YouTube video ID for testing
}


def run_pipeline(
    channel_id=DEFAULT_CHANNEL_ID,
    channel_name=DEFAULT_CHANNEL_NAME,
    api_key=DEFAULT_API_KEY,
    output_dir="transcripts",
    test_mode=False,
    test_video=None,
    progress_callback=None,
):
    """
    Main pipeline: fetch all video IDs, download transcripts, save to file.

    Args:
        channel_id:        YouTube channel ID (e.g. 'UCn0lK_IfpMItgdVfug6_WaQ')
        channel_name:      Human-readable channel name used as the output filename
        api_key:           YouTube Data API v3 key
        output_dir:        Directory in which to save the transcript file
        test_mode:         If True, skip the API call and use a single test video
        test_video:        Dict with 'title' and 'video_id' keys (used when test_mode=True)
        progress_callback: Optional callable(current, total, message) for real-time updates

    Returns:
        Path of the saved transcript file.
    """
    if test_mode:
        video = test_video or DEFAULT_TEST_VIDEO
        print(f"TEST_MODE: using test video '{video['title']}' ({video['video_id']})")
        items_to_process = [video]
    else:
        all_videos = get_all_channel_videos(api_key, channel_id)
        videos = {title: url for title, url in all_videos}
        items_to_process = extract_video_ids_from_list(videos)
        print(f"Fetched {len(items_to_process)} videos from channel.")

    total = len(items_to_process)
    all_transcripts = []
    sleep_cycle = itertools.cycle([4, 5, 6])

    for i, item in enumerate(items_to_process, start=1):
        message = f"Fetching transcript {i}/{total}: {item.get('title')}"
        print(message)
        if progress_callback:
            progress_callback(i, total, message)
        transcript_data = get_transcript_from_dict(item)
        all_transcripts.append(transcript_data)

        if i < total:
            sleep_secs = next(sleep_cycle)
            print(f"Sleeping {sleep_secs}s before next API call...")
            time.sleep(sleep_secs)

    file_path = save_all_transcripts_to_file(
        all_transcripts, output_dir=output_dir, filename=channel_name
    )
    return file_path


if __name__ == "__main__":
    run_pipeline()
