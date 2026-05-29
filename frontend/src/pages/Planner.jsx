import React, { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/layout/Layout";
import { getWardrobeItems } from "../utils/wardrobeStore";
import { apiGetSavedOutfits } from "../utils/outfitStore";
import {
  apiGetPlannerEntries,
  apiScheduleOutfit,
  apiUnscheduleOutfit,
  apiUpdatePlannedOutfit,
  apiAutoGeneratePlanner,
  apiUploadWearLog,
  apiDeleteWearLog
} from "../utils/plannerStore";

export const Planner = () => {
  // ── DATE CALCULATIONS (10-DAY OPERATIONAL TRACK) ──────────────────────────────
  const todayDateStr = useMemo(() => new Date().toISOString().split("T")[0], []);

  const dateTrack = useMemo(() => {
    const track = [];
    const today = new Date();
    // 2 days in past to 7 days in future
    for (let i = -2; i <= 7; i++) {
      const d = new Date(today);
      d.setDate(today.getDate() + i);
      const dateStr = d.toISOString().split("T")[0];
      const isToday = dateStr === todayDateStr;
      
      track.push({
        dateStr,
        label: isToday ? "TODAY" : d.toLocaleString("en-US", { weekday: "short" }).toUpperCase(),
        day: d.getDate().toString(),
        monthLabel: d.toLocaleString("en-US", { month: "long" }),
        year: d.getFullYear(),
        rawDate: d
      });
    }
    return track;
  }, [todayDateStr]);

  // ── STATES ──────────────────────────────────────────────────────────────────
  const [selectedDateStr, setSelectedDateStr] = useState(todayDateStr);
  const [calendarGrid, setCalendarGrid] = useState({});
  const [loading, setLoading] = useState(false);
  const [aiPlanning, setAiPlanning] = useState(false);
  const [aiStepMsg, setAiStepMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // Modals & Forms
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [selectedSavedOutfit, setSelectedSavedOutfit] = useState(null);
  const [savedOutfitsList, setSavedOutfitsList] = useState([]);
  const [customItems, setCustomItems] = useState([]);
  const [selectedCustomIds, setSelectedCustomIds] = useState([]);
  const [outfitSource, setOutfitSource] = useState("custom_user"); // "custom_user" | "saved_outfit"

  // Schedule Form Fields
  const [timeSlot, setTimeSlot] = useState("Morning Meeting");
  const [occasion, setOccasion] = useState("WORK");
  const [notes, setNotes] = useState("");

  // Snapshot Logs
  const [uploadingSlotId, setUploadingSlotId] = useState(null);

  // Active Month Header Calculation
  const activeDateInfo = useMemo(() => {
    return dateTrack.find(d => d.dateStr === selectedDateStr) || dateTrack[2];
  }, [selectedDateStr, dateTrack]);

  // ── FETCH CALENDAR & DATA ──────────────────────────────────────────────────
  const fetchPlannerGrid = async () => {
    setLoading(true);
    setErrorMsg("");
    try {
      const start = dateTrack[0].dateStr;
      const end = dateTrack[dateTrack.length - 1].dateStr;
      const response = await apiGetPlannerEntries(start, end);
      
      const grid = {};
      if (response && response.calendar) {
        response.calendar.forEach(day => {
          grid[day.date] = day;
        });
      }
      setCalendarGrid(grid);
    } catch (err) {
      console.error("Failed fetching calendar grid:", err);
      setErrorMsg("Unable to retrieve planner. Displaying cached schedule.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlannerGrid();
    // Cache wardrobe custom items
    setCustomItems(getWardrobeItems());
    
    // Fetch user's saved outfits
    apiGetSavedOutfits()
      .then(res => {
        if (res && res.outfits) {
          setSavedOutfitsList(res.outfits);
        }
      })
      .catch(err => console.warn("Failed fetching saved outfits:", err));
  }, [dateTrack]);

  // ── ACTIVE AGENDA FOR SELECTED DATE ─────────────────────────────────────────
  const activeDaySlots = useMemo(() => {
    const dayData = calendarGrid[selectedDateStr];
    return dayData ? dayData.planned_slots : [];
  }, [calendarGrid, selectedDateStr]);

  // ── HANDLERS ───────────────────────────────────────────────────────────────

  // A. Trigger AI Auto-Planner
  const handleTriggerAiPlanner = async (days = 3) => {
    setIsAiModalOpen(false);
    setAiPlanning(true);
    setErrorMsg("");
    
    const steps = [
      "Analyzing 10-day local micro-climate forecast...",
      "Evaluating wardrobe HSL color distribution indices...",
      "Matching garment textures & fabric density...",
      "Running body type drape compatibility parameters...",
      "Structuring professional vs. casual agenda tracks...",
      "Finalizing smart calendar look overlays..."
    ];

    let currentStep = 0;
    setAiStepMsg(steps[0]);
    const stepInterval = setInterval(() => {
      currentStep++;
      if (currentStep < steps.length) {
        setAiStepMsg(steps[currentStep]);
      }
    }, 700);

    try {
      // Build daily agendas starting from today
      const startTodayIndex = dateTrack.findIndex(d => d.dateStr === todayDateStr);
      const usableDates = dateTrack.slice(startTodayIndex, startTodayIndex + days);
      
      const agendas = usableDates.map(d => ({
        date: d.dateStr,
        slots: [
          { time_slot: "Morning Meeting", occasion: "work" },
          { time_slot: "Evening Lounge", occasion: "casual" }
        ]
      }));

      await apiAutoGeneratePlanner({
        start_date: todayDateStr,
        days_count: days,
        agendas
      });

      await fetchPlannerGrid();
    } catch (err) {
      console.error("AI Planner generation failed:", err);
      setErrorMsg("Failed to auto-plan looks: " + err.message);
    } finally {
      clearInterval(stepInterval);
      setAiPlanning(false);
      setAiStepMsg("");
    }
  };

  // B. Schedule Outfit Submit
  const handleScheduleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");

    const payload = {
      date: selectedDateStr,
      time_slot: timeSlot,
      occasion,
      outfit_source: outfitSource,
      notes,
      clothing_item_ids: outfitSource === "custom_user" ? selectedCustomIds : [],
      outfit_id: outfitSource === "saved_outfit" ? selectedSavedOutfit : null
    };

    if (outfitSource === "custom_user" && selectedCustomIds.length === 0) {
      setErrorMsg("Please select at least one wardrobe garment.");
      return;
    }

    if (outfitSource === "saved_outfit" && !selectedSavedOutfit) {
      setErrorMsg("Please select a saved outfit template.");
      return;
    }

    try {
      await apiScheduleOutfit(payload);
      setIsScheduleModalOpen(false);
      // Reset form states
      setSelectedCustomIds([]);
      setSelectedSavedOutfit(null);
      setNotes("");
      
      await fetchPlannerGrid();
    } catch (err) {
      console.error("Failed to schedule outfit:", err);
      setErrorMsg(err.message || "Failed to schedule slot.");
    }
  };

  // C. Unschedule Active Slot
  const handleUnscheduleSlot = async (slotId) => {
    if (!window.confirm("Are you sure you want to cancel and delete this planned outfit?")) return;
    setErrorMsg("");
    try {
      await apiUnscheduleOutfit(slotId);
      await fetchPlannerGrid();
    } catch (err) {
      console.error("Failed to unschedule outfit:", err);
      setErrorMsg(err.message || "Failed to remove outfit.");
    }
  };

  // D. Wear Log Snapshot Photo Upload
  const handleUploadWearLog = async (e, slotId) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploadingSlotId(slotId);
    setErrorMsg("");

    try {
      await apiUploadWearLog(file, selectedDateStr, slotId, "Real-life fit check snapshot.");
      await fetchPlannerGrid();
    } catch (err) {
      console.error("Failed uploading wear log snapshot:", err);
      setErrorMsg(err.message || "Failed uploading snapshot image.");
    } finally {
      setUploadingSlotId(null);
    }
  };

  // E. Delete Wear Log Snapshot
  const handleDeleteWearLog = async (logId) => {
    if (!window.confirm("Do you want to delete this real-life snapshot photo?")) return;
    setErrorMsg("");
    try {
      await apiDeleteWearLog(logId);
      await fetchPlannerGrid();
    } catch (err) {
      console.error("Failed deleting wear log snapshot:", err);
      setErrorMsg(err.message || "Failed to remove snapshot.");
    }
  };

  // F. Helper grouping flat garments categories
  const categorizedGarments = useMemo(() => {
    const categories = { tops: [], bottoms: [], footwear: [], outerwear: [], accessories: [] };
    customItems.forEach(item => {
      const cat = item.categories?.[0] || item.category || "tops";
      if (categories[cat]) {
        categories[cat].push(item);
      } else {
        categories.tops.push(item);
      }
    });
    return categories;
  }, [customItems]);

  const toggleGarmentSelection = (id) => {
    setSelectedCustomIds(prev => 
      prev.includes(id) ? prev.filter(cId => cId !== id) : [...prev, id]
    );
  };

  return (
    <Layout title="Outfit Planner">
      {/* Dynamic Header */}
      <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl mb-2 tracking-wide text-on-surface">Planner</h1>
          <p className="text-on-surface-variant text-sm font-medium">
            {activeDateInfo.monthLabel} {activeDateInfo.year}
          </p>
        </div>

        {/* Global Operations Buttons */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => setIsAiModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-tertiary/20 to-tertiary/30 hover:from-tertiary/30 hover:to-tertiary/40 text-tertiary border border-tertiary/30 rounded-full font-bold tracking-wider text-xs uppercase cursor-pointer transition-all duration-300 transform hover:scale-[1.02] shadow-md shadow-tertiary/5"
          >
            <span className="material-symbols-outlined text-sm select-none">auto_awesome</span>
            AI Auto-Plan
          </button>
          
          <button
            onClick={() => setIsScheduleModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-on-surface text-surface hover:bg-white rounded-full font-bold tracking-wider text-xs uppercase cursor-pointer transition-all duration-300 transform hover:scale-[1.02] shadow-md"
          >
            <span className="material-symbols-outlined text-sm select-none">add</span>
            Schedule Outfit
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-red-400 text-xs font-semibold flex items-center gap-2">
          <span className="material-symbols-outlined text-sm">warning</span>
          {errorMsg}
        </div>
      )}

      {/* Dynamic 10-Day Date Track */}
      <div className="flex space-x-4 overflow-x-auto hide-scrollbar pb-6 mb-8 border-b border-white/5 scroll-smooth">
        {dateTrack.map((date) => {
          const isSelected = selectedDateStr === date.dateStr;
          const isToday = date.dateStr === todayDateStr;
          const hasSlots = calendarGrid[date.dateStr]?.planned_slots?.length > 0;

          return (
            <button
              key={date.dateStr}
              onClick={() => setSelectedDateStr(date.dateStr)}
              className={`flex-shrink-0 flex flex-col items-center justify-center w-16 h-22 rounded-full transition-all duration-300 cursor-pointer relative ${
                isSelected
                  ? "bg-on-surface text-surface scale-105 shadow-xl"
                  : "border border-white/10 hover:border-white/20 text-on-surface bg-surface-container/30 hover:bg-surface-container/50"
              }`}
            >
              {isToday && (
                <span className={`absolute top-2 w-1.5 h-1.5 rounded-full ${isSelected ? "bg-surface" : "bg-tertiary animate-pulse"}`} />
              )}
              
              <span className={`text-[9px] mb-2 font-extrabold tracking-widest ${isSelected ? "opacity-90" : "text-on-surface-variant"}`}>
                {date.label}
              </span>
              
              <span className="font-display text-xl font-bold">{date.day}</span>
              
              {hasSlots && (
                <span className={`w-1 h-1 rounded-full mt-1.5 ${isSelected ? "bg-surface/50" : "bg-white/40"}`} />
              )}
            </button>
          );
        })}
      </div>

      {/* Visual Day Schedule Grid */}
      <div className="space-y-6">
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center gap-3">
            <div className="w-10 h-10 border-2 border-white/10 border-t-tertiary rounded-full animate-spin" />
            <p className="text-xs text-on-surface-variant font-medium">Synchronizing outfit agenda...</p>
          </div>
        ) : activeDaySlots.length === 0 ? (
          <div className="glass-panel p-10 rounded-2xl text-center flex flex-col items-center justify-center max-w-lg mx-auto border border-white/5 bg-white/[0.01]">
            <div className="w-16 h-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-4">
              <span className="material-symbols-outlined text-2xl text-on-surface-variant select-none">calendar_today</span>
            </div>
            <h3 className="font-display text-lg font-bold text-on-surface mb-2">No Looks Planned</h3>
            <p className="text-xs text-on-surface-variant leading-relaxed max-w-sm mb-6">
              You haven't scheduled any garments for {activeDateInfo.label.toLowerCase()} {activeDateInfo.monthLabel} {activeDateInfo.day} yet. Select a template or curate a custom outline!
            </p>
            <button
              onClick={() => setIsScheduleModalOpen(true)}
              className="px-5 py-2.5 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 text-on-surface text-xs font-bold uppercase tracking-wider transition-colors cursor-pointer"
            >
              Curate Active Slot
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-8">
            {activeDaySlots.map((slot) => {
              const hasWearLog = !!slot.wear_log;
              
              return (
                <div 
                  key={slot.planned_outfit_id}
                  className="glass-panel p-6 rounded-2xl border border-white/5 flex flex-col lg:flex-row gap-6 items-start relative hover:border-tertiary/10 transition-all duration-300 shadow-xl bg-gradient-to-br from-white/[0.02] to-transparent"
                >
                  
                  {/* Left: Slot info & Actions */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-3 mb-2">
                      <span className="text-[10px] text-tertiary tracking-widest uppercase font-bold px-2 py-0.5 bg-tertiary/10 border border-tertiary/20 rounded-md">
                        {slot.time_slot}
                      </span>
                      <span className="text-[10px] text-on-surface-variant tracking-wider uppercase font-semibold px-2 py-0.5 bg-white/5 border border-white/10 rounded-md">
                        {slot.occasion}
                      </span>
                      {slot.vogue_score && (
                        <span className="text-[10px] text-amber-400 font-semibold flex items-center gap-1">
                          <span className="material-symbols-outlined text-[10px] select-none fill-amber-400">star</span>
                          {slot.vogue_score}% Vogue score
                        </span>
                      )}
                    </div>
                    
                    <h3 className="font-display text-2xl font-bold mb-3 text-on-surface tracking-wide">
                      {slot.outfit_source === "saved_outfit" ? "Curated Ensemble" : "Custom Outfit Coordination"}
                    </h3>
                    
                    <p className="text-sm text-on-surface-variant leading-relaxed mb-6 font-medium">
                      {slot.notes || "No custom styling remarks logged."}
                    </p>

                    {/* Garment flat icons layout */}
                    <div className="mb-6">
                      <h4 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-3">Garments Selection</h4>
                      <div className="flex flex-wrap gap-4">
                        {slot.items.map((item, idx) => (
                          <div key={item.id || idx} className="flex items-center gap-3 bg-white/[0.02] border border-white/5 p-2 rounded-xl">
                            <img 
                              src={item.processed_image_url || "/assets/curation_collage_feature.png"} 
                              alt={item.name} 
                              className="w-10 h-10 object-cover rounded-lg bg-surface-container"
                              onError={(e) => { e.target.src = "/assets/curation_collage_feature.png"; }}
                            />
                            <div className="text-left">
                              <p className="text-[10px] font-bold text-on-surface line-clamp-1">{item.name}</p>
                              <p className="text-[9px] text-on-surface-variant capitalize">{item.category}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="flex items-center gap-4 mt-auto">
                      <button
                        onClick={() => handleUnscheduleSlot(slot.planned_outfit_id)}
                        className="text-xs text-red-400 hover:text-red-300 font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
                      >
                        <span className="material-symbols-outlined text-sm select-none">delete</span>
                        Unschedule
                      </button>
                      
                      {slot.outfit_id && (
                        <Link
                          to={`/app/outfit/${slot.outfit_id}`}
                          className="text-xs text-on-surface font-semibold underline hover:text-tertiary transition-colors flex items-center gap-1"
                        >
                          View Stylist Details
                        </Link>
                      )}
                    </div>
                  </div>

                  {/* Middle / Right: Real-life Snap wear log */}
                  <div className="w-full lg:w-72 shrink-0 border-t lg:border-t-0 lg:border-l border-white/5 pt-6 lg:pt-0 lg:pl-6 flex flex-col gap-4">
                    <h4 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase">Wear Snapshot</h4>
                    
                    {hasWearLog ? (
                      <div className="group relative rounded-xl overflow-hidden aspect-[4/5] bg-surface-container border border-white/10 shadow-lg flex flex-col justify-end">
                        <img 
                          src={slot.wear_log.image_url} 
                          alt="Logged look" 
                          className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                        />
                        {/* Overlay backdrop */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent p-4 flex flex-col justify-end">
                          <p className="text-[10px] text-tertiary font-bold tracking-wider mb-1 uppercase">Logged Snapshot</p>
                          <p className="text-[11px] text-white/95 leading-relaxed line-clamp-3 italic">
                            "{slot.wear_log.notes}"
                          </p>
                          
                          <button
                            onClick={() => handleDeleteWearLog(slot.wear_log.log_id)}
                            className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/60 backdrop-blur-md border border-white/10 flex items-center justify-center text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer shadow-md"
                            title="Delete snapshot"
                          >
                            <span className="material-symbols-outlined text-sm select-none">delete</span>
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="border border-dashed border-white/15 rounded-xl aspect-[4/5] flex flex-col items-center justify-center p-6 text-center hover:border-tertiary/30 transition-colors relative bg-white/[0.005]">
                        {uploadingSlotId === slot.planned_outfit_id ? (
                          <div className="flex flex-col items-center gap-2">
                            <div className="w-8 h-8 border-2 border-white/10 border-t-tertiary rounded-full animate-spin" />
                            <p className="text-[10px] text-tertiary font-bold tracking-wider uppercase animate-pulse">Uploading Snapshot...</p>
                          </div>
                        ) : (
                          <>
                            <span className="material-symbols-outlined text-2xl text-on-surface-variant mb-2 select-none">add_a_photo</span>
                            <span className="text-[10px] font-bold text-on-surface mb-1 uppercase">Log Fit Snapshot</span>
                            <span className="text-[9px] text-on-surface-variant leading-relaxed mb-4">Wore this outfit? Upload a snapshot to check fit reactions!</span>
                            
                            <label className="px-3.5 py-1.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-on-surface text-[10px] font-bold uppercase tracking-wider transition-colors cursor-pointer block">
                              Select Image
                              <input 
                                type="file" 
                                accept="image/jpeg,image/png,image/webp" 
                                onChange={(e) => handleUploadWearLog(e, slot.planned_outfit_id)} 
                                className="hidden" 
                              />
                            </label>
                          </>
                        )}
                      </div>
                    )}
                  </div>

                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── MODAL: SCHEDULE OUTFIT (BUILD CUSTOM OR SELECT TEMPLATE) ─────────────── */}
      {isScheduleModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
          <div className="glass-panel max-w-2xl w-full p-8 rounded-2xl border border-white/10 shadow-2xl relative max-h-[90vh] overflow-y-auto scrollbar-thin bg-[#121317]">
            
            <button 
              onClick={() => {
                setIsScheduleModalOpen(false);
                setSelectedCustomIds([]);
                setSelectedSavedOutfit(null);
                setNotes("");
              }}
              className="absolute top-4 right-4 text-on-surface-variant hover:text-white transition-colors cursor-pointer w-8 h-8 flex items-center justify-center rounded-full bg-white/5 border border-white/10"
            >
              <span className="material-symbols-outlined text-sm select-none">close</span>
            </button>

            <h2 className="font-display text-2xl font-bold mb-6 text-on-surface tracking-wide flex items-center gap-2">
              <span className="material-symbols-outlined text-tertiary select-none">checkroom</span>
              Schedule Calendar Outfit
            </h2>

            <form onSubmit={handleScheduleSubmit} className="space-y-6">
              
              {/* Row 1: Slot Name & Occasion */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-2">Time Slot Name</label>
                  <select 
                    value={timeSlot} 
                    onChange={(e) => setTimeSlot(e.target.value)}
                    className="w-full bg-white/5 border border-white/15 p-3 rounded-xl text-xs text-on-surface font-semibold focus:border-tertiary focus:outline-none"
                  >
                    <option value="Morning Meeting" className="bg-[#121317]">Morning Meeting</option>
                    <option value="Afternoon Coffee" className="bg-[#121317]">Afternoon Coffee</option>
                    <option value="Evening Lounge" className="bg-[#121317]">Evening Lounge</option>
                    <option value="Night Gala" className="bg-[#121317]">Night Gala</option>
                    <option value="Cardio Workout" className="bg-[#121317]">Cardio Workout</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-2">Occasion Theme</label>
                  <select 
                    value={occasion} 
                    onChange={(e) => setOccasion(e.target.value)}
                    className="w-full bg-white/5 border border-white/15 p-3 rounded-xl text-xs text-on-surface font-semibold focus:border-tertiary focus:outline-none"
                  >
                    <option value="WORK" className="bg-[#121317]">WORKPLACE CHIC</option>
                    <option value="CASUAL" className="bg-[#121317]">SMART CASUAL</option>
                    <option value="FORMAL" className="bg-[#121317]">FORMAL ELEGANCE</option>
                    <option value="SPORTY" className="bg-[#121317]">ATHLEISURE / GYM</option>
                  </select>
                </div>
              </div>

              {/* Remarks */}
              <div>
                <label className="block text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-2">Styling Remarks / Notes</label>
                <textarea 
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="E.g., Match the leather textures with dark metal accessories."
                  rows={2}
                  className="w-full bg-white/5 border border-white/15 p-3.5 rounded-xl text-xs text-on-surface placeholder:text-on-surface-variant/40 focus:border-tertiary focus:outline-none resize-none"
                />
              </div>

              {/* Outfit Source Selector */}
              <div>
                <label className="block text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-2">Curation Source</label>
                <div className="flex border border-white/10 rounded-xl overflow-hidden p-1 bg-white/[0.02]">
                  <button
                    type="button"
                    onClick={() => setOutfitSource("custom_user")}
                    className={`flex-1 py-2 text-center text-xs font-bold rounded-lg cursor-pointer transition-all duration-300 ${
                      outfitSource === "custom_user" ? "bg-on-surface text-surface" : "text-on-surface-variant hover:text-white"
                    }`}
                  >
                    Build Outfit on the go
                  </button>
                  <button
                    type="button"
                    onClick={() => setOutfitSource("saved_outfit")}
                    className={`flex-1 py-2 text-center text-xs font-bold rounded-lg cursor-pointer transition-all duration-300 ${
                      outfitSource === "saved_outfit" ? "bg-on-surface text-surface" : "text-on-surface-variant hover:text-white"
                    }`}
                  >
                    Select Saved Template
                  </button>
                </div>
              </div>

              {/* Conditional grid selector */}
              {outfitSource === "custom_user" ? (
                <div className="space-y-4 border-t border-white/5 pt-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-on-surface tracking-wider uppercase">Select Wardrobe Garments</h4>
                    <span className="text-[10px] text-tertiary font-bold tracking-widest uppercase bg-tertiary/10 border border-tertiary/20 px-2.5 py-0.5 rounded-md">
                      {selectedCustomIds.length} Selected
                    </span>
                  </div>

                  <div className="space-y-4 max-h-[35vh] overflow-y-auto pr-2 scrollbar-thin">
                    {Object.keys(categorizedGarments).map(catKey => {
                      const items = categorizedGarments[catKey];
                      if (items.length === 0) return null;
                      
                      return (
                        <div key={catKey}>
                          <h5 className="text-[9px] font-bold tracking-widest text-on-surface-variant uppercase mb-2">{catKey}</h5>
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                            {items.map(item => {
                              const isSelected = selectedCustomIds.includes(item.id);
                              
                              return (
                                <button
                                  type="button"
                                  key={item.id}
                                  onClick={() => toggleGarmentSelection(item.id)}
                                  className={`flex items-center gap-2 p-2 rounded-xl text-left border cursor-pointer transition-all duration-200 ${
                                    isSelected 
                                      ? "border-tertiary bg-tertiary/10 text-white" 
                                      : "border-white/5 bg-white/[0.01] hover:border-white/20 text-on-surface-variant hover:text-white"
                                  }`}
                                >
                                  <img 
                                    src={item.image} 
                                    alt={item.name} 
                                    className="w-8 h-8 object-cover rounded-lg bg-surface-container"
                                    onError={(e) => { e.target.src = "/assets/curation_collage_feature.png"; }}
                                  />
                                  <span className="text-[10px] font-bold line-clamp-1 leading-tight">{item.name}</span>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="space-y-4 border-t border-white/5 pt-4">
                  <h4 className="text-xs font-bold text-on-surface tracking-wider uppercase">Select Saved Template</h4>
                  
                  {savedOutfitsList.length === 0 ? (
                    <p className="text-[10px] text-on-surface-variant italic p-4 text-center border border-white/5 rounded-xl bg-white/[0.005]">
                      No saved outfits templates found. Build an outfit on the go instead!
                    </p>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-[35vh] overflow-y-auto pr-2 scrollbar-thin">
                      {savedOutfitsList.map(outfit => {
                        const isSelected = selectedSavedOutfit === outfit.id;
                        
                        return (
                          <button
                            type="button"
                            key={outfit.id}
                            onClick={() => setSelectedSavedOutfit(outfit.id)}
                            className={`flex gap-3 p-3 rounded-xl text-left border cursor-pointer transition-all duration-200 ${
                              isSelected 
                                ? "border-tertiary bg-tertiary/10" 
                                : "border-white/5 bg-white/[0.01] hover:border-white/20"
                            }`}
                          >
                            <div className="w-12 h-12 bg-surface-container border border-white/5 rounded-lg flex items-center justify-center shrink-0 overflow-hidden shadow-inner">
                              <img 
                                src={formatPreviewUrl(outfit.preview_url)} 
                                alt={outfit.name} 
                                className="w-full h-full object-cover"
                                onError={(e) => { e.target.src = "/assets/modern_noir_hero.png"; }}
                              />
                            </div>
                            <div className="min-w-0">
                              <p className="text-[10px] font-bold text-on-surface line-clamp-1">{outfit.name}</p>
                              <p className="text-[9px] text-tertiary uppercase font-extrabold tracking-wider">{outfit.occasion}</p>
                              <p className="text-[9px] text-on-surface-variant line-clamp-1 leading-normal mt-1">{outfit.reasoning}</p>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              <button
                type="submit"
                className="w-full py-3.5 bg-on-surface text-surface hover:bg-white transition-all font-bold tracking-widest text-xs uppercase rounded-xl cursor-pointer shadow-lg mt-4 flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined text-sm select-none">calendar_today</span>
                Schedule Look
              </button>

            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: AI AUTO-PLAN INTENSITY SELECTOR ────────────────────────────────── */}
      {isAiModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel max-w-sm w-full p-6 rounded-2xl border border-white/10 shadow-2xl relative text-center bg-[#121317]">
            <button 
              onClick={() => setIsAiModalOpen(false)}
              className="absolute top-4 right-4 text-on-surface-variant hover:text-white transition-colors cursor-pointer w-7 h-7 flex items-center justify-center rounded-full bg-white/5 border border-white/10"
            >
              <span className="material-symbols-outlined text-xs select-none">close</span>
            </button>

            <span className="material-symbols-outlined text-4xl text-tertiary select-none animate-pulse mb-3">auto_awesome</span>
            
            <h3 className="font-display text-xl font-bold text-on-surface mb-2">VOGUE.AI Auto-Planning</h3>
            <p className="text-xs text-on-surface-variant leading-relaxed mb-6">
              Let the curation engine dynamically build color-harmonized, weather-tailored daily outfit tracks directly from your closet.
            </p>

            <div className="space-y-3">
              <button
                onClick={() => handleTriggerAiPlanner(3)}
                className="w-full py-3 bg-gradient-to-r from-tertiary/20 to-tertiary/30 hover:from-tertiary/30 hover:to-tertiary/40 border border-tertiary/25 text-tertiary transition-all font-bold tracking-wider text-xs uppercase rounded-xl cursor-pointer flex items-center justify-center gap-2 shadow-md shadow-tertiary/5"
              >
                Plan Next 3 Days
              </button>
              
              <button
                onClick={() => handleTriggerAiPlanner(7)}
                className="w-full py-3 bg-white/5 border border-white/10 hover:bg-white/10 text-on-surface transition-all font-bold tracking-wider text-xs uppercase rounded-xl cursor-pointer"
              >
                Plan Next 7 Days (Full Week)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── AI PLANNING FULLSCREEN BLUR LOADER ────────────────────────────────────────── */}
      {aiPlanning && (
        <div className="fixed inset-0 z-[100] bg-black/85 backdrop-blur-lg flex flex-col items-center justify-center p-6 text-center select-none">
          <div className="relative mb-6">
            {/* Double golden orbits spinner */}
            <div className="w-16 h-16 rounded-full border-2 border-white/5 border-t-tertiary animate-spin" />
            <div className="absolute inset-2 rounded-full border border-white/5 border-b-tertiary/50 animate-spin-reverse" />
          </div>
          
          <p className="font-display text-lg font-extrabold tracking-widest text-white uppercase mb-2 animate-pulse">
            VOGUE.AI Stylist Active
          </p>
          
          <p className="text-xs text-tertiary font-bold tracking-wider uppercase h-4">
            {aiStepMsg}
          </p>
        </div>
      )}
    </Layout>
  );
};

export default Planner;
