import React, { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";
import { apiCreateItem } from "../utils/wardrobeStore";
import { ModelTryOn } from "../components/ui/ModelTryOn";

const LUXURY_COLORS = [
  { name: "Midnight Charcoal", hex: "#2A2B2E" },
  { name: "Cashmere Creme", hex: "#F5EBE6" },
  { name: "Slate Gray", hex: "#707A8A" },
  { name: "Obsidian Black", hex: "#121317" },
  { name: "Sage Green", hex: "#8F9779" },
  { name: "Burgundy", hex: "#4A1525" },
  { name: "Raw Indigo", hex: "#1C2E4A" },
  { name: "Alabaster White", hex: "#F5F5F7" },
  { name: "Champagne Gold", hex: "#D4AF37" }
];

export const VerifyItem = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const scanResult = location.state?.scanResult;
  const imageUrl = location.state?.imageUrl;

  const colorInputRef = useRef(null);

  // States
  const [name, setName] = useState("");
  const [textile, setTextile] = useState("");
  const [colorName, setColorName] = useState("");
  const [colorHex, setColorHex] = useState("");
  const [secondaryColors, setSecondaryColors] = useState([]);
  const [moreDetails, setMoreDetails] = useState("");
  const [occasion, setOccasion] = useState("casual");
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [image, setImage] = useState("");
  const [verified, setVerified] = useState(true);
  const [long, setLong] = useState(false);
  const [hasAIService, setHasAIService] = useState(true);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isEyeDropperSupported, setIsEyeDropperSupported] = useState(false);
  const [viewMode, setViewMode] = useState("tryon");

  // Clean redirection if accessed illegally
  useEffect(() => {
    if (!scanResult || !imageUrl) {
      navigate("/app/camera");
      return;
    }

    setIsEyeDropperSupported("EyeDropper" in window);

    // Pre-fill states from AI scan telemetry
    const defaultName = `${scanResult.colorName || "Curated"} ${scanResult.textile || "Garment"}`;
    setName(defaultName);
    setTextile(scanResult.textile || "100% Cashmere");
    setColorName(scanResult.colorName || "Midnight Charcoal");
    setColorHex(scanResult.colorHex || "#2A2B2E");
    setOccasion(scanResult.category === "footwear" ? "casual" : "work");
    
    // Set categories (auto-map footwear slug)
    const initialCat = scanResult.category === "shoes" ? "footwear" : (scanResult.category || "tops");
    setSelectedCategories([initialCat]);
    
    // Set final image path. If scan uploaded a backend image url, use it. Otherwise use local preview url.
    setImage(scanResult.tempFileKey || imageUrl);
  }, [scanResult, imageUrl, navigate]);

  // Eye Dropper activation
  const handleEyeDrop = async () => {
    if ("EyeDropper" in window) {
      const eyeDropper = new window.EyeDropper();
      try {
        const result = await eyeDropper.open();
        const hex = result.sRGBHex.toUpperCase();
        setColorHex(hex);
        const matched = LUXURY_COLORS.find(c => c.hex.toLowerCase() === hex.toLowerCase());
        setColorName(matched ? matched.name : `Custom Color (${hex})`);
      } catch (e) {
        console.log("Eye dropper canceled");
      }
    }
  };

  // Commit garment to closet database
  const handleCommitGarment = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSubmitting(true);
    try {
      const payload = {
        name: name.trim(),
        textile: textile.trim(),
        colorName,
        colorHex,
        secondaryColors,
        moreDetails: moreDetails.trim(),
        occasion,
        image,
        verified,
        long,
        hasAIService,
        categories: selectedCategories
      };

      await apiCreateItem(payload);

      // Create micro toast notification
      const toast = document.createElement("div");
      toast.className = "fixed bottom-36 left-1/2 -translate-x-1/2 bg-on-surface text-background px-6 py-3 rounded-full font-label-sm text-[11px] uppercase tracking-[0.2em] shadow-2xl z-[99] border border-white/10 animate-fade-in flex items-center gap-2";
      toast.innerHTML = `<span class="material-symbols-outlined text-sm font-bold text-tertiary">check_circle</span> Archived in digital closet`;
      document.body.appendChild(toast);
      
      setTimeout(() => {
        toast.classList.add("animate-fade-out");
        setTimeout(() => toast.remove(), 400);
      }, 2000);

      // Redirect cleanly back to Wardrobe Inventory
      setTimeout(() => {
        navigate("/app/wardrobe");
      }, 800);
    } catch (err) {
      console.error("Error creating wardrobe item:", err);
      alert(err.message || "Failed to commit garment to virtual closet.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!imageUrl) return null;

  return (
    <Layout title="Verify Specifications" hideNav showBack>
      <div className="w-full relative pb-40 select-none">
        
        {/* Full Screen glass submit loader overlay */}
        {isSubmitting && (
          <div className="fixed inset-0 bg-background/60 backdrop-blur-md z-50 flex flex-col items-center justify-center animate-fade-in">
            <div className="w-10 h-10 border-2 border-tertiary/20 border-t-tertiary rounded-full animate-spin mb-4"></div>
            <p className="font-label-sm text-[10px] uppercase tracking-widest text-on-surface-variant/80">
              Archiving analyzed specifications to digital closet...
            </p>
          </div>
        )}

        {/* Sub-Header bar */}
        <div className="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <span className="w-2.5 h-2.5 rounded-full bg-tertiary animate-pulse"></span>
            <span className="font-display text-base italic text-on-surface">
              Verify Garment Specifications
            </span>
          </div>
          <span className="text-[10px] font-mono text-tertiary bg-tertiary/10 px-3 py-1 rounded border border-tertiary/20">
            {Math.round((scanResult?.confidence || 0.94) * 100)}% AI CONFIDENCE GAUGE
          </span>
        </div>

        {/* Form grid layout */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter items-start">
          
          {/* Left Column: Image Spotlights */}
          <div className="md:col-span-5 md:sticky md:top-32 flex flex-col gap-4">
            {/* Try-On / Flat Lay Glass Toggle Tabs */}
            <div className="flex gap-2 bg-white/[0.02] p-1 rounded-lg border border-white/5 w-full select-none">
              <button
                type="button"
                onClick={() => setViewMode("tryon")}
                className={`flex-grow py-2 text-[10px] uppercase tracking-widest font-semibold rounded-md transition-all cursor-pointer ${
                  viewMode === "tryon" ? "bg-white/5 text-on-surface border border-white/10 font-bold" : "text-on-surface-variant hover:text-on-surface bg-transparent border border-transparent font-medium"
                }`}
              >
                Model Try-On
              </button>
              <button
                type="button"
                onClick={() => setViewMode("flat")}
                className={`flex-grow py-2 text-[10px] uppercase tracking-widest font-semibold rounded-md transition-all cursor-pointer ${
                  viewMode === "flat" ? "bg-white/5 text-on-surface border border-white/10 font-bold" : "text-on-surface-variant hover:text-on-surface bg-transparent border border-transparent font-medium"
                }`}
              >
                Flat Lay
              </button>
            </div>

            <div className="w-full bg-[#0d0e12] relative flex justify-center rounded-xl overflow-hidden shadow-2xl border border-white/5 aspect-[4/5] md:aspect-square">
              {viewMode === "tryon" ? (
                <ModelTryOn
                  items={{
                    categoryId: selectedCategories[0],
                    category: selectedCategories[0],
                    image: image,
                    name: name
                  }}
                  className="!rounded-none !border-none shadow-none"
                />
              ) : (
                <img
                  alt="Uploaded garment preview"
                  className="w-full h-full object-cover"
                  src={imageUrl}
                />
              )}
              <div className="absolute bottom-6 right-6 bg-[#1A1A1A]/40 backdrop-blur-xl border border-tertiary/30 rounded-full px-4 py-2 flex items-center gap-2 shadow-2xl select-none z-30">
                <span className="material-symbols-outlined text-tertiary text-[16px] animate-pulse" style={{ fontVariationSettings: "'FILL' 1" }}>
                  auto_awesome
                </span>
                <span className="font-label-sm text-[9px] text-on-surface uppercase tracking-[0.15em] font-semibold">
                  AI Analyzed
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Spec form controls */}
          <form onSubmit={handleCommitGarment} className="md:col-span-7 bg-transparent space-y-8">
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              
              {/* Garment Name */}
              <div className="flex flex-col gap-2 group sm:col-span-1">
                <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-1 font-semibold">
                  Garment Label Name
                </label>
                <div className="relative border-b border-outline-variant/30 focus-within:border-tertiary transition-colors">
                  <input
                    required
                    className="w-full bg-transparent border-0 py-3 pl-0 pr-10 font-body-md text-body-md text-on-surface focus:ring-0 focus:outline-none placeholder:text-on-surface-variant/40"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter garment label"
                  />
                  <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant/40 text-[18px]">
                    edit
                  </span>
                </div>
              </div>

              {/* Occasions */}
              <div className="flex flex-col gap-2 sm:col-span-1">
                <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-1.5 font-semibold">
                  Recommended Occasion
                </label>
                <div className="flex flex-wrap gap-2 pt-1">
                  {["casual", "work", "evening", "event"].map((occ) => {
                    const isActive = occasion === occ;
                    const labels = {
                      casual: "Casual",
                      work: "Workwear",
                      evening: "Evening",
                      event: "Special Event"
                    };
                    return (
                      <button
                        key={occ}
                        type="button"
                        onClick={() => setOccasion(occ)}
                        className={`px-3 py-1.5 rounded-full border text-[10px] uppercase tracking-wider font-semibold transition-all duration-300 cursor-pointer ${
                          isActive
                            ? "border-primary bg-white/5 text-on-surface"
                            : "border-outline-variant/30 text-on-surface-variant hover:border-outline hover:text-on-surface bg-transparent"
                        }`}
                      >
                        {labels[occ]}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Fabric composition */}
              <div className="flex flex-col gap-2 group sm:col-span-1">
                <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-1 font-semibold">
                  Analyzed Fabric Blend
                </label>
                <div className="relative border-b border-outline-variant/30 focus-within:border-tertiary transition-colors">
                  <input
                    className="w-full bg-transparent border-0 py-3 pl-0 pr-10 font-body-md text-body-md text-on-surface focus:ring-0 focus:outline-none placeholder:text-on-surface-variant/40"
                    type="text"
                    value={textile}
                    onChange={(e) => setTextile(e.target.value)}
                    placeholder="Enter textile blend (e.g. 100% Merino Wool)"
                  />
                  <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant/40 text-[18px]">
                    tshirt
                  </span>
                </div>
              </div>

              {/* Categories classifications */}
              <div className="flex flex-col gap-2 sm:col-span-1">
                <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-1.5 font-semibold">
                  Closet Classifications
                </label>
                <div className="flex flex-wrap gap-2 pt-1">
                  {[
                    { id: "outerwear", label: "Outerwear" },
                    { id: "tops", label: "Tops" },
                    { id: "bottoms", label: "Bottoms" },
                    { id: "footwear", label: "Shoes" },
                    { id: "accessories", label: "Accessories" }
                  ].map((cat) => {
                    const isActive = selectedCategories.includes(cat.id);
                    return (
                      <button
                        key={cat.id}
                        type="button"
                        onClick={() => {
                          if (isActive) {
                            if (selectedCategories.length > 1) {
                              setSelectedCategories(selectedCategories.filter((id) => id !== cat.id));
                            }
                          } else {
                            setSelectedCategories([...selectedCategories, cat.id]);
                          }
                        }}
                        className={`px-3 py-1.5 rounded-full border text-[10px] uppercase tracking-wider font-semibold transition-all duration-300 cursor-pointer ${
                          isActive
                            ? "border-primary bg-white/5 text-on-surface"
                            : "border-outline-variant/30 text-on-surface-variant hover:border-outline hover:text-on-surface bg-transparent"
                        }`}
                      >
                        {cat.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Colors */}
              <div className="flex flex-col gap-6 sm:col-span-2 border-t border-white/5 pt-6">
                <div>
                  <h4 className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-4 font-semibold">
                    Dominant Chromatic Color Profile
                  </h4>
                  
                  <input
                    type="color"
                    ref={colorInputRef}
                    value={colorHex}
                    onChange={(e) => {
                      const hex = e.target.value.toUpperCase();
                      setColorHex(hex);
                      const matched = LUXURY_COLORS.find(c => c.hex.toLowerCase() === hex.toLowerCase());
                      setColorName(matched ? matched.name : `Custom Color (${hex})`);
                    }}
                    className="sr-only"
                  />

                  <div className="flex gap-4 items-center">
                    <div
                      className="w-12 h-12 rounded-full border border-white/20 shadow-inner relative flex items-center justify-center cursor-pointer overflow-hidden transition-transform duration-300 hover:scale-105 group/color"
                      style={{ backgroundColor: colorHex }}
                      onClick={() => colorInputRef.current.click()}
                      title="Open Color Wheel"
                    >
                      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/color:opacity-100 transition-opacity flex items-center justify-center">
                        <span className="material-symbols-outlined text-on-surface text-sm">palette</span>
                      </div>
                    </div>

                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-2.5">
                        <span className="font-body-md text-sm text-on-surface font-semibold">{colorName}</span>
                        <span className="text-[10px] font-mono text-on-surface-variant bg-white/5 border border-white/5 px-2 py-0.5 rounded">{colorHex}</span>
                      </div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => colorInputRef.current.click()}
                          className="text-[9px] uppercase tracking-widest font-label-sm border border-white/10 px-2.5 py-1.5 rounded bg-white/[0.02] hover:bg-white/5 transition-all text-on-surface cursor-pointer font-bold"
                        >
                          Manual Picker
                        </button>
                        {isEyeDropperSupported && (
                          <button
                            type="button"
                            onClick={handleEyeDrop}
                            className="text-[9px] uppercase tracking-widest font-label-sm border border-tertiary/20 px-2.5 py-1.5 rounded bg-tertiary/5 hover:bg-tertiary/10 transition-all text-tertiary flex items-center gap-1 cursor-pointer font-bold"
                          >
                            <span className="material-symbols-outlined text-[12px] font-bold">colorize</span> Eye Dropper
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Extra Details */}
              <div className="flex flex-col gap-2 group sm:col-span-2 border-t border-white/5 pt-6">
                <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-1 font-semibold">
                  Garment Curation & Fit Notes
                </label>
                <div className="relative border-b border-outline-variant/30 focus-within:border-tertiary transition-colors">
                  <textarea
                    className="w-full bg-transparent border-0 py-3 pl-0 pr-10 font-body-md text-body-md text-on-surface focus:ring-0 focus:outline-none placeholder:text-on-surface-variant/35 resize-none h-20"
                    value={moreDetails}
                    onChange={(e) => setMoreDetails(e.target.value)}
                    placeholder="Enter fit, silhouette, pattern details or other curation notes..."
                  />
                  <span className="material-symbols-outlined absolute right-2 top-3 text-on-surface-variant/40 text-[18px]">
                    notes
                  </span>
                </div>
              </div>

            </div>

            {/* Commit controls */}
            <div className="pt-4 border-t border-white/5">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-4 bg-on-surface text-background rounded-lg font-label-sm text-[10px] uppercase tracking-[0.2em] hover:bg-on-surface/90 transition-all active:scale-[0.98] shadow-2xl font-bold cursor-pointer disabled:opacity-50"
              >
                {isSubmitting ? "Archiving garment..." : "Commit to digital closet"}
              </button>
            </div>

          </form>

        </div>
      </div>
    </Layout>
  );
};

export default VerifyItem;
