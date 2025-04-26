import { useState, useEffect } from 'react';
import VideoUploader from './components/VideoUploader';
import VideoItem from './components/VideoItem';
import VideoPlayer from './components/VideoPlayer';
import DetectionPlayer from './components/DetectionPlayer';
import { ArrowRightCircleIcon } from '@heroicons/react/24/outline';

function App() {
  const [videos, setVideos] = useState([]);
  const [serverVideos, setServerVideos] = useState([]);
  const [currentVideo, setCurrentVideo] = useState(null);
  const [currentDetections, setCurrentDetections] = useState(null);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [loading, setLoading] = useState({});
  
  // Fetch videos from server when component mounts and after uploads
  useEffect(() => {
    fetchServerVideos();
  }, []);
  
  const fetchServerVideos = async () => {
    try {
      const response = await fetch('/api/videos');
      if (!response.ok) {
        throw new Error('Failed to fetch videos from server');
      }
      const data = await response.json();
      setServerVideos(data);
    } catch (error) {
      console.error('Error fetching videos:', error);
    }
  };
  
  const uploadVideoToServer = async (videoFile) => {
    const formData = new FormData();
    formData.append('file', videoFile);
    
    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to upload video');
      }
      
      // Refresh the server videos list after successful upload
      fetchServerVideos();
      return await response.json();
    } catch (error) {
      console.error('Error uploading video:', error);
      throw error;
    }
  };
  
  const handleVideoUpload = async (video) => {
    setVideos(prevVideos => [...prevVideos, video]);
    
    try {
      setLoading(prev => ({ ...prev, [video.id]: 'uploading' }));
      await uploadVideoToServer(video.file);
      setLoading(prev => ({ ...prev, [video.id]: 'uploaded' }));
    } catch (error) {
      setLoading(prev => ({ ...prev, [video.id]: 'error' }));
      alert(`Error uploading video: ${error.message}`);
    }
  };
  
  const handlePlayVideo = (video) => {
    setCurrentVideo(video);
    setCurrentDetections(null); // Clear detections when just playing the video
  };
  
  const handlePlayServerVideo = (video) => {
    // Create a video object compatible with VideoPlayer
    const videoObj = {
      id: video.name,
      name: video.name,
      size: video.size,
      url: video.path,
      type: 'video/' + video.name.split('.').pop().toLowerCase()
    };
    setCurrentVideo(videoObj);
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
    setCurrentDetections(null); // Also clear detections when closing the player
  };
  
  const processVideoWithModel = async (videoName) => {
    try {
      const response = await fetch('/api/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ video_name: videoName }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to process video');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error processing video:', error);
      throw error;
    }
  };
  
  const handleLoadToModel = async (video) => {
    try {
      setLoading(prev => ({ ...prev, [video.id]: 'processing' }));
      
      // Check if the video is already uploaded to the server
      if (loading[video.id] !== 'uploaded' && loading[video.id] !== 'processing' && loading[video.id] !== 'processed') {
        // Upload video first if not already uploaded
        await uploadVideoToServer(video.file);
      }
      
      // Process the video with the YOLO model
      const result = await processVideoWithModel(video.name);
      setLoading(prev => ({ ...prev, [video.id]: 'processed' }));
      
      alert(`Video processed successfully: ${result.message || 'JSON data generated'}`);
    } catch (error) {
      setLoading(prev => ({ ...prev, [video.id]: 'error' }));
      alert(`Error processing video: ${error.message}`);
    }
  };
  
  const handleProcessServerVideo = async (videoName) => {
    try {
      // Process the video with the YOLO model
      const result = await processVideoWithModel(videoName);
      alert(`Video processed successfully: ${result.message || 'JSON data generated'}`);
    } catch (error) {
      alert(`Error processing video: ${error.message}`);
    }
  };

  const handleViewDetections = async (video) => {
    try {
      setLoading(prev => ({ ...prev, [video.id]: 'loading-detections' }));
      
      // Get the video name
      const videoName = video.name;
      
      // Load detection data
      const response = await fetch(`/api/detections/${videoName}`);
      if (!response.ok) {
        throw new Error('Failed to load detections');
      }
      
      const detectionData = await response.json();
      
      // Set the current video and its detections, but DON'T open the video player popup
      setCurrentVideo({...video, showInPlayer: false}); // Add a flag to indicate this should show in DetectionPlayer
      setCurrentDetections(detectionData);
      setCurrentFrame(0);
      
      setLoading(prev => ({ ...prev, [video.id]: 'detections-loaded' }));
    } catch (error) {
      console.error('Error loading detections:', error);
      setLoading(prev => ({ ...prev, [video.id]: 'error' }));
      alert(`Error loading detections: ${error.message}`);
    }
  };

  const handleLoadDetections = async (videoName) => {
    try {
      const response = await fetch(`/api/detections/${videoName}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to load detections');
      }

      const data = await response.json();
      setCurrentDetections(data.detections);
      setCurrentFrame(0);
    } catch (error) {
      console.error('Error loading detections:', error);
      alert(`Error loading detections: ${error.message}`);
    }
  }

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
              <span>Server Videos</span>
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Videos available on the server for processing
            </p>
            
            {serverVideos.length === 0 ? (
              <p className="text-center text-gray-500 italic py-8">No videos found on server</p>
            ) : (
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {serverVideos.map((video) => (
                  <div 
                    key={video.name}
                    className="card flex items-center justify-between p-3 hover:bg-gray-50"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{video.name}</p>
                      <p className="text-xs text-gray-500">{(video.size / (1024 * 1024)).toFixed(2)} MB</p>
                    </div>
                    <div className="flex space-x-2">
                      <button 
                        onClick={() => handlePlayServerVideo(video)}
                        className="btn btn-primary py-1 px-2 text-xs"
                      >
                        Play
                      </button>
                      <button 
                        onClick={() => handleProcessServerVideo(video.name)}
                        className="btn btn-success py-1 px-2 text-xs"
                      >
                        Process
                      </button>
                      <button 
                        onClick={() => handleViewDetections({
                          id: video.name,
                          name: video.name,
                          url: video.path
                        })}
                        className="btn btn-secondary py-1 px-2 text-xs"
                      >
                        View Detections
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
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
                  onLoadToModel={handleLoadToModel}
                  onViewDetections={handleViewDetections}
                  loading={loading}
                />
              ))}
            </div>
          </div>
        )}
        
        {currentVideo && !currentDetections && (
          <VideoPlayer
            video={currentVideo}
            onClose={handleClosePlayer}
          />
        )}
      </div>
      {currentVideo && currentDetections && (
        <div className="mt-8 card">
          <h2 className="text-xl font-semibold p-4 border-b">Detection Viewer</h2>
          <DetectionPlayer
            video={currentVideo}
            detections={currentDetections}
            currentFrame={currentFrame}
            setCurrentFrame={setCurrentFrame}
            onClose={() => {
              setCurrentDetections(null); 
              // Optionally also clear currentVideo if you want to fully reset the state
              // setCurrentVideo(null);
            }}
          />
        </div>
      )}
    </div>
  );
}

export default App;
