import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";

export const CameraCapture = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [isCapturingSimulated, setIsCapturingSimulated] = useState(false);

  // Handle local file choosing
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      proceedToProcessing(file);
    }
  };

  // Drag-and-drop handlers
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith("image/")) {
      proceedToProcessing(file);
    }
  };

  const proceedToProcessing = (file) => {
    const localUrl = URL.createObjectURL(file);
    navigate("/app/processing", { 
      state: { 
        imageFile: file, 
        imageUrl: localUrl 
      } 
    });
  };

  // Trigger simulated camera snapshot
  const triggerSimulatedCapture = async () => {
    setIsCapturingSimulated(true);
    
    // Simulate camera click shutter delay
    await new Promise((resolve) => setTimeout(resolve, 800));
    
    // Create a mock canvas image representing a captured garment (e.g. blazer)
    try {
      const response = await fetch("/assets/outerwear_category.png");
      const blob = await response.blob();
      const mockFile = new File([blob], "camera-capture.png", { type: "image/png" });
      proceedToProcessing(mockFile);
    } catch (err) {
      // Fallback in case outerwear asset is missing
      const canvas = document.createElement("canvas");
      canvas.width = 600;
      canvas.height = 800;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#1E2024";
      ctx.fillRect(0, 0, 600, 800);
      ctx.fillStyle = "#adc6ff";
      ctx.font = "italic 24px serif";
      ctx.fillText("VOGUE.AI CAPTURED PIECE", 150, 400);
      
      canvas.toBlob((blob) => {
        const mockFile = new File([blob], "simulated-garment.png", { type: "image/png" });
        proceedToProcessing(mockFile);
      }, "image/png");
    }
  };

  return (
    <Layout title="Garment Capture" showBack>
      <div className="max-w-2xl mx-auto w-full pb-20 space-y-8 select-none">
        
        {/* Sub-Header info block */}
        <div className="text-center space-y-2">
          <span className="w-2 h-2 rounded-full bg-tertiary inline-block animate-ping mr-2"></span>
          <span className="font-label-sm text-[10px] uppercase tracking-[0.25em] text-on-surface-variant font-bold">
            Digitizing Closet
          </span>
          <h2 className="font-display text-3xl italic luxury-text-gradient">
            Archive a New Piece
          </h2>
          <p className="font-body text-xs text-on-surface-variant/60 max-w-md mx-auto leading-relaxed">
            Photograph your garment or upload an editorial flatlay to activate instant AI pattern, color, and textile analysis.
          </p>
        </div>

        {/* Shutter simulated camera viewport */}
        <div className="relative aspect-[4/5] sm:aspect-video rounded-2xl overflow-hidden border border-white/5 bg-[#0D0E12] shadow-2xl flex flex-col items-center justify-center p-6 group">
          
          {/* Simulated Viewfinder overlay corners */}
          <div className="absolute top-6 left-6 w-8 h-8 border-t-2 border-l-2 border-tertiary/40 rounded-tl-md group-hover:border-tertiary transition-colors duration-500"></div>
          <div className="absolute top-6 right-6 w-8 h-8 border-t-2 border-r-2 border-tertiary/40 rounded-tr-md group-hover:border-tertiary transition-colors duration-500"></div>
          <div className="absolute bottom-6 left-6 w-8 h-8 border-b-2 border-l-2 border-tertiary/40 rounded-bl-md group-hover:border-tertiary transition-colors duration-500"></div>
          <div className="absolute bottom-6 right-6 w-8 h-8 border-b-2 border-r-2 border-tertiary/40 rounded-br-md group-hover:border-tertiary transition-colors duration-500"></div>
          
          {/* Viewfinder grid alignment guides */}
          <div className="absolute inset-0 pointer-events-none grid grid-cols-3 grid-rows-3 opacity-25">
            <div className="border-r border-b border-white/10"></div>
            <div className="border-r border-b border-white/10"></div>
            <div className="border-b border-white/10"></div>
            <div className="border-r border-b border-white/10"></div>
            <div className="border-r border-b border-white/10"></div>
            <div className="border-b border-white/10"></div>
            <div className="border-r border-white/10"></div>
            <div className="border-r border-white/10"></div>
            <div></div>
          </div>

          {/* Flash screen overlay during capture snaps */}
          {isCapturingSimulated && (
            <div className="absolute inset-0 bg-white z-40 animate-flash flex items-center justify-center">
              <span className="material-symbols-outlined text-background text-5xl">photo_camera</span>
            </div>
          )}

          {/* Viewfinder Action Center */}
          <div className="relative z-10 flex flex-col items-center text-center space-y-6">
            <span className="material-symbols-outlined text-5xl text-tertiary/65 animate-pulse">
              photo_camera
            </span>
            <div>
              <p className="font-display text-lg italic text-on-surface mb-1">
                Virtual Archival Camera
              </p>
              <p className="font-body text-[11px] text-on-surface-variant/40 max-w-xs leading-relaxed font-light">
                Align garment flat in focus brackets and click below to snap.
              </p>
            </div>
            
            <button
              onClick={triggerSimulatedCapture}
              disabled={isCapturingSimulated}
              className="px-6 py-3.5 glass-panel bg-white/5 hover:bg-white/10 text-on-surface text-[10px] uppercase font-label-sm tracking-[0.2em] rounded-full transition-all duration-300 hover:scale-105 active:scale-95 shadow-lg flex items-center gap-2 cursor-pointer font-bold disabled:opacity-50"
            >
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
              Shutter Trigger
            </button>
          </div>
        </div>

        {/* Drag and Drop Upload container */}
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
          className={`border border-dashed rounded-2xl p-10 flex flex-col items-center justify-center text-center cursor-pointer shadow-xl select-none transition-all duration-500 ${
            isDragActive 
              ? "border-tertiary bg-tertiary/5 scale-[0.99] ring-2 ring-tertiary/20" 
              : "border-white/10 hover:border-white/20 hover:bg-white/[0.01]"
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            className="hidden"
          />
          <span className="material-symbols-outlined text-4xl text-on-surface-variant/50 mb-4">
            cloud_upload
          </span>
          <p className="font-display text-lg italic text-on-surface mb-2">
            Upload Flatlay Photography
          </p>
          <p className="font-body text-xs text-on-surface-variant/50 max-w-sm leading-relaxed font-light">
            Drag & drop your PNG, JPEG, or WebP photo files here, or <span className="text-tertiary font-medium">browse local library</span>.
          </p>
        </div>

      </div>
    </Layout>
  );
};

export default CameraCapture;
