import { useState } from 'react';
import VideoUploader from './components/VideoUploader';
import VideoItem from './components/VideoItem';
import VideoPlayer from './components/VideoPlayer';
import { ArrowRightCircleIcon } from '@heroicons/react/24/outline';

function App() {
  const [videos, setVideos] = useState([]);
  const [currentVideo, setCurrentVideo] = useState(null);
  
  const handleVideoUpload = (video) => {
    setVideos(prevVideos => [...prevVideos, video]);
  };
  
  const handlePlayVideo = (video) => {
    setCurrentVideo(video);
  };
  
  const handleRemoveVideo = (videoId) => {
    setVideos(prevVideos => prevVideos.filter(video => video.id !== videoId));
    
    // If the current video is being removed, close the player
    if (currentVideo && currentVideo.id === videoId) {
      setCurrentVideo(null);
    }
  };
  
  const handleClosePlayer = () => {
    setCurrentVideo(null);
  };
  
  const handleLoadVideo = () => {
    // This will be implemented in the next phase to connect to the YOLO model
    alert('This feature will be implemented in the next phase to connect to the YOLO model');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 sm:text-4xl">
            Video Detector Annotation Agent
          </h1>
          <p className="mt-3 text-lg text-gray-600">
            Upload videos for object detection and annotation
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="card p-6 hover:shadow-md transition-shadow">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-primary-700">
              <span>Add Video</span>
            </h2>
            <VideoUploader onVideoUpload={handleVideoUpload} />
          </div>
          
          <div className="card p-6 hover:shadow-md transition-shadow">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-primary-700">
              <span>Load to Model</span>
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Send a video to the YOLO model for object detection and analysis
            </p>
            <button 
              onClick={handleLoadVideo}
              className="btn btn-primary w-full flex items-center justify-center"
              disabled={videos.length === 0}
            >
              <ArrowRightCircleIcon className="h-5 w-5 mr-2" />
              <span>Load Video to Model</span>
            </button>
          </div>
        </div>
        
        {videos.length > 0 && (
          <div className="card p-6">
            <h2 className="text-xl font-semibold mb-4 text-primary-700">Your Videos</h2>
            <div className="space-y-2">
              {videos.map(video => (
                <VideoItem
                  key={video.id}
                  video={video}
                  onPlay={handlePlayVideo}
                  onRemove={handleRemoveVideo}
                />
              ))}
            </div>
          </div>
        )}
        
        {currentVideo && (
          <VideoPlayer
            video={currentVideo}
            onClose={handleClosePlayer}
          />
        )}
      </div>
    </div>
  );
}

export default App;
