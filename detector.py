import os
from ultralytics import YOLO
import supervision as sv
import numpy as np
import shutil
from tqdm import tqdm
import cv2
import pandas as pd
import subprocess
import json
from scipy.interpolate import splrep, splev, splder, splprep
import math

<<<<<<< HEAD
VIDEO_FOLDER = os.getenv('VIDEO_FOLDER')
DATASETS_FOLDER = os.getenv('DATASETS_FOLDER')
CONSTANT_VIDEO_WIDTH = 1920

=======

VIDEO_FOLDER = 'videos'
DATASETS_FOLDER = 'datasets'
CONSTANT_VIDEO_WIDTH = 1920

os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(DATASETS_FOLDER, exist_ok=True)

>>>>>>> b5bf8e679c938e015dcb00daa6217e98f28b3a74
model = YOLO('yolov8s.pt')
object_tracker = sv.ByteTrack()

box_annotator = sv.BoxCornerAnnotator(thickness=5, corner_length=20)
label_annotator = sv.LabelAnnotator(text_padding=10, text_scale=1.4, text_thickness=3)
trace_annotator = sv.TraceAnnotator(position=sv.Position.CENTER, trace_length=200, thickness=8)

def copy_file(source_path, destination_path):
    shutil.copy(source_path, destination_path)
    print(f"File copied from {source_path} to {destination_path}")

def detect_frame(frame: np.ndarray, frame_index: int):
<<<<<<< HEAD
    resize_frame = sv.resize_image(frame, resolution_wh=(CONSTANT_VIDEO_WIDTH, CONSTANT_VIDEO_WIDTH), keep_aspect_ratio=True)
    results = model(resize_frame, verbose=False)[0]
=======
    # resize_frame = sv.resize_image(frame, resolution_wh=(CONSTANT_VIDEO_WIDTH, CONSTANT_VIDEO_WIDTH), keep_aspect_ratio=True)
    results = model(frame, verbose=False)[0]
>>>>>>> b5bf8e679c938e015dcb00daa6217e98f28b3a74
    detections = sv.Detections.from_ultralytics(results)
    detections = object_tracker.update_with_detections(detections=detections)
    detections.data["frame_index"] = np.full(len(detections), frame_index)

    labels = [
        f"#{tracker_id} {model.model.names[class_id]} {confidence:.2f}"
        for xyxy, mask, confidence, class_id, tracker_id, data in detections
    ]

<<<<<<< HEAD
    out_frame = box_annotator.annotate(scene=resize_frame.copy(), detections=detections)
    out_frame = trace_annotator.annotate(scene=out_frame, detections=detections)
    out_frame = label_annotator.annotate(scene=out_frame, detections=detections, labels=labels)
    return out_frame, detections
=======
    # out_frame = box_annotator.annotate(scene=resize_frame.copy(), detections=detections)
    # out_frame = trace_annotator.annotate(scene=out_frame, detections=detections)
    # out_frame = label_annotator.annotate(scene=out_frame, detections=detections, labels=labels)
    return detections

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

    # dataset_name = video_name.split('.')[0] + '.json'
    # output_path = os.path.join(DATASETS_FOLDER, dataset_name)

    # with sv.JSONSink(output_path) as sink:
    #     sink.append(detections=total_detections)
    # # with open(output_path, 'w') as f:
    # #     json.dump(total_detections.to_json(), f)
    cap.release()
    print(f"Processed video {video_name} and saved detections to {video_name.split('.')[0]}.json")
>>>>>>> b5bf8e679c938e015dcb00daa6217e98f28b3a74
