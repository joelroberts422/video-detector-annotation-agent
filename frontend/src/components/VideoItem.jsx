import { PlayIcon, ArrowRightCircleIcon, XMarkIcon, EyeIcon } from '@heroicons/react/24/solid';

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const VideoItem = ({ video, onPlay, onRemove, onLoadToModel, onViewDetections, loading = {} }) => {
  return (
    <div className="card flex items-center justify-between p-4 mb-3 group hover:shadow-lg transition-shadow duration-200">
      <div className="flex items-center">
        <div className="flex-shrink-0 w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
          <PlayIcon className="h-6 w-6 text-gray-500" />
        </div>
        <div className="ml-4">
          <h3 className="text-sm font-medium text-gray-900 truncate max-w-[250px]">{video.name}</h3>
          <p className="text-xs text-gray-500">{formatFileSize(video.size)}</p>
        </div>
      </div>
      
      <div className="flex space-x-2 items-center">
        <button
          onClick={() => onRemove(video.id)}
          className="text-gray-400 hover:text-red-500 transition-colors p-1"
          aria-label="Remove video"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
        
        <button
          onClick={() => onPlay(video)}
          className="btn btn-primary py-1.5 px-3 flex items-center"
        >
          <PlayIcon className="h-4 w-4 mr-1" />
          <span>Play</span>
        </button>
        
        <button
          onClick={() => onLoadToModel(video)}
          className="btn btn-success py-1.5 px-3 flex items-center"
        >
          <ArrowRightCircleIcon className="h-4 w-4 mr-1" />
          <span>Load to Model</span>
        </button>
        
        <button 
          onClick={() => onViewDetections(video)}
          className="btn btn-secondary py-1.5 px-3 flex items-center"
          disabled={loading[video.id] === 'loading-detections'}
        >
          <EyeIcon className="h-4 w-4 mr-1" />
          <span>{loading[video.id] === 'loading-detections' ? 'Loading...' : 'View Detections'}</span>
        </button>
      </div>
    </div>
  );
};

export default VideoItem;