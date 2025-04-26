import os
from ultralytics import YOLO
import supervision as sv
import numpy as np
import shutil
from tqdm import tqdm
import cv2


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
