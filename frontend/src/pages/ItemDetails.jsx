import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { apiGetItem, apiUpdateItem, apiDeleteItem } from "../utils/wardrobeStore";
import Layout from "../components/layout/Layout";
import { ModelTryOn } from "../components/ui/ModelTryOn";

// Predefined premium Quiet Luxury color palette options
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

export const ItemDetails = ({
  categoryId: propCategoryId,
  itemId: propItemId,
  initialIsEdit = false,
  onSave,
  onDelete,
  onClose
}) => {
  const { categoryId: routeCategoryId, itemId: routeItemId } = useParams();
  const navigate = useNavigate();

  // Determine if we are running in page (router) mode or prop-controlled mode
  const isControlled = !!(propCategoryId && propItemId);
  const activeCategoryId = isControlled ? propCategoryId : routeCategoryId;
  const activeItemId = isControlled ? propItemId : routeItemId;

  // Refs for hidden inputs
  const primaryColorInputRef = useRef(null);
  const secondaryColorInputRef = useRef(null);

  // States
  const [isEditMode, setIsEditMode] = useState(initialIsEdit);
  const [name, setName] = useState("");
  const [textile, setTextile] = useState("");
  const [colorName, setColorName] = useState("");
  const [colorHex, setColorHex] = useState("");
  const [secondaryColors, setSecondaryColors] = useState([]);
  const [moreDetails, setMoreDetails] = useState("");
  const [occasion, setOccasion] = useState("casual");
  const [image, setImage] = useState("");
  const [verified, setVerified] = useState(false);
  const [long, setLong] = useState(false);
  const [hasAIService, setHasAIService] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [viewMode, setViewMode] = useState("tryon");

  // UI state for browser EyeDropper API availability
  const [isEyeDropperSupported, setIsEyeDropperSupported] = useState(false);

  // Original data for Reset functionality
  const [originalData, setOriginalData] = useState(null);

  // Async States
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Detect EyeDropper API support on mount & reset viewport scroll to top
  useEffect(() => {
    setIsEyeDropperSupported("EyeDropper" in window);
    window.scrollTo(0, 0);
    const mainEl = document.querySelector("main");
    if (mainEl) {
      mainEl.scrollTop = 0;
    }
  }, [activeCategoryId, activeItemId]);

  // Load item details from store asynchronously
  useEffect(() => {
    let isMounted = true;
    const fetchItem = async () => {
      setIsLoading(true);
      setErrorMsg("");
      try {
        const item = await apiGetItem(activeItemId);
        if (isMounted) {
          if (item) {
            const data = {
              name: item.name || "",
              textile: item.textile || "",
              colorName: item.colorName || "Midnight Charcoal",
              colorHex: item.colorHex || "#2A2B2E",
              secondaryColors: item.secondaryColors || [],
              moreDetails: item.moreDetails || "",
              occasion: item.occasion || "casual",
              image: item.image || "/assets/blouse_recent.png",
              verified: !!item.verified,
              long: !!item.long,
              hasAIService: !!item.hasAIService,
              categoryId: activeCategoryId,
              categories: item.categories || [activeCategoryId]
            };
            
            setOriginalData(data);
            loadFields(data);
          } else {
            setErrorMsg("Garment not found.");
          }
        }
      } catch (err) {
        console.error("Error fetching item details:", err);
        if (isMounted) {
          setErrorMsg(err.message || "Failed to load garment specifications.");
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    fetchItem();
    return () => {
      isMounted = false;
    };
  }, [activeCategoryId, activeItemId]);

  const loadFields = (data) => {
    setName(data.name);
    setTextile(data.textile);
    setColorName(data.colorName);
    setColorHex(data.colorHex);
    setSecondaryColors(data.secondaryColors);
    setMoreDetails(data.moreDetails);
    setOccasion(data.occasion);
    setImage(data.image);
    setVerified(data.verified);
    setLong(data.long);
    setHasAIService(data.hasAIService);
    setSelectedCategories(data.categories || [data.categoryId]);
  };

  // Reset fields to last saved state
  const handleReset = () => {
    if (originalData) {
      loadFields(originalData);
    }
  };

  // Handle Cancel / Close action
  const handleClose = () => {
    if (isControlled && onClose) {
      onClose();
    } else {
      if (window.history.length > 1) {
        navigate(-1);
      } else {
        navigate(`/app/inventory/${activeCategoryId}`);
      }
    }
  };

  // Eye Dropper activation for Primary Color
  const handleEyeDropPrimary = async () => {
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

  // Add Secondary Color method
  const handleAddSecondaryColor = (hex) => {
    const upperHex = hex.toUpperCase();
    const matched = LUXURY_COLORS.find(c => c.hex.toLowerCase() === hex.toLowerCase());
    const name = matched ? matched.name : `Accent (${upperHex})`;
    
    // Don't add duplicate accent colors
    if (secondaryColors.some(c => c.hex.toUpperCase() === upperHex)) return;
    
    setSecondaryColors([...secondaryColors, { name, hex: upperHex }]);
  };

  // Eye Dropper activation for Secondary Color
  const handleEyeDropSecondary = async () => {
    if ("EyeDropper" in window) {
      const eyeDropper = new window.EyeDropper();
      try {
        const result = await eyeDropper.open();
        handleAddSecondaryColor(result.sRGBHex);
      } catch (e) {
        console.log("Eye dropper canceled");
      }
    }
  };

  // Handle Save
  const handleSave = async () => {
    const updatedFields = {
      name,
      textile,
      colorName,
      colorHex,
      secondaryColors,
      moreDetails,
      occasion,
      image,
      verified,
      long,
      hasAIService,
      categories: selectedCategories
    };

    setIsSubmitting(true);
    try {
      if (isControlled && onSave) {
        await onSave(activeCategoryId, activeItemId, updatedFields);
      } else {
        const updatedItem = await apiUpdateItem(activeItemId, updatedFields);
        const data = {
          name: updatedItem.name || "",
          textile: updatedItem.textile || "",
          colorName: updatedItem.colorName || "Midnight Charcoal",
          colorHex: updatedItem.colorHex || "#2A2B2E",
          secondaryColors: updatedItem.secondaryColors || [],
          moreDetails: updatedItem.moreDetails || "",
          occasion: updatedItem.occasion || "casual",
          image: updatedItem.image || "/assets/blouse_recent.png",
          verified: !!updatedItem.verified,
          long: !!updatedItem.long,
          hasAIService: !!updatedItem.hasAIService,
          categoryId: activeCategoryId,
          categories: updatedItem.categories || [activeCategoryId]
        };
        setOriginalData(data);
        loadFields(data);
        setIsEditMode(false);

        // Create micro toast notification
        const toast = document.createElement("div");
        toast.className = "fixed bottom-36 left-1/2 -translate-x-1/2 bg-on-surface text-background px-6 py-3 rounded-full font-label-sm text-[11px] uppercase tracking-[0.2em] shadow-2xl z-[99] border border-white/10 animate-fade-in flex items-center gap-2";
        toast.innerHTML = `<span class="material-symbols-outlined text-sm font-bold text-tertiary">check_circle</span> Changes Saved`;
        document.body.appendChild(toast);
        setTimeout(() => {
          toast.classList.add("animate-fade-out");
          setTimeout(() => toast.remove(), 400);
        }, 2000);

        // If active category has changed (no longer in categories list), redirect
        if (!selectedCategories.includes(activeCategoryId) && selectedCategories.length > 0) {
          setTimeout(() => {
            navigate(`/app/inventory/${selectedCategories[0]}`);
          }, 800);
        }
      }
    } catch (err) {
      console.error("Error saving item changes:", err);
      alert(err.message || "Failed to save wardrobe changes.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Delete
  const handleDelete = async () => {
    const confirmDelete = window.confirm(
      `Are you sure you want to remove "${name}" from your digitized wardrobe?`
    );
    if (!confirmDelete) return;

    setIsSubmitting(true);
    try {
      if (isControlled && onDelete) {
        await onDelete(activeCategoryId, activeItemId);
      } else {
        await apiDeleteItem(activeItemId);
        navigate(`/app/inventory/${activeCategoryId}`);
      }
    } catch (err) {
      console.error("Error deleting item:", err);
      alert(err.message || "Failed to remove garment from wardrobe.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Custom AI suggestions computed dynamically based on category
  const getAISuggestion = () => {
    const primaryCat = selectedCategories[0] || "";
    switch (primaryCat) {
      case "tops":
        return `AI suggests this item pairs exceptionally well with your Tailored Wool Trousers. Updating the occasion to '${occasion.charAt(0).toUpperCase() + occasion.slice(1)}' will re-index it in your capsule wardrobe.`;
      case "bottoms":
        return `AI recommends styling this silhouette with your Stone Cashmere Knit and Minimalist Derby shoes for an effortless, relaxed Quiet Luxury drape.`;
      case "outerwear":
        return `AI suggests layering this over your Essential White Shirt. Extremely well suited for sophisticated transitional styling between 12°C and 18°C.`;
      case "footwear":
      case "shoes":
        return `AI highlights these grounded pieces as the crucial balancing element for your casual and workwear capsule rotations.`;
      case "accessories":
        return `AI notes this editorial accessory adds immediate dimension. Pairs exceptionally well with monochromatic charcoal or cream knit textures.`;
      default:
        return "AI scanned and verified. Perfectly balanced for versatile wardrobe combinations.";
    }
  };

  // List of wardrobe categories
  const categoriesList = [
    { id: "outerwear", label: "Outerwear" },
    { id: "tops", label: "Tops" },
    { id: "bottoms", label: "Bottoms" },
    { id: "footwear", label: "Shoes" },
    { id: "accessories", label: "Accessories" }
  ];

  // Internal content renderer for layout structures
  const renderContent = () => (
    <div className="w-full relative pb-40">
      {/* Submitting Overlay */}
      {isSubmitting && (
        <div className="fixed inset-0 bg-background/60 backdrop-blur-md z-50 flex flex-col items-center justify-center select-none animate-fade-in">
          <div className="w-10 h-10 border-2 border-tertiary/20 border-t-tertiary rounded-full animate-spin mb-4"></div>
          <p className="font-label-sm text-[10px] uppercase tracking-widest text-on-surface-variant/85">
            Archiving changes to digital vault...
          </p>
        </div>
      )}
      
      {/* Internal Sub-Header / Control bar below breadcrumbs */}
      <div className="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <span className="w-2.5 h-2.5 rounded-full bg-tertiary animate-pulse"></span>
          <span className="font-display text-base italic text-on-surface select-none">
            {isEditMode ? "Editing Piece Details" : "Digitized Collection Archive"}
          </span>
        </div>

        {isEditMode && (
          <button
            onClick={handleReset}
            className="text-on-surface-variant font-label-sm text-[10px] uppercase tracking-[0.2em] hover:text-on-surface transition-colors font-semibold border border-white/10 px-4 py-2 rounded-sm bg-white/[0.02] cursor-pointer"
          >
            Reset Form
          </button>
        )}
      </div>

      {/* Main Grid: 2-column e-commerce split on desktop, 1-column stack on mobile */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter items-start">
        
        {/* Left Column: Spotlight Image (Sticky on Desktop) - Original Luxury Colors Maintained */}
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

          <div className="w-full bg-[#0d0e12] relative flex justify-center rounded-xl overflow-hidden group shadow-2xl border border-white/5">
            <div className="relative w-full aspect-[4/5] md:aspect-square overflow-hidden">
              {viewMode === "tryon" ? (
                <ModelTryOn
                  items={{
                    id: activeItemId,
                    categoryId: selectedCategories[0] || activeCategoryId,
                    category: selectedCategories[0] || activeCategoryId,
                    image: image,
                    name: name
                  }}
                  className="!rounded-none !border-none shadow-none"
                />
              ) : (
                <img
                  alt={name || "Wardrobe Item"}
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                  src={image || "/assets/blouse_recent.png"}
                />
              )}
              {/* AI Enhancement Chip Overlay */}
              <div className="absolute bottom-6 right-6 bg-[#1A1A1A]/40 backdrop-blur-xl border border-tertiary/30 rounded-full px-4 py-2 flex items-center gap-2 shadow-2xl select-none z-30">
                <span
                  className="material-symbols-outlined text-tertiary text-[16px] animate-pulse"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  auto_awesome
                </span>
                <span className="font-label-sm text-[9px] text-on-surface uppercase tracking-[0.15em] font-semibold">
                  {verified ? "AI Scanned & Verified" : "AI Scanned"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Information & Form Control Fields */}
        <div className="md:col-span-7 bg-transparent">
          
          {/* Inner Grid for Input Boxes: 2-boxes side-by-side on desktop */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            
            {/* Box 1: Item Name */}
            <div className="flex flex-col gap-2 group sm:col-span-1">
              <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-1 font-semibold select-none">
                Item Name
              </label>
              {isEditMode ? (
                <div className="relative border-b border-outline-variant/30 focus-within:border-tertiary transition-colors">
                  <input
                    className="w-full bg-transparent border-0 py-3 pl-0 pr-10 font-body-md text-body-md text-on-surface focus:ring-0 focus:outline-none placeholder:text-on-surface-variant/40"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter item name"
                  />
                  <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant/40 text-[18px]">
                    edit
                  </span>
                </div>
              ) : (
                <p className="font-display text-xl italic text-on-surface tracking-wide py-3 select-none leading-snug">
                  {name || "Untitled Item"}
                </p>
              )}
            </div>

            {/* Box 2: Category Classification (Multi-select enabled!) */}
            <div className="flex flex-col gap-2 sm:col-span-1">
              <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-1.5 font-semibold select-none">
                Category Classifications
              </label>
              {isEditMode ? (
                <div className="flex flex-wrap gap-2 pt-1">
                  {categoriesList.map((cat) => {
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
              ) : (
                <div className="flex flex-wrap gap-2 select-none py-2.5">
                  {selectedCategories.map((catId) => {
                    const label = categoriesList.find((c) => c.id === catId)?.label || catId;
                    return (
                      <span
                        key={catId}
                        className="px-4 py-1.5 rounded-full border border-primary/20 bg-white/5 text-[11px] text-on-surface tracking-wider uppercase font-semibold"
                      >
                        {label}
                      </span>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Box 3: Fabric Composition */}
            <div className="flex flex-col gap-2 group sm:col-span-1">
              <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-1 font-semibold select-none">
                Fabric Composition
              </label>
              {isEditMode ? (
                <div className="relative border-b border-outline-variant/30 focus-within:border-tertiary transition-colors">
                  <input
                    className="w-full bg-transparent border-0 py-3 pl-0 pr-10 font-body-md text-body-md text-on-surface focus:ring-0 focus:outline-none placeholder:text-on-surface-variant/40"
                    type="text"
                    value={textile}
                    onChange={(e) => setTextile(e.target.value)}
                    placeholder="Enter fabric composition (e.g. 100% Cashmere)"
                  />
                  <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant/40 text-[18px]">
                    edit
                  </span>
                </div>
              ) : (
                <p className="font-body-md text-sm text-on-surface py-3 leading-snug select-none">
                  {textile || "Not specified"}
                </p>
              )}
            </div>

            {/* Box 4: Primary Occasion */}
            <div className="flex flex-col gap-2 sm:col-span-1">
              <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-1.5 font-semibold select-none">
                Primary Occasion
              </label>
              {isEditMode ? (
                <div className="flex flex-wrap gap-2 pt-1">
                  {["casual", "work", "evening", "event"].map((occ) => {
                    const isActive = occasion === occ;
                    const labels = {
                      casual: "Casual",
                      work: "Work",
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
              ) : (
                <div className="flex select-none py-2.5">
                  {["casual", "work", "evening", "event"].map((occ) => {
                    const isActive = occasion === occ;
                    const labels = {
                      casual: "Casual",
                      work: "Workwear",
                      evening: "Evening",
                      event: "Special Event"
                    };
                    if (!isActive) return null;
                    return (
                      <span
                        key={occ}
                        className="px-4 py-1.5 rounded-full border border-primary/20 bg-white/5 text-[11px] text-on-surface tracking-wider uppercase font-semibold flex items-center gap-1.5"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-tertiary"></span>
                        {labels[occ]}
                      </span>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Box 5 & 6: Colors (Primary & Secondary Categories) - Spans full width inside inner grid */}
            <div className="flex flex-col gap-6 sm:col-span-2 border-t border-white/5 pt-6">
              
              {isEditMode ? (
                <div>
                  <h4 className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-4 font-semibold select-none">
                    Color Palette (Dominant & Accent Tones)
                  </h4>
                  
                  {/* Hidden Native Picker for Primary Color (Color Wheel) */}
                  <input
                    type="color"
                    ref={primaryColorInputRef}
                    value={colorHex}
                    onChange={(e) => {
                      const hex = e.target.value.toUpperCase();
                      setColorHex(hex);
                      const matched = LUXURY_COLORS.find(c => c.hex.toLowerCase() === hex.toLowerCase());
                      setColorName(matched ? matched.name : `Custom Color (${hex})`);
                    }}
                    className="sr-only"
                  />

                  {/* Hidden Native Picker for Secondary Color */}
                  <input
                    type="color"
                    ref={secondaryColorInputRef}
                    onChange={(e) => handleAddSecondaryColor(e.target.value)}
                    className="sr-only"
                  />

                  <div className="flex flex-col gap-6">
                    {/* Primary Color selection (Only One) */}
                    <div className="flex flex-col gap-2">
                      <span className="text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">Primary Color (Dominant Tone)</span>
                      
                      <div className="flex gap-4 items-center mt-1">
                        <div
                          className="w-12 h-12 rounded-full border border-white/20 shadow-inner relative flex items-center justify-center cursor-pointer group/primary overflow-hidden transition-transform duration-300 hover:scale-105"
                          style={{ backgroundColor: colorHex }}
                          onClick={() => primaryColorInputRef.current.click()}
                          title="Open Color Wheel"
                        >
                          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/primary:opacity-100 transition-opacity flex items-center justify-center">
                            <span className="material-symbols-outlined text-on-surface text-sm">palette</span>
                          </div>
                        </div>

                        <div className="flex flex-col gap-1">
                          <div className="flex items-center gap-2.5">
                            <span className="font-body-md text-sm text-on-surface font-semibold">{colorName}</span>
                            <span className="text-[10px] font-mono text-on-surface-variant bg-white/5 border border-white/5 px-2 py-0.5 rounded select-all">{colorHex}</span>
                          </div>
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => primaryColorInputRef.current.click()}
                              className="text-[9px] uppercase tracking-widest font-label-sm border border-white/10 px-2.5 py-1.5 rounded bg-white/[0.02] hover:bg-white/5 transition-all text-on-surface cursor-pointer font-bold"
                            >
                              Color Wheel
                            </button>
                            {isEyeDropperSupported && (
                              <button
                                type="button"
                                onClick={handleEyeDropPrimary}
                                className="text-[9px] uppercase tracking-widest font-label-sm border border-tertiary/20 px-2.5 py-1.5 rounded bg-tertiary/5 hover:bg-tertiary/10 transition-all text-tertiary flex items-center gap-1 cursor-pointer font-bold"
                              >
                                <span className="material-symbols-outlined text-[12px] font-bold">colorize</span> Eye Dropper
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Secondary Colors selection (Multiple Allowed) */}
                    <div className="flex flex-col gap-2 border-t border-white/5 pt-4">
                      <span className="text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">Secondary Colors (Accent Tones)</span>
                      
                      <div className="flex flex-wrap items-center gap-3 mt-1">
                        {/* Render existing secondary colors with delete badges */}
                        {secondaryColors.map((color, index) => (
                          <div
                            key={index}
                            className="group/sec relative w-10 h-10 rounded-full border border-white/10 shadow-md flex items-center justify-center transition-transform"
                            style={{ backgroundColor: color.hex }}
                            title={`${color.name} (${color.hex})`}
                          >
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover/sec:opacity-100 transition-opacity rounded-full flex items-center justify-center">
                              <button
                                type="button"
                                onClick={() => {
                                  const filtered = secondaryColors.filter((_, idx) => idx !== index);
                                  setSecondaryColors(filtered);
                                }}
                                className="text-error hover:text-red-400 transition-colors p-1"
                                title="Remove accent color"
                              >
                                <span className="material-symbols-outlined text-xs">close</span>
                              </button>
                            </div>
                          </div>
                        ))}

                        {/* Add from Color Wheel */}
                        <button
                          type="button"
                          onClick={() => secondaryColorInputRef.current.click()}
                          className="w-10 h-10 rounded-full border border-dashed border-white/20 flex items-center justify-center hover:border-white/40 hover:bg-white/[0.02] transition-all cursor-pointer group/addsec"
                          title="Add accent color from wheel"
                        >
                          <span className="material-symbols-outlined text-on-surface-variant/60 group-hover/addsec:text-on-surface text-base">add</span>
                        </button>

                        {/* Add from Eye Dropper */}
                        {isEyeDropperSupported && (
                          <button
                            type="button"
                            onClick={handleEyeDropSecondary}
                            className="w-10 h-10 rounded-full border border-dashed border-tertiary/20 flex items-center justify-center hover:border-tertiary hover:bg-tertiary/5 transition-all cursor-pointer group/addpip"
                            title="Add accent color using eye dropper pipette"
                          >
                            <span className="material-symbols-outlined text-tertiary/60 group-hover/addpip:text-tertiary text-sm">colorize</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="select-none">
                  <h4 className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-4 font-semibold">
                    Garment Color Palette
                  </h4>
                  
                  <div className="flex flex-col gap-6">
                    {/* Primary dominant color */}
                    <div className="flex items-center gap-4">
                      <div
                        className="w-10 h-10 rounded-full border border-white/10 shadow-inner relative overflow-hidden"
                        style={{ backgroundColor: colorHex }}
                      >
                        <div className="absolute inset-0 bg-gradient-to-tr from-transparent to-white/10 rounded-full"></div>
                      </div>
                      <div>
                        <p className="text-[9px] text-on-surface-variant uppercase tracking-wider leading-none mb-1">Primary Color</p>
                        <p className="font-body-md text-sm text-on-surface font-semibold flex items-center gap-2">
                          {colorName}
                          <span className="font-mono text-[9px] text-on-surface-variant font-light">({colorHex})</span>
                        </p>
                      </div>
                    </div>

                    {/* Secondary accent colors */}
                    <div className="border-t border-white/5 pt-4">
                      <p className="text-[9px] text-on-surface-variant uppercase tracking-wider mb-2">Secondary Colors</p>
                      <div className="flex flex-wrap items-center gap-2.5">
                        {secondaryColors.length > 0 ? (
                          secondaryColors.map((color, index) => (
                            <div
                              key={index}
                              className="w-8 h-8 rounded-full border border-white/10 shadow-md relative group/secview"
                              style={{ backgroundColor: color.hex }}
                            >
                              <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-surface border border-outline-variant/35 text-[8px] uppercase tracking-widest text-on-surface px-2 py-0.5 rounded pointer-events-none opacity-0 group-hover/secview:opacity-100 transition-opacity z-10 whitespace-nowrap shadow-xl">
                                {color.name} ({color.hex})
                              </div>
                            </div>
                          ))
                        ) : (
                          <span className="text-[11px] text-on-surface-variant/40 italic">No secondary accent tones mapped.</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Box 7: More Details - Spans full width inside inner grid */}
            <div className="flex flex-col gap-2 group sm:col-span-2 border-t border-white/5 pt-6">
              <label className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-[0.2em] mb-1 font-semibold select-none">
                Additional Curation Notes (Pattern & Fit details)
              </label>
              {isEditMode ? (
                <div className="relative border-b border-outline-variant/30 focus-within:border-tertiary transition-colors">
                  <textarea
                    className="w-full bg-transparent border-0 py-3 pl-0 pr-10 font-body-md text-body-md text-on-surface focus:ring-0 focus:outline-none placeholder:text-on-surface-variant/35 resize-none h-20"
                    value={moreDetails}
                    onChange={(e) => setMoreDetails(e.target.value)}
                    placeholder="E.g. Herringbone weave, relaxed chest fitting, gold analog dials, double-face lining details..."
                  />
                  <span className="material-symbols-outlined absolute right-2 top-3 text-on-surface-variant/40 text-[18px]">
                    notes
                  </span>
                </div>
              ) : (
                <p className="font-body-md text-sm text-on-surface-variant/80 py-2 italic font-light leading-relaxed select-none">
                  {moreDetails || "No additional pattern or curation details registered for this piece."}
                </p>
              )}
            </div>

          </div>

          {/* Contextual Note / AI insight */}
          <div className="mt-8 p-5 rounded-xl bg-white/[0.02] border border-white/5 flex gap-4 items-start shadow-md select-none">
            <span className="material-symbols-outlined text-tertiary mt-0.5" style={{ fontVariationSettings: "'FILL' 1" }}>
              info
            </span>
            <p className="font-body text-xs text-on-surface-variant/80 leading-relaxed">
              {getAISuggestion()}
            </p>
          </div>
        </div>
      </div>

      {/* Fixed Bottom Action Bar */}
      <div className="fixed bottom-0 left-0 w-full bg-background/80 backdrop-blur-2xl border-t border-outline-variant/10 px-6 py-6 z-40">
        <div className="max-w-2xl mx-auto w-full flex flex-col gap-3">
          {isEditMode ? (
            <>
              <button
                onClick={handleSave}
                className="w-full py-4 bg-on-surface text-background rounded-lg font-label-sm text-[10px] uppercase tracking-[0.2em] hover:bg-on-surface/90 transition-all active:scale-[0.98] shadow-2xl font-bold cursor-pointer"
              >
                Save Changes
              </button>
              <button
                onClick={handleDelete}
                className="w-full py-4 bg-transparent border border-error/20 text-error rounded-lg font-label-sm text-[10px] uppercase tracking-[0.2em] hover:bg-error/5 hover:border-error transition-all active:scale-[0.98] font-bold cursor-pointer"
              >
                Delete Item
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setIsEditMode(true)}
                className="w-full py-4 bg-on-surface text-background rounded-lg font-label-sm text-[10px] uppercase tracking-[0.2em] hover:bg-on-surface/90 transition-all active:scale-[0.98] shadow-2xl font-bold cursor-pointer"
              >
                Edit Details
              </button>
              <button
                onClick={handleClose}
                className="w-full py-4 bg-transparent border border-white/10 text-on-surface rounded-lg font-label-sm text-[10px] uppercase tracking-[0.2em] hover:bg-white/5 transition-all active:scale-[0.98] font-bold cursor-pointer"
              >
                Back to Archive
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );

  if (isLoading) {
    const loadingContent = (
      <div className="flex flex-col items-center justify-center py-40 select-none min-h-[60vh]">
        <div className="w-10 h-10 border-2 border-tertiary/20 border-t-tertiary rounded-full animate-spin mb-4"></div>
        <p className="font-label-sm text-[10px] uppercase tracking-widest text-on-surface-variant/50">
          Retrieving Archival Garment...
        </p>
      </div>
    );
    if (isControlled) {
      return (
        <div className="relative bg-background text-on-surface w-full flex items-center justify-center min-h-[50vh]">
          {loadingContent}
        </div>
      );
    }
    return (
      <Layout hideNav={true} showBack={true} title="Item Details">
        {loadingContent}
      </Layout>
    );
  }

  if (errorMsg) {
    const errorContent = (
      <div className="flex flex-col items-center justify-center py-20 px-6 text-center select-none min-h-[50vh]">
        <span className="material-symbols-outlined text-error text-4xl mb-4">warning</span>
        <h3 className="font-display text-lg italic text-on-surface mb-2">Garment Synchronization Error</h3>
        <p className="font-body-md text-sm text-on-surface-variant/80 max-w-md mb-8 leading-relaxed">
          {errorMsg}
        </p>
        <button
          onClick={handleClose}
          className="px-6 py-3 border border-white/10 rounded-lg font-label-sm text-[10px] uppercase tracking-widest text-on-surface hover:bg-white/5 transition-all active:scale-95 cursor-pointer font-bold"
        >
          Return to Archive
        </button>
      </div>
    );
    if (isControlled) {
      return (
        <div className="relative bg-background text-on-surface w-full">
          {errorContent}
        </div>
      );
    }
    return (
      <Layout hideNav={true} showBack={true} title="Error">
        {errorContent}
      </Layout>
    );
  }

  // If in widget/controlled mode, render bare content, otherwise wrap inside standard VOGUE.AI Layout
  if (isControlled) {
    return (
      <div className="relative bg-background text-on-surface w-full">
        {renderContent()}
      </div>
    );
  }

  return (
    <Layout hideNav={true} showBack={true} title="Item Details">
      {renderContent()}
    </Layout>
  );
};

export default ItemDetails;
