// VOGUE.AI | Outfit Calendar & Planner Client Store
// Handles async API integrations with uvicorn and provides localized offline local storage fallbacks.

import { getWardrobeItems, formatImageUrl } from "./wardrobeStore";
import { formatPreviewUrl } from "./outfitStore";

const API_BASE = "http://localhost:8000";

// Local Storage Fallback Cache Key
const CALENDAR_CACHE_KEY = "vogue_planner_calendar_v1";

// ── GLOBAL DEDUPLICATION REGISTRY & HELPER ────────────────────────────────────
const activePromises = new Map();

/**
 * Custom fetch wrapper that de-duplicates concurrent requests to the exact same 
 * URL, method, and request payload, resolving them to the same active promise.
 */
const dedupeFetch = async (url, options = {}) => {
  const method = options.method || "GET";
  const bodyHash = options.body 
    ? (options.body instanceof FormData ? "formdata" : typeof options.body === "string" ? options.body : JSON.stringify(options.body))
    : "";
  const key = `${method}:${url}:${bodyHash}`;

  if (activePromises.has(key)) {
    console.log(`[DEDUPE] Joining existing inflight planner request: ${key}`);
    return activePromises.get(key);
  }

  const promise = (async () => {
    const res = await fetch(url, options);
    if (!res.ok) {
      const errText = await res.text().catch(() => "");
      throw new Error(`HTTP Error ${res.status}: ${errText || "Request failed"}`);
    }
    // Return text/json dynamically
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return await res.json();
    }
    return await res.text();
  })();

  activePromises.set(key, promise);

  try {
    return await promise;
  } finally {
    activePromises.delete(key);
  }
};

// Helper: Generate UUID for offline operations
const generateUUID = () => {
  return "offline-uuid-" + Math.random().toString(36).substr(2, 9) + "-" + Date.now();
};

// ── INITIAL / SEED DATA FOR LOCAL STORAGE ──────────────────────────────────────
const getInitialOfflineCalendar = () => {
  // Generates dynamic dates relative to today so the seed calendar is always fresh
  const today = new Date();
  const getOffsetDateString = (offset) => {
    const d = new Date(today);
    d.setDate(today.getDate() + offset);
    return d.toISOString().split("T")[0];
  };

  const dates = [
    { offset: -1, dayOfWeek: "YESTERDAY" },
    { offset: 0, dayOfWeek: "TODAY" },
    { offset: 1, dayOfWeek: "TOMORROW" },
    { offset: 2, dayOfWeek: "FUTURE" },
  ];

  const closet = getWardrobeItems();
  const getMockItem = (cat, index = 0) => {
    const matches = closet.filter(c => c.categories.includes(cat) || c.category === cat);
    const item = matches[index % (matches.length || 1)] || matches[0];
    if (item) {
      return {
        id: item.id,
        name: item.name,
        category: item.categories[0] || item.category || cat,
        processed_image_url: formatImageUrl(item.image)
      };
    }
    return null;
  };

  const calendarSeed = {};

  dates.forEach(({ offset, dayOfWeek }) => {
    const dateStr = getOffsetDateString(offset);
    let slots = [];

    if (offset === -1) {
      // Yesterday: Office Meeting + Wear Log Snap
      const trench = getMockItem("outerwear", 0) || { id: "trench", name: "Charcoal Wool Trench", category: "outerwear", processed_image_url: "/assets/outerwear_category.png" };
      const slacks = getMockItem("bottoms", 0) || { id: "slacks", name: "Slate Trousers", category: "bottoms", processed_image_url: "/assets/bottoms_category.png" };
      const boots = getMockItem("footwear", 0) || { id: "boots", name: "Derby Boots", category: "footwear", processed_image_url: "/assets/shoes_category.png" };

      slots.push({
        planned_outfit_id: "slot-yesterday-1",
        time_slot: "Office Meeting",
        occasion: "WORK",
        outfit_source: "custom_user",
        outfit_id: null,
        notes: "Crucial client deck pitch. Solid formal reaction.",
        vogue_score: 95,
        items: [trench, slacks, boots].filter(Boolean),
        wear_log: {
          log_id: "log-yesterday-snap",
          image_url: "/assets/fashion_portrait_gap.png",
          notes: "Felt incredibly classy. The wool layers held together flawlessly under overcast wind.",
          logged_at: new Date(new Date().setDate(new Date().getDate() - 1)).toISOString()
        }
      });
    } else if (offset === 0) {
      // Today: Casual Evening
      const knit = getMockItem("tops", 0) || { id: "knit", name: "Stone Cashmere Knit", category: "tops", processed_image_url: "/assets/tops_category.png" };
      const denim = getMockItem("bottoms", 1) || { id: "denim", name: "Raw Selvedge Denim", category: "bottoms", processed_image_url: "/assets/bottoms_category.png" };
      const sneakers = getMockItem("footwear", 1) || { id: "sneakers", name: "Minimal Leather Trainers", category: "footwear", processed_image_url: "/assets/shoes_category.png" };

      slots.push({
        planned_outfit_id: "slot-today-1",
        time_slot: "Evening Lounge",
        occasion: "CASUAL",
        outfit_source: "saved_outfit",
        outfit_id: "today-curation",
        notes: "Relaxing cozy weekend vibe.",
        vogue_score: 89,
        items: [knit, denim, sneakers].filter(Boolean),
        wear_log: null
      });
    } else if (offset === 1) {
      // Tomorrow: Morning Run
      const windbreaker = getMockItem("outerwear", 1) || { id: "windbreaker", name: "Reflective Windbreaker", category: "outerwear", processed_image_url: "/assets/outerwear_category.png" };
      const joggers = getMockItem("bottoms", 2) || { id: "joggers", name: "Utility Jogger Pants", category: "bottoms", processed_image_url: "/assets/bottoms_category.png" };

      slots.push({
        planned_outfit_id: "slot-tomorrow-1",
        time_slot: "Morning Cardio",
        occasion: "SPORTY",
        outfit_source: "custom_user",
        outfit_id: null,
        notes: "High-intensity wind protection.",
        vogue_score: 82,
        items: [windbreaker, joggers].filter(Boolean),
        wear_log: null
      });
    }

    calendarSeed[dateStr] = {
      date: dateStr,
      day_of_week: new Date(dateStr + "T00:00:00").toLocaleString("en-US", { weekday: "long" }).toUpperCase(),
      planned_slots: slots
    };
  });

  return calendarSeed;
};

// Read / Write Cache Helpers
const loadLocalCalendar = () => {
  try {
    const data = localStorage.getItem(CALENDAR_CACHE_KEY);
    if (data) return JSON.parse(data);
  } catch (e) {
    console.error("Failed to parse local calendar, rebuilding seed:", e);
  }
  const seed = getInitialOfflineCalendar();
  localStorage.setItem(CALENDAR_CACHE_KEY, JSON.stringify(seed));
  return seed;
};

const saveLocalCalendar = (cal) => {
  localStorage.setItem(CALENDAR_CACHE_KEY, JSON.stringify(cal));
};

// ── BACKEND API INTEGRATIONS (WITH RESILIENT LOCAL FALLBACKS) ─────────────────

/**
 * 1. GET /api/planner
 * Fetches scheduled calendar grid inside date range.
 */
export const apiGetPlannerEntries = async (startDate, endDate) => {
  try {
    const url = `${API_BASE}/api/planner?start_date=${startDate}&end_date=${endDate}`;
    const data = await dedupeFetch(url);
    
    // Store in local storage for synchronicity
    const cachedCal = loadLocalCalendar();
    if (data && data.calendar) {
      data.calendar.forEach(day => {
        cachedCal[day.date] = day;
      });
      saveLocalCalendar(cachedCal);
    }
    
    return data;
  } catch (err) {
    console.warn("Backend planner entries API unavailable, returning offline fallback:", err);
    
    const cachedCal = loadLocalCalendar();
    
    // Build calendar list dynamically for range
    const calendarList = [];
    let cur = new Date(startDate + "T00:00:00");
    const end = new Date(endDate + "T00:00:00");
    
    while (cur <= end) {
      const dateStr = cur.toISOString().split("T")[0];
      if (cachedCal[dateStr]) {
        calendarList.push(cachedCal[dateStr]);
      } else {
        calendarList.push({
          date: dateStr,
          day_of_week: cur.toLocaleString("en-US", { weekday: "long" }).toUpperCase(),
          planned_slots: []
        });
      }
      cur.setDate(cur.getDate() + 1);
    }
    
    return {
      start_date: startDate,
      end_date: endDate,
      calendar: calendarList
    };
  }
};

/**
 * 2. POST /api/planner/schedule
 * Schedules an outfit in a specific time slot on a specific date.
 */
export const apiScheduleOutfit = async (payload) => {
  try {
    const data = await dedupeFetch(`${API_BASE}/api/planner/schedule`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: payload.user_id || "default_user",
        date: payload.date,
        time_slot: payload.time_slot,
        occasion: payload.occasion || "CASUAL",
        outfit_source: payload.outfit_source || "custom_user",
        outfit_id: payload.outfit_id || null,
        clothing_item_ids: payload.clothing_item_ids || [],
        notes: payload.notes || ""
      })
    });
    return data;
  } catch (err) {
    console.warn("Backend planner schedule API down, writing to local mock storage:", err);
    
    const cachedCal = loadLocalCalendar();
    const dateStr = payload.date;
    
    if (!cachedCal[dateStr]) {
      cachedCal[dateStr] = {
        date: dateStr,
        day_of_week: new Date(dateStr + "T00:00:00").toLocaleString("en-US", { weekday: "long" }).toUpperCase(),
        planned_slots: []
      };
    }
    
    // Check slot uniqueness
    const exists = cachedCal[dateStr].planned_slots.some(s => s.time_slot.toLowerCase() === payload.time_slot.toLowerCase());
    if (exists) {
      throw new Error(`An outfit is already planned for the '${payload.time_slot}' slot on ${payload.date}.`);
    }
    
    // Enrich item thumbnails
    const closet = getWardrobeItems();
    const responseItems = (payload.clothing_item_ids || []).map(id => {
      const fullItem = closet.find(c => c.id === id);
      if (fullItem) {
        return {
          id: fullItem.id,
          name: fullItem.name,
          category: fullItem.categories[0] || "tops",
          processed_image_url: formatImageUrl(fullItem.image)
        };
      }
      return { id, name: "Closet Item", category: "tops", processed_image_url: "/assets/curation_collage_feature.png" };
    });
    
    const newSlotId = generateUUID();
    const newSlot = {
      planned_outfit_id: newSlotId,
      time_slot: payload.time_slot,
      occasion: (payload.occasion || "CASUAL").toUpperCase(),
      outfit_source: payload.outfit_source || "custom_user",
      outfit_id: payload.outfit_id || null,
      notes: payload.notes || "",
      vogue_score: payload.outfit_id ? 92 : 80,
      items: responseItems,
      wear_log: null
    };
    
    cachedCal[dateStr].planned_slots.push(newSlot);
    saveLocalCalendar(cachedCal);
    
    return {
      message: "Outfit scheduled successfully",
      planned_outfit_id: newSlotId,
      date: dateStr,
      time_slot: payload.time_slot,
      items_count: responseItems.length
    };
  }
};

/**
 * 3. DELETE /api/planner/schedule/{planned_outfit_id}
 * Un-schedules / deletes an outfit card slot.
 */
export const apiUnscheduleOutfit = async (plannedOutfitId) => {
  try {
    const data = await dedupeFetch(`${API_BASE}/api/planner/schedule/${plannedOutfitId}`, {
      method: "DELETE"
    });
    return data;
  } catch (err) {
    console.warn("Backend unschedule API down, evicting local mock entry:", err);
    
    const cachedCal = loadLocalCalendar();
    let found = false;
    
    Object.keys(cachedCal).forEach(dateStr => {
      const initialCount = cachedCal[dateStr].planned_slots.length;
      cachedCal[dateStr].planned_slots = cachedCal[dateStr].planned_slots.filter(
        slot => slot.planned_outfit_id !== plannedOutfitId
      );
      if (cachedCal[dateStr].planned_slots.length < initialCount) {
        found = true;
      }
    });
    
    if (found) {
      saveLocalCalendar(cachedCal);
      return {
        message: "Planned outfit successfully unscheduled.",
        planned_outfit_id: plannedOutfitId
      };
    }
    
    throw new Error("Planned scheduled outfit block not found.");
  }
};

/**
 * 4. PUT /api/planner/schedule/{planned_outfit_id}
 * Modifies remarks, time_slot, or garment items linked to an active slot.
 */
export const apiUpdatePlannedOutfit = async (plannedOutfitId, payload) => {
  try {
    const data = await dedupeFetch(`${API_BASE}/api/planner/schedule/${plannedOutfitId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return data;
  } catch (err) {
    console.warn("Backend update schedule API down, writing to local mock:", err);
    
    const cachedCal = loadLocalCalendar();
    let targetSlot = null;
    let targetDateStr = null;
    
    Object.keys(cachedCal).forEach(dateStr => {
      const slot = cachedCal[dateStr].planned_slots.find(s => s.planned_outfit_id === plannedOutfitId);
      if (slot) {
        targetSlot = slot;
        targetDateStr = dateStr;
      }
    });
    
    if (!targetSlot) {
      throw new Error("Planned scheduled outfit block not found.");
    }
    
    const updatedFields = [];
    
    if (payload.time_slot !== undefined) {
      // Check conflict
      const conflict = cachedCal[targetDateStr].planned_slots.some(
        s => s.planned_outfit_id !== plannedOutfitId && s.time_slot.toLowerCase() === payload.time_slot.toLowerCase()
      );
      if (conflict) {
        throw new Error(`An outfit is already planned for the '${payload.time_slot}' slot on ${targetDateStr}.`);
      }
      targetSlot.time_slot = payload.time_slot;
      updatedFields.push("time_slot");
    }
    
    if (payload.notes !== undefined) {
      targetSlot.notes = payload.notes;
      updatedFields.push("notes");
    }
    
    if (payload.clothing_item_ids !== undefined) {
      const closet = getWardrobeItems();
      targetSlot.items = payload.clothing_item_ids.map(id => {
        const fullItem = closet.find(c => c.id === id);
        if (fullItem) {
          return {
            id: fullItem.id,
            name: fullItem.name,
            category: fullItem.categories[0] || "tops",
            processed_image_url: formatImageUrl(fullItem.image)
          };
        }
        return { id, name: "Closet Item", category: "tops", processed_image_url: "/assets/curation_collage_feature.png" };
      });
      updatedFields.push("clothing_item_ids");
    }
    
    saveLocalCalendar(cachedCal);
    
    return {
      message: "Planned outfit schedule updated successfully.",
      planned_outfit_id: plannedOutfitId,
      updated_fields: updatedFields
    };
  }
};

/**
 * 5. POST /api/planner/auto-generate
 * AI Auto-Planner engine. Generates and plans ensembles across multiple days dynamically.
 */
export const apiAutoGeneratePlanner = async (payload) => {
  try {
    const data = await dedupeFetch(`${API_BASE}/api/planner/auto-generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: payload.user_id || "default_user",
        start_date: payload.start_date,
        days_count: payload.days_count || 3,
        agendas: payload.agendas || []
      })
    });
    return data;
  } catch (err) {
    console.warn("Backend AI auto-planner down, running localized offline styling simulation:", err);
    
    const cachedCal = loadLocalCalendar();
    const closet = getWardrobeItems();
    
    if (closet.length === 0) {
      throw new Error("Your digital closet is empty! Please upload garments first to enable AI planning.");
    }
    
    let autoScheduledCount = 0;
    const plannedDays = [];
    
    const getOfflineLook = (occasion) => {
      // Simple filters
      const tops = closet.filter(c => c.categories.includes("tops") || c.category === "tops");
      const bottoms = closet.filter(c => c.categories.includes("bottoms") || c.category === "bottoms");
      const outers = closet.filter(c => c.categories.includes("outerwear") || c.category === "outerwear");
      const footwear = closet.filter(c => c.categories.includes("footwear") || c.category === "footwear");
      
      const seedIndex = Math.floor(Math.random() * 100);
      const top = tops[seedIndex % (tops.length || 1)] || tops[0];
      const bottom = bottoms[(seedIndex + 1) % (bottoms.length || 1)] || bottoms[0];
      const outer = outers[(seedIndex + 2) % (outers.length || 1)] || outers[0];
      const shoe = footwear[(seedIndex + 3) % (footwear.length || 1)] || footwear[0];
      
      const items = [top, bottom, outer, shoe]
        .filter(Boolean)
        .map(item => ({
          id: item.id,
          name: item.name,
          category: item.categories[0] || item.category || "tops",
          processed_image_url: formatImageUrl(item.image)
        }));
        
      return {
        items,
        reasoning: `Seeding an organic ${occasion.toUpperCase()} coordination with optimal contrast layers, balancing the fabric density perfectly.`,
        score: 85 + (seedIndex % 11)
      };
    };
    
    (payload.agendas || []).forEach(agenda => {
      const dateStr = agenda.date;
      plannedDays.push(dateStr);
      
      if (!cachedCal[dateStr]) {
        cachedCal[dateStr] = {
          date: dateStr,
          day_of_week: new Date(dateStr + "T00:00:00").toLocaleString("en-US", { weekday: "long" }).toUpperCase(),
          planned_slots: []
        };
      }
      
      agenda.slots.forEach(slot => {
        // Remove existing identical slot to overwrite cleanly
        cachedCal[dateStr].planned_slots = cachedCal[dateStr].planned_slots.filter(
          s => s.time_slot.toLowerCase() !== slot.time_slot.toLowerCase()
        );
        
        const aiLook = getOfflineLook(slot.occasion || "casual");
        cachedCal[dateStr].planned_slots.push({
          planned_outfit_id: generateUUID(),
          time_slot: slot.time_slot,
          occasion: (slot.occasion || "CASUAL").toUpperCase(),
          outfit_source: "saved_outfit",
          outfit_id: generateUUID(),
          notes: aiLook.reasoning,
          vogue_score: aiLook.score,
          items: aiLook.items,
          wear_log: null
        });
        
        autoScheduledCount++;
      });
    });
    
    saveLocalCalendar(cachedCal);
    
    // Simulate short loader wait time
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    return {
      message: "AI Calendar Auto-Planning successfully completed.",
      auto_scheduled_count: autoScheduledCount,
      planned_days: plannedDays
    };
  }
};

/**
 * 6. POST /api/planner/log-photo
 * Uploads a physical wear snapshot and notes, linking it optionally to a planned slot.
 */
export const apiUploadWearLog = async (file, date, plannedOutfitId = null, notes = "") => {
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("date", date);
    if (plannedOutfitId) formData.append("planned_outfit_id", plannedOutfitId);
    if (notes) formData.append("notes", notes);
    
    const data = await dedupeFetch(`${API_BASE}/api/planner/log-photo`, {
      method: "POST",
      body: formData
    });
    return data;
  } catch (err) {
    console.warn("Backend wear log snapshot API down, saving snapshot locally in Base64:", err);
    
    // Convert physical File to Base64 dataURL for offline local storage persistence
    const base64Url = await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = () => resolve("/assets/fashion_portrait_gap.png");
      reader.readAsDataURL(file);
    });
    
    const cachedCal = loadLocalCalendar();
    const dateStr = date;
    const newLogId = generateUUID();
    
    const localWearLog = {
      log_id: newLogId,
      image_url: base64Url,
      notes: notes || "Offline fit snap log check.",
      logged_at: new Date().toISOString()
    };
    
    // Link directly to the specific calendar slot if given
    let linked = false;
    if (plannedOutfitId) {
      Object.keys(cachedCal).forEach(dStr => {
        const slot = cachedCal[dStr].planned_slots.find(s => s.planned_outfit_id === plannedOutfitId);
        if (slot) {
          slot.wear_log = localWearLog;
          linked = true;
        }
      });
    }
    
    // If not linked to a slot, we can save it at the day level or seed a stub slot
    if (!linked) {
      if (!cachedCal[dateStr]) {
        cachedCal[dateStr] = {
          date: dateStr,
          day_of_week: new Date(dateStr + "T00:00:00").toLocaleString("en-US", { weekday: "long" }).toUpperCase(),
          planned_slots: []
        };
      }
      // Seed a Wear Log check entry
      cachedCal[dateStr].planned_slots.push({
        planned_outfit_id: generateUUID(),
        time_slot: "Daily Reflection",
        occasion: "CASUAL",
        outfit_source: "custom_user",
        outfit_id: null,
        notes: "Real-life wear snapshot logged.",
        vogue_score: 85,
        items: [],
        wear_log: localWearLog
      });
    }
    
    saveLocalCalendar(cachedCal);
    
    return {
      message: "Outfit wear snapshot logged successfully",
      log_id: newLogId,
      date: dateStr,
      image_url: base64Url,
      notes: notes,
      planned_outfit_id: plannedOutfitId
    };
  }
};

/**
 * 7. DELETE /api/planner/log-photo/{log_id}
 * Deletes a previously uploaded snapshot wear log.
 */
export const apiDeleteWearLog = async (logId) => {
  try {
    const data = await dedupeFetch(`${API_BASE}/api/planner/log-photo/${logId}`, {
      method: "DELETE"
    });
    return data;
  } catch (err) {
    console.warn("Backend delete wear log API down, evicting local snapshot:", err);
    
    const cachedCal = loadLocalCalendar();
    let found = false;
    
    Object.keys(cachedCal).forEach(dateStr => {
      cachedCal[dateStr].planned_slots.forEach(slot => {
        if (slot.wear_log && slot.wear_log.log_id === logId) {
          slot.wear_log = null;
          found = true;
        }
      });
    });
    
    if (found) {
      saveLocalCalendar(cachedCal);
      return {
        message: "Logged wear snapshot deleted successfully.",
        log_id: logId
      };
    }
    
    throw new Error("Wear log snapshot not found.");
  }
};
