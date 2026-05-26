// Social & Curation Store - Vogue.AI
// Handles API requests for social profile, feed curation, recreation matching, explore, communities, and semantic search.
// Implements resilient localStorage fallbacks for offline-ready operations.

const API_BASE = "http://localhost:8000/v1/social";

// Helper checking if backend is active/available
const checkBackendOnline = async () => {
  try {
    const res = await fetch("http://localhost:8000/health", { signal: AbortSignal.timeout(1000) });
    return res.ok;
  } catch (e) {
    return false;
  }
};

// ── LOCAL STORAGE FALLBACK SEEDS ─────────────────────────────────────────────
const DEFAULT_PROFILES = {
  "social_curator": {
    id: "00000000-0000-0000-0000-000000000001",
    username: "social_curator",
    vanity_username: "Aesthetic_Curator",
    first_name: "Alex",
    last_name: "Sterling",
    bio: "Minimalist monochrome fits | Quiet luxury | NYC",
    avatar_url: "https://lh3.googleusercontent.com/aida-public/AB6AXuCUhrbSCCyvL4gMnA4wJKdCIy8rVXkUi-RbzyXY0huiYdfDG1hbrZTi-unXTQtHZr7f0ylpE97bhRPNcOAuBoGKXLZ9h6MkdQTX2Ta77wOdUoQSSmQB-gtnME4J5WbRKBfLHRHGbjQ9nvppXanviB6KFDGHhH3UASuuDBy4oIWLee_5z-H844_4Mt1y2nDji5MV2TT9xd2rZAt5yi9SC4sfotZz_y65OxC_DpSb0DD2ZGoAr5G5CWtbh_ouFF8GyRaY91qgXtX9DUof",
    verified_badge: true,
    favorite_brands: ["COS", "Zara", "Uniqlo", "Rick Owens"],
    wardrobe_visibility: "public",
    followers_count: 384,
    following_count: 192,
    posts_count: 4,
    style_personas: ["minimalist", "quiet_luxury"]
  },
  "quiet_luxury_edits": {
    id: "00000000-0000-0000-0000-000000000002",
    username: "quiet_luxury_edits",
    vanity_username: "QuietLuxuryEdits",
    first_name: "Elena",
    last_name: "Rostova",
    bio: "Neutral tailoring | Premium knitwear styling | London",
    avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=Elena",
    verified_badge: true,
    favorite_brands: ["COS", "Loro Piana", "Max Mara", "Brunello Cucinelli"],
    wardrobe_visibility: "public",
    followers_count: 1205,
    following_count: 430,
    posts_count: 3,
    style_personas: ["quiet_luxury", "minimalist"]
  },
  "tokyo_streetwear": {
    id: "00000000-0000-0000-0000-000000000003",
    username: "tokyo_streetwear",
    vanity_username: "TokyoStreetwear",
    first_name: "Kenji",
    last_name: "Sato",
    bio: "Oversized silhouettes | Techwear layering | Harajuku",
    avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=Kenji",
    verified_badge: false,
    favorite_brands: ["Rick Owens", "Nike", "Uniqlo", "Y-3"],
    wardrobe_visibility: "public",
    followers_count: 852,
    following_count: 220,
    posts_count: 2,
    style_personas: ["streetwear", "techwear"]
  }
};

const DEFAULT_POSTS = [
  {
    id: "post-1",
    user_id: "00000000-0000-0000-0000-000000000001",
    username: "social_curator",
    avatar_url: "https://lh3.googleusercontent.com/aida-public/AB6AXuCUhrbSCCyvL4gMnA4wJKdCIy8rVXkUi-RbzyXY0huiYdfDG1hbrZTi-unXTQtHZr7f0ylpE97bhRPNcOAuBoGKXLZ9h6MkdQTX2Ta77wOdUoQSSmQB-gtnME4J5WbRKBfLHRHGbjQ9nvppXanviB6KFDGHhH3UASuuDBy4oIWLee_5z-H844_4Mt1y2nDji5MV2TT9xd2rZAt5yi9SC4sfotZz_y65OxC_DpSb0DD2ZGoAr5G5CWtbh_ouFF8GyRaY91qgXtX9DUof",
    verified_badge: true,
    image_url: "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?auto=format&fit=crop&w=800&q=80",
    caption: "Minimalist grey wool tailoring layered over basic essential poplin shirt. Autumn morning layout.",
    weather_context: "Mild (15°C)",
    occasion_tag: "Work / Office",
    style_persona: "minimalist",
    community_id: null,
    created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
    likes_count: 42,
    comments_count: 2,
    saves_count: 18,
    is_liked_by_user: false,
    is_saved_by_user: false,
    tagged_items: [
      {
        id: "tag-1-1",
        post_id: "post-1",
        wardrobe_item_id: "shirt",
        x_coord: 50.0,
        y_coord: 40.0,
        wardrobe_item: {
          id: "shirt",
          name: "Essential White Shirt",
          textile: "100% Poplin Cotton",
          colorName: "Alabaster White",
          colorHex: "#F5F5F7",
          categories: ["tops"]
        }
      },
      {
        id: "tag-1-2",
        post_id: "post-1",
        wardrobe_item_id: "pants",
        x_coord: 52.0,
        y_coord: 75.0,
        wardrobe_item: {
          id: "pants",
          name: "Tapered Wool Trousers",
          textile: "Worsted Wool Blend",
          colorName: "Charcoal Grey",
          colorHex: "#3A3B3C",
          categories: ["bottoms"]
        }
      }
    ]
  },
  {
    id: "post-2",
    user_id: "00000000-0000-0000-0000-000000000002",
    username: "quiet_luxury_edits",
    avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=Elena",
    verified_badge: true,
    image_url: "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=800&q=80",
    caption: "Cashmere wrap trench coat paired with warm calfskin boots. Perfect tailoring for chilly London nights.",
    weather_context: "Cold (8°C)",
    occasion_tag: "Date Night",
    style_persona: "quiet_luxury",
    community_id: null,
    created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
    likes_count: 128,
    comments_count: 1,
    saves_count: 52,
    is_liked_by_user: true,
    is_saved_by_user: true,
    tagged_items: [
      {
        id: "tag-2-1",
        post_id: "post-2",
        wardrobe_item_id: "trench",
        x_coord: 50.0,
        y_coord: 45.0,
        wardrobe_item: {
          id: "trench",
          name: "Cashmere Wool Trench",
          textile: "100% Cashmere-Wool",
          colorName: "Espresso Camel",
          colorHex: "#C59B73",
          categories: ["outerwear"]
        }
      }
    ]
  }
];

const DEFAULT_COMMUNITIES = [
  {
    id: "comm-1",
    name: "Minimalist Uniform",
    slug: "minimalist-uniform",
    description: "Architectural shapes, neutral palettes, quiet luxury layering, and capsule closet capsule ideas.",
    cover_image_url: "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=800&q=80",
    rules: "1. Only neutral color tones.\n2. Focus on textile and drape.\n3. Respect fellow capsule creators.",
    creator_id: "00000000-0000-0000-0000-000000000001",
    members_count: 842,
    posts_count: 124,
    is_joined: true,
    created_at: new Date(Date.now() - 3600000 * 240).toISOString()
  },
  {
    id: "comm-2",
    name: "Streetwear Layering",
    slug: "streetwear-layering",
    description: "Oversized shapes, drop shoulders, cargo utilities, premium sneakers, and avant-garde drapes.",
    cover_image_url: "https://images.unsplash.com/photo-1516257984-b1b4d707412e?auto=format&fit=crop&w=800&q=80",
    rules: "1. Focus on silhouette and volume proportions.\n2. Respect authentic designers.\n3. Share styling tips.",
    creator_id: "00000000-0000-0000-0000-000000000003",
    members_count: 531,
    posts_count: 67,
    is_joined: false,
    created_at: new Date(Date.now() - 3600000 * 120).toISOString()
  }
];

const DEFAULT_COMMENTS = {
  "post-1": [
    {
      id: "comm-1",
      post_id: "post-1",
      user_id: "00000000-0000-0000-0000-000000000002",
      username: "quiet_luxury_edits",
      avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=Elena",
      content: "The worsted wool tailoring drapes beautifully!",
      created_at: new Date(Date.now() - 3600000 * 3.5).toISOString()
    },
    {
      id: "comm-2",
      post_id: "post-1",
      user_id: "00000000-0000-0000-0000-000000000003",
      username: "tokyo_streetwear",
      avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=Kenji",
      content: "Insanely clean layering. Tones are harmonized perfectly.",
      created_at: new Date(Date.now() - 3600000 * 2).toISOString()
    }
  ],
  "post-2": [
    {
      id: "comm-3",
      post_id: "post-2",
      user_id: "00000000-0000-0000-0000-000000000001",
      username: "social_curator",
      avatar_url: "https://lh3.googleusercontent.com/aida-public/AB6AXuCUhrbSCCyvL4gMnA4wJKdCIy8rVXkUi-RbzyXY0huiYdfDG1hbrZTi-unXTQtHZr7f0ylpE97bhRPNcOAuBoGKXLZ9h6MkdQTX2Ta77wOdUoQSSmQB-gtnME4J5WbRKBfLHRHGbjQ9nvppXanviB6KFDGHhH3UASuuDBy4oIWLee_5z-H844_4Mt1y2nDji5MV2TT9xd2rZAt5yi9SC4sfotZz_y65OxC_DpSb0DD2ZGoAr5G5CWtbh_ouFF8GyRaY91qgXtX9DUof",
      content: "Espresso camel looks incredible in cashmere. Truly elevated styling!",
      created_at: new Date(Date.now() - 3600000 * 20).toISOString()
    }
  ]
};

// Keys
const PROFILES_KEY = "vogue_social_profiles";
const POSTS_KEY = "vogue_social_posts";
const COMMUNITIES_KEY = "vogue_social_communities";
const COMMENTS_KEY = "vogue_social_comments";
const FOLLOWS_KEY = "vogue_social_follows";

// Initialize localStorage fallback arrays
const initStore = () => {
  if (!localStorage.getItem(PROFILES_KEY)) {
    localStorage.setItem(PROFILES_KEY, JSON.stringify(DEFAULT_PROFILES));
  }
  if (!localStorage.getItem(POSTS_KEY)) {
    localStorage.setItem(POSTS_KEY, JSON.stringify(DEFAULT_POSTS));
  }
  if (!localStorage.getItem(COMMUNITIES_KEY)) {
    localStorage.setItem(COMMUNITIES_KEY, JSON.stringify(DEFAULT_COMMUNITIES));
  }
  if (!localStorage.getItem(COMMENTS_KEY)) {
    localStorage.setItem(COMMENTS_KEY, JSON.stringify(DEFAULT_COMMENTS));
  }
  if (!localStorage.getItem(FOLLOWS_KEY)) {
    localStorage.setItem(FOLLOWS_KEY, JSON.stringify(["quiet_luxury_edits"]));
  }
};

initStore();

// ── API IMPLEMENTATIONS ──────────────────────────────────────────────────────

// Profile APIs
export const apiGetSocialProfile = async (username) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`${API_BASE}/profile/${username}`);
    if (!res.ok) throw new Error("Failed to fetch profile");
    return await res.json();
  } catch (err) {
    console.warn(`Profile API unavailable, using offline fallback for @${username}`, err);
    const localProfiles = JSON.parse(localStorage.getItem(PROFILES_KEY) || "{}");
    if (localProfiles[username]) {
      const following = JSON.parse(localStorage.getItem(FOLLOWS_KEY) || "[]");
      const isFollowing = following.includes(username);
      return {
        ...localProfiles[username],
        followers_count: localProfiles[username].followers_count + (isFollowing ? 1 : 0)
      };
    }
    return {
      id: "00000000-0000-0000-0000-user-fallback",
      username: username,
      vanity_username: username.toUpperCase(),
      bio: "Fashion enthusiast | Capsule styling lover",
      avatar_url: `https://api.dicebear.com/7.x/initials/svg?seed=${username}`,
      verified_badge: false,
      favorite_brands: ["Zara", "Uniqlo"],
      wardrobe_visibility: "public",
      followers_count: 42,
      following_count: 88,
      posts_count: 0,
      style_personas: ["minimalist"]
    };
  }
};

// Follow graph APIs
export const apiToggleFollow = async (userId, username, action) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`${API_BASE}/follow/${userId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action })
    });
    return await res.json();
  } catch (err) {
    console.warn("Follow POST unavailable, modifying local follows key:", err);
    const following = JSON.parse(localStorage.getItem(FOLLOWS_KEY) || "[]");
    let updated;
    if (action === "follow") {
      updated = [...new Set([...following, username])];
    } else {
      updated = following.filter(u => u !== username);
    }
    localStorage.setItem(FOLLOWS_KEY, JSON.stringify(updated));
    return { message: `Successfully ${action}ed user.` };
  }
};

export const getFollowingUsernames = () => {
  return JSON.parse(localStorage.getItem(FOLLOWS_KEY) || "[]");
};

// Outfit Post creation APIs
export const apiCreatePost = async (payload) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`${API_BASE}/posts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Post create failed");
    return await res.json();
  } catch (err) {
    console.warn("Create Post unavailable, saving locally:", err);
    const posts = JSON.parse(localStorage.getItem(POSTS_KEY) || "[]");
    const newId = "post-local-" + Math.random().toString(36).substring(2, 9);
    
    // Resolve tagged items from wardrobe items flat list
    const taggedHydrated = (payload.tagged_items || []).map(ti => {
      const wardrobeItems = JSON.parse(localStorage.getItem("vogue_wardrobe_items_flat") || "[]");
      const matched = wardrobeItems.find(item => item.id === ti.wardrobe_item_id);
      return {
        id: "tag-" + Math.random().toString(36).substring(2, 9),
        post_id: newId,
        wardrobe_item_id: ti.wardrobe_item_id,
        x_coord: ti.x_coord,
        y_coord: ti.y_coord,
        wardrobe_item: matched ? {
          id: matched.id,
          name: matched.name,
          textile: matched.textile,
          colorName: matched.colorName,
          colorHex: matched.colorHex,
          categories: matched.categories || ["tops"]
        } : {
          id: "mock-clothing-id",
          name: "Wardrobe Item",
          textile: "Cotton",
          colorName: "Alabaster White",
          colorHex: "#F5F5F7",
          categories: ["tops"]
        }
      };
    });

    const newPost = {
      id: newId,
      user_id: "00000000-0000-0000-0000-000000000001",
      username: "social_curator",
      avatar_url: "https://lh3.googleusercontent.com/aida-public/AB6AXuCUhrbSCCyvL4gMnA4wJKdCIy8rVXkUi-RbzyXY0huiYdfDG1hbrZTi-unXTQtHZr7f0ylpE97bhRPNcOAuBoGKXLZ9h6MkdQTX2Ta77wOdUoQSSmQB-gtnME4J5WbRKBfLHRHGbjQ9nvppXanviB6KFDGHhH3UASuuDBy4oIWLee_5z-H844_4Mt1y2nDji5MV2TT9xd2rZAt5yi9SC4sfotZz_y65OxC_DpSb0DD2ZGoAr5G5CWtbh_ouFF8GyRaY91qgXtX9DUof",
      verified_badge: true,
      image_url: payload.image_url,
      caption: payload.caption,
      weather_context: payload.weather_context || "Mild (16°C)",
      occasion_tag: payload.occasion_tag || "Everyday Casual",
      style_persona: payload.style_persona || "minimalist",
      community_id: payload.community_id || null,
      created_at: new Date().toISOString(),
      likes_count: 0,
      comments_count: 0,
      saves_count: 0,
      is_liked_by_user: false,
      is_saved_by_user: false,
      tagged_items: taggedHydrated
    };

    posts.unshift(newPost);
    localStorage.setItem(POSTS_KEY, JSON.stringify(posts));

    // If community_id is targeted, increment community posts count
    if (payload.community_id) {
      const comms = JSON.parse(localStorage.getItem(COMMUNITIES_KEY) || "[]");
      const idx = comms.findIndex(c => c.id === payload.community_id);
      if (idx !== -1) {
        comms[idx].posts_count += 1;
        localStorage.setItem(COMMUNITIES_KEY, JSON.stringify(comms));
      }
    }

    // Update posts count on profile
    const profiles = JSON.parse(localStorage.getItem(PROFILES_KEY) || "{}");
    if (profiles["social_curator"]) {
      profiles["social_curator"].posts_count += 1;
      localStorage.setItem(PROFILES_KEY, JSON.stringify(profiles));
    }

    return newPost;
  }
};

// Feed lists APIs
export const apiListFeed = async (feedType) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`${API_BASE}/feed/${feedType}`);
    if (!res.ok) throw new Error("Feed list error");
    return await res.json();
  } catch (err) {
    console.warn(`Feed list for ${feedType} unavailable, reading locally:`, err);
    const localPosts = JSON.parse(localStorage.getItem(POSTS_KEY) || "[]");
    
    if (feedType === "following") {
      const following = getFollowingUsernames();
      return localPosts.filter(p => p.username === "social_curator" || following.includes(p.username));
    } else if (feedType === "curated") {
      return localPosts.filter(p => p.style_persona === "minimalist" || p.style_persona === "quiet_luxury");
    }
    
    // trending: sort by likes + saves
    return [...localPosts].sort((a, b) => (b.likes_count + b.saves_count) - (a.likes_count + a.saves_count));
  }
};

// Likes & Saves interaction APIs
export const apiToggleLike = async (postId) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`${API_BASE}/posts/${postId}/like`, { method: "POST" });
    return await res.json();
  } catch (err) {
    console.warn("Like API failed, updating locally:", err);
    const posts = JSON.parse(localStorage.getItem(POSTS_KEY) || "[]");
    const idx = posts.findIndex(p => p.id === postId);
    if (idx !== -1) {
      const state = posts[idx].is_liked_by_user;
      posts[idx].is_liked_by_user = !state;
      posts[idx].likes_count += state ? -1 : 1;
      localStorage.setItem(POSTS_KEY, JSON.stringify(posts));
      return { liked: !state };
    }
    return { liked: false };
  }
};

export const apiToggleSave = async (postId) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`${API_BASE}/posts/${postId}/save`, { method: "POST" });
    return await res.json();
  } catch (err) {
    console.warn("Save API failed, updating locally:", err);
    const posts = JSON.parse(localStorage.getItem(POSTS_KEY) || "[]");
    const idx = posts.findIndex(p => p.id === postId);
    if (idx !== -1) {
      const state = posts[idx].is_saved_by_user;
      posts[idx].is_saved_by_user = !state;
      posts[idx].saves_count += state ? -1 : 1;
      localStorage.setItem(POSTS_KEY, JSON.stringify(posts));
      return { saved: !state };
    }
    return { saved: false };
  }
};

// Threaded Comments APIs
export const apiGetComments = async (postId) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`${API_BASE}/posts/${postId}/comments`);
    return await res.json();
  } catch (err) {
    console.warn("Comments GET failed, pulling locally:", err);
    const localComments = JSON.parse(localStorage.getItem(COMMENTS_KEY) || "{}");
    return localComments[postId] || [];
  }
};

export const apiAddComment = async (postId, content, parentCommentId = null) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`${API_BASE}/posts/${postId}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, parent_comment_id: parentCommentId })
    });
    return await res.json();
  } catch (err) {
    console.warn("Comments POST failed, writing locally:", err);
    const localComments = JSON.parse(localStorage.getItem(COMMENTS_KEY) || "{}");
    if (!localComments[postId]) localComments[postId] = [];

    const newComment = {
      id: "comm-local-" + Math.random().toString(36).substring(2, 9),
      post_id: postId,
      user_id: "00000000-0000-0000-0000-000000000001",
      username: "social_curator",
      avatar_url: "https://lh3.googleusercontent.com/aida-public/AB6AXuCUhrbSCCyvL4gMnA4wJKdCIy8rVXkUi-RbzyXY0huiYdfDG1hbrZTi-unXTQtHZr7f0ylpE97bhRPNcOAuBoGKXLZ9h6MkdQTX2Ta77wOdUoQSSmQB-gtnME4J5WbRKBfLHRHGbjQ9nvppXanviB6KFDGHhH3UASuuDBy4oIWLee_5z-H844_4Mt1y2nDji5MV2TT9xd2rZAt5yi9SC4sfotZz_y65OxC_DpSb0DD2ZGoAr5G5CWtbh_ouFF8GyRaY91qgXtX9DUof",
      content: content,
      created_at: new Date().toISOString(),
      parent_comment_id: parentCommentId
    };

    localComments[postId].push(newComment);
    localStorage.setItem(COMMENTS_KEY, JSON.stringify(localComments));

    // Update posts comment count
    const posts = JSON.parse(localStorage.getItem(POSTS_KEY) || "[]");
    const idx = posts.findIndex(p => p.id === postId);
    if (idx !== -1) {
      posts[idx].comments_count += 1;
      localStorage.setItem(POSTS_KEY, JSON.stringify(posts));
    }

    return newComment;
  }
};

// "Recreate Outfit" Similarity Vector Engine APIs
export const apiGetRecreateStats = async (postId) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`${API_BASE}/posts/${postId}/recreate`);
    if (!res.ok) throw new Error("Recreation failed");
    return await res.json();
  } catch (err) {
    console.warn("Recreation GET failed, executing client-side simulation fallback:", err);
    const posts = JSON.parse(localStorage.getItem(POSTS_KEY) || "[]");
    const post = posts.find(p => p.id === postId);
    if (!post) throw new Error("Post not found");

    const wardrobeItems = JSON.parse(localStorage.getItem("vogue_wardrobe_items_flat") || "[]");
    
    let totalSlots = 0;
    let totalSim = 0.0;

    const slots = (post.tagged_items || []).map(ti => {
      totalSlots += 1;
      const cat = ti.wardrobe_item.categories[0];
      const candidates = wardrobeItems.filter(item => (item.categories || []).includes(cat));

      let bestMatch = null;
      let bestScore = 0.0;
      let statusTag = "Missing";

      candidates.forEach(cand => {
        let score = 0.45;
        if (cand.id === ti.wardrobe_item_id) {
          score = 1.0;
        } else {
          if (cand.colorName === ti.wardrobe_item.colorName) score += 0.25;
          if (cand.textile === ti.wardrobe_item.textile) score += 0.15;
          score += Math.random() * 0.10; // Jitter
        }
        score = Math.min(1.0, score);
        if (score > bestScore) {
          bestScore = score;
          bestMatch = cand;
        }
      });

      if (bestScore >= 0.82) {
        statusTag = "Perfect Match";
      } else if (bestScore >= 0.65) {
        statusTag = "Substitute";
      } else {
        statusTag = "Missing";
        bestMatch = null;
        bestScore = 0.0;
      }

      totalSim += bestScore;

      return {
        role: cat,
        tagged_item_id: ti.wardrobe_item_id,
        tagged_item_name: ti.wardrobe_item.name,
        matched_item: bestMatch,
        similarity_score: Number(bestScore.toFixed(3)),
        match_status: statusTag,
        buy_link: statusTag === "Missing" ? `https://www.cos.com/en_usd/search.html?q=${ti.wardrobe_item.name.replace(" ", "+")}` : null
      };
    });

    const overallMatch = totalSlots > 0 ? Number(((totalSim / totalSlots) * 100).toFixed(1)) : 0.0;

    // Save to offline history list
    try {
      const history = JSON.parse(localStorage.getItem("vogue_social_recreate_history") || "[]");
      // Prevent duplicating entries for same post recreation in local cache
      const updatedHistory = history.filter(h => h.post_id !== postId);
      updatedHistory.unshift({
        id: "rec-local-" + Math.random().toString(36).substring(2, 9),
        post_id: postId,
        overall_match_percentage: overallMatch,
        details: slots,
        created_at: new Date().toISOString(),
        post_username: post.username,
        post_image_url: post.image_url,
        post_caption: post.caption
      });
      localStorage.setItem("vogue_social_recreate_history", JSON.stringify(updatedHistory));
    } catch (e) {
      console.warn("Failed to write recreation log to offline history cache", e);
    }

    return {
      post_id: postId,
      overall_match_percentage: overallMatch,
      slots: slots,
      style_persona: post.style_persona,
      weather_context: post.weather_context
    };
  }
};

// Explore Page Discover APIs
export const apiGetExploreData = async () => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`${API_BASE}/explore`);
    if (!res.ok) throw new Error("Explore failed");
    return await res.json();
  } catch (err) {
    console.warn("Explore GET failed, returning local aggregates fallback:", err);
    
    // Trending Posts: Sort local posts by engagement
    const posts = JSON.parse(localStorage.getItem(POSTS_KEY) || "[]");
    const trendingPosts = [...posts].sort((a, b) => (b.likes_count + b.saves_count) - (a.likes_count + a.saves_count)).slice(0, 3);
    
    // Trending Personas
    const trendingPersonas = [
      { name: "minimalist", post_count: 5, popular_image_url: "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?auto=format&fit=crop&w=800&q=80" },
      { name: "quiet_luxury", post_count: 3, popular_image_url: "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=800&q=80" },
      { name: "streetwear", post_count: 2, popular_image_url: "https://images.unsplash.com/photo-1516257984-b1b4d707412e?auto=format&fit=crop&w=800&q=80" }
    ];

    // Popular Creators
    const profiles = JSON.parse(localStorage.getItem(PROFILES_KEY) || "{}");
    const popularCreators = Object.values(profiles).map(p => ({
      id: p.id,
      username: p.username,
      vanity_username: p.vanity_username,
      avatar_url: p.avatar_url,
      verified_badge: p.verified_badge,
      style_personas: p.style_personas,
      followers_count: p.followers_count,
      is_followed_by_user: getFollowingUsernames().includes(p.username)
    })).sort((a, b) => b.followers_count - a.followers_count);

    // Trending Occasions
    const trendingOccasions = [
      { name: "Work / Office", post_count: 3 },
      { name: "Date Night", post_count: 2 },
      { name: "Casual Outing", post_count: 1 }
    ];

    return {
      trending_posts: trendingPosts,
      trending_personas: trendingPersonas,
      popular_creators: popularCreators,
      trending_occasions: trendingOccasions
    };
  }
};

// Communities APIs
export const apiCreateCommunity = async (payload) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch("http://localhost:8000/v1/social/communities", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Community create failed");
    return await res.json();
  } catch (err) {
    console.warn("Create Community failed, saving locally:", err);
    const comms = JSON.parse(localStorage.getItem(COMMUNITIES_KEY) || "[]");
    const slug = payload.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
    
    const newComm = {
      id: "comm-local-" + Math.random().toString(36).substring(2, 9),
      name: payload.name,
      slug: slug,
      description: payload.description,
      cover_image_url: payload.cover_image_url || "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=800&q=80",
      rules: payload.rules,
      creator_id: "00000000-0000-0000-0000-000000000001",
      members_count: 1,
      posts_count: 0,
      is_joined: true,
      created_at: new Date().toISOString()
    };

    comms.push(newComm);
    localStorage.setItem(COMMUNITIES_KEY, JSON.stringify(comms));
    return newComm;
  }
};

export const apiListCommunities = async (q = "") => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const url = q ? `http://localhost:8000/v1/social/communities?q=${q}` : "http://localhost:8000/v1/social/communities";
    const res = await fetch(url);
    return await res.json();
  } catch (err) {
    console.warn("List Communities failed, pulling locally:", err);
    const comms = JSON.parse(localStorage.getItem(COMMUNITIES_KEY) || "[]");
    if (q) {
      const term = q.toLowerCase();
      return comms.filter(c => c.name.toLowerCase().includes(term) || c.description.toLowerCase().includes(term));
    }
    return comms;
  }
};

export const apiGetMyCommunities = async () => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch("http://localhost:8000/v1/social/communities/my");
    return await res.json();
  } catch (err) {
    console.warn("Get joined communities failed, loading locally:", err);
    const comms = JSON.parse(localStorage.getItem(COMMUNITIES_KEY) || "[]");
    return comms.filter(c => c.is_joined);
  }
};

export const apiGetCommunityDetails = async (slug) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`http://localhost:8000/v1/social/communities/${slug}`);
    if (!res.ok) throw new Error("Failed to fetch community");
    return await res.json();
  } catch (err) {
    console.warn(`Get community slug ${slug} failed, fetching locally:`, err);
    const comms = JSON.parse(localStorage.getItem(COMMUNITIES_KEY) || "[]");
    const matched = comms.find(c => c.slug === slug);
    if (!matched) throw new Error("Community not found locally");
    return matched;
  }
};

export const apiToggleCommunityMembership = async (communityId, isJoined) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const action = isJoined ? "leave" : "join";
    const res = await fetch(`http://localhost:8000/v1/social/communities/${communityId}/${action}`, { method: "POST" });
    return await res.json();
  } catch (err) {
    console.warn("Toggle community membership failed, writing locally:", err);
    const comms = JSON.parse(localStorage.getItem(COMMUNITIES_KEY) || "[]");
    const idx = comms.findIndex(c => c.id === communityId);
    if (idx !== -1) {
      const nextState = !isJoined;
      comms[idx].is_joined = nextState;
      comms[idx].members_count += nextState ? 1 : -1;
      localStorage.setItem(COMMUNITIES_KEY, JSON.stringify(comms));
      return { message: `Successfully ${nextState ? 'joined' : 'left'} community.` };
    }
    return { message: "Error" };
  }
};

export const apiListCommunityPosts = async (communityId) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`http://localhost:8000/v1/social/communities/${communityId}/posts`);
    return await res.json();
  } catch (err) {
    console.warn(`List community posts failed for ${communityId}, filtering locally:`, err);
    const posts = JSON.parse(localStorage.getItem(POSTS_KEY) || "[]");
    return posts.filter(p => p.community_id === communityId);
  }
};

export const apiListCommunityMembers = async (communityId) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`http://localhost:8000/v1/social/communities/${communityId}/members`);
    return await res.json();
  } catch (err) {
    console.warn("List community members failed, returning local stub:", err);
    return [
      { user_id: "00000000-0000-0000-0000-000000000001", username: "social_curator", avatar_url: "https://lh3.googleusercontent.com/aida-public/AB6AXuCUhrbSCCyvL4gMnA4wJKdCIy8rVXkUi-RbzyXY0huiYdfDG1hbrZTi-unXTQtHZr7f0ylpE97bhRPNcOAuBoGKXLZ9h6MkdQTX2Ta77wOdUoQSSmQB-gtnME4J5WbRKBfLHRHGbjQ9nvppXanviB6KFDGHhH3UASuuDBy4oIWLee_5z-H844_4Mt1y2nDji5MV2TT9xd2rZAt5yi9SC4sfotZz_y65OxC_DpSb0DD2ZGoAr5G5CWtbh_ouFF8GyRaY91qgXtX9DUof", role: "admin", joined_at: new Date(Date.now() - 3600000 * 240).toISOString() },
      { user_id: "00000000-0000-0000-0000-000000000002", username: "quiet_luxury_edits", avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=Elena", role: "member", joined_at: new Date(Date.now() - 3600000 * 120).toISOString() }
    ];
  }
};

// Semantic Fashion Search APIs
export const apiSemanticFashionSearch = async (q) => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(q)}`);
    return await res.json();
  } catch (err) {
    console.warn(`Semantic search for "${q}" failed, running local text fallback:`, err);
    const posts = JSON.parse(localStorage.getItem(POSTS_KEY) || "[]");
    const term = q.toLowerCase();
    
    // Local keyword fallback: Match caption, style, or occasion
    return posts.filter(p => 
      (p.caption && p.caption.toLowerCase().includes(term)) ||
      (p.style_persona && p.style_persona.toLowerCase().includes(term)) ||
      (p.occasion_tag && p.occasion_tag.toLowerCase().includes(term))
    );
  }
};

export const apiGetRecreateHistory = async () => {
  try {
    const isOnline = await checkBackendOnline();
    if (!isOnline) throw new Error("Offline");
    const res = await fetch("http://localhost:8000/v1/social/recreate/history");
    return await res.json();
  } catch (err) {
    console.warn("Recreation history GET failed, pulling locally:", err);
    return JSON.parse(localStorage.getItem("vogue_social_recreate_history") || "[]");
  }
};
