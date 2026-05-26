import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import SocialLayout from "../components/layout/SocialLayout";
import {
  apiListFeed, apiToggleLike, apiToggleSave, apiGetComments, apiAddComment, apiToggleFollow, getFollowingUsernames
} from "../utils/socialStore";

export const SocialFeed = () => {
  const navigate = useNavigate();
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [followingList, setFollowingList] = useState([]);
  
  // Interactive Drawer States
  const [activeCommentPost, setActiveCommentPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [newCommentText, setNewCommentText] = useState("");
  
  // Hotspot Popups State
  const [activeTagPopup, setActiveTagPopup] = useState(null); // { postId, tagId }

  // Load Home Feed Data (Only posts of creators that user follows)
  const loadFeed = async () => {
    setLoading(true);
    try {
      const following = getFollowingUsernames();
      setFollowingList(following);

      // Fetch following feed
      const data = await apiListFeed("following");
      
      // Filter strictly on the frontend to ensure 100% correctness in both offline/online states
      const filtered = data.filter(p => p.username === "social_curator" || following.includes(p.username));
      setPosts(filtered);
    } catch (e) {
      console.error("Error loading social feed:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFeed();
  }, []);

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

  // Optimistic Follow Toggling
  const handleFollowToggle = async (post) => {
    const isCurrentlyFollowing = followingList.includes(post.username);
    const action = isCurrentlyFollowing ? "unfollow" : "follow";
    
    // Update local list optimistically
    const nextFollowingList = isCurrentlyFollowing
      ? followingList.filter(u => u !== post.username)
      : [...followingList, post.username];
    setFollowingList(nextFollowingList);

    try {
      await apiToggleFollow(post.user_id, post.username, action);
      
      // If we unfollowed, filter post out of Home feed
      if (action === "unfollow") {
        setPosts(prev => prev.filter(p => p.username !== post.username));
      }
    } catch (e) {
      console.error("Error toggling follow:", e);
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
      console.error("Error getting comments:", e);
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
      
      // Increment comment count on feed item
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

  return (
    <SocialLayout title="Home Feed">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8 select-none">
        <div>
          <h2 className="font-display text-3xl italic luxury-text-gradient mb-1">Style Feed</h2>
          <p className="font-body-md text-on-surface-variant/40 tracking-[0.2em] uppercase text-[9px] font-semibold">
            Outfits shared by stylists you follow
          </p>
        </div>
      </div>

      {/* Feed Deck */}
      <div className="flex flex-col gap-8 max-w-xl mx-auto w-full">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <span className="material-symbols-outlined text-4xl text-tertiary animate-spin mb-4">
              auto_awesome
            </span>
            <p className="font-body-md text-xs text-on-surface-variant/60 tracking-wider">Loading styling feed...</p>
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-16 px-6 glass rounded-2xl border border-white/5">
            <span className="material-symbols-outlined text-4xl text-on-surface-variant/40 mb-3 select-none">
              style
            </span>
            <h4 className="font-display text-lg italic text-on-surface mb-1 select-none">Style Feed is Empty</h4>
            <p className="font-body-md text-xs text-on-surface-variant/60 mb-6 max-w-sm mx-auto leading-relaxed select-none">
              You are not following any stylists yet. Discover creators on the Explore page to populate your feed!
            </p>
            <button
              onClick={() => navigate("/app/social/explore")}
              className="px-6 py-3 bg-white text-background font-label-sm text-[9px] uppercase tracking-widest rounded hover:bg-tertiary hover:text-on-tertiary transition-all duration-300 font-bold shadow-md cursor-pointer"
            >
              Explore Stylists
            </button>
          </div>
        ) : (
          posts.map(post => {
            const isFollowing = followingList.includes(post.username);
            return (
              <div 
                key={post.id}
                className="glass rounded-2xl border border-white/[0.08] overflow-hidden flex flex-col shadow-2xl animate-fade-in hover:border-white/15 transition-all duration-500"
              >
                {/* 4) Post Creator Header (Instagram style: above photo, follow toggle on right) */}
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
                        {/* Pulsing Dot */}
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
                      {/* Like Toggle Fix */}
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

                      {/* Bookmarks Toggle Fix (No count shown, filled if bookmarked) */}
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

                    {/* 5) Recreate Button redirects to dedicated RecreateFit page */}
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
      </div>

      {/* ==================== 3) COMMENTS SLIDE-UP DRAWER (Safe rendering guards) ==================== */}
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

export default SocialFeed;
