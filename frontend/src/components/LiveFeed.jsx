import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Camera, AlertCircle, Shield, ShieldAlert, Zap, Users } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const LiveFeed = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [stream, setStream] = useState(null);
  const [detections, setDetections] = useState([]);
  const [fps, setFps] = useState(0);

  // Start Webcam
  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
      setStream(mediaStream);
      setIsStreaming(true);
    } catch (err) {
      console.error("Error accessing webcam:", err);
    }
  };

  useEffect(() => {
    if (isStreaming && videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [isStreaming, stream]);

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      setIsStreaming(false);
      setDetections([]);
    }
  };

  // Inference loop
  const processFrame = useCallback(async () => {
    if (!isStreaming || !videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert canvas to blob and send to API
      canvas.toBlob(async (blob) => {
        if (!blob) return;

        const formData = new FormData();
        formData.append('file', blob, 'frame.jpg');

        try {
          const startTime = performance.now();
          const response = await fetch(`${API_BASE}/predict`, {
            method: 'POST',
            body: formData,
          });
          
          if (response.ok) {
            const result = await response.json();
            setDetections(result.faces || []);
          }
          const endTime = performance.now();
          setFps(Math.round(1000 / (endTime - startTime)));

        } catch (error) {
          console.error("Inference Error:", error);
        }
      }, 'image/jpeg', 0.8);
    }
  }, [isStreaming]);

  useEffect(() => {
    let interval;
    if (isStreaming) {
      // Run inference every 500ms for demo purposes (can be faster depending on GPU)
      interval = setInterval(processFrame, 500);
    }
    return () => clearInterval(interval);
  }, [isStreaming, processFrame]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Main Camera Feed */}
      <div className="lg:col-span-2 glass overflow-hidden flex flex-col relative">
        <div className="bg-slate-800 p-3 border-b border-glass-border flex justify-between items-center z-10">
          <div className="flex items-center gap-2">
            <Camera size={18} className="text-slate-400" />
            <h3 className="font-semibold text-slate-200">Main Entrance Camera (CAM-01)</h3>
          </div>
          {isStreaming ? (
            <span className="flex items-center gap-2 text-xs font-medium bg-rose-500/20 text-rose-400 px-2 py-1 rounded">
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
              LIVE RECORDING
            </span>
          ) : (
            <span className="flex items-center gap-2 text-xs font-medium bg-slate-500/20 text-slate-400 px-2 py-1 rounded">
              OFFLINE
            </span>
          )}
        </div>
        
        <div className="relative aspect-video bg-black flex-1 flex items-center justify-center">
          {!isStreaming ? (
            <button 
              onClick={startCamera}
              className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-lg font-medium transition-colors shadow-lg shadow-blue-500/30">
              Initialize Camera
            </button>
          ) : (
            <>
              <video 
                ref={videoRef} 
                autoPlay 
                playsInline 
                muted 
                className="absolute inset-0 w-full h-full object-contain"
              />
              <canvas ref={canvasRef} className="hidden" />
              
              {/* Bounding Boxes Overlay */}
              {detections.map((face, idx) => {
                const [x, y, w, h] = face.bbox;
                const isMask = face.prediction === "Mask";
                const isNoMask = face.prediction === "No Mask";
                const color = isMask ? "border-emerald-500" : isNoMask ? "border-rose-500" : "border-amber-500";
                
                return (
                  <div 
                    key={idx}
                    className={`absolute border-2 ${color} transition-all duration-200`}
                    style={{
                      left: `${(x / videoRef.current.videoWidth) * 100}%`,
                      top: `${(y / videoRef.current.videoHeight) * 100}%`,
                      width: `${(w / videoRef.current.videoWidth) * 100}%`,
                      height: `${(h / videoRef.current.videoHeight) * 100}%`
                    }}
                  >
                    <div className={`absolute -top-6 left-0 whitespace-nowrap px-2 py-1 text-xs font-bold text-white rounded-t ${isMask ? 'bg-emerald-500' : isNoMask ? 'bg-rose-500' : 'bg-amber-500'}`}>
                      {face.prediction} ({(face.confidence * 100).toFixed(0)}%) - ID: {face.tracking_id}
                    </div>
                  </div>
                );
              })}
            </>
          )}
        </div>
        
        {isStreaming && (
          <div className="absolute bottom-4 left-4 right-4 flex justify-between items-center z-10">
             <div className="bg-black/60 backdrop-blur text-white text-xs px-3 py-1.5 rounded flex items-center gap-2">
                <Zap size={14} className="text-yellow-400" />
                Inference FPS: {fps}
             </div>
             <button 
                onClick={stopCamera}
                className="bg-slate-700/80 hover:bg-slate-600 backdrop-blur text-white px-4 py-1.5 rounded text-sm transition-colors">
                Stop Stream
              </button>
          </div>
        )}
      </div>

      {/* Side Panel: Detections */}
      <div className="glass flex flex-col h-[600px]">
        <div className="p-4 border-b border-glass-border">
          <h3 className="font-semibold flex items-center gap-2">
            <Users size={18} className="text-blue-400" />
            Live Activity
          </h3>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
          {detections.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-500 text-sm">
               <Shield size={32} className="mb-2 opacity-50" />
               <p>Area Secure</p>
               <p>Waiting for subjects...</p>
            </div>
          ) : (
            detections.map((face, idx) => (
              <div key={idx} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-8 rounded-full ${face.prediction === 'Mask' ? 'bg-emerald-400' : face.prediction === 'No Mask' ? 'bg-rose-400' : 'bg-amber-400'}`}></div>
                  <div>
                    <p className="font-medium text-sm text-slate-200">ID: #{face.tracking_id}</p>
                    <p className="text-xs text-slate-400">Confidence: {(face.confidence * 100).toFixed(1)}%</p>
                  </div>
                </div>
                {face.prediction === 'No Mask' ? (
                  <span className="flex items-center gap-1 text-xs text-rose-400 font-medium bg-rose-400/10 px-2 py-1 rounded">
                    <AlertCircle size={12} />
                    NO MASK
                  </span>
                ) : face.prediction === 'Mask' ? (
                  <span className="flex items-center gap-1 text-xs text-emerald-400 font-medium bg-emerald-400/10 px-2 py-1 rounded">
                    <Shield size={12} />
                    COMPLIANT
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs text-amber-400 font-medium bg-amber-400/10 px-2 py-1 rounded">
                    <ShieldAlert size={12} />
                    INCORRECT
                  </span>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default LiveFeed;
