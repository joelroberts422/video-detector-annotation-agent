import { useState, useEffect, useRef } from 'react';
import ReactPlayer from 'react-player';
import { XMarkIcon } from '@heroicons/react/24/solid';

const VideoPlayer = ({ video, onClose }) => {
  const [playing, setPlaying] = useState(true);
  const [volume, setVolume] = useState(0.8);
  const [played, setPlayed] = useState(0);
  const [seeking, setSeeking] = useState(false);
  const playerRef = useRef(null);
  
  // Handle keyboard shortcuts for the player
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === ' ') {
        setPlaying(!playing);
        e.preventDefault();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [playing, onClose]);
  
  const handlePlayPause = () => {
    setPlaying(!playing);
  };
  
  const handleVolumeChange = (e) => {
    setVolume(parseFloat(e.target.value));
  };
  
  const handleProgress = (state) => {
    if (!seeking) {
      setPlayed(state.played);
    }
  };
  
  const handleSeekMouseDown = () => {
    setSeeking(true);
  };
  
  const handleSeekChange = (e) => {
    setPlayed(parseFloat(e.target.value));
  };
  
  const handleSeekMouseUp = (e) => {
    setSeeking(false);
    playerRef.current.seekTo(parseFloat(e.target.value));
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-6">
      <div className="bg-black rounded-lg overflow-hidden shadow-2xl w-full max-w-4xl">
        <div className="relative">
          <button
            onClick={onClose}
            className="absolute right-2 top-2 z-10 bg-black bg-opacity-50 rounded-full p-1 text-white hover:bg-opacity-70 transition-all"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
          
          <div className="aspect-video bg-black">
            <ReactPlayer
              ref={playerRef}
              url={video.url}
              width="100%"
              height="100%"
              playing={playing}
              volume={volume}
              onProgress={handleProgress}
              progressInterval={100}
              controls={false}
            />
          </div>
          
          <div className="bg-gray-900 text-white px-4 py-3">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium truncate">{video.name}</h3>
            </div>
            
            <div className="flex flex-col space-y-2">
              <input
                type="range"
                min={0}
                max={0.999999}
                step="any"
                value={played}
                onMouseDown={handleSeekMouseDown}
                onChange={handleSeekChange}
                onMouseUp={handleSeekMouseUp}
                className="w-full accent-primary-500"
              />
              
              <div className="flex items-center justify-between">
                <button
                  onClick={handlePlayPause}
                  className="bg-primary-600 hover:bg-primary-700 rounded-lg px-4 py-1.5 text-sm"
                >
                  {playing ? 'Pause' : 'Play'}
                </button>
                
                <div className="flex items-center">
                  <span className="mr-2 text-sm">Volume</span>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step="any"
                    value={volume}
                    onChange={handleVolumeChange}
                    className="w-24 accent-primary-500"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer; 