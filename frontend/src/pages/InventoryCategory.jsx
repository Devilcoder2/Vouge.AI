import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";
import { 
  apiGetCategory, 
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

export const InventoryCategory = () => {
  const { categoryId } = useParams();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [currentCategory, setCurrentCategory] = useState({ title: "", description: "", items: [], rawMeta: null });
  const [isLoading, setIsLoading] = useState(true);

  // Edit / Delete Category Modal States
  const [showEditModal, setShowEditModal] = useState(false);
  const [editName, setEditName] = useState("");
  const [editSubtitle, setEditSubtitle] = useState("");
  const [editImage, setEditImage] = useState("");
  const [editCustomImageUrl, setEditCustomImageUrl] = useState("");
  
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [cleanupMode, setCleanupMode] = useState("keep_orphans");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Scroll reveal Intersection Observer on mount and when categoryId changes
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
    revealElements.forEach((el) => {
      el.classList.remove("active");
      observer.observe(el);
    });

    return () => {
      revealElements.forEach((el) => observer.unobserve(el));
    };
  }, [categoryId]);

  // Fetch current category metadata & items asynchronously
  const fetchCategoryData = async () => {
    setIsLoading(true);
    const data = await apiGetCategory(categoryId);
    setCurrentCategory(data);
    setIsLoading(false);
  };

  useEffect(() => {
    fetchCategoryData();
  }, [categoryId]);

  const filteredItems = (currentCategory.items || []).filter(
    (item) =>
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.textile.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Edit Actions
  const openEditModal = () => {
    const meta = currentCategory.rawMeta || {};
    setEditName(currentCategory.title);
    setEditSubtitle(meta.subtitle || "");
    setEditImage(meta.image || "");
    setEditCustomImageUrl(meta.image && meta.image.startsWith("http") ? meta.image : "");
    setShowEditModal(true);
  };

  const handleUpdateCategory = async (e) => {
    e.preventDefault();
    if (!editName.trim()) return;

    setIsSubmitting(true);
    try {
      const finalImage = editCustomImageUrl.trim() ? editCustomImageUrl.trim() : editImage;
      await apiUpdateCategory(categoryId, {
        name: editName.trim(),
        subtitle: editSubtitle.trim(),
        image: finalImage
      });
      
      triggerToast(`Collection "${editName}" Updated`);
      setShowEditModal(false);
      fetchCategoryData();
    } catch (err) {
      alert(err.message || "Failed to update category");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Delete Actions
  const openDeleteModal = () => {
    setCleanupMode("keep_orphans");
    setShowDeleteModal(true);
  };

  const handleDeleteCategory = async () => {
    setIsSubmitting(true);
    try {
      await apiDeleteCategory(categoryId, cleanupMode);
      triggerToast(`Collection "${currentCategory.title}" Deleted`);
      setShowDeleteModal(false);
      // Wait for toast to fade then redirect back to dashboard
      setTimeout(() => {
        navigate("/app/wardrobe");
      }, 800);
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
      <div className="space-y-8 max-w-container-max mx-auto w-full pb-20">
        
        {/* Search & Filter */}
        <section className="relative hero-reveal" style={{ animationDelay: "0.1s" }}>
          <div className="flex gap-4 items-center">
            <div className="relative flex-grow w-full glass-panel rounded-xl overflow-hidden flex items-center px-6 py-4 focus-within:ring-1 focus-within:ring-white/20 transition-all shadow-lg">
              <span className="material-symbols-outlined text-outline mr-4 select-none">search</span>
              <input
                className="bg-transparent border-none w-full text-on-surface font-body-md text-body-md focus:ring-0 focus:outline-none placeholder:text-outline-variant/50"
                placeholder="Search Inventory"
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

              <div className="h-6 w-[1px] bg-white/10 mx-3 select-none"></div>
              <button 
                onClick={() => navigate("/app/analysis")}
                className="text-primary hover:opacity-80 transition-opacity flex items-center justify-center p-1 cursor-pointer" 
                title="Style Filter"
              >
                <span className="material-symbols-outlined text-xl">tune</span>
              </button>
            </div>
          </div>
        </section>

        {/* Collection Header Info */}
        <section className="reveal flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 border-b border-white/5 pb-6 select-none">
          <div>
            <h2 className="font-display text-4xl md:text-5xl text-on-surface italic luxury-text-gradient mb-1">
              {currentCategory.title}
            </h2>
            <p className="font-label-sm text-xs text-on-surface-variant uppercase tracking-[0.2em] font-semibold">
              {filteredItems.length} Editorial Piece{filteredItems.length !== 1 ? "s" : ""}
            </p>
          </div>

          {/* Edit / Delete triggers */}
          <div className="flex items-center gap-3">
            <button
              onClick={openEditModal}
              className="px-4 py-2 border border-white/10 text-on-surface hover:text-tertiary hover:border-white/20 hover:bg-white/5 rounded-lg font-label-sm text-[10px] uppercase tracking-widest transition-all cursor-pointer font-bold flex items-center gap-1.5 active:scale-95 shadow-md"
              title="Edit Collection Title"
            >
              <span className="material-symbols-outlined text-[16px]">edit</span>
              Edit Meta
            </button>
            <button
              onClick={openDeleteModal}
              className="px-4 py-2 border border-error/20 text-error/85 hover:text-error hover:bg-error/5 hover:border-error/30 rounded-lg font-label-sm text-[10px] uppercase tracking-widest transition-all cursor-pointer font-bold flex items-center gap-1.5 active:scale-95 shadow-md"
              title="Remove Collection"
            >
              <span className="material-symbols-outlined text-[16px]">delete</span>
              Delete Collection
            </button>
          </div>
        </section>

        {/* Masonry Inventory Grid */}
        <section className="reveal">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20 select-none">
              <div className="w-10 h-10 border-2 border-tertiary/20 border-t-tertiary rounded-full animate-spin mb-4"></div>
              <p className="font-label-sm text-[10px] uppercase tracking-widest text-on-surface-variant/50">
                Retrieving Collection Vault...
              </p>
            </div>
          ) : filteredItems.length > 0 ? (
            <div className="columns-2 lg:columns-4 gap-6 space-y-6">
              {filteredItems.map((item) => (
                <div
                  key={item.id}
                  className="break-inside-avoid glass-card rounded-xl overflow-hidden flex flex-col group transition-all duration-500 hover:border-primary/30 shadow-xl"
                >
                  {/* Clickable Image Section */}
                  <div
                    onClick={() => navigate(`/app/item/${categoryId}/${item.id}`)}
                    className="cursor-pointer overflow-hidden animate-fade-in"
                  >
                    {/* Image Block with Variable Heights */}
                    <div
                      className={`relative overflow-hidden bg-[#1A1A1A] w-full ${
                        item.long ? "aspect-[3/4.2]" : "aspect-[3/3.6]"
                      }`}
                    >
                      <img
                        className="w-full h-full object-cover transition-transform duration-1000 ease-out group-hover:scale-105"
                        src={item.image}
                        alt={item.name}
                      />
                      
                      {item.verified && (
                        <div className="absolute top-3 left-3 bg-background/60 backdrop-blur-md px-2 py-1 rounded flex items-center gap-1 border border-white/5 select-none">
                          <span
                            className="material-symbols-outlined text-[10px] text-tertiary font-bold"
                            style={{ fontVariationSettings: "'FILL' 1" }}
                          >
                            auto_awesome
                          </span>
                          <span className="text-[8px] font-label-sm text-on-surface tracking-widest uppercase font-semibold">
                            AI Verified
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Card Content & Action Button */}
                  <div className="p-4 bg-surface-container-low flex-grow flex flex-col justify-between select-none">
                    <div
                      onClick={() => navigate(`/app/item/${categoryId}/${item.id}`)}
                      className="mb-4 cursor-pointer"
                    >
                      <p className="font-label-sm text-on-surface-variant uppercase text-[10px] tracking-wider mb-1 font-semibold truncate">
                        {item.textile}
                      </p>
                      <h3 className="font-display text-[16px] text-on-surface mb-2 leading-tight italic truncate hover:text-tertiary transition-colors">
                        {item.name}
                      </h3>
                    </div>

                    <button
                      onClick={() => navigate("/app/chat")}
                      className={`w-full py-2.5 font-label-sm text-[10px] uppercase tracking-widest rounded-sm active:scale-95 transition-transform cursor-pointer font-bold duration-300 ${
                        item.hasAIService
                          ? "bg-on-surface text-background hover:bg-tertiary hover:text-on-tertiary shadow-lg"
                          : "border border-white/10 text-on-surface hover:bg-white/5"
                      }`}
                    >
                      {item.hasAIService ? "Style with AI" : "Style"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16 glass-panel rounded-2xl shadow-xl animate-fade-in select-none">
              <span className="material-symbols-outlined text-5xl opacity-40 mb-3 text-tertiary">
                checkroom
              </span>
              <p className="font-body-md text-sm text-on-surface-variant">
                No inventory pieces matched your search criteria.
              </p>
            </div>
          )}
        </section>
      </div>

      {/* ==================== EDIT CATEGORY MODAL ==================== */}
      {showEditModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-md z-[100] flex items-center justify-center p-4 animate-fade-in">
          <div className="glass-panel w-full max-w-lg rounded-2xl p-8 border border-white/10 shadow-2xl space-y-6 select-none animate-scale-up">
            <div className="flex justify-between items-center pb-4 border-b border-white/5">
              <h3 className="font-display text-2xl italic luxury-text-gradient">Edit Collection</h3>
              <button
                onClick={() => setShowEditModal(false)}
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
                  onClick={() => setShowEditModal(false)}
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
      {showDeleteModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-md z-[100] flex items-center justify-center p-4 animate-fade-in">
          <div className="glass-panel w-full max-w-md rounded-2xl p-8 border border-white/10 shadow-2xl space-y-6 select-none animate-scale-up">
            <div className="flex justify-between items-center pb-4 border-b border-white/5">
              <h3 className="font-display text-2xl italic text-error">Delete Collection</h3>
              <button
                onClick={() => setShowDeleteModal(false)}
                className="text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="space-y-4">
              <p className="font-body-md text-xs text-on-surface-variant leading-relaxed">
                Are you sure you want to permanently delete the collection <span className="text-on-surface font-semibold">"{currentCategory.title}"</span>?
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
                onClick={() => setShowDeleteModal(false)}
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

export default InventoryCategory;
