from detector import process_video, json_to_paths
import os
import json


VIDEO_FOLDER = 'videos'
DATASETS_FOLDER = 'datasets'

if __name__ == "__main__":
    video_name = "tapco.mp4"

    # process_video(video_name)

    dataset_path = os.path.join(DATASETS_FOLDER, video_name.split('.')[0] + '.json')
    paths = json_to_paths(dataset_path)

    paths_file_path = os.path.join(DATASETS_FOLDER, video_name.split('.')[0] + '_paths.json')
    with open(paths_file_path, 'w') as f:
        json.dump(paths, f, indent=4)

