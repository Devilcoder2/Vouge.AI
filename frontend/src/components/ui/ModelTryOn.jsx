import React, { useState, useEffect } from "react";
import { formatImageUrl } from "../../utils/wardrobeStore";

/**
 * Premium Virtual Try-On Model Component
 * Layers transparent digitized wardrobe garments over a central male/female model base.
 * Dynamically reacts to user gender settings.
 */
export const ModelTryOn = ({
  items = null,       // Can be a single item object OR an array of item objects
  genderOverride = null,
  className = "",
  showLabels = false
}) => {
  const [gender, setGender] = useState("male");
  const [tryonUrl, setTryonUrl] = useState(null);
  const [loading, setLoading] = useState(false);

  // Load active model gender bias from profile cache
  useEffect(() => {
    const loadGender = () => {
      try {
        const saved = localStorage.getItem("vogue_user_profile");
        if (saved) {
          const profile = JSON.parse(saved);
          if (profile.gender) {
            setGender(profile.gender);
          }
        }
      } catch (e) {
        console.error("Failed loading model gender preference:", e);
      }
    };

    loadGender();
    // Listen for storage changes in case gender updates on Profile page
    window.addEventListener("storage", loadGender);
    return () => window.removeEventListener("storage", loadGender);
  }, []);

  const activeGender = genderOverride || gender;
  const modelUrl = activeGender === "female" ? "/assets/female_model.png" : "/assets/male_model.png";

  // Normalize inputs to a list of items
  const outfitList = Array.isArray(items)
    ? items
    : items
    ? [items]
    : [];

  // 1. SOTA STUDIO MOCKUP INTERCEPTS (HYBRID ARCHITECTURE)
  const itemIds = outfitList.map(item => item?.id).filter(Boolean);
  
  // Detect Modern Minimalist Outfit Curation (Trench + Knit + Trouser + Boots)
  const hasTrench = itemIds.includes("trench");
  const hasKnit = itemIds.includes("knit");
  const hasTrouser = itemIds.includes("trouser");
  const hasBoots = itemIds.includes("boots");
  const isModernMinimalist = hasTrench && (hasKnit || hasTrouser || hasBoots);
  
  // Catalog of items for which we generated flawless pre-rendered studio mockups
  const PRE_RENDERED_ITEMS = ["shirt", "trench", "denim", "trouser"];
  
  let preRenderedUrl = null;
  if (isModernMinimalist) {
    preRenderedUrl = `/assets/tryon/${activeGender}_outfit_modern_minimalist.png`;
  } else if (outfitList.length === 1 && PRE_RENDERED_ITEMS.includes(outfitList[0].id)) {
    preRenderedUrl = `/assets/tryon/${activeGender}_${outfitList[0].id}.png`;
  }

  // Trigger backend SOTA Virtual Try-On dynamically for custom scanned uploads
  useEffect(() => {
    if (preRenderedUrl) {
      setTryonUrl(preRenderedUrl);
      return;
    }

    // Only process dynamic tryon if it's a single item (custom upload / scan)
    if (outfitList.length === 1 && outfitList[0]?.id) {
      const fetchDynamicTryOn = async () => {
        setLoading(true);
        try {
          const res = await fetch("http://localhost:8000/recommendations/tryon", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              item_id: outfitList[0].id,
              gender: activeGender
            })
          });
          if (res.ok) {
            const data = await res.json();
            if (data.tryon_url) {
              const absoluteUrl = data.tryon_url.startsWith("http")
                ? data.tryon_url
                : `http://localhost:8000${data.tryon_url}`;
              setTryonUrl(absoluteUrl);
            } else {
              setTryonUrl(null);
            }
          } else {
            setTryonUrl(null);
          }
        } catch (err) {
          console.error("Failed to generate dynamic tryon from backend API:", err);
          setTryonUrl(null);
        } finally {
          setLoading(false);
        }
      };

      fetchDynamicTryOn();
    } else {
      setTryonUrl(null);
    }
  }, [items, activeGender, preRenderedUrl]);

  // Group garments by category slot key for dynamic CPU fallback overlay
  const slots = {
    tops: null,
    bottoms: null,
    footwear: null,
    outerwear: null,
    accessories: null
  };

  outfitList.forEach(item => {
    if (!item) return;
    
    let cat = (item.categoryId || item.category || "").toLowerCase();
    if (!cat && Array.isArray(item.categories) && item.categories.length > 0) {
      cat = item.categories[0];
    }
    cat = (cat || "").toLowerCase();
    
    if (cat === "tops" || cat === "shirts" || cat === "knitwear") {
      slots.tops = item;
    } else if (cat === "bottoms" || cat === "pants" || cat === "trousers" || cat === "jeans") {
      slots.bottoms = item;
    } else if (cat === "footwear" || cat === "shoes" || cat === "boots") {
      slots.footwear = item;
    } else if (cat === "outerwear" || cat === "coats" || cat === "jackets" || cat === "blazers") {
      slots.outerwear = item;
    } else if (cat === "accessories" || cat === "bags" || cat === "watches") {
      slots.accessories = item;
    }
  });

  // Layer scaling coordinates matching standard centered portrait posture
  // Fits standard centered Square or Portrait viewport aspect ratios
  const layerStyles = {
    outerwear: {
      top: "16.5%",
      left: "27.5%",
      width: "45%",
      height: "42%",
      zIndex: 25,
    },
    tops: {
      top: "17.5%",
      left: "31%",
      width: "38%",
      height: "33%",
      zIndex: 15,
    },
    bottoms: {
      top: "43.5%",
      left: "32.5%",
      width: "35%",
      height: "44%",
      zIndex: 10,
    },
    footwear: {
      top: "84.5%",
      left: "37.5%",
      width: "25%",
      height: "12%",
      zIndex: 20,
    },
    accessories: {
      top: "22%",
      left: "37%",
      width: "26%",
      height: "10%",
      zIndex: 30,
    }
  };

  const getCleanImageUrl = (item) => {
    if (!item) return "";
    const imgUrl = item.image || item.processed_image_url || item.original_image_url || "";
    return formatImageUrl(imgUrl);
  };

  // If we resolved a pre-rendered portrait or dynamic VTON URL, serve it instantly
  if (tryonUrl) {
    return (
      <div className={`relative w-full aspect-[1/1] sm:aspect-[4/5] bg-[#0d0e12] rounded-xl overflow-hidden shadow-2xl border border-white/5 flex items-center justify-center select-none ${className}`}>
        {loading && (
          <div className="absolute inset-0 bg-[#0d0e12]/80 backdrop-blur-md z-50 flex flex-col items-center justify-center animate-fade-in">
            <div className="w-10 h-10 border-2 border-tertiary/20 border-t-tertiary rounded-full animate-spin mb-4"></div>
            <p className="font-label-sm text-[9px] uppercase tracking-widest text-on-surface/60 font-semibold animate-pulse">
              Synthesizing SOTA VTON...
            </p>
          </div>
        )}
        <img
          src={tryonUrl}
          alt={`${activeGender} SOTA Try-On`}
          className="absolute inset-0 w-full h-full object-cover z-0 pointer-events-none transition-all duration-700 ease-out animate-fade-in"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background/20 via-transparent to-transparent z-1 pointer-events-none" />
      </div>
    );
  }

  return (
    <div className={`relative w-full aspect-[1/1] sm:aspect-[4/5] bg-[#0d0e12] rounded-xl overflow-hidden shadow-2xl border border-white/5 flex items-center justify-center select-none ${className}`}>
      
      {/* Base Model Layer */}
      <img
        src={modelUrl}
        alt={`${activeGender} try-on model`}
        className="absolute inset-0 w-full h-full object-cover z-0 pointer-events-none"
      />
      
      {/* Ambient Lighting Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-background/20 via-transparent to-transparent z-1 pointer-events-none" />

      {/* Try-On Garment Overlays */}
      {Object.entries(slots).map(([slotKey, item]) => {
        if (!item) return null;
        const imgUrl = getCleanImageUrl(item);
        if (!imgUrl) return null;

        let coords = layerStyles[slotKey];
        
        // Handle specialized wrist snapping watch coordinate override
        const isWatch = item.id === "watch" || 
                        (item.name || "").toLowerCase().includes("watch") || 
                        (item.name || "").toLowerCase().includes("timepiece");
        if (slotKey === "accessories" && isWatch) {
          coords = activeGender === "female"
            ? { top: "52.5%", left: "27.5%", width: "5.5%", height: "5.5%", zIndex: 30 }
            : { top: "53.5%", left: "26.5%", width: "5.5%", height: "5.5%", zIndex: 30 };
        }

        return (
          <div
            key={slotKey}
            className="absolute pointer-events-none transition-all duration-700 ease-out animate-fade-in flex items-center justify-center"
            style={{
              top: coords.top,
              left: coords.left,
              width: coords.width,
              height: coords.height,
              zIndex: coords.zIndex
            }}
          >
            <img
              src={imgUrl}
              alt={item.name || slotKey}
              className="w-full h-full object-contain filter drop-shadow-[0_12px_24px_rgba(0,0,0,0.55)] drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)] brightness-[1.02] contrast-[1.03] saturate-[1.02] transition-transform duration-700"
            />
          </div>
        );
      })}

      {/* Label Indicator Badges (Optional HUD Overlay) */}
      {showLabels && outfitList.length > 0 && (
        <div className="absolute top-4 left-4 z-40 flex flex-col gap-1.5 pointer-events-none">
          {Object.entries(slots).map(([slotKey, item]) => {
            if (!item) return null;
            return (
              <div
                key={slotKey}
                className="px-2.5 py-1 rounded bg-[#16171E]/60 backdrop-blur-xl border border-white/5 flex items-center gap-1.5 animate-slide-in shadow-lg"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-tertiary" />
                <span className="text-[8px] font-label-sm uppercase tracking-widest text-on-surface/80 font-bold">
                  {slotKey}: {item.name || "Enriched"}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ModelTryOn;
