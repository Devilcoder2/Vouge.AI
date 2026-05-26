import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import SocialLayout from "../components/layout/SocialLayout";
import {
  apiGetExploreData, apiToggleLike, apiToggleSave, apiGetComments, apiAddComment, apiToggleFollow, getFollowingUsernames, apiListFeed
} from "../utils/socialStore";

export const Explore = () => {
  const navigate = useNavigate();

  // Search & Discover States
  const [searchQuery, setSearchQuery] = useState("");
  const [exploreData, setExploreData] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [followingList, setFollowingList] = useState([]);

  // Comment Drawer States
  const [activeCommentPost, setActiveCommentPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [newCommentText, setNewCommentText] = useState("");
  const [activeTagPopup, setActiveTagPopup] = useState(null);

  const loadExploreData = async () => {
    setLoading(true);
    try {
      const data = await apiGetExploreData();
      setExploreData(data);

      const following = getFollowingUsernames();
      setFollowingList(following);

      // Load curated/trending posts for the random feeds grid
      const trendingPosts = await apiListFeed("trending");
      
      // Filter out curators that represent the active user to keep it as random new creators
      const randomFeed = trendingPosts.filter(p => p.username !== "social_curator");
      setPosts(randomFeed);
    } catch (e) {
      console.error("Error loading explore data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExploreData();
  }, []);

  // Optimistic Follow Toggling
  const handleFollowToggle = async (post) => {
    const isCurrentlyFollowing = followingList.includes(post.username);
    const action = isCurrentlyFollowing ? "unfollow" : "follow";
    
    const nextFollowingList = isCurrentlyFollowing
      ? followingList.filter(u => u !== post.username)
      : [...followingList, post.username];
    setFollowingList(nextFollowingList);

    try {
      await apiToggleFollow(post.user_id, post.username, action);
    } catch (e) {
      console.error("Error toggling follow:", e);
    }
  };

  // Optimistic Follow for Search results list
  const handleCreatorFollowToggle = async (e, creator) => {
    e.stopPropagation();
    const isCurrentlyFollowing = followingList.includes(creator.username);
    const action = isCurrentlyFollowing ? "unfollow" : "follow";

    const nextFollowingList = isCurrentlyFollowing
      ? followingList.filter(u => u !== creator.username)
      : [...followingList, creator.username];
    setFollowingList(nextFollowingList);

    try {
      await apiToggleFollow(creator.id, creator.username, action);
    } catch (e) {
      console.error("Error toggling follow on search result:", e);
    }
  };

  // Optimistic Likes Toggling
  const handleLike = async (postId) => {
    setPosts(prev => prev.map(p => {
      if (p.id === postId) {
        const nextLiked = !p.is_liked_by_user;
        return {
          ...p,
          is_liked_by_user: nextLiked,
          likes_count: p.likes_count + (nextLiked ? 1 : -1)
        };
      }
      return p;
    }));

    try {
      await apiToggleLike(postId);
    } catch (e) {
      console.error("Error toggling like:", e);
    }
  };

  // Optimistic Bookmarks Toggling (No bookmark counts shown)
  const handleSave = async (postId) => {
    setPosts(prev => prev.map(p => {
      if (p.id === postId) {
        return {
          ...p,
          is_saved_by_user: !p.is_saved_by_user
        };
      }
      return p;
    }));

    try {
      await apiToggleSave(postId);
    } catch (e) {
      console.error("Error toggling save:", e);
    }
  };

  // Comments Actions (with Array validation guard to prevent black screen crashes)
  const openComments = async (post) => {
    setActiveCommentPost(post);
    setComments([]);
    try {
      const list = await apiGetComments(post.id);
      setComments(Array.isArray(list) ? list : []);
    } catch (e) {
      console.error("Error loading comments:", e);
      setComments([]);
    }
  };

  const submitComment = async (e) => {
    e.preventDefault();
    if (!newCommentText.trim() || !activeCommentPost) return;
    try {
      const added = await apiAddComment(activeCommentPost.id, newCommentText);
      setComments(prev => [...(Array.isArray(prev) ? prev : []), added]);
      setNewCommentText("");
      
      setPosts(prev => prev.map(p => {
        if (p.id === activeCommentPost.id) {
          return { ...p, comments_count: p.comments_count + 1 };
        }
        return p;
      }));
    } catch (e) {
      console.error("Error submitting comment:", e);
    }
  };

  // Simple username or name search matching on seed popular creators
  const getFilteredCreators = () => {
    if (!searchQuery.trim() || !exploreData?.popular_creators) return [];
    const term = searchQuery.toLowerCase();
    return exploreData.popular_creators.filter(
      c => c.username.toLowerCase().includes(term) || 
           (c.vanity_username && c.vanity_username.toLowerCase().includes(term))
    );
  };

  const searchedCreators = getFilteredCreators();

  return (
    <SocialLayout title="Explore Trends">
      <div className="w-full relative pb-20 select-text">
        {/* Title Header */}
        <div className="mb-6 select-none">
          <h2 className="font-display text-2xl italic luxury-text-gradient mb-1">Explore Trends</h2>
          <p className="text-[7px] uppercase tracking-[0.2em] text-on-surface-variant/40 font-semibold">
            Search creators and discover random outfit feeds
          </p>
        </div>

        {/* 2) Top Search Bar (Simple username / name search, no filters) */}
        <section className="glass rounded-2xl border border-white/[0.08] p-4 shadow-2xl mb-8 select-none">
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/40 text-lg">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search stylists by name or username (e.g. Elena, tokyo_streetwear)..."
              className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-10 py-3 text-xs text-white placeholder-on-surface-variant/40 focus:outline-none focus:border-white/20 transition-all font-light"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant/50 text-base hover:text-white cursor-pointer"
              >
                close
              </button>
            )}
          </div>
        </section>

        {/* Search Results list layout */}
        {searchQuery.trim() !== "" && (
          <section className="mb-8 select-none">
            <h3 className="font-display text-sm italic text-white mb-4">
              Stylists Found ({searchedCreators.length})
            </h3>
            
            {searchedCreators.length === 0 ? (
              <div className="text-center py-10 px-6 glass rounded-2xl border border-white/5">
                <span className="material-symbols-outlined text-3xl text-on-surface-variant/30 mb-2">
                  person_off
                </span>
                <p className="font-body-md text-xs text-on-surface-variant/50">
                  No stylists match "{searchQuery}"
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-xl mx-auto">
                {searchedCreators.map(creator => {
                  const isFollowing = followingList.includes(creator.username);
                  return (
                    <div
                      key={creator.id}
                      onClick={() => navigate(`/app/social/profile/${creator.username}`)}
                      className="glass rounded-xl border border-white/5 p-4 flex items-center justify-between gap-3 hover:border-white/15 transition-all cursor-pointer shadow-md"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-10 h-10 rounded-full overflow-hidden border border-white/10 shrink-0">
                          <img src={creator.avatar_url} alt={creator.username} className="w-full h-full object-cover" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className="font-display italic text-sm text-white truncate">
                              {creator.vanity_username || creator.username}
                            </span>
                            {creator.verified_badge && (
                              <span className="material-symbols-outlined text-[12px] text-tertiary font-bold" style={{ fontVariationSettings: "'FILL' 1" }}>
                                verified
                              </span>
                            )}
                          </div>
                          <span className="text-[9px] text-tertiary uppercase tracking-widest font-semibold block">
                            @{creator.username}
                          </span>
                        </div>
                      </div>

                      {creator.username !== "social_curator" && (
                        <button
                          onClick={(e) => handleCreatorFollowToggle(e, creator)}
                          className={`px-4 py-1.5 rounded-full font-label-sm text-[8px] uppercase tracking-widest font-bold transition-all cursor-pointer ${
                            isFollowing
                              ? "bg-white/10 text-white border border-white/10 hover:bg-error/10 hover:border-error/20 hover:text-error"
                              : "bg-white text-background hover:bg-tertiary hover:text-on-tertiary"
                          }`}
                        >
                          {isFollowing ? "Following" : "Follow"}
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        )}

        {/* Explore Feed of Random People */}
        {searchQuery.trim() === "" && (
          <section className="flex flex-col gap-8 max-w-xl mx-auto w-full">
            <h3 className="font-display text-base italic text-white select-none">Discover New Styles</h3>
            
            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <span className="material-symbols-outlined text-4xl text-tertiary animate-spin mb-4">
                  auto_awesome
                </span>
                <p className="font-body-md text-xs text-on-surface-variant/60 tracking-wider">Syncing style network...</p>
              </div>
            ) : posts.length === 0 ? (
              <div className="text-center py-10 opacity-50 select-none">
                <p className="font-body-md text-xs tracking-wider">No posts available to explore.</p>
              </div>
            ) : (
              posts.map(post => {
                const isFollowing = followingList.includes(post.username);
                return (
                  <div 
                    key={post.id}
                    className="glass rounded-2xl border border-white/[0.08] overflow-hidden flex flex-col shadow-2xl animate-fade-in hover:border-white/15 transition-all duration-500"
                  >
                    {/* Post Creator Header */}
                    <div className="p-4 flex items-center justify-between border-b border-white/5 select-none">
                      <div className="flex items-center gap-3">
                        <div 
                          onClick={() => navigate(`/app/social/profile/${post.username}`)}
                          className="w-9 h-9 rounded-full overflow-hidden border border-white/10 hover:scale-105 active:scale-95 transition-transform cursor-pointer"
                        >
                          <img src={post.avatar_url} alt={post.username} className="w-full h-full object-cover" />
                        </div>
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span 
                              onClick={() => navigate(`/app/social/profile/${post.username}`)}
                              className="font-display text-sm text-white italic hover:underline cursor-pointer"
                            >
                              @{post.username}
                            </span>
                            {post.verified_badge && (
                              <span className="material-symbols-outlined text-[13px] text-tertiary font-bold" style={{ fontVariationSettings: "'FILL' 1" }}>
                                verified
                              </span>
                            )}
                          </div>
                          <span className="text-[8px] text-on-surface-variant/40 tracking-wider font-semibold block uppercase">
                            {new Date(post.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                          </span>
                        </div>
                      </div>

                      {post.username !== "social_curator" && (
                        <button
                          onClick={() => handleFollowToggle(post)}
                          className={`px-4 py-1.5 rounded-full font-label-sm text-[8px] uppercase tracking-widest font-bold transition-all duration-300 cursor-pointer ${
                            isFollowing 
                              ? "bg-white/10 text-white border border-white/10 hover:bg-error/10 hover:border-error/20 hover:text-error" 
                              : "bg-white text-background hover:bg-tertiary hover:text-on-tertiary"
                          }`}
                        >
                          {isFollowing ? "Following" : "Follow"}
                        </button>
                      )}
                    </div>

                    {/* Outfit Photo with Hotspots */}
                    <div className="relative aspect-[4/5] bg-black/40 border-b border-white/5 flex items-center justify-center overflow-hidden">
                      <img 
                        src={post.image_url} 
                        alt="Outfit Post" 
                        className="w-full h-full object-cover select-none"
                      />

                      {/* Hotspots */}
                      {post.tagged_items && post.tagged_items.map(ti => {
                        const isPopupActive = activeTagPopup?.postId === post.id && activeTagPopup?.tagId === ti.id;
                        return (
                          <div
                            key={ti.id}
                            style={{ left: `${ti.x_coord}%`, top: `${ti.y_coord}%` }}
                            className="absolute -translate-x-1/2 -translate-y-1/2 z-20 group animate-fade-in"
                          >
                            <div 
                              onClick={() => {
                                if (isPopupActive) setActiveTagPopup(null);
                                else setActiveTagPopup({ postId: post.id, tagId: ti.id });
                              }}
                              className="w-6 h-6 bg-white/20 backdrop-blur-md rounded-full border-2 border-white flex items-center justify-center shadow-2xl cursor-pointer hover:scale-115 active:scale-95 transition-all animate-pulse"
                            >
                              <div className="w-2.5 h-2.5 bg-white rounded-full"></div>
                            </div>

                            {/* Floating Hotspot Popup */}
                            {isPopupActive && ti.wardrobe_item && (
                              <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-44 p-3 glass-heavy border border-white/15 rounded-xl shadow-2xl animate-scale-up z-30 select-none">
                                <span className="font-label-sm text-[7px] text-tertiary uppercase tracking-widest font-bold block mb-0.5">
                                  {ti.wardrobe_item.categories[0]}
                                </span>
                                <h5 className="font-display text-[11px] text-white italic truncate mb-1">
                                  {ti.wardrobe_item.name}
                                </h5>
                                <p className="font-body-md text-[9px] text-on-surface-variant/70 mb-2 truncate">
                                  {ti.wardrobe_item.textile}
                                </p>
                                <div className="flex items-center gap-1.5 mb-2.5">
                                  <div 
                                    style={{ backgroundColor: ti.wardrobe_item.colorHex }}
                                    className="w-2.5 h-2.5 rounded-full border border-white/20"
                                  ></div>
                                  <span className="text-[8px] text-on-surface-variant/80 truncate uppercase tracking-wider font-semibold">
                                    {ti.wardrobe_item.colorName}
                                  </span>
                                </div>
                                <button
                                  onClick={() => navigate(`/app/inventory/${ti.wardrobe_item.categories[0]}`)}
                                  className="w-full py-1 bg-white text-background font-label-sm text-[7px] uppercase tracking-widest rounded font-bold hover:bg-tertiary hover:text-on-tertiary transition-all"
                                >
                                  Explore Closet
                                </button>
                              </div>
                            )}
                          </div>
                        );
                      })}

                      {/* Context Badges */}
                      <div className="absolute bottom-4 left-4 z-20 flex gap-2 select-none">
                        {post.occasion_tag && (
                          <div className="bg-[#1A1A1A]/75 backdrop-blur-xl border border-white/10 px-2.5 py-1 rounded-full flex items-center gap-1">
                            <span className="material-symbols-outlined text-[11px] text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
                              event
                            </span>
                            <span className="font-label-sm text-[8px] text-on-surface uppercase tracking-wider font-semibold">
                              {post.occasion_tag}
                            </span>
                          </div>
                        )}
                        {post.weather_context && (
                          <div className="bg-[#1A1A1A]/75 backdrop-blur-xl border border-white/10 px-2.5 py-1 rounded-full flex items-center gap-1">
                            <span className="material-symbols-outlined text-[11px] text-tertiary" style={{ fontVariationSettings: "'FILL' 1" }}>
                              wb_sunny
                            </span>
                            <span className="font-label-sm text-[8px] text-on-surface uppercase tracking-wider font-semibold">
                              {post.weather_context}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Caption & Interactions */}
                    <div className="p-4 flex flex-col justify-between flex-1 select-text">
                      <p className="font-body-md text-xs text-on-surface-variant/90 leading-relaxed font-light mb-4">
                        <span className="font-display italic text-white mr-2">@{post.username}</span>
                        {post.caption}
                      </p>

                      <div className="flex justify-between items-center border-t border-white/5 pt-4 mt-auto select-none">
                        <div className="flex gap-5">
                          {/* Like */}
                          <button onClick={() => handleLike(post.id)} className="flex items-center gap-1.5 group cursor-pointer">
                            <span 
                              className={`material-symbols-outlined text-lg transition-transform group-active:scale-120 ${
                                post.is_liked_by_user ? "text-tertiary" : "text-primary hover:text-tertiary"
                              }`}
                              style={{ fontVariationSettings: post.is_liked_by_user ? "'FILL' 1" : "'FILL' 0" }}
                            >
                              favorite
                            </span>
                            <span className="text-[10px] text-on-surface-variant/60 font-semibold">{post.likes_count}</span>
                          </button>

                          {/* Comment */}
                          <button onClick={() => openComments(post)} className="flex items-center gap-1.5 group cursor-pointer">
                            <span className="material-symbols-outlined text-lg text-primary group-hover:text-white">
                              chat_bubble
                            </span>
                            <span className="text-[10px] text-on-surface-variant/60 font-semibold">{post.comments_count}</span>
                          </button>

                          {/* Saves */}
                          <button onClick={() => handleSave(post.id)} className="flex items-center gap-1.5 group cursor-pointer">
                            <span 
                              className={`material-symbols-outlined text-lg transition-transform group-active:scale-120 ${
                                post.is_saved_by_user ? "text-primary" : "text-primary hover:text-white"
                              }`}
                              style={{ fontVariationSettings: post.is_saved_by_user ? "'FILL' 1" : "'FILL' 0" }}
                            >
                              bookmark
                            </span>
                          </button>
                        </div>

                        {/* Recreate Fit action */}
                        <button
                          onClick={() => navigate(`/app/social/recreate/${post.id}`)}
                          className="flex items-center gap-1.5 px-4 py-2 bg-white/15 hover:bg-white text-white hover:text-background font-label-sm text-[8px] uppercase tracking-widest rounded-lg font-bold transition-all active:scale-[0.96] cursor-pointer shadow-md border border-white/5"
                        >
                          <span className="material-symbols-outlined text-xs animate-pulse">auto_awesome</span>
                          Recreate Fit
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </section>
        )}
      </div>

      {/* ==================== COMMENTS SLIDE-UP DRAWER (Safe rendering guards) ==================== */}
      {activeCommentPost && (
        <div className="fixed inset-0 z-[70] bg-background/80 backdrop-blur-sm flex justify-center items-end md:items-center p-0 md:p-4 animate-fade-in">
          <div className="absolute inset-0 cursor-pointer" onClick={() => setActiveCommentPost(null)}></div>
          <div className="relative w-full md:max-w-xl bg-surface border border-white/10 rounded-t-2xl md:rounded-2xl flex flex-col h-[75vh] md:h-[550px] shadow-2xl animate-slide-up z-50 overflow-hidden">
            
            <div className="p-4 border-b border-white/5 flex justify-between items-center select-none">
              <div>
                <h3 className="font-display text-base italic text-white">Comment Threads</h3>
                <p className="text-[7px] text-on-surface-variant/40 uppercase tracking-[0.2em] font-semibold">
                  Outfit checks and style analysis
                </p>
              </div>
              <button 
                onClick={() => setActiveCommentPost(null)}
                className="w-7 h-7 rounded-full bg-white/5 border border-white/5 flex items-center justify-center text-primary hover:bg-white/10 transition-all cursor-pointer"
              >
                <span className="material-symbols-outlined text-sm">close</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 select-text">
              {Array.isArray(comments) && comments.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center py-10 opacity-40">
                  <span className="material-symbols-outlined text-3xl mb-2">forum</span>
                  <p className="font-body-md text-xs tracking-wider">No comments yet. Drop style thoughts below!</p>
                </div>
              ) : (
                Array.isArray(comments) && comments.map(c => (
                  <div key={c.id} className="flex gap-3">
                    <div className="w-8 h-8 rounded-full overflow-hidden border border-white/10 shrink-0">
                      <img 
                        src={c.avatar_url || `https://api.dicebear.com/7.x/initials/svg?seed=${c.username}`} 
                        alt={c.username} 
                        className="w-full h-full object-cover" 
                      />
                    </div>
                    <div className="flex-1 bg-white/5 border border-white/5 rounded-xl p-3">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-display italic text-[11px] text-white">@{c.username}</span>
                        <span className="text-[8px] text-on-surface-variant/40 tracking-wider">
                          {c.created_at ? new Date(c.created_at).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }) : "Just Now"}
                        </span>
                      </div>
                      <p className="font-body-md text-xs text-on-surface-variant leading-relaxed">
                        {c.content}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>

            <form onSubmit={submitComment} className="p-4 border-t border-white/5 bg-surface flex gap-3 select-none">
              <input 
                type="text" 
                value={newCommentText}
                onChange={(e) => setNewCommentText(e.target.value)}
                placeholder="Write styled comment..."
                className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-xs text-white placeholder-on-surface-variant/40 focus:outline-none focus:border-white/20 transition-all font-light"
              />
              <button
                type="submit"
                disabled={!newCommentText.trim()}
                className="px-4 py-2.5 bg-white text-background font-label-sm text-[8px] uppercase tracking-widest rounded-lg font-bold hover:bg-tertiary hover:text-on-tertiary transition-all active:scale-[0.97] cursor-pointer disabled:opacity-40"
              >
                Post
              </button>
            </form>
          </div>
        </div>
      )}
    </SocialLayout>
  );
};

export default Explore;
