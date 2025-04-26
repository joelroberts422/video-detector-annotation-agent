import React, { useState, useEffect, useRef } from "react";

const CLASSES_NAMES = {0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 6: 'train', 7: 'truck'};
const COLOR_PALETTE = {0: 'A351FB', 1: 'FF4040', 2: 'FFA1A0', 3: 'FF7633', 5: 'D1D435', 6: '4CFB12', 7: '94CF1A'};

const DetectionPlayer = ({ video, detections, currentFrame, setCurrentFrame, onClose }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [videoSpeed, setVideoSpeed] = useState(1);
  const [videoInfo, setVideoInfo] = useState({ width: 640, height: 480, fps: 30, total_frames: 0 });
  const [detectionsByFrame, setDetectionsByFrame] = useState({});
  const [videoDimensions, setVideoDimensions] = useState({ width: 0, height: 0 });
  const [annotationsOn, setAnnotationsOn] = useState(true);
  const [highlightedTrajectory, setHighlightedTrajectory] = useState(null);
  const videoRef = useRef(null);
  const animationFrameRef = useRef(null);
  
  const labelConstant = 20; // Smaller than original for a more compact UI

  useEffect(() => {
    // If video or detections change, reset and prepare the player
    if (video && detections) {
      setVideoInfo(prevInfo => ({
        ...prevInfo,
        ...(detections.video_info || {})
      }));
      
      // Group detections by frame for easier access
      const byFrame = createDetectionsByFrameDict(detections.detections || []);
      setDetectionsByFrame(byFrame);
      
      // Reset playback state
      setIsPlaying(false);
      setCurrentFrame(0);
      
      if (videoRef.current) {
        videoRef.current.currentTime = 0;
      }
    }
  }, [video, detections, setCurrentFrame]);

  const createDetectionsByFrameDict = (detections) => {
    return detections.reduce((acc, detection) => {
      const frameIndex = detection.frame_index;
      if (!acc[frameIndex]) {
        acc[frameIndex] = [];
      }
      acc[frameIndex].push(detection);
      return acc;
    }, {});
  };

  useEffect(() => {
    const videoElement = videoRef.current;
    if (videoElement) {
    // Replace lines 50-55 with this improved function:
    const updateVideoDimensions = () => {
      const rect = videoElement.getBoundingClientRect();
      const videoWidth = videoElement.videoWidth || videoInfo.width;
      const videoHeight = videoElement.videoHeight || videoInfo.height;
      
      // Calculate scaling factor between original video and rendered size
      let displayWidth = rect.width;
      let displayHeight = rect.height;
      
      // Check if video is letterboxed (black bars on top/bottom)
      const videoRatio = videoWidth / videoHeight;
      const displayRatio = displayWidth / displayHeight;
      
      // Adjust dimensions to account for letterboxing
      let offsetX = 0;
      let offsetY = 0;
      
      if (displayRatio > videoRatio) {
        // Video has black bars on sides
        displayWidth = displayHeight * videoRatio;
        offsetX = (rect.width - displayWidth) / 2;
      } else {
        // Video has black bars on top/bottom
        displayHeight = displayWidth / videoRatio;
        offsetY = (rect.height - displayHeight) / 2;
      }
      
      setVideoDimensions({
        width: displayWidth,
        height: displayHeight,
        offsetX: offsetX,
        offsetY: offsetY,
        actualWidth: rect.width,
        actualHeight: rect.height
      });
    };

      videoElement.addEventListener('loadedmetadata', updateVideoDimensions);
      window.addEventListener('resize', updateVideoDimensions);
      videoElement.addEventListener('loadeddata', updateVideoDimensions);
      videoElement.addEventListener('canplay', updateVideoDimensions);
      updateVideoDimensions();

      const updateFrame = () => {
        const currentTime = videoElement.currentTime;
        const newFrame = Math.floor(currentTime * videoInfo.fps);
        setCurrentFrame(newFrame);
        animationFrameRef.current = requestAnimationFrame(updateFrame);
      };

      if (isPlaying) {
        animationFrameRef.current = requestAnimationFrame(updateFrame);
      } else {
        try {
          videoElement.currentTime = currentFrame / videoInfo.fps;
        } catch (error) {
          console.error("Error setting video time:", error);
        }
      }

      const handleVideoEnd = () => {
        videoElement.currentTime = 0;
        setCurrentFrame(0);
        setIsPlaying(false);
      };
      
      videoElement.addEventListener('ended', handleVideoEnd);

      return () => {
        videoElement.removeEventListener('loadedmetadata', updateVideoDimensions);
        window.removeEventListener('resize', updateVideoDimensions);
        videoElement.removeEventListener('ended', handleVideoEnd);
        cancelAnimationFrame(animationFrameRef.current);
      };
    }
  }, [videoRef, videoInfo.fps, currentFrame, isPlaying, setCurrentFrame]);

  useEffect(() => {
    const videoElement = videoRef.current;
    if (videoElement) {
      videoElement.playbackRate = videoSpeed;
      if (isPlaying) {
        videoElement.play();
      } else {
        videoElement.pause();
        cancelAnimationFrame(animationFrameRef.current);
      }
    }
  }, [isPlaying, videoSpeed]);

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleFrameChange = (e) => {
    const newFrame = parseInt(e.target.value);
    setCurrentFrame(newFrame);
    if (videoRef.current) {
      videoRef.current.currentTime = newFrame / videoInfo.fps;
    }
  };

  const toggleAnnotations = () => {
    setAnnotationsOn(!annotationsOn);
  };

  const updateHighlightedTrajectory = (trackerId) => {
    setHighlightedTrajectory(prev => prev === trackerId ? null : trackerId);
  };

    const getLabelHeight = () => {
    return labelConstant * (videoDimensions.height / videoInfo.height);
    };

    const getLabelWidth = () => {
    const scale = videoDimensions.width / videoInfo.width;
    return 5 * labelConstant * scale;
    };

    const getLabelFontSize = () => {
    const scale = Math.min(
        videoDimensions.width / videoInfo.width,
        videoDimensions.height / videoInfo.height
    );
    return 0.7 * labelConstant * scale;
    };

    const getLabelOffset = () => {
    const scale = Math.min(
        videoDimensions.width / videoInfo.width,
        videoDimensions.height / videoInfo.height
    );
    return 0.2 * labelConstant * scale;
    };

  if (!video || !detections) {
    return (
      <div className="text-center p-4 text-gray-500">
        Select a video and load its detections to view
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="relative" style={{ width: '100%', maxHeight: '70vh' }}>
        <video
          src={video.url}
          ref={videoRef}
          style={{ width: '100%', height: 'auto', maxHeight: '70vh' }}
          controls={false}
          muted
          playsInline
        />
        {annotationsOn && detectionsByFrame[currentFrame] && (
            // Replace the SVG style object around line 160-170:
            <svg
            style={{
                position: 'absolute',
                top: videoDimensions.offsetY || 0,
                left: videoDimensions.offsetX || 0,
                width: videoDimensions.width || '100%',
                height: videoDimensions.height || '100%',
                pointerEvents: 'auto',  // Changed to auto to allow clicking
            }}
            >
            {detectionsByFrame[currentFrame].map((detection, index) => {
                const scaleX = videoDimensions.width / videoInfo.width;
                const scaleY = videoDimensions.height / videoInfo.height;
                
                const x = detection.x_min * scaleX;
                const y = detection.y_min * scaleY;
                const w = (detection.x_max - detection.x_min) * scaleX;
                const h = (detection.y_max - detection.y_min) * scaleY;

              // Only attempt to draw if we have valid dimensions
              if (isNaN(x) || isNaN(y) || isNaN(w) || isNaN(h)) return null;
              
              const color = `#${COLOR_PALETTE[detection.class_id] || 'FF0000'}`;
              const isHighlighted = detection.tracker_id === highlightedTrajectory;
              
              // For trajectory lines (if available in future)
              const centerX = x + w/2;
              const centerY = y + h/2;

              return (
                <g 
                  key={`detection_${index}`} 
                  style={{ cursor: 'pointer' }}
                  onMouseDown={(e) => {
                    e.stopPropagation();
                    updateHighlightedTrajectory(detection.tracker_id);
                  }}
                >
                  <rect
                    x={x}
                    y={y}
                    width={w}
                    height={h}
                    stroke={isHighlighted ? "red" : color}
                    strokeWidth={isHighlighted ? "3" : "2"}
                    fill="transparent"
                  />
                  <rect
                    x={x}
                    y={y - getLabelHeight()}
                    width={getLabelWidth()}
                    height={getLabelHeight()}
                    stroke={isHighlighted ? "red" : color}
                    strokeWidth="1"
                    fill={isHighlighted ? "rgba(255,0,0,0.7)" : `${color}CC`}
                  />
                  <text
                    x={x + getLabelOffset()}
                    y={y - getLabelOffset()}
                    fill="white"
                    fontSize={getLabelFontSize()}
                    fontWeight="bold"
                  >
                    {`${detection.tracker_id}, ${CLASSES_NAMES[detection.class_id] || 'unknown'}, ${detection.confidence.toFixed(2)}`}
                  </text>
                </g>
              );
            })}
          </svg>
        )}
      </div>

      <div className="p-4 bg-gray-100 border-t">
        <div className="flex items-center justify-between mb-2">
          <button 
            onClick={handlePlayPause} 
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            {isPlaying ? 'Pause' : 'Play'}
          </button>
          
            <div className="flex items-center space-x-2">
            <label className="text-sm">Speed:</label>
            <select 
                value={videoSpeed} 
                onChange={(e) => setVideoSpeed(parseFloat(e.target.value))}
                className="border rounded px-2 py-1"
            >
                <option value={0.25}>0.25x</option>
                <option value={0.5}>0.5x</option>
                <option value={1}>1x</option>
                <option value={1.5}>1.5x</option>
                <option value={2}>2x</option>
            </select>
            
            <button 
                onClick={toggleAnnotations}
                className={`px-3 py-1 rounded ${annotationsOn ? 'bg-green-600 text-white' : 'bg-gray-300'}`}
            >
                {annotationsOn ? 'Annotations On' : 'Annotations Off'}
            </button>
            
            <button 
                onClick={onClose} 
                className="px-3 py-1 rounded bg-red-600 text-white hover:bg-red-700"
            >
                Close
            </button>
            </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-sm">{currentFrame}</span>
          <input 
            type="range" 
            min="0" 
            max={videoInfo.total_frames - 1 || 100}
            value={currentFrame} 
            onChange={handleFrameChange}
            className="w-full"
          />
          <span className="text-sm">{videoInfo.total_frames - 1 || '?'}</span>
        </div>
      </div>
    </div>
  );
};

export default DetectionPlayer;