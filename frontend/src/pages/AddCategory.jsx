import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";
import { apiCreateCategory } from "../utils/wardrobeStore";

// Beautiful, curated Quiet Luxury fashion images already present in project assets
const CURATED_COVERS = [
  { name: "Curation Collage", url: "/assets/curation_collage_feature.png" },
  { name: "Textile Layout", url: "/assets/clothing_layout_gap.png" },
  { name: "Stone Knitwear", url: "/assets/tops_category.png" },
  { name: "Raw Denim Indigo", url: "/assets/bottoms_category.png" },
  { name: "Charcoal Wool Trench", url: "/assets/outerwear_category.png" },
  { name: "Polished calfskin Derby", url: "/assets/shoes_category.png" }
];

// Luxury quick classification suggestions
const SUBTITLE_SUGGESTIONS = [
  "Essentials",
  "Structured",
  "Layering",
  "Atelier",
  "Tailored",
  "Footwear",
  "Details",
  "Resortwear"
];

export const AddCategory = () => {
  const navigate = useNavigate();

  // States
  const [name, setName] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [status, setStatus] = useState("Sync Complete");
  const [image, setImage] = useState(CURATED_COVERS[0].url);
  const [customImageUrl, setCustomImageUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Scroll to top on mount
  useEffect(() => {
    window.scrollTo(0, 0);
    const mainEl = document.querySelector("main");
    if (mainEl) {
      mainEl.scrollTop = 0;
    }
  }, []);

  const handleClose = () => {
    navigate("/app/wardrobe");
  };

  // Update image when custom URL is typed
  const handleCustomImageChange = (url) => {
    setCustomImageUrl(url);
    if (url.trim()) {
      setImage(url.trim());
    } else {
      setImage(CURATED_COVERS[0].url);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setErrorMsg("Please enter a category name.");
      return;
    }

    setIsSubmitting(true);
    setErrorMsg("");

    try {
      const payload = {
        name: name.trim(),
        subtitle: subtitle.trim() || "Collection",
        image: image
      };

      const newCat = await apiCreateCategory(payload);
      
      // Create success toast notification
      const toast = document.createElement("div");
      toast.className = "fixed bottom-36 left-1/2 -translate-x-1/2 bg-on-surface text-background px-6 py-3 rounded-full font-label-sm text-[11px] uppercase tracking-[0.2em] shadow-2xl z-[99] border border-white/10 animate-fade-in flex items-center gap-2";
      toast.innerHTML = `<span class="material-symbols-outlined text-sm font-bold text-tertiary">check_circle</span> Category "${newCat.name}" Created`;
      document.body.appendChild(toast);
      
      setTimeout(() => {
        toast.classList.add("animate-fade-out");
        setTimeout(() => toast.remove(), 400);
      }, 2000);

      // Redirect back to wardrobe
      setTimeout(() => {
        navigate("/app/wardrobe");
      }, 800);
    } catch (err) {
      setErrorMsg(err.message || "A category with this name already exists in your wardrobe.");
      setIsSubmitting(false);
    }
  };

  return (
    <Layout hideNav={true} showBack={true} title="New Category">
      <div className="w-full relative pb-40">
        
        {/* Sub-Header bar */}
        <div className="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <span className="w-2.5 h-2.5 rounded-full bg-tertiary animate-pulse"></span>
            <span className="font-display text-base italic text-on-surface select-none">
              Add New Digital Wardrobe Category
            </span>
          </div>
        </div>

        {/* Responsive Grid layout */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter items-start">
          
          {/* Left Column: Live updating Wardrobe Card Preview (Sticky on Desktop) */}
          <div className="md:col-span-5 md:sticky md:top-32">
            <div className="w-full flex flex-col gap-3">
              <span className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] font-semibold select-none">
                Wardrobe Card Preview
              </span>
              
              {/* Preview Category Card - Matches the card layout in Wardrobe.jsx */}
              <div className="relative aspect-[4/5] rounded-2xl overflow-hidden glass-panel flex flex-col justify-end p-8 border border-white/15 shadow-2xl transition-all duration-700 bg-background/50 select-none">
                <img
                  alt="Category Preview"
                  className="absolute inset-0 w-full h-full object-cover opacity-60 grayscale-[0.2] transition-all duration-1000 ease-out"
                  src={image}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-background via-background/60 to-transparent"></div>
                <div className="relative z-10 space-y-2">
                  <span className="font-label-sm text-[9px] text-tertiary/80 uppercase tracking-[0.3em] block font-bold">
                    {subtitle.trim() || "CLASSIFICATION"}
                  </span>
                  <h3 className="font-display text-3xl luxury-text-gradient italic leading-none">
                    {name.trim() || "Untitled Category"}
                  </h3>
                  <div className="flex items-center gap-3 pt-4 border-t border-white/5 mt-4">
                    <span className="font-body-md text-xs text-on-surface-variant/70">
                      0 Items
                    </span>
                    <span className="w-1.5 h-1.5 rounded-full bg-white/15"></span>
                    <span className="font-label-sm text-[8px] text-on-surface-variant/50 uppercase tracking-widest font-semibold">
                      {status}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Interactive Form Fields */}
          <div className="md:col-span-7 bg-transparent">
            <form onSubmit={handleCreate} className="flex flex-col gap-10">
              
              {/* Validation Error Message */}
              {errorMsg && (
                <div className="p-4 rounded-xl bg-error-container/20 border border-error/20 flex gap-3 items-center text-error animate-fade-in select-none">
                  <span className="material-symbols-outlined text-sm font-bold">warning</span>
                  <p className="font-body text-xs font-medium">{errorMsg}</p>
                </div>
              )}

              {/* Symmetrical grid for input boxes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                
                {/* Field 1: Category Name */}
                <div className="flex flex-col gap-2 group sm:col-span-1">
                  <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-1 font-semibold select-none">
                    Category Name
                  </label>
                  <div className="relative border-b border-outline-variant/30 focus-within:border-tertiary transition-colors">
                    <input
                      className="w-full bg-transparent border-0 py-3 pl-0 pr-10 font-body-md text-body-md text-on-surface focus:ring-0 focus:outline-none placeholder:text-on-surface-variant/35"
                      type="text"
                      value={name}
                      onChange={(e) => {
                        setName(e.target.value);
                        setErrorMsg("");
                      }}
                      placeholder="E.g. Knitwear, Activewear, Bags..."
                      required
                    />
                    <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant/40 text-[18px]">
                      edit
                    </span>
                  </div>
                </div>

                {/* Field 2: Subtitle / Classification */}
                <div className="flex flex-col gap-2 group sm:col-span-1">
                  <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-1 font-semibold select-none">
                    Subtitle / Classification
                  </label>
                  <div className="relative border-b border-outline-variant/30 focus-within:border-tertiary transition-colors">
                    <input
                      className="w-full bg-transparent border-0 py-3 pl-0 pr-10 font-body-md text-body-md text-on-surface focus:ring-0 focus:outline-none placeholder:text-on-surface-variant/35"
                      type="text"
                      value={subtitle}
                      onChange={(e) => setSubtitle(e.target.value)}
                      placeholder="E.g. Essentials, Structured, Layering..."
                    />
                    <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant/40 text-[18px]">
                      label
                    </span>
                  </div>
                </div>

                {/* Field 3: Suggestion Badges (Spans full width in grid) */}
                <div className="flex flex-col gap-2 sm:col-span-2 select-none -mt-2">
                  <span className="text-[10px] text-on-surface-variant/60 uppercase tracking-wider font-semibold">Quick Subtitle Suggestions</span>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {SUBTITLE_SUGGESTIONS.map((sug) => (
                      <button
                        key={sug}
                        type="button"
                        onClick={() => setSubtitle(sug)}
                        className="px-3 py-1.5 rounded-full border border-outline-variant/30 text-[10px] uppercase tracking-wider text-on-surface-variant hover:border-outline hover:text-on-surface transition-all cursor-pointer font-semibold"
                      >
                        {sug}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Field 4: Curation Status */}
                <div className="flex flex-col gap-2 sm:col-span-2 border-t border-white/5 pt-6 select-none">
                  <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-3 font-semibold">
                    Curation Status / Sync State
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      "Sync Complete",
                      "Scanning...",
                      "Season Ready",
                      "Verified"
                    ].map((st) => {
                      const isActive = status === st;
                      return (
                        <button
                          key={st}
                          type="button"
                          onClick={() => setStatus(st)}
                          className={`w-full p-4 rounded-xl border text-center transition-all duration-300 cursor-pointer font-body-md text-xs ${
                            isActive
                              ? "border-primary bg-white/5 text-on-surface shadow-[0_0_20px_rgba(255,255,255,0.03)] font-semibold scale-[1.01]"
                              : "border-outline-variant/20 bg-transparent text-on-surface-variant hover:border-outline hover:text-on-surface"
                          }`}
                        >
                          {st}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Field 5: Cover Photo Selection (Spans full width) */}
                <div className="flex flex-col gap-4 sm:col-span-2 border-t border-white/5 pt-6 select-none">
                  <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] font-semibold">
                    Curated Fashion Cover Image
                  </label>
                  
                  {/* Grid of cover images */}
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
                    {CURATED_COVERS.map((cov) => {
                      const isActive = image === cov.url && !customImageUrl;
                      return (
                        <button
                          key={cov.url}
                          type="button"
                          onClick={() => {
                            setImage(cov.url);
                            setCustomImageUrl("");
                          }}
                          className={`aspect-square rounded-lg overflow-hidden border relative transition-all duration-300 hover:scale-[1.03] shadow-md cursor-pointer ${
                            isActive ? "border-primary ring-2 ring-primary/20 scale-[1.03]" : "border-white/10 opacity-70 hover:opacity-100"
                          }`}
                          title={cov.name}
                        >
                          <img src={cov.url} alt={cov.name} className="w-full h-full object-cover" />
                          {isActive && (
                            <div className="absolute inset-0 bg-primary/20 flex items-center justify-center">
                              <span className="material-symbols-outlined text-background text-base font-bold">check</span>
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Field 6: Custom Image URL */}
                <div className="flex flex-col gap-2 group sm:col-span-2 border-t border-white/5 pt-6">
                  <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-1 font-semibold select-none">
                    Custom Cover Photo Image URL (Optional)
                  </label>
                  <div className="relative border-b border-outline-variant/30 focus-within:border-tertiary transition-colors">
                    <input
                      className="w-full bg-transparent border-0 py-3 pl-0 pr-10 font-body-md text-body-md text-on-surface focus:ring-0 focus:outline-none placeholder:text-on-surface-variant/35"
                      type="url"
                      value={customImageUrl}
                      onChange={(e) => handleCustomImageChange(e.target.value)}
                      placeholder="Input custom web image URL..."
                    />
                    <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant/40 text-[18px]">
                      link
                    </span>
                  </div>
                </div>

              </div>
            </form>
          </div>
        </div>

        {/* Fixed Bottom Action Bar */}
        <div className="fixed bottom-0 left-0 w-full bg-background/80 backdrop-blur-2xl border-t border-outline-variant/10 px-6 py-6 z-40">
          <div className="max-w-2xl mx-auto w-full flex flex-col gap-3">
            <button
              onClick={handleCreate}
              disabled={isSubmitting}
              className="w-full py-4 bg-on-surface text-background rounded-lg font-label-sm text-[10px] uppercase tracking-[0.2em] hover:bg-on-surface/90 transition-all active:scale-[0.98] shadow-2xl font-bold cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isSubmitting ? "Creating Category..." : "Create Category"}
            </button>
            <button
              type="button"
              onClick={handleClose}
              className="w-full py-4 bg-transparent border border-white/10 text-on-surface rounded-lg font-label-sm text-[10px] uppercase tracking-[0.2em] hover:bg-white/5 transition-all active:scale-[0.98] font-bold cursor-pointer"
            >
              Cancel
            </button>
          </div>
        </div>

      </div>
    </Layout>
  );
};

export default AddCategory;
