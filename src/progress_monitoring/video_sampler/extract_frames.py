import cv2
import os
import math


def time_to_seconds(time_str):
    """Convert time string (MM:SS or M:SS) to seconds"""
    if ":" in time_str:
        parts = time_str.split(":")
        minutes = int(parts[0])
        seconds = int(parts[1])
        return minutes * 60 + seconds
    else:
        return int(time_str) * 60  # assume it's just minutes


def extract_sample_frames(
    video_path, output_dir="extracted_frames", frames_per_segment=5
):
    """
    Extract sample frames from video at specified time intervals

    Args:
        video_path (str): Path to the input video file
        output_dir (str): Base directory to save extracted frames
        frames_per_segment (int): Number of frames to extract per time segment
    """

    # Define time segments (start, end) in seconds
    time_segments = [
        (0, 4 * 60),  # 0-4 min
        (4 * 60, 6 * 60),  # 4-6 min
        (6 * 60, 8 * 60 + 18),  # 6 min to 8:18
        (8 * 60 + 18, 11 * 60 + 21),  # 8:18 to 11:21
        (11 * 60 + 21, None),  # 11:21 to end 
    ]

    # Create base output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create individual day folders for each segment
    day_folders = []
    for i in range(len(time_segments)):
        day_folder = os.path.join(output_dir, f"day{i+1}")
        day_folders.append(day_folder)
        if not os.path.exists(day_folder):
            os.makedirs(day_folder)
            print(f"Created folder: {day_folder}")

    # Open video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    print(f"Video Info:")
    print(f"  Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    print(f"  FPS: {fps}")
    print(f"  Total frames: {total_frames}")
    print(f"  Extracting {frames_per_segment} frames per segment\n")

    frame_count = 0

    for segment_idx, (start_time, end_time) in enumerate(time_segments):
        # Handle end time for last segment
        if end_time is None:
            end_time = duration

        # Skip segment if start time is beyond video duration
        if start_time >= duration:
            print(f"Segment {segment_idx + 1}: Skipped (beyond video duration)")
            continue

        # Adjust end time if it exceeds video duration
        if end_time > duration:
            end_time = duration

        segment_duration = end_time - start_time

        print(
            f"Day{segment_idx + 1} (Segment {segment_idx + 1}): {start_time//60:.0f}:{start_time%60:02.0f} - {end_time//60:.0f}:{end_time%60:02.0f}"
        )

        # Calculate frame positions to extract
        if frames_per_segment == 1:
            # Extract middle frame
            time_positions = [start_time + segment_duration / 2]
        else:
            # Extract evenly spaced frames
            time_positions = []
            for i in range(frames_per_segment):
                position = start_time + (
                    segment_duration * i / (frames_per_segment - 1)
                )
                time_positions.append(position)

        # Extract frames at calculated positions
        for frame_idx, time_pos in enumerate(time_positions):
            # Convert time to frame number
            frame_number = int(time_pos * fps)

            # Set video position to the desired frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

            # Read the frame
            ret, frame = cap.read()
            if ret:
                # Create filename
                timestamp = f"{int(time_pos//60):02d}m{int(time_pos%60):02d}s"
                filename = f"frame_{frame_idx+1}_{timestamp}.jpg"
                filepath = os.path.join(day_folders[segment_idx], filename)

                # Save frame
                cv2.imwrite(filepath, frame)
                frame_count += 1
                print(f"  Saved: day{segment_idx+1}/{filename}")
            else:
                print(f"  Error: Could not read frame at {time_pos:.1f}s")

    # Clean up
    cap.release()
    print(
        f"\nExtraction complete! {frame_count} frames saved across {len(time_segments)} day folders in '{output_dir}'"
    )
    print("Folder structure:")
    for i in range(len(time_segments)):
        print(f"  day{i+1}/ - Contains frames from segment {i+1}")


def main():
    # Configuration
    video_path = "video/construction_site_build.mp4"  
    output_directory = "img_data"  
    frames_per_segment = 6  

    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found!")
        print(
            "Please update the 'video_path' variable with the correct path to your video file."
        )
        return

    # Extract frames
    extract_sample_frames(video_path, output_directory, frames_per_segment)


if __name__ == "__main__":
    main()
