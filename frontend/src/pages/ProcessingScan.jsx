import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";
import { apiScanImage } from "../utils/wardrobeStore";

const TELEMETRY_STEPS = [
  "INITIALIZING DIGITAL ARCHIVE CONNECTION...",
  "EXTRACTING CHROMATIC CORRELATION MATRIX...",
  "RUNNING FIBER TEXTURE SPECTRAL DENSITY ANALYSIS...",
  "CROSS-INDEXING WITH CAPSULE WARDROBE SCHEMAS...",
  "AI CLASSIFIER RECOMMENDATION CONVERGED!"
];

export const ProcessingScan = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [telemetryIndex, setTelemetryIndex] = useState(0);
  const [telemetryText, setTelemetryText] = useState(TELEMETRY_STEPS[0]);

  const imageFile = location.state?.imageFile;
  const imageUrl = location.state?.imageUrl;

  // Clean redirection if accessed illegally
  useEffect(() => {
    if (!imageFile || !imageUrl) {
      navigate("/app/camera");
    }
  }, [imageFile, imageUrl, navigate]);

  // Telemetry typewriter updates
  useEffect(() => {
    if (telemetryIndex >= TELEMETRY_STEPS.length - 1) return;
    
    const timer = setTimeout(() => {
      const nextIndex = telemetryIndex + 1;
      setTelemetryIndex(nextIndex);
      setTelemetryText(TELEMETRY_STEPS[nextIndex]);
    }, 700);

    return () => clearTimeout(timer);
  }, [telemetryIndex]);

  // Execute Async Image Scanning
  useEffect(() => {
    if (!imageFile) return;

    let isMounted = true;
    const executeScan = async () => {
      try {
        const result = await apiScanImage(imageFile);
        
        // Ensure a minimum 2.8s aesthetic scan delay so the user enjoys the premium sweeping laser animations
        await new Promise((resolve) => setTimeout(resolve, 2800));

        if (isMounted) {
          navigate("/app/verify", { 
            state: { 
              scanResult: result, 
              imageUrl 
            } 
          });
        }
      } catch (err) {
        console.error("AI Garment Scan Failed:", err);
        if (isMounted) {
          alert(err.message || "Garment classification timed out. Proceeding to manual verification.");
          // Create fallback stub to allow manual entry if API fails
          navigate("/app/verify", { 
            state: { 
              scanResult: {
                colorName: "Midnight Charcoal",
                colorHex: "#2A2B2E",
                textile: "Cashmere Wool Blend",
                category: "tops",
                subcategory: "knitwear",
                confidence: 0.50,
                tempFileKey: imageUrl
              }, 
              imageUrl 
            } 
          });
        }
      }
    };

    executeScan();
    return () => {
      isMounted = false;
    };
  }, [imageFile, imageUrl, navigate]);

  if (!imageUrl) return null;

  return (
    <Layout title="AI Curation Processing" hideNav>
      {/* Inline styles for sweeping laser and scan telemetry */}
      <style>{`
        @keyframes laser-sweep {
          0% { top: 0%; opacity: 0.3; }
          50% { top: 100%; opacity: 1; }
          100% { top: 0%; opacity: 0.3; }
        }
        .sweeping-laser {
          animation: laser-sweep 3.5s ease-in-out infinite;
        }
        @keyframes glow-pulse {
          0%, 100% { box-shadow: 0 0 20px 2px rgba(212, 175, 55, 0.15); }
          50% { box-shadow: 0 0 35px 8px rgba(212, 175, 55, 0.35); }
        }
        .pulse-glow {
          animation: glow-pulse 2s infinite;
        }
      `}</style>

      <div className="max-w-md mx-auto w-full pb-20 flex flex-col items-center justify-center min-h-[75vh] space-y-10 select-none">
        
        {/* Futuristic pulsing scanning block */}
        <div className="relative w-72 aspect-[3/4] rounded-2xl overflow-hidden shadow-2xl border border-white/10 bg-[#0d0e12] pulse-glow">
          {/* Garment Image */}
          <img
            src={imageUrl}
            alt="Analyzing Garment"
            className="w-full h-full object-cover opacity-85 saturate-[0.8]"
          />

          {/* Holographic matrix color overlay */}
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-tertiary/5 to-transparent pointer-events-none"></div>

          {/* Sweeping gold laser line */}
          <div className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-tertiary to-transparent sweeping-laser shadow-[0_0_15px_4px_rgba(212,175,55,0.7)] pointer-events-none"></div>

          {/* Glass scanner overlay grids */}
          <div className="absolute inset-0 pointer-events-none grid grid-cols-6 grid-rows-8 opacity-10">
            {Array.from({ length: 48 }).map((_, i) => (
              <div key={i} className="border-r border-b border-white"></div>
            ))}
          </div>
        </div>

        {/* Telemetry Loader Text */}
        <div className="w-full text-center space-y-4 px-4">
          <div className="flex justify-center items-center gap-2">
            <span className="w-2.5 h-2.5 border border-tertiary border-t-transparent rounded-full animate-spin"></span>
            <span className="font-label-sm text-[10px] uppercase tracking-[0.25em] text-tertiary font-bold animate-pulse">
              AI CLASSIFIER SCANNING
            </span>
          </div>

          <div className="h-10 flex items-center justify-center">
            <p className="font-mono text-[10px] text-on-surface-variant bg-white/[0.02] border border-white/5 px-4 py-2.5 rounded-lg select-all leading-normal max-w-sm">
              &gt; {telemetryText}
            </p>
          </div>
        </div>

      </div>
    </Layout>
  );
};

export default ProcessingScan;
