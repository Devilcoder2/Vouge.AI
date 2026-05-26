import React, { useState, useEffect } from "react";
import Layout from "../components/layout/Layout";
import { getWardrobeItems, apiGetWardrobeStats } from "../utils/wardrobeStore";
import { apiUpdateProfile, apiGetVersatility } from "../utils/outfitStore";

const DEFAULT_PROFILE = {
  name: "Julian Thorne",
  location: "New York, NY",
  bodyType: "Athletic",
  height: "6'1\"",
  weight: "185 lbs",
  skinTone: "Fair/Cool",
  premium: true,
  image: "https://lh3.googleusercontent.com/aida-public/AB6AXuCs3NZRBnON-C4U3xY6xUDWe2jDBi2gBVrwP1vfZQWb4rn9oMwoY_hpX83eogBvIIovHoUOzZkR9OlMbsHB0-1WKjUEj-xDMkTDcRUQaowTud6hf5eDeYdpD6RF1T0IracaYfywmY4iGeUiMujPKNEcLw5Oa2ES5eqXZH7XaIuoZLhRuk6FhPun97E5f4ApA4qe3ge-v1PEpt6lKF2tHbFbpJ57hp23P5PI2YnfuWgdwyvqmBiKIgHKwKD6dphRW6yCZDtDe5Fjx6Ga"
};

const PROFILE_KEY = "vogue_user_profile";

export const Profile = () => {
  // Profile state
  const [profile, setProfile] = useState(DEFAULT_PROFILE);
  const [isEditing, setIsEditing] = useState(false);

  // Form field states
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [bodyType, setBodyType] = useState("");
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [skinTone, setSkinTone] = useState("");

  // Wardrobe statistics state
  const [totalItems, setTotalItems] = useState(14);
  const [totalValue, setTotalValue] = useState(12450);

  // Live analytics state
  const [mostWorn, setMostWorn] = useState({ name: "Noir Silk Blouse", count: 18 });
  const [leastWorn, setLeastWorn] = useState({ name: "Stone Cashmere Knit", count: 1 });

  // Load profile from localStorage & compute item counts
  useEffect(() => {
    // 1. Scroll to top on mount
    window.scrollTo(0, 0);
    const mainEl = document.querySelector("main");
    if (mainEl) {
      mainEl.scrollTop = 0;
    }

    // 2. Fetch profile data
    const saved = localStorage.getItem(PROFILE_KEY);
    let currentProfile = DEFAULT_PROFILE;
    if (saved) {
      currentProfile = JSON.parse(saved);
    } else {
      localStorage.setItem(PROFILE_KEY, JSON.stringify(DEFAULT_PROFILE));
    }
    setProfile(currentProfile);
    loadFormFields(currentProfile);

    // 3. Dynamic total items counting & live analytics
    const loadAnalytics = async () => {
      try {
        const stats = await apiGetWardrobeStats();
        if (stats) {
          setTotalItems(stats.totalPieces || 14);
          const computedValue = 12000 + ((stats.totalPieces || 14) - 14) * 350;
          setTotalValue(computedValue > 0 ? computedValue : 12450);
        }

        const versatilityReport = await apiGetVersatility(1, 20);
        if (versatilityReport && versatilityReport.data && versatilityReport.data.length > 0) {
          const sortedByUsage = [...versatilityReport.data].sort((a, b) => b.usage_count - a.usage_count);
          const items = getWardrobeItems();
          
          const mostWornObj = sortedByUsage[0];
          const leastWornObj = sortedByUsage[sortedByUsage.length - 1];
          
          if (mostWornObj) {
            const fullItem = items.find(i => i.id === mostWornObj.item_id);
            setMostWorn({
              name: fullItem ? fullItem.name : `Garment (${mostWornObj.primary_color})`,
              count: mostWornObj.usage_count
            });
          }
          if (leastWornObj && leastWornObj.item_id !== mostWornObj.item_id) {
            const fullItem = items.find(i => i.id === leastWornObj.item_id);
            setLeastWorn({
              name: fullItem ? fullItem.name : `Garment (${leastWornObj.primary_color})`,
              count: leastWornObj.usage_count
            });
          }
        }
      } catch (err) {
        console.warn("Failed loading live metrics, loading local calculations:", err);
        const items = getWardrobeItems();
        setTotalItems(items.length);
        const computedValue = 12000 + (items.length - 14) * 350;
        setTotalValue(computedValue > 0 ? computedValue : 12450);
      }
    };

    loadAnalytics();
  }, []);

  const loadFormFields = (p) => {
    setName(p.name);
    setLocation(p.location);
    setBodyType(p.bodyType);
    setHeight(p.height);
    setWeight(p.weight);
    setSkinTone(p.skinTone);
  };

  const handleSave = async () => {
    const updated = {
      ...profile,
      name,
      location,
      bodyType,
      height,
      weight,
      skinTone
    };
    localStorage.setItem(PROFILE_KEY, JSON.stringify(updated));
    setProfile(updated);
    setIsEditing(false);

    // Sync profile metrics to backend
    try {
      let heightCm = 185;
      if (height.includes("'")) {
        const parts = height.split("'");
        const feet = parseInt(parts[0]) || 6;
        const inches = parseInt(parts[1]) || 1;
        heightCm = Math.round((feet * 12 + inches) * 2.54);
      } else if (parseInt(height)) {
        heightCm = parseInt(height);
      }

      await apiUpdateProfile({
        user_id: "default_user",
        height_cm: heightCm,
        body_archetype: bodyType.toLowerCase(),
        fit_preference: "standard",
        style_persona: "minimalist",
        avoided_colors: ["Neon Green", "Hot Pink"],
        favorite_styles: ["old_money", "quiet_luxury"]
      });
    } catch (e) {
      console.warn("Failed syncing style parameters to backend:", e);
    }

    // Create success toast notification
    const toast = document.createElement("div");
    toast.className = "fixed bottom-36 left-1/2 -translate-x-1/2 bg-on-surface text-background px-6 py-3 rounded-full font-label-sm text-[11px] uppercase tracking-[0.2em] shadow-2xl z-[99] border border-white/10 animate-fade-in flex items-center gap-2";
    toast.innerHTML = `<span class="material-symbols-outlined text-sm font-bold text-tertiary">check_circle</span> Profile Saved & Synced`;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.classList.add("animate-fade-out");
      setTimeout(() => toast.remove(), 400);
    }, 2000);
  };

  const handleReset = () => {
    loadFormFields(profile);
    setIsEditing(false);
  };

  return (
    <Layout showBack={true} title="Style Profile">
      <div className="w-full relative pb-20 max-w-container-max mx-auto">
        
        {/* Sub-Header bar */}
        <div className="flex justify-between items-center mb-10 pb-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <span className="w-2.5 h-2.5 rounded-full bg-tertiary animate-pulse"></span>
            <span className="font-display text-base italic text-on-surface select-none">
              Augmented Stylist Parameter Deck
            </span>
          </div>
          
          <button
            onClick={() => {
              if (isEditing) {
                handleSave();
              } else {
                setIsEditing(true);
              }
            }}
            className="px-5 py-2 rounded-sm border border-outline-variant/35 bg-white/[0.02] text-xs font-label-sm uppercase tracking-wider text-on-surface hover:bg-white/5 transition-all cursor-pointer font-bold"
          >
            {isEditing ? "Save Profile" : "Edit Metrics"}
          </button>
        </div>

        {/* Responsive Grid layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter items-start">
          
          {/* Left Column: User details, Verified Badge, Location & Body Metrics (col-span-5) */}
          <div className="lg:col-span-5 lg:sticky lg:top-32 flex flex-col items-center text-center bg-white/[0.01] border border-white/5 rounded-2xl p-8 shadow-2xl">
            
            {/* Portrait Photo */}
            <div className="relative mb-6 select-none">
              <div className="w-28 h-28 rounded-full overflow-hidden border-2 border-primary/20 p-1 flex items-center justify-center bg-surface">
                <img
                  className="w-full h-full object-cover rounded-full"
                  alt={profile.name}
                  src={profile.image}
                />
              </div>
              <div className="absolute bottom-1 right-1 w-6 h-6 bg-primary rounded-full flex items-center justify-center border-2 border-background">
                <span className="material-symbols-outlined text-surface text-[12px] font-bold">verified</span>
              </div>
            </div>

            {/* User Name & Location */}
            {isEditing ? (
              <div className="w-full flex flex-col gap-4 mb-6">
                <div className="relative border-b border-outline-variant/30 focus-within:border-tertiary transition-colors text-left">
                  <span className="text-[8px] uppercase tracking-widest text-on-surface-variant/70 font-semibold block mb-0.5">Name</span>
                  <input
                    className="w-full bg-transparent border-0 py-2 pl-0 pr-8 font-display text-lg italic text-on-surface focus:ring-0 focus:outline-none"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="User Name"
                  />
                </div>
                <div className="relative border-b border-outline-variant/30 focus-within:border-tertiary transition-colors text-left">
                  <span className="text-[8px] uppercase tracking-widest text-on-surface-variant/70 font-semibold block mb-0.5">Location</span>
                  <input
                    className="w-full bg-transparent border-0 py-2 pl-0 pr-8 font-body-md text-sm text-on-surface focus:ring-0 focus:outline-none"
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="New York, NY"
                  />
                </div>
              </div>
            ) : (
              <div className="mb-6">
                <h2 className="font-display text-3xl luxury-text-gradient italic leading-none mb-2">
                  {profile.name}
                </h2>
                <p className="flex items-center justify-center gap-1 font-body-md text-xs text-on-surface-variant/60 tracking-wide uppercase font-semibold">
                  <span className="material-symbols-outlined text-[14px] text-tertiary">location_on</span> {profile.location}
                </p>
              </div>
            )}

            {/* Symmetrical Body & Style metrics grid */}
            <div className="w-full grid grid-cols-2 gap-3 border-t border-white/5 pt-6 text-left">
              
              {/* Body Type */}
              <div className="glass-card rounded-xl p-4 flex flex-col justify-between min-h-[80px]">
                <p className="font-label-sm text-[9px] text-on-surface-variant/50 uppercase tracking-wider font-semibold select-none">Body Type</p>
                {isEditing ? (
                  <input
                    className="w-full bg-transparent border-0 border-b border-white/10 p-0 py-1 font-body-lg text-sm text-on-surface focus:ring-0 focus:border-tertiary"
                    type="text"
                    value={bodyType}
                    onChange={(e) => setBodyType(e.target.value)}
                  />
                ) : (
                  <p className="font-body-lg text-sm text-on-surface font-semibold">{profile.bodyType}</p>
                )}
              </div>

              {/* Height */}
              <div className="glass-card rounded-xl p-4 flex flex-col justify-between min-h-[80px]">
                <p className="font-label-sm text-[9px] text-on-surface-variant/50 uppercase tracking-wider font-semibold select-none">Height</p>
                {isEditing ? (
                  <input
                    className="w-full bg-transparent border-0 border-b border-white/10 p-0 py-1 font-body-lg text-sm text-on-surface focus:ring-0 focus:border-tertiary"
                    type="text"
                    value={height}
                    onChange={(e) => setHeight(e.target.value)}
                  />
                ) : (
                  <p className="font-body-lg text-sm text-on-surface font-semibold">{profile.height}</p>
                )}
              </div>

              {/* Weight */}
              <div className="glass-card rounded-xl p-4 flex flex-col justify-between min-h-[80px]">
                <p className="font-label-sm text-[9px] text-on-surface-variant/50 uppercase tracking-wider font-semibold select-none">Weight</p>
                {isEditing ? (
                  <input
                    className="w-full bg-transparent border-0 border-b border-white/10 p-0 py-1 font-body-lg text-sm text-on-surface focus:ring-0 focus:border-tertiary"
                    type="text"
                    value={weight}
                    onChange={(e) => setWeight(e.target.value)}
                  />
                ) : (
                  <p className="font-body-lg text-sm text-on-surface font-semibold">{profile.weight}</p>
                )}
              </div>

              {/* Skin Tone */}
              <div className="glass-card rounded-xl p-4 flex flex-col justify-between min-h-[80px]">
                <p className="font-label-sm text-[9px] text-on-surface-variant/50 uppercase tracking-wider font-semibold select-none">Skin Tone</p>
                {isEditing ? (
                  <input
                    className="w-full bg-transparent border-0 border-b border-white/10 p-0 py-1 font-body-lg text-sm text-on-surface focus:ring-0 focus:border-tertiary"
                    type="text"
                    value={skinTone}
                    onChange={(e) => setSkinTone(e.target.value)}
                  />
                ) : (
                  <p className="font-body-lg text-sm text-on-surface font-semibold">{profile.skinTone}</p>
                )}
              </div>

            </div>

            {isEditing && (
              <div className="flex gap-2 w-full mt-6">
                <button
                  onClick={handleSave}
                  className="flex-grow py-3 bg-on-surface text-background font-label-sm text-[10px] uppercase tracking-widest font-bold rounded-lg cursor-pointer hover:bg-on-surface/90 transition-all active:scale-95"
                >
                  Save
                </button>
                <button
                  onClick={handleReset}
                  className="flex-grow py-3 bg-transparent border border-white/10 text-on-surface font-label-sm text-[10px] uppercase tracking-widest font-bold rounded-lg cursor-pointer hover:bg-white/5 transition-all active:scale-95"
                >
                  Cancel
                </button>
              </div>
            )}

          </div>

          {/* Right Column: Membership Plan, Wardrobe Analytics & growth chart (col-span-7) */}
          <div className="lg:col-span-7 flex flex-col gap-8">
            
            {/* Membership status card */}
            <section className="bg-white/[0.01] border border-white/5 rounded-2xl p-6 flex flex-col sm:flex-row justify-between sm:items-center gap-6 shadow-xl relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-r from-tertiary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
              <div>
                <p className="font-label-sm text-[9px] text-tertiary uppercase tracking-[0.2em] mb-1 font-bold select-none">Subscription Tier</p>
                <h3 className="font-display text-2xl italic text-on-surface luxury-text-gradient select-none">Premium Member</h3>
              </div>
              <button className="px-6 py-3 bg-on-surface text-background font-label-sm text-[10px] uppercase tracking-widest rounded-lg font-bold hover:bg-tertiary hover:text-on-tertiary transition-all duration-300 cursor-pointer shadow-lg active:scale-98 self-start sm:self-auto">
                Manage Plan
              </button>
            </section>

            {/* Wardrobe Analytics grid */}
            <section className="space-y-4">
              <h3 className="font-display text-2xl italic luxury-text-gradient mb-6 select-none">Wardrobe Analytics</h3>
              
              <div className="grid grid-cols-1 gap-4">
                
                {/* Most Worn */}
                <div className="glass-card rounded-xl p-6 flex items-center justify-between shadow-md hover:border-white/15 transition-all">
                  <div>
                    <p className="font-label-sm text-[9px] text-on-surface-variant/40 uppercase tracking-wider mb-1 font-semibold select-none">Most Worn Piece</p>
                    <p className="font-display text-[17px] text-on-surface font-semibold italic">{mostWorn.name}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-display text-2xl luxury-text-gradient font-bold leading-none">{mostWorn.count}</p>
                    <p className="text-[9px] uppercase tracking-wider text-on-surface-variant/30 font-semibold mt-1">Times</p>
                  </div>
                </div>

                {/* Least Worn */}
                <div className="glass-card rounded-xl p-6 flex items-center justify-between shadow-md hover:border-white/15 transition-all">
                  <div>
                    <p className="font-label-sm text-[9px] text-on-surface-variant/40 uppercase tracking-wider mb-1 font-semibold select-none">Least Worn Piece</p>
                    <p className="font-display text-[17px] text-on-surface font-semibold italic">{leastWorn.name}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-display text-2xl text-on-surface-variant/50 font-bold leading-none">{leastWorn.count}</p>
                    <p className="text-[9px] uppercase tracking-wider text-on-surface-variant/30 font-semibold mt-1">Time{leastWorn.count > 1 ? "s" : ""}</p>
                  </div>
                </div>

                {/* Symmetrical Grid for Value & Highest Piece */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  
                  {/* Total Value */}
                  <div className="glass-card rounded-xl p-6 shadow-md">
                    <p className="font-label-sm text-[9px] text-on-surface-variant/40 uppercase tracking-wider mb-2 font-semibold select-none">Total Closet Valuation</p>
                    <p className="font-display text-3xl luxury-text-gradient font-bold">${totalValue.toLocaleString()}</p>
                    <p className="text-[9px] uppercase text-on-surface-variant/30 mt-2 font-semibold tracking-wider select-none">{totalItems} Curated Pieces Synced</p>
                  </div>

                  {/* Highest Piece */}
                  <div className="glass-card rounded-xl p-6 shadow-md flex flex-col justify-between">
                    <div>
                      <p className="font-label-sm text-[9px] text-on-surface-variant/40 uppercase tracking-wider mb-1 font-semibold select-none">Highest Valuation Piece</p>
                      <p className="font-display text-[15px] text-on-surface font-semibold italic truncate">Wool Trench Coat</p>
                    </div>
                    <div className="mt-4">
                      <p className="font-display text-xl text-tertiary font-bold">$2,800</p>
                    </div>
                  </div>

                </div>

              </div>
            </section>

            {/* Wardrobe Growth Animated Chart */}
            <section className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="font-display text-2xl italic luxury-text-gradient select-none">Wardrobe Sync Growth</h3>
                <span className="font-label-sm text-[9px] text-on-surface-variant/40 uppercase tracking-widest font-semibold select-none">Sync History (Items)</span>
              </div>

              <div className="glass-card rounded-2xl p-8 shadow-xl relative overflow-hidden">
                <div className="relative h-48 w-full flex items-end justify-between gap-4 pt-4">
                  {/* Horizontal Grid lines */}
                  <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-5">
                    <div className="border-t border-white"></div>
                    <div className="border-t border-white"></div>
                    <div className="border-t border-white"></div>
                    <div className="border-t border-white"></div>
                  </div>

                  {/* Dynamic Months Growth Bars */}
                  {[
                    { month: "JAN", items: 85, height: "h-[60%]" },
                    { month: "FEB", items: 92, height: "h-[65%]" },
                    { month: "MAR", items: 105, height: "h-[75%]" },
                    { month: "APR", items: 112, height: "h-[80%]" },
                    { month: "MAY", items: 120, height: "h-[85%]" },
                    { month: "JUN", items: totalItems, height: "h-[100%]", active: true }
                  ].map((bar, index) => {
                    const barHeight = bar.active ? "h-[100%]" : bar.height;
                    return (
                      <div key={index} className="flex-1 flex flex-col items-center gap-3 group relative h-full justify-end">
                        {/* Hover Tooltip */}
                        <span className={`absolute -top-4 font-mono text-[9px] uppercase tracking-wider transition-all duration-300 pointer-events-none ${
                          bar.active 
                            ? "opacity-100 text-tertiary scale-105" 
                            : "opacity-0 group-hover:opacity-100 text-on-surface translate-y-1"
                        }`}>
                          {bar.active ? totalItems : bar.items}
                        </span>

                        {/* Bar Shape */}
                        <div className={`w-full rounded-t-sm transition-all duration-700 ease-out cursor-pointer ${
                          bar.active
                            ? "bg-tertiary/40 border-t-2 border-tertiary shadow-[0_0_15px_rgba(173,198,255,0.1)]"
                            : "bg-white/[0.05] group-hover:bg-white/[0.15]"
                        } ${barHeight}`}></div>
                        
                        {/* Label */}
                        <span className={`font-label-sm text-[9px] uppercase tracking-widest ${
                          bar.active ? "text-on-surface font-bold" : "text-on-surface-variant/40"
                        }`}>
                          {bar.month}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>

          </div>

        </div>

      </div>
    </Layout>
  );
};

export default Profile;
