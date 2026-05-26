import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";
import { 
  apiListCategories, 
  apiUpdateCategory, 
  apiDeleteCategory 
} from "../utils/wardrobeStore";

// Beautiful, curated Quiet Luxury fashion images already present in project assets
const CURATED_COVERS = [
  { name: "Curation Collage", url: "/assets/curation_collage_feature.png" },
  { name: "Textile Layout", url: "/assets/clothing_layout_gap.png" },
  { name: "Stone Knitwear", url: "/assets/tops_category.png" },
  { name: "Raw Denim Indigo", url: "/assets/bottoms_category.png" },
  { name: "Charcoal Wool Trench", url: "/assets/outerwear_category.png" },
  { name: "Polished calfskin Derby", url: "/assets/shoes_category.png" }
];

export const Wardrobe = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Edit / Delete Modals & Dropdown States
  const [activeDropdownId, setActiveDropdownId] = useState(null);
  
  // Edit Category Modal Form States
  const [editingCategory, setEditingCategory] = useState(null);
  const [editName, setEditName] = useState("");
  const [editSubtitle, setEditSubtitle] = useState("");
  const [editImage, setEditImage] = useState("");
  const [editCustomImageUrl, setEditCustomImageUrl] = useState("");
  
  // Delete Category Modal Form States
  const [deletingCategory, setDeletingCategory] = useState(null);
  const [cleanupMode, setCleanupMode] = useState("keep_orphans");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Scroll reveal Intersection Observer on mount
  useEffect(() => {
    const observerOptions = {
      threshold: 0.05,
      rootMargin: "0px 0px -40px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("active");
        }
      });
    }, observerOptions);

    const revealElements = document.querySelectorAll(".reveal");
    revealElements.forEach((el) => observer.observe(el));

    return () => {
      revealElements.forEach((el) => observer.unobserve(el));
    };
  }, []);

  // Fetch categories asynchronously (handles search debouncing)
  const loadCategories = async (query = "") => {
    setIsLoading(true);
    const data = await apiListCategories(query);
    setCategories(data);
    setIsLoading(false);
  };

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      loadCategories(searchQuery);
    }, 250);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  // Close dropdown on click outside
  useEffect(() => {
    const handleOutsideClick = () => setActiveDropdownId(null);
    window.addEventListener("click", handleOutsideClick);
    return () => window.removeEventListener("click", handleOutsideClick);
  }, []);

  const openEditModal = (cat, e) => {
    e.preventDefault();
    e.stopPropagation();
    setActiveDropdownId(null);
    setEditingCategory(cat);
    setEditName(cat.name);
    setEditSubtitle(cat.subtitle || "");
    setEditImage(cat.image || "");
    setEditCustomImageUrl(cat.image && cat.image.startsWith("http") ? cat.image : "");
  };

  const handleUpdateCategory = async (e) => {
    e.preventDefault();
    if (!editName.trim()) return;

    setIsSubmitting(true);
    try {
      const finalImage = editCustomImageUrl.trim() ? editCustomImageUrl.trim() : editImage;
      await apiUpdateCategory(editingCategory.id, {
        name: editName.trim(),
        subtitle: editSubtitle.trim(),
        image: finalImage
      });
      
      triggerToast(`Collection "${editName}" Updated`);
      setEditingCategory(null);
      loadCategories(searchQuery);
    } catch (err) {
      alert(err.message || "Failed to update category");
    } finally {
      setIsSubmitting(false);
    }
  };

  const openDeleteModal = (cat, e) => {
    e.preventDefault();
    e.stopPropagation();
    setActiveDropdownId(null);
    setDeletingCategory(cat);
    setCleanupMode("keep_orphans");
  };

  const handleDeleteCategory = async () => {
    setIsSubmitting(true);
    try {
      await apiDeleteCategory(deletingCategory.id, cleanupMode);
      triggerToast(`Collection "${deletingCategory.name}" Deleted`);
      setDeletingCategory(null);
      loadCategories(searchQuery);
    } catch (err) {
      alert(err.message || "Failed to delete category");
    } finally {
      setIsSubmitting(false);
    }
  };

  const triggerToast = (msg) => {
    const toast = document.createElement("div");
    toast.className = "fixed bottom-36 left-1/2 -translate-x-1/2 bg-on-surface text-background px-6 py-3 rounded-full font-label-sm text-[11px] uppercase tracking-[0.2em] shadow-2xl z-[120] border border-white/10 animate-fade-in flex items-center gap-2";
    toast.innerHTML = `<span class="material-symbols-outlined text-sm font-bold text-tertiary">check_circle</span> ${msg}`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.classList.add("animate-fade-out");
      setTimeout(() => toast.remove(), 400);
    }, 2000);
  };

  return (
    <Layout>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter relative">
        
        {/* Content Area */}
        <div className="lg:col-span-8 xl:col-span-9 space-y-12">
          
          {/* Enhanced Search Bar */}
          <section className="relative hero-reveal" style={{ animationDelay: "0.1s" }}>
            <div className="flex flex-col md:flex-row gap-4 items-center">
              <div className="relative flex-grow w-full glass-panel rounded-xl overflow-hidden flex items-center px-6 py-4 focus-within:ring-1 focus-within:ring-white/20 transition-all shadow-lg">
                <span className="material-symbols-outlined text-on-surface-variant/40 mr-4 select-none">
                  search
                </span>
                <input
                  className="bg-transparent border-none w-full text-on-surface font-body-md text-body-md focus:ring-0 focus:outline-none placeholder-on-surface-variant/30"
                  placeholder="Search your digital wardrobe..."
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="text-on-surface-variant/50 hover:text-on-surface transition-colors mr-3 cursor-pointer"
                    aria-label="Clear search"
                  >
                    <span className="material-symbols-outlined text-lg">close</span>
                  </button>
                )}

                <div className="flex items-center gap-3 ml-4 border-l border-white/10 pl-4 select-none">
                  <button 
                    onClick={() => navigate("/app/camera")}
                    className="text-on-surface-variant/50 hover:text-tertiary transition-colors flex items-center gap-2 group cursor-pointer" 
                    title="Visual Search"
                  >
                    <span className="material-symbols-outlined text-xl">photo_camera</span>
                    <span className="hidden md:inline font-label-sm text-[9px] uppercase tracking-widest group-hover:text-tertiary">
                      Visual
                    </span>
                  </button>
                  <button 
                    onClick={() => navigate("/app/analysis")}
                    className="text-on-surface-variant/50 hover:text-tertiary transition-colors flex items-center gap-2 group cursor-pointer" 
                    title="Style Filter"
                  >
                    <span className="material-symbols-outlined text-xl">tune</span>
                    <span className="hidden md:inline font-label-sm text-[9px] uppercase tracking-widest group-hover:text-tertiary">
                      Filter
                    </span>
                  </button>
                </div>
              </div>
              
              <button 
                onClick={() => navigate("/app/recommendations")}
                className="hidden md:flex px-10 py-4 glass-panel bg-white/5 hover:bg-white/10 text-on-surface rounded-xl font-label-sm text-[10px] uppercase tracking-[0.2em] transition-all border border-white/10 active:scale-95 cursor-pointer font-bold shadow-lg"
              >
                Find Outfit
              </button>
            </div>
          </section>

          {/* Digital Wardrobe Grid */}
          <section className="reveal">
            <div className="flex items-end justify-between mb-10">
              <div>
                <h2 className="font-display text-4xl md:text-5xl italic luxury-text-gradient mb-2 select-none">
                  The Collection
                </h2>
                <p className="font-body-md text-on-surface-variant/40 tracking-[0.2em] uppercase text-[9px] font-semibold select-none">
                  Your curated digital archive
                </p>
              </div>
              
              <div className="flex gap-3 select-none">
                <button className="p-2.5 glass-panel rounded-lg text-on-surface-variant/40 hover:text-on-surface transition-all cursor-pointer">
                  <span className="material-symbols-outlined text-sm">grid_view</span>
                </button>
                <button className="p-2.5 glass-panel rounded-lg text-on-surface-variant/40 hover:text-on-surface transition-all cursor-pointer">
                  <span className="material-symbols-outlined text-sm">view_agenda</span>
                </button>
              </div>
            </div>

            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-20 select-none">
                <div className="w-10 h-10 border-2 border-tertiary/20 border-t-tertiary rounded-full animate-spin mb-4"></div>
                <p className="font-label-sm text-[10px] uppercase tracking-widest text-on-surface-variant/50">
                  Retrieving Wardrobe Vault...
                </p>
              </div>
            ) : categories.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-8">
                {categories.map((cat) => (
                  <div key={cat.id} className="relative group aspect-[4/5] rounded-2xl overflow-hidden shadow-2xl hover:scale-[1.01] transition-all duration-500 border border-white/5 hover:border-white/15">
                    
                    {/* Category Action Dropdown Trigger (Isolated from card navigation) */}
                    <div className="absolute top-4 right-4 z-20">
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          setActiveDropdownId(activeDropdownId === cat.id ? null : cat.id);
                        }}
                        className="w-8 h-8 rounded-full bg-[#1A1A1A]/60 backdrop-blur-xl border border-white/10 text-on-surface hover:text-tertiary flex items-center justify-center transition-all cursor-pointer hover:scale-105 active:scale-95 shadow-lg"
                        title="Actions"
                      >
                        <span className="material-symbols-outlined text-[18px]">more_vert</span>
                      </button>

                      {/* Dropdown Options Box */}
                      {activeDropdownId === cat.id && (
                        <div 
                          onClick={(e) => e.stopPropagation()} 
                          className="absolute top-9 right-0 w-36 glass-panel rounded-lg shadow-2xl py-1.5 z-30 animate-fade-in border border-white/10 select-none"
                        >
                          <button
                            onClick={(e) => openEditModal(cat, e)}
                            className="w-full text-left px-4 py-2.5 text-[10px] uppercase tracking-wider text-on-surface-variant hover:text-on-surface hover:bg-white/5 transition-all flex items-center gap-2 font-bold cursor-pointer"
                          >
                            <span className="material-symbols-outlined text-sm">edit</span>
                            Edit Meta
                          </button>
                          <button
                            onClick={(e) => openDeleteModal(cat, e)}
                            className="w-full text-left px-4 py-2.5 text-[10px] uppercase tracking-wider text-error/80 hover:text-error hover:bg-error/5 transition-all flex items-center gap-2 font-bold cursor-pointer"
                          >
                            <span className="material-symbols-outlined text-sm text-error/80">delete</span>
                            Remove
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Standard Category Link Card */}
                    <Link
                      to={cat.path || `/app/inventory/${cat.id}`}
                      className="absolute inset-0 flex flex-col justify-end p-8"
                    >
                      <img
                        alt={cat.name}
                        className="category-image absolute inset-0 w-full h-full object-cover opacity-50 grayscale-[0.2] transition-all duration-1000 ease-out group-hover:scale-103"
                        src={cat.image || "/assets/curation_collage_feature.png"}
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-background via-background/60 to-transparent"></div>
                      <div className="relative z-10 space-y-2 select-none">
                        <span className="font-label-sm text-[9px] text-tertiary/70 uppercase tracking-[0.3em] block font-bold">
                          {cat.subtitle || "Collection"}
                        </span>
                        <h3 className="font-display text-3xl luxury-text-gradient italic">
                          {cat.name}
                        </h3>
                        <div className="flex items-center gap-3 pt-4 border-t border-white/5 mt-4">
                          <span className="font-body-md text-xs text-on-surface-variant/50">
                            {cat.count} Item{cat.count !== 1 ? "s" : ""}
                          </span>
                          <span className="w-1 h-1 rounded-full bg-white/10"></span>
                          <span className="font-label-sm text-[8px] text-on-surface-variant/40 uppercase tracking-widest font-semibold">
                            {cat.status || "Active"}
                          </span>
                        </div>
                      </div>
                    </Link>
                  </div>
                ))}

                {/* Add New Category Card */}
                <button 
                  onClick={() => navigate("/app/category/new")}
                  className="group relative aspect-[4/5] rounded-2xl overflow-hidden glass-panel flex flex-col items-center justify-center border-dashed border border-white/10 hover:border-white/20 hover:bg-white/[0.02] transition-all duration-500 cursor-pointer shadow-xl select-none"
                >
                  <div className="w-14 h-14 rounded-full glass-panel bg-white/5 flex items-center justify-center mb-4 group-hover:bg-tertiary group-hover:text-on-tertiary transition-all duration-300 shadow-inner">
                    <span className="material-symbols-outlined text-2xl">add</span>
                  </div>
                  <span className="font-label-sm text-[10px] uppercase tracking-[0.2em] text-on-surface-variant/40 group-hover:text-on-surface font-bold">
                    New Category
                  </span>
                </button>
              </div>
            ) : (
              <div className="text-center py-16 glass-panel rounded-2xl shadow-xl select-none">
                <span className="material-symbols-outlined text-5xl opacity-40 mb-3 text-tertiary animate-bounce">
                  checkroom
                </span>
                <p className="font-body-md text-sm text-on-surface-variant">
                  No matching wardrobe categories found.
                </p>
              </div>
            )}
          </section>
        </div>

        {/* Refined Sidebar */}
        <aside className="hidden lg:flex lg:col-span-4 xl:col-span-3 flex-col gap-gutter reveal">
          
          {/* Stats Card */}
          <div className="glass-panel rounded-2xl p-8 ai-glow shadow-xl">
            <h3 className="font-display text-xl italic luxury-text-gradient mb-8 select-none">
              Wardrobe Pulse
            </h3>
            
            <div className="space-y-8">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-label-sm text-[9px] text-on-surface-variant/40 uppercase tracking-[0.2em] mb-1.5 font-bold">
                    Items Sync
                  </p>
                  <p className="font-display text-2xl luxury-text-gradient font-semibold">
                    84%
                  </p>
                </div>
                <span className="material-symbols-outlined text-tertiary/20 text-2xl">
                  cloud_done
                </span>
              </div>
              
              <div className="h-[2px] bg-white/5 rounded-full overflow-hidden select-none">
                <div className="h-full bg-tertiary/60 w-[84%] rounded-full"></div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 pt-6 border-t border-white/5">
                <div>
                  <p className="font-label-sm text-[9px] text-on-surface-variant/40 uppercase tracking-[0.2em] mb-1.5 font-bold">
                    Total Pieces
                  </p>
                  <p className="font-display text-xl luxury-text-gradient font-semibold">
                    1,248
                  </p>
                </div>
                <div>
                  <p className="font-label-sm text-[9px] text-on-surface-variant/40 uppercase tracking-[0.2em] mb-1.5 font-bold">
                    Outfits
                  </p>
                  <p className="font-display text-xl luxury-text-gradient font-semibold">
                    342
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Recently Viewed */}
          <div className="glass-panel rounded-2xl p-8 flex flex-col flex-grow shadow-xl">
            <h3 className="font-display text-xl italic luxury-text-gradient mb-8 select-none">
              Recent History
            </h3>
            
            <div className="space-y-6 flex-grow overflow-y-auto no-scrollbar max-h-[350px]">
              
              {/* Blouse */}
              <div 
                onClick={() => navigate("/app/item/tops/blouse")}
                className="flex items-center gap-4 group cursor-pointer"
              >
                <div className="w-16 h-20 rounded-lg overflow-hidden flex-shrink-0 glass-panel shadow-md">
                  <img
                    alt="Noir Silk"
                    className="w-full h-full object-cover grayscale opacity-60 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700"
                    src="/assets/blouse_recent.png"
                  />
                </div>
                <div>
                  <h4 className="font-body text-xs text-on-surface-variant/80 group-hover:text-on-surface transition-colors font-medium font-light">
                    Noir Silk Blouse
                  </h4>
                  <p className="font-label-sm text-[8px] text-on-surface-variant/30 uppercase mt-1.5 tracking-widest font-semibold">
                    2 hours ago
                  </p>
                </div>
              </div>

              {/* Sneakers */}
              <div 
                onClick={() => navigate("/app/item/footwear/sneakers")}
                className="flex items-center gap-4 group cursor-pointer"
              >
                <div className="w-16 h-20 rounded-lg overflow-hidden flex-shrink-0 glass-panel shadow-md">
                  <img
                    alt="Low Tops"
                    className="w-full h-full object-cover grayscale opacity-60 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700"
                    src="/assets/sneakers_recent.png"
                  />
                </div>
                <div>
                  <h4 className="font-body text-xs text-on-surface-variant/80 group-hover:text-on-surface transition-colors font-medium font-light">
                    Essential Sneakers
                  </h4>
                  <p className="font-label-sm text-[8px] text-on-surface-variant/30 uppercase mt-1.5 tracking-widest font-semibold">
                    Yesterday
                  </p>
                </div>
              </div>
            </div>
            
            <button 
              onClick={() => navigate("/app/recommendations")}
              className="mt-8 text-on-surface-variant/40 hover:text-on-surface transition-colors font-label-sm text-[9px] uppercase tracking-[0.2em] text-left font-bold cursor-pointer"
            >
              View All History
            </button>
          </div>

          {/* Premium CTA */}
          <div className="relative rounded-2xl overflow-hidden p-8 border border-white/5 bg-gradient-to-br from-white/[0.03] to-transparent shadow-xl">
            <h3 className="font-display text-lg mb-2 italic luxury-text-gradient select-none">
              Elevate Status
            </h3>
            <p className="font-body text-[11px] text-on-surface-variant/40 mb-8 leading-relaxed font-light select-none">
              Unlock generative fabric analysis and private collection vaults.
            </p>
            <button 
              onClick={() => navigate("/app/profile")}
              className="w-full py-4 glass-panel bg-white/5 hover:bg-white/10 text-on-surface rounded-lg font-label-sm text-[9px] uppercase tracking-[0.3em] transition-all cursor-pointer font-bold active:scale-95"
            >
              Go Premium
            </button>
          </div>
        </aside>
      </div>

      {/* Contextual FAB (Mobile Upload New Item) */}
      <button
        onClick={() => navigate("/app/camera")}
        aria-label="Upload New Item"
        className="md:hidden fixed bottom-24 right-6 z-[55] w-14 h-14 glass-panel bg-white/10 text-on-surface rounded-full flex items-center justify-center shadow-2xl hover:scale-105 active:scale-95 transition-transform cursor-pointer"
      >
        <span className="material-symbols-outlined text-2xl font-bold">add</span>
      </button>

      {/* ==================== EDIT CATEGORY MODAL ==================== */}
      {editingCategory && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-md z-[100] flex items-center justify-center p-4 animate-fade-in">
          <div className="glass-panel w-full max-w-lg rounded-2xl p-8 border border-white/10 shadow-2xl space-y-6 select-none animate-scale-up">
            <div className="flex justify-between items-center pb-4 border-b border-white/5">
              <h3 className="font-display text-2xl italic luxury-text-gradient">Edit Collection</h3>
              <button
                onClick={() => setEditingCategory(null)}
                className="text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <form onSubmit={handleUpdateCategory} className="space-y-6">
              <div className="space-y-2">
                <label className="block text-[10px] font-label-sm uppercase tracking-wider text-on-surface-variant">
                  Collection Name
                </label>
                <input
                  type="text"
                  required
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-on-surface font-body-md focus:outline-none focus:border-tertiary transition-all"
                  placeholder="e.g. Resortwear"
                />
              </div>

              <div className="space-y-2">
                <label className="block text-[10px] font-label-sm uppercase tracking-wider text-on-surface-variant">
                  Subtitle Classification
                </label>
                <input
                  type="text"
                  value={editSubtitle}
                  onChange={(e) => setEditSubtitle(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-on-surface font-body-md focus:outline-none focus:border-tertiary transition-all"
                  placeholder="e.g. Tailored Luxury"
                />
              </div>

              {/* Cover Image Curator */}
              <div className="space-y-3">
                <label className="block text-[10px] font-label-sm uppercase tracking-wider text-on-surface-variant">
                  Curated Cover Selection
                </label>
                <div className="grid grid-cols-6 gap-2">
                  {CURATED_COVERS.map((cover, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => {
                        setEditImage(cover.url);
                        setEditCustomImageUrl("");
                      }}
                      className={`relative aspect-[3/4] rounded-lg overflow-hidden border transition-all cursor-pointer ${
                        editImage === cover.url && !editCustomImageUrl
                          ? "border-tertiary scale-95 ring-2 ring-tertiary/20"
                          : "border-white/5 opacity-60 hover:opacity-100"
                      }`}
                    >
                      <img src={cover.url} alt={cover.name} className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-[10px] font-label-sm uppercase tracking-wider text-on-surface-variant">
                  Or Custom Image URL
                </label>
                <input
                  type="url"
                  value={editCustomImageUrl}
                  onChange={(e) => {
                    setEditCustomImageUrl(e.target.value);
                    if (e.target.value.trim()) setEditImage(e.target.value.trim());
                  }}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-on-surface font-body-md focus:outline-none focus:border-tertiary transition-all"
                  placeholder="https://images.unsplash.com/..."
                />
              </div>

              <div className="flex gap-4 pt-4 border-t border-white/5">
                <button
                  type="button"
                  onClick={() => setEditingCategory(null)}
                  className="flex-1 py-3.5 border border-white/10 rounded-lg font-label-sm text-[10px] uppercase tracking-widest text-on-surface hover:bg-white/5 transition-all font-bold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 py-3.5 bg-white text-background rounded-lg font-label-sm text-[10px] uppercase tracking-widest hover:bg-tertiary hover:text-on-tertiary transition-all font-bold cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? "Updating..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ==================== DELETE CATEGORY MODAL ==================== */}
      {deletingCategory && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-md z-[100] flex items-center justify-center p-4 animate-fade-in">
          <div className="glass-panel w-full max-w-md rounded-2xl p-8 border border-white/10 shadow-2xl space-y-6 select-none animate-scale-up">
            <div className="flex justify-between items-center pb-4 border-b border-white/5">
              <h3 className="font-display text-2xl italic text-error">Delete Collection</h3>
              <button
                onClick={() => setDeletingCategory(null)}
                className="text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="space-y-4">
              <p className="font-body-md text-xs text-on-surface-variant leading-relaxed">
                Are you sure you want to permanently delete the collection <span className="text-on-surface font-semibold">"{deletingCategory.name}"</span>?
              </p>
              
              <div className="space-y-2 pt-2">
                <label className="block text-[10px] font-label-sm uppercase tracking-wider text-on-surface-variant font-bold">
                  Orphaned Items Cleanup Mode
                </label>
                <div className="space-y-3 bg-white/5 border border-white/5 rounded-xl p-4">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name="cleanupMode"
                      value="keep_orphans"
                      checked={cleanupMode === "keep_orphans"}
                      onChange={(e) => setCleanupMode(e.target.value)}
                      className="mt-0.5 text-tertiary focus:ring-0 bg-transparent border-white/20"
                    />
                    <div>
                      <p className="text-[11px] font-label-sm uppercase tracking-wider text-on-surface font-semibold">
                        Keep Items (Recommended)
                      </p>
                      <p className="text-[10px] text-on-surface-variant/60 leading-relaxed font-light">
                        Removes the collection container tag but keeps all the wardrobe pieces intact in other collections.
                      </p>
                    </div>
                  </label>

                  <div className="h-[1px] bg-white/5"></div>

                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name="cleanupMode"
                      value="delete_items"
                      checked={cleanupMode === "delete_items"}
                      onChange={(e) => setCleanupMode(e.target.value)}
                      className="mt-0.5 text-error focus:ring-0 bg-transparent border-white/20"
                    />
                    <div>
                      <p className="text-[11px] font-label-sm uppercase tracking-wider text-error font-semibold">
                        Delete Contained Items
                      </p>
                      <p className="text-[10px] text-on-surface-variant/60 leading-relaxed font-light">
                        Deletes the collection and permanently purges all the individual wardrobe items contained within.
                      </p>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <div className="flex gap-4 pt-4 border-t border-white/5">
              <button
                type="button"
                onClick={() => setDeletingCategory(null)}
                className="flex-1 py-3.5 border border-white/10 rounded-lg font-label-sm text-[10px] uppercase tracking-widest text-on-surface hover:bg-white/5 transition-all font-bold cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteCategory}
                disabled={isSubmitting}
                className="flex-1 py-3.5 bg-error text-white rounded-lg font-label-sm text-[10px] uppercase tracking-widest hover:bg-red-700 transition-all font-bold cursor-pointer disabled:opacity-50"
              >
                {isSubmitting ? "Deleting..." : "Confirm Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

    </Layout>
  );
};

export default Wardrobe;
