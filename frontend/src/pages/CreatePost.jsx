import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import SocialLayout from "../components/layout/SocialLayout";
import { getWardrobeItems } from "../utils/wardrobeStore";
import { apiCreatePost, apiListCommunities } from "../utils/socialStore";

export const CreatePost = () => {
  const navigate = useNavigate();

  // Form parameters
  const [imageUrl, setImageUrl] = useState("");
  const [caption, setCaption] = useState("");
  const [occasionTag, setOccasionTag] = useState("Everyday Casual");
  const [stylePersona, setStylePersona] = useState("minimalist");
  const [weatherContext, setWeatherContext] = useState("Mild (16°C)");
  const [communityId, setCommunityId] = useState("");

  // Lists from store/API
  const [wardrobeItems, setWardrobeItems] = useState([]);
  const [communities, setCommunities] = useState([]);
  const [loadingComms, setLoadingComms] = useState(false);

  // Hotspot Tagging states
  const [taggedItems, setTaggedItems] = useState([]); // Array of { wardrobe_item_id, x_coord, y_coord, wardrobe_item }
  const [pendingTag, setPendingTag] = useState(null); // { x_coord, y_coord }
  const [selectedItemId, setSelectedItemId] = useState("");

  // Mock upload images array for instant rich aesthetic integration
  const MOCK_IMAGES = [
    "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?auto=format&fit=crop&w=800&q=80"
  ];

  useEffect(() => {
    // 1. Fetch wardrobe garments
    const closet = getWardrobeItems();
    setWardrobeItems(closet);

    // 2. Fetch communities
    const loadComms = async () => {
      setLoadingComms(true);
      try {
        const commsList = await apiListCommunities();
        setCommunities(commsList);
      } catch (e) {
        console.error(e);
      } finally {
        setLoadingComms(false);
      }
    };
    loadComms();
  }, []);

  // Handle click coordinates on image canvas
  const handleImageClick = (e) => {
    if (!imageUrl) return;
    const rect = e.target.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setPendingTag({ x_coord: Number(x.toFixed(1)), y_coord: Number(y.toFixed(1)) });
    setSelectedItemId("");
  };

  const addTag = () => {
    if (!pendingTag || !selectedItemId) return;
    const item = wardrobeItems.find(wi => wi.id === selectedItemId);
    if (!item) return;

    // Avoid double tagging same item
    if (taggedItems.some(ti => ti.wardrobe_item_id === selectedItemId)) {
      setPendingTag(null);
      return;
    }

    setTaggedItems(prev => [
      ...prev,
      {
        wardrobe_item_id: selectedItemId,
        x_coord: pendingTag.x_coord,
        y_coord: pendingTag.y_coord,
        wardrobe_item: item
      }
    ]);
    setPendingTag(null);
  };

  const removeTag = (itemId) => {
    setTaggedItems(prev => prev.filter(ti => ti.wardrobe_item_id !== itemId));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!imageUrl || !caption.trim()) return;

    const payload = {
      image_url: imageUrl,
      caption: caption,
      occasion_tag: occasionTag,
      style_persona: stylePersona,
      weather_context: weatherContext,
      community_id: communityId || null,
      tagged_items: taggedItems.map(ti => ({
        wardrobe_item_id: ti.wardrobe_item_id,
        x_coord: ti.x_coord,
        y_coord: ti.y_coord
      }))
    };

    try {
      await apiCreatePost(payload);
      
      // Toast notification
      const toast = document.createElement("div");
      toast.className = "fixed bottom-36 left-1/2 -translate-x-1/2 bg-on-surface text-background px-6 py-3 rounded-full font-label-sm text-[11px] uppercase tracking-[0.2em] shadow-2xl z-[99] border border-white/10 animate-fade-in flex items-center gap-2";
      toast.innerHTML = `<span class="material-symbols-outlined text-sm font-bold text-tertiary">check_circle</span> Outfit Catalog Shared`;
      document.body.appendChild(toast);
      setTimeout(() => {
        toast.classList.add("animate-fade-out");
        setTimeout(() => toast.remove(), 400);
      }, 2000);

      navigate("/app/social/feed");
    } catch (err) {
      console.error("Failed creating post:", err);
    }
  };

  return (
    <SocialLayout title="Publish Outfit">
      <div className="max-w-2xl mx-auto pb-16 select-none">
        <div className="mb-8">
          <h2 className="font-display text-2xl italic luxury-text-gradient mb-1">Publish Curation</h2>
          <p className="text-[7px] uppercase tracking-[0.2em] text-on-surface-variant/40 font-semibold">
            Tag digitized garments directly on your outfit catalog
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          
          {/* Image Ingestion Box */}
          <div className="flex flex-col gap-3">
            <label className="font-label-sm text-[8px] uppercase tracking-widest text-on-surface-variant font-bold">
              Outfit Photo
            </label>
            
            {!imageUrl ? (
              <div className="glass rounded-2xl border-2 border-dashed border-white/10 p-8 flex flex-col items-center justify-center text-center gap-4 hover:border-white/20 transition-all select-none">
                <span className="material-symbols-outlined text-4xl text-on-surface-variant/30 animate-pulse">
                  add_a_photo
                </span>
                <div>
                  <h4 className="font-display text-sm italic text-white mb-0.5">Ingest Look Photo</h4>
                  <p className="text-[9px] text-on-surface-variant/50 max-w-xs mx-auto leading-relaxed">
                    Paste an image URL, choose a gorgeous aesthetic preset, or drop a wardrobe flat-lay.
                  </p>
                </div>

                <div className="w-full max-w-md mt-2">
                  <input
                    type="url"
                    value={imageUrl}
                    onChange={(e) => setImageUrl(e.target.value)}
                    placeholder="https://example.com/outfit-mirror-selfie.png"
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-on-surface-variant/30 focus:outline-none focus:border-white/20 font-light"
                  />
                </div>

                <div className="flex flex-col items-center gap-2 mt-2 w-full">
                  <span className="text-[7px] text-on-surface-variant/40 uppercase tracking-widest font-bold">
                    Or select pre-styled preset layout
                  </span>
                  <div className="flex gap-2">
                    {MOCK_IMAGES.map((img, idx) => (
                      <div
                        key={idx}
                        onClick={() => setImageUrl(img)}
                        className="w-12 h-14 rounded-lg overflow-hidden border border-white/10 cursor-pointer hover:border-tertiary hover:scale-105 active:scale-95 transition-all"
                      >
                        <img src={img} alt="Preset" className="w-full h-full object-cover" />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                {/* Hotspot canvas area */}
                <div className="relative aspect-[4/5] bg-black/40 border border-white/10 rounded-2xl overflow-hidden shadow-2xl flex items-center justify-center select-none">
                  <img
                    src={imageUrl}
                    alt="Uploaded flat lay"
                    onClick={handleImageClick}
                    className="w-full h-full object-cover cursor-crosshair"
                  />

                  {/* Instructions Overlay */}
                  <div className="absolute top-3 left-3 bg-[#1A1A1A]/75 backdrop-blur-xl border border-white/10 px-3 py-1.5 rounded-lg flex items-center gap-1.5 pointer-events-none select-none">
                    <span className="material-symbols-outlined text-[10px] text-tertiary animate-pulse">info</span>
                    <span className="font-label-sm text-[7px] text-on-surface uppercase tracking-wider font-semibold">
                      Click coordinates on photo to tag garments
                    </span>
                  </div>

                  {/* Change photo button */}
                  <button
                    type="button"
                    onClick={() => {
                      setImageUrl("");
                      setTaggedItems([]);
                      setPendingTag(null);
                    }}
                    className="absolute top-3 right-3 p-1.5 rounded-lg bg-surface-container-heavy border border-white/10 text-white hover:bg-error hover:text-white transition-all cursor-pointer shadow-md"
                  >
                    <span className="material-symbols-outlined text-xs">delete</span>
                  </button>

                  {/* Placed Hotspots */}
                  {taggedItems.map(ti => (
                    <div
                      key={ti.wardrobe_item_id}
                      style={{ left: `${ti.x_coord}%`, top: `${ti.y_coord}%` }}
                      className="absolute -translate-x-1/2 -translate-y-1/2 z-20 group"
                    >
                      <div className="w-6 h-6 bg-white/20 backdrop-blur-md rounded-full border-2 border-white flex items-center justify-center shadow-2xl animate-pulse">
                        <div className="w-2.5 h-2.5 bg-white rounded-full"></div>
                      </div>

                      {/* Info badge with quick remove */}
                      <div className="absolute bottom-7 left-1/2 -translate-x-1/2 bg-surface-container-heavy border border-white/10 rounded px-2 py-1 text-[8px] text-white truncate max-w-[120px] shadow-xl flex items-center gap-1">
                        <span className="truncate">{ti.wardrobe_item.name}</span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeTag(ti.wardrobe_item_id);
                          }}
                          className="text-on-surface-variant hover:text-error ml-1 font-bold text-[9px]"
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  ))}

                  {/* Temporary Pending Hotspot */}
                  {pendingTag && (
                    <div
                      style={{ left: `${pendingTag.x_coord}%`, top: `${pendingTag.y_coord}%` }}
                      className="absolute -translate-x-1/2 -translate-y-1/2 z-30"
                    >
                      <div className="w-6 h-6 bg-tertiary/40 backdrop-blur-md rounded-full border-2 border-tertiary flex items-center justify-center shadow-2xl">
                        <div className="w-2.5 h-2.5 bg-tertiary rounded-full"></div>
                      </div>

                      {/* Garment Selector Popup */}
                      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-48 p-2.5 bg-surface-container-heavy border border-white/15 rounded-xl shadow-2xl animate-scale-up z-40">
                        <span className="text-[7px] text-tertiary uppercase tracking-widest block font-bold mb-1.5 text-center">
                          Tag Wardrobe Item
                        </span>
                        
                        {wardrobeItems.length === 0 ? (
                          <p className="text-[7px] text-on-surface-variant/50 text-center py-2">
                            No digitized closet garments found.
                          </p>
                        ) : (
                          <div className="flex flex-col gap-1.5">
                            <select
                              value={selectedItemId}
                              onChange={(e) => setSelectedItemId(e.target.value)}
                              className="w-full bg-white/5 border border-white/10 rounded px-2 py-1 text-[9px] text-white focus:outline-none focus:border-white/20 font-light"
                            >
                              <option value="" className="bg-[#121317] text-white/40">Select item...</option>
                              {wardrobeItems.map(wi => {
                                const isAlreadyTagged = taggedItems.some(ti => ti.wardrobe_item_id === wi.id);
                                return (
                                  <option
                                    key={wi.id}
                                    value={wi.id}
                                    disabled={isAlreadyTagged}
                                    className="bg-[#121317] text-white"
                                  >
                                    {wi.name} ({wi.categories[0]})
                                  </option>
                                );
                              })}
                            </select>
                            
                            <div className="flex gap-1.5 mt-1">
                              <button
                                type="button"
                                onClick={addTag}
                                disabled={!selectedItemId}
                                className="flex-1 py-1 bg-white text-background font-label-sm text-[7px] uppercase tracking-widest rounded font-bold hover:bg-tertiary hover:text-on-tertiary disabled:opacity-40"
                              >
                                Tag
                              </button>
                              <button
                                type="button"
                                onClick={() => setPendingTag(null)}
                                className="flex-1 py-1 bg-transparent border border-white/10 text-white font-label-sm text-[7px] uppercase tracking-widest rounded font-bold hover:bg-white/5"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Form details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            
            {/* Occasion */}
            <div className="flex flex-col gap-2 select-none">
              <label className="font-label-sm text-[8px] uppercase tracking-widest text-on-surface-variant font-bold">
                Styling Occasion
              </label>
              <select
                value={occasionTag}
                onChange={(e) => setOccasionTag(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-xs text-white focus:outline-none focus:border-white/20 font-light"
              >
                {["Everyday Casual", "Work / Office", "Date Night", "Sport / Gym", "Evening Gala", "Casual Outing"].map(occ => (
                  <option key={occ} value={occ} className="bg-[#121317] text-white">{occ}</option>
                ))}
              </select>
            </div>

            {/* Persona */}
            <div className="flex flex-col gap-2 select-none">
              <label className="font-label-sm text-[8px] uppercase tracking-widest text-on-surface-variant font-bold">
                Style Persona
              </label>
              <select
                value={stylePersona}
                onChange={(e) => setStylePersona(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-xs text-white focus:outline-none focus:border-white/20 font-light"
              >
                {[
                  { value: "minimalist", label: "Minimalist" },
                  { value: "quiet_luxury", label: "Quiet Luxury" },
                  { value: "streetwear", label: "Streetwear" },
                  { value: "techwear", label: "Techwear" },
                  { value: "avant_garde", label: "Avant-Garde" },
                  { value: "vintage", label: "Vintage" }
                ].map(p => (
                  <option key={p.value} value={p.value} className="bg-[#121317] text-white">{p.label}</option>
                ))}
              </select>
            </div>

            {/* Weather Context */}
            <div className="flex flex-col gap-2 select-none">
              <label className="font-label-sm text-[8px] uppercase tracking-widest text-on-surface-variant font-bold">
                Weather Climate
              </label>
              <select
                value={weatherContext}
                onChange={(e) => setWeatherContext(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-xs text-white focus:outline-none focus:border-white/20 font-light"
              >
                {["Mild (16°C)", "Warm (22°C)", "Cold (8°C)", "Rainy (12°C)", "Hot (30°C)"].map(w => (
                  <option key={w} value={w} className="bg-[#121317] text-white">{w}</option>
                ))}
              </select>
            </div>

            {/* Target Community Group */}
            <div className="flex flex-col gap-2 select-none">
              <label className="font-label-sm text-[8px] uppercase tracking-widest text-on-surface-variant font-bold">
                Publish to Community (Optional)
              </label>
              <select
                value={communityId}
                onChange={(e) => setCommunityId(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-xs text-white focus:outline-none focus:border-white/20 font-light"
                disabled={loadingComms}
              >
                <option value="" className="bg-[#121317] text-white/40">Keep on Global Feed</option>
                {communities.map(c => (
                  <option key={c.id} value={c.id} className="bg-[#121317] text-white">{c.name}</option>
                ))}
              </select>
            </div>
            
          </div>

          {/* Caption */}
          <div className="flex flex-col gap-2">
            <label className="font-label-sm text-[8px] uppercase tracking-widest text-on-surface-variant font-bold select-none">
              Styling Caption
            </label>
            <textarea
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder="Describe the textile layers, silhouette, or draping coordinates..."
              rows={3}
              required
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-xs text-white placeholder-on-surface-variant/30 focus:outline-none focus:border-white/20 font-light resize-none"
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={!imageUrl || !caption.trim()}
            className="w-full py-3.5 bg-white text-background font-label-sm text-[10px] uppercase tracking-widest rounded-lg font-bold hover:bg-tertiary hover:text-on-tertiary transition-all active:scale-[0.98] disabled:opacity-40 cursor-pointer shadow-lg mt-2"
          >
            Publish Styled Look
          </button>
        </form>
      </div>
    </SocialLayout>
  );
};

export default CreatePost;
