import os
import asyncio
import numpy as np
import librosa
import discord
from discord.ext import commands
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

# Set up Discord Bot Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Directory to save temporary uploads and outputs
TEMP_DIR = "./temp_edits"
os.makedirs(TEMP_DIR, exist_ok=True)


def detect_beats(audio_path):
    """Analyzes an audio file and returns a list of beat timestamps in seconds."""
    y, sr = librosa.load(audio_path)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    return beat_times


def create_beat_synced_video(video_paths, audio_path, watermark_text, output_path):
    """
    Cuts video clips to match audio beats, adds a watermark, 
    and overlays the full song track.
    """
    beat_times = detect_beats(audio_path)
    if len(beat_times) < 2:
        raise ValueError("Could not detect enough beats in the audio file.")

    processed_clips = []
    video_idx = 0
    num_videos = len(video_paths)

    # Open all video files
    video_objects = [VideoFileClip(path) for path in video_paths]

    # Iterate through beat intervals and assign a video slice to each beat
    for i in range(len(beat_times) - 1):
        start_time = beat_times[i]
        end_time = beat_times[i + 1]
        duration = end_time - start_time

        # Cycle through provided video clips
        current_video = video_objects[video_idx % num_videos]
        video_idx += 1

        # Pick a segment from the video clip
        # If segment exceeds video length, loop back to start
        clip_start = (i * 0.5) % max(1, (current_video.duration - duration))
        sub_clip = current_video.subclip(clip_start, clip_start + duration)

        # Standardize video resolution (e.g., 1080x1920 vertical format)
        sub_clip = sub_clip.resize(height=1080)
        processed_clips.append(sub_clip)

    # Concatenate all short beat clips together
    final_visual = concatenate_videoclips(processed_clips, method="compose")

    # Add the full song back over the video
    audio_track = AudioFileClip(audio_path).subclip(0, final_visual.duration)
    final_visual = final_visual.set_audio(audio_track)

    # Create Watermark Text Overlay
    txt_clip = (
        TextClip(watermark_text, fontsize=50, color='white', font='Arial-Bold')
        .set_opacity(0.4)
        .set_position(('center', 'center'))
        .set_duration(final_visual.duration)
    )

    # Composite video and watermark together
    final_output = CompositeVideoClip([final_visual, txt_clip])

    # Export final file
    final_output.write_videofile(
        output_path, 
        codec="libx264", 
        audio_codec="aac", 
        fps=30, 
        preset="ultrafast"
    )

    # Close clips to free up system memory
    for v in video_objects:
        v.close()
    final_output.close()


@bot.event
async def on_ready():
    print(f'Bot is logged in as {bot.user.name}')


@bot.command(name="edit")
async def edit_video(ctx, watermark: str = "MY WATERMARK"):
    """
    Usage: Send !edit "YourWatermark" and attach 1 audio file (MP3/WAV) 
    and 1 or more video files (MP4/MOV).
    """
    if not ctx.message.attachments:
        await ctx.send("Please attach an audio file and video clips to your message!")
        return

    await ctx.send("Downloading attachments and processing your edit... This may take a minute!")

    saved_videos = []
    saved_audio = None

    # Download attachments sent with the message
    for idx, attachment in enumerate(ctx.message.attachments):
        filename = attachment.filename.lower()
        save_path = os.path.join(TEMP_DIR, f"{idx}_{attachment.filename}")
        await attachment.save(save_path)

        if filename.endswith(('.mp3', '.wav', '.m4a')):
            saved_audio = save_path
        elif filename.endswith(('.mp4', '.mov', '.avi', '.mkv')):
            saved_videos.append(save_path)

    if not saved_audio or not saved_videos:
        await ctx.send("Error: You must provide at least 1 audio file and at least 1 video file.")
        return

    output_filename = os.path.join(TEMP_DIR, f"final_{ctx.author.id}.mp4")

    # Run the video rendering function in a separate thread to prevent lagging Discord
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            None, 
            create_beat_synced_video, 
            saved_videos, 
            saved_audio, 
            watermark, 
            output_filename
        )

        # Upload final video back to Discord
        await ctx.send(
            content=f"Here is your edit, {ctx.author.mention}!", 
            file=discord.File(output_filename)
        )
    except Exception as e:
        await ctx.send(f"An error occurred while creating the edit: `{str(e)}`")

    # Clean up temporary files
    for path in saved_videos + [saved_audio, output_filename]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

# Replace 'YOUR_BOT_TOKEN_HERE' with your actual Discord Bot Token
bot.run(MTU1MjkwMTI5MTY2MTg2MDg2NA.GsNCRR.wd8tWK0oM_Dz5qQJ7P1srLNeaya51NJCSB2pc8)
  
