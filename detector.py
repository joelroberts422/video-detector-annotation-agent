import os
from ultralytics import YOLO
import supervision as sv
import numpy as np
import shutil
from tqdm import tqdm
import cv2
import json
from collections import defaultdict
import subprocess


VIDEO_FOLDER = 'videos'
DATASETS_FOLDER = 'datasets'
CONSTANT_VIDEO_WIDTH = 1920

os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(DATASETS_FOLDER, exist_ok=True)

model = YOLO('yolov8s.pt')
object_tracker = sv.ByteTrack()

box_annotator = sv.BoxCornerAnnotator(thickness=5, corner_length=20)
label_annotator = sv.LabelAnnotator(text_padding=10, text_scale=1.4, text_thickness=3)
trace_annotator = sv.TraceAnnotator(position=sv.Position.CENTER, trace_length=200, thickness=8)

def copy_file(source_path, destination_path):
    shutil.copy(source_path, destination_path)
    print(f"File copied from {source_path} to {destination_path}")

def process_video(video_name: str):

    # ffmpeg reencode video, assume frames = fps * length
    video_path = os.path.join(VIDEO_FOLDER, video_name)
    cap = cv2.VideoCapture(video_path)
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_detections = sv.Detections.empty()

    # Check if the video has the correct number of frames
    if not check_and_correct_video_fps(video_path):
        print(f"Error: Video {video_name} has incorrect number of frames. Skipping processing.")
        return
    
    with sv.JSONSink(os.path.join(DATASETS_FOLDER, video_name.split('.')[0] + '.json')) as sink:
        for i in tqdm(range(length)):
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame, verbose=False)[0]
            detections = sv.Detections.from_ultralytics(results)
            detections = object_tracker.update_with_detections(detections=detections)
            detections.data["frame_index"] = np.full(len(detections), i)

            sink.append(detections=detections, custom_data={"frame_index": i})
            total_detections = sv.Detections.merge([total_detections, detections])

    cap.release()
    print(f"Processed video {video_name} and saved detections to {video_name.split('.')[0]}.json")


def json_to_paths(json_path):
    """
    Reads a JSON detection file and converts it into a paths object.
    
    Args:
        json_path (str): Path to the JSON file
        
    Returns:
        list: List of path objects, each containing tracking information for a unique object
    """
    # Read the JSON file
    with open(json_path, 'r') as f:
        detections = json.load(f)
    
    # Group detections by tracker_id
    tracker_groups = defaultdict(list)
    for detection in detections:
        tracker_id = detection['tracker_id']
        tracker_groups[tracker_id].append(detection)
    
    # Create paths list
    paths = []
    
    for tracker_id, group in tracker_groups.items():
        # Sort detections by frame_index
        sorted_group = sorted(group, key=lambda x: x['frame_index'])
        
        # Extract data sequences
        bboxes = [(det['x_min'], det['y_min'], det['x_max'], det['y_max']) for det in sorted_group]
        frame_indices = [det['frame_index'] for det in sorted_group]
        class_ids = [det['class_id'] for det in sorted_group]
        class_names = [det['class_name'] for det in sorted_group]
        confidences = [det['confidence'] for det in sorted_group]
        
        # Create path object
        path = {
            'tracker_id': tracker_id,
            'bboxes': bboxes,
            'frame_indices': frame_indices,
            'class_ids': class_ids,
            'class_names': class_names,
            'confidences': confidences
        }
        
        paths.append(path)
    
    return paths

def check_and_correct_video_fps(video_path, target_fps=None):
    """
    Checks if a video file has the correct number of frames based on its duration
    and frame rate. If not, it re-encodes the video in place to enforce the
    target frame rate.  If target_fps is None, it attempts to get the FPS
    from the video file itself using cv2.

    Args:
        video_path (str): The path to the video file.
        target_fps (float, optional): The target frames per second.
            If None, the function will attempt to get the FPS from the video.
            Defaults to None.

    Returns:
        bool: True if the operation was successful (or the video already had
              the correct FPS), False otherwise.
    """
    try:
        # 1. Get target_fps if not provided.
        if target_fps is None:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"Error: Could not open video file: {video_path} with cv2.")
                return False
            target_fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            if target_fps <= 0:
                print(f"Error: Could not get valid FPS from video file {video_path} with cv2.  FFmpeg will be used to attempt correction with default/inferred rate, which may not be correct.")
                target_fps = None #set to None so ffmpeg will try to use the rate

        # 2. Use ffprobe to get duration and frame rate.
        ffprobe_command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=avg_frame_rate,duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        ffprobe_output = subprocess.run(ffprobe_command, capture_output=True, text=True, check=True)
        stdout_text = ffprobe_output.stdout.strip()
        output_lines = stdout_text.split('\n')

        # Now parse the values properly
        frame_rate_str = output_lines[0]  # The first line contains the frame rate
        duration_str = output_lines[1] if len(output_lines) > 1 else "0"  # The second line has duration
        
        # Convert frame_rate_str (like "15000/1001") to a float
        if '/' in frame_rate_str:
            numerator, denominator = frame_rate_str.split('/')
            frame_rate = float(numerator) / float(denominator)
        else:
            frame_rate = float(frame_rate_str)

        duration = float(duration_str)
        expected_frames = round(frame_rate * duration)

        # 3. Use FFmpeg to count the actual number of frames.
        ffmpeg_count_command = [
            "ffmpeg",
            "-i", video_path,
            "-map", "0:v:0",
            "-c", "copy",  # Don't re-encode during counting for speed
            "-f", "null",
            "-"
        ]
        ffmpeg_count_output = subprocess.run(ffmpeg_count_command, capture_output=True, text=True, check=True)
        for line in ffmpeg_count_output.stderr.splitlines():
            if "frame=" in line:
                frame_count_str = line.split("frame=")[1].split()[0]
                try:
                    actual_frames = int(frame_count_str)
                except ValueError:
                    print(f"Error: Could not parse frame count from FFmpeg output: {frame_count_str}")
                    return False
                break
        else:
            print("Error: Could not find frame count in FFmpeg output.")
            return False

        # 4. Compare expected and actual frame counts.
        if abs(actual_frames - expected_frames) <= 1:  # Allow a small tolerance
            print(f"Video '{video_path}' has the correct number of frames.")
            return True  # No change needed
        else:
            print(f"Video '{video_path}' has incorrect frame count. Expected: {expected_frames}, Actual: {actual_frames}. Correcting...")

        # 5. Re-encode the video with the target frame rate, in place.
        # Create a temporary file to store the re-encoded video.
        temp_video_path = video_path + ".tmp"
        ffmpeg_reencode_command = [
            "ffmpeg",
            "-i", video_path,
            "-r", str(target_fps) if target_fps else "-r 30",  # Use provided or default
            "-y",  # Overwrite output file without asking
            temp_video_path  # Output to temporary file
        ]

        subprocess.run(ffmpeg_reencode_command, check=True)

        # Replace the original video file with the re-encoded version.
        try:
            os.remove(video_path)
            os.rename(temp_video_path, video_path)
        except OSError as e:
            print(f"Error: Failed to replace original video file: {e}")
            return False

        print(f"Video '{video_path}' re-encoded to {target_fps} FPS.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg/FFprobe error: {e}")
        print(f"Command: {e.cmd}")
        print(f"Output: {e.output}")
        return False
    except FileNotFoundError:
        print("Error: FFmpeg or FFprobe not found. Please ensure they are installed and in your system's PATH.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
