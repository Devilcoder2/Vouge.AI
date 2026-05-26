import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import SocialLayout from "../components/layout/SocialLayout";
import {
  apiGetSocialProfile, apiToggleFollow, getFollowingUsernames, apiListFeed
} from "../utils/socialStore";

export const SocialProfile = () => {
  const { username = "social_curator" } = useParams();
  const navigate = useNavigate();
  
  const [profile, setProfile] = useState(null);
  const [myPosts, setMyPosts] = useState([]);
  const [savedPosts, setSavedPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [followingList, setFollowingList] = useState([]);
  const [isFollowing, setIsFollowing] = useState(false);

  // Active Tab inside Profile (posts vs saved)
  const [activeProfileTab, setActiveProfileTab] = useState("posts"); // posts, saved

  // Modal Dialog states
  const [showFollowersModal, setShowFollowersModal] = useState(false);
  const [showFollowingModal, setShowFollowingModal] = useState(false);

  // Lists of users inside modals (seed references)
  const [followersList, setFollowersList] = useState([]);
  const [followingUsers, setFollowingUsers] = useState([]);

  // Load Profile and Posts
  const loadProfileData = async () => {
    setLoading(true);
    try {
      // 1. Fetch Profile Details
      const data = await apiGetSocialProfile(username);
      setProfile(data);
      
      // 2. Fetch Following lists
      const following = getFollowingUsernames();
      setFollowingList(following);
      setIsFollowing(following.includes(username));
      
      // 3. Fetch All Posts to filter
      const allPosts = await apiListFeed("trending");
      
      // Filter posts created by this user
      const userPostsList = allPosts.filter(p => p.username === username);
      setMyPosts(userPostsList);

      // Filter posts bookmarked/saved by this user (only curator saves)
      const bookmarked = allPosts.filter(p => p.is_saved_by_user);
      setSavedPosts(bookmarked);

      // 4. Populate mock follow lists for modal registries
      const allCreatorsMock = [
        { username: "quiet_luxury_edits", vanity_username: "Elena Rostova", avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=Elena", bio: "Neutral tailoring | London" },
        { username: "tokyo_streetwear", vanity_username: "Kenji Sato", avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=Kenji", bio: "Techwear layering | Harajuku" },
        { username: "old_money_tailoring", vanity_username: "Alessandro Rossi", avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=Alessandro", bio: "Sartorial tailoring | Milan" },
        { username: "minimalist_vibes", vanity_username: "Astrid Lind", avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=Astrid", bio: "Less is more | Stockholm" },
        { username: "retro_chic_vintage", vanity_username: "Camille Moreau", avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=Camille", bio: "70s vintage | Paris" },
        { username: "capsule_closet_ideas", vanity_username: "Chloe Chen", avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=Chloe", bio: "Smart capsule closet | Toronto" }
      ];

      if (username === "social_curator") {
        setFollowersList(allCreatorsMock.slice(0, 4));
        setFollowingUsers(allCreatorsMock.slice(0, 3));
      } else {
        // Mutual list
        setFollowersList(allCreatorsMock.filter(c => c.username !== username).slice(0, 2));
        setFollowingUsers(allCreatorsMock.filter(c => c.username !== username).slice(1, 3));
      }

    } catch (e) {
      console.error("Error loading social profile:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfileData();
    window.scrollTo(0, 0);
  }, [username]);

  // Profile follow toggle
  const handleFollowToggle = async () => {
    if (!profile) return;
    const action = isFollowing ? "unfollow" : "follow";
    setIsFollowing(!isFollowing);
    
    // Update local following list
    let nextFollowingList;
    if (action === "follow") {
      nextFollowingList = [...followingList, username];
    } else {
      nextFollowingList = followingList.filter(u => u !== username);
    }
    setFollowingList(nextFollowingList);

    setProfile(prev => {
      if (!prev) return null;
      return {
        ...prev,
        followers_count: prev.followers_count + (action === "follow" ? 1 : -1)
      };
    });

    try {
      await apiToggleFollow(profile.id, profile.username, action);
    } catch (e) {
      console.error(e);
    }
  };

  // Follow/Unfollow toggle inside modallists
  const handleModalFollowToggle = async (creatorUsername) => {
    const isCurrentlyFollowing = followingList.includes(creatorUsername);
    const action = isCurrentlyFollowing ? "unfollow" : "follow";

    const nextFollowingList = isCurrentlyFollowing
      ? followingList.filter(u => u !== creatorUsername)
      : [...followingList, creatorUsername];
    setFollowingList(nextFollowingList);

    // If active profile is social_curator and we unfollowed from following modal, decrement profile following_count
    if (username === "social_curator" && showFollowingModal) {
      setProfile(prev => {
        if (!prev) return null;
        return {
          ...prev,
          following_count: prev.following_count + (action === "follow" ? 1 : -1)
        };
      });
    }

    try {
      // Find matching mock id or use standard fallback
      await apiToggleFollow("00000000-0000-0000-0000-creator-mock-id", creatorUsername, action);
    } catch (e) {
      console.error(e);
    }
  };

  const isMe = username === "social_curator";

  if (loading) {
    return (
      <SocialLayout title="Profile">
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <span className="material-symbols-outlined text-4xl text-tertiary animate-spin mb-4">
            auto_awesome
          </span>
          <p className="font-body-md text-xs text-on-surface-variant/60 tracking-wider">
            Loading stylist profile...
          </p>
        </div>
      </SocialLayout>
    );
  }

  if (!profile) {
    return (
      <SocialLayout title="Profile">
        <div className="text-center py-16 px-6 glass rounded-2xl border border-white/5 max-w-md mx-auto">
          <span className="material-symbols-outlined text-4xl text-on-surface-variant/40 mb-3 select-none">
            person_off
          </span>
          <h4 className="font-display text-lg italic text-on-surface mb-1">Profile Not Found</h4>
          <p className="font-body-md text-xs text-on-surface-variant/60 mb-6 leading-relaxed">
            The fashion persona handle you requested doesn't exist or hasn't synced with the database.
          </p>
          <button
            onClick={() => navigate("/app/social/feed")}
            className="px-6 py-3 bg-white text-background font-label-sm text-[9px] uppercase tracking-widest rounded hover:bg-tertiary hover:text-on-tertiary transition-all duration-300 font-bold shadow-md cursor-pointer"
          >
            Back to feed
          </button>
        </div>
      </SocialLayout>
    );
  }

  return (
    <SocialLayout title={`@${profile.username} Profile`}>
      <div className="w-full relative pb-20 select-text max-w-2xl mx-auto">
        
        {/* ==================== 4) INSTAGRAM PROFILE LAYOUT ==================== */}
        <section className="flex flex-col md:flex-row items-center md:items-start gap-8 md:gap-12 select-none mb-10 pb-8 border-b border-white/5">
          {/* Avatar Area */}
          <div className="relative shrink-0 select-none">
            <div className="w-24 h-24 md:w-32 md:h-32 rounded-full overflow-hidden border-2 border-white/10 p-1 bg-surface shadow-xl">
              <img
                src={profile.avatar_url || `https://api.dicebear.com/7.x/initials/svg?seed=${profile.username}`}
                alt={profile.username}
                className="w-full h-full object-cover rounded-full"
              />
            </div>
            {profile.verified_badge && (
              <div className="absolute bottom-1 right-1 w-6 h-6 bg-tertiary rounded-full flex items-center justify-center border-2 border-background shadow-md">
                <span className="material-symbols-outlined text-surface text-[12px] font-bold" style={{ fontVariationSettings: "'FILL' 1" }}>
                  verified
                </span>
              </div>
            )}
          </div>

          {/* Identity & Stats Area */}
          <div className="flex-1 flex flex-col items-center md:items-start text-center md:text-left w-full">
            {/* Top row: username + buttons */}
            <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-4 w-full justify-center md:justify-start">
              <h2 className="font-display text-xl md:text-2xl italic text-white font-semibold leading-none">
                {profile.username}
              </h2>

              <div className="flex items-center gap-2">
                {isMe ? (
                  <button
                    onClick={() => navigate("/app/profile")}
                    className="px-5 py-1.5 bg-white/10 border border-white/10 text-white rounded font-label-sm text-[9px] uppercase tracking-widest font-bold hover:bg-white/15 transition-all shadow-md cursor-pointer"
                  >
                    Edit Profile
                  </button>
                ) : (
                  <button
                    onClick={handleFollowToggle}
                    className={`px-6 py-1.5 rounded font-label-sm text-[9px] uppercase tracking-widest font-bold transition-all duration-300 shadow-md cursor-pointer ${
                      isFollowing
                        ? "bg-white/10 text-white border border-white/10 hover:bg-error/15 hover:border-error/25 hover:text-error"
                        : "bg-white text-background hover:bg-tertiary hover:text-on-tertiary"
                    }`}
                  >
                    {isFollowing ? "Following" : "Follow"}
                  </button>
                )}
              </div>
            </div>

            {/* Middle row: Stats counts (clickable triggers for Modals) */}
            <div className="flex items-center gap-8 mb-5 select-none text-sm text-on-surface-variant font-light w-full justify-center md:justify-start">
              <div>
                <span className="font-bold text-white mr-1">{profile.posts_count || myPosts.length}</span>
                posts
              </div>
              
              {/* Followers count trigger */}
              <button 
                onClick={() => setShowFollowersModal(true)} 
                className="hover:text-white cursor-pointer transition-colors"
              >
                <span className="font-bold text-white mr-1">{profile.followers_count}</span>
                followers
              </button>

              {/* Following count trigger */}
              <button 
                onClick={() => setShowFollowingModal(true)}
                className="hover:text-white cursor-pointer transition-colors"
              >
                <span className="font-bold text-white mr-1">{profile.following_count}</span>
                following
              </button>
            </div>

            {/* Bottom row: Bio Description */}
            <div className="w-full">
              <h3 className="font-body-md text-xs font-bold text-white mb-0.5 leading-none">
                {profile.vanity_username || profile.username}
              </h3>
              <p className="font-body-md text-xs text-on-surface-variant/90 leading-relaxed font-light mb-3 max-w-md whitespace-pre-line">
                {profile.bio || "No fashion bio loaded."}
              </p>
              
              {/* Style Personas tags */}
              <div className="flex flex-wrap gap-1.5 justify-center md:justify-start mt-2">
                {profile.style_personas.map(persona => (
                  <span
                    key={persona}
                    className="px-2.5 py-0.5 bg-tertiary/10 border border-tertiary/20 rounded text-[7px] font-label-sm uppercase tracking-wider text-tertiary"
                  >
                    #{persona.replace("_", "")}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ==================== TABS BAR NAVIGATION (My Posts vs Saves) ==================== */}
        <div className="flex justify-center border-t border-white/5 gap-12 mb-6 select-none">
          <button
            onClick={() => setActiveProfileTab("posts")}
            className={`flex items-center gap-1.5 py-3.5 border-t-2 font-label-sm text-[10px] uppercase tracking-[0.2em] transition-all cursor-pointer ${
              activeProfileTab === "posts"
                ? "border-white text-white font-bold"
                : "border-transparent text-on-surface-variant/40 hover:text-white/60"
            }`}
          >
            <span className="material-symbols-outlined text-[15px]">grid_on</span>
            Posts
          </button>

          {isMe && (
            <button
              onClick={() => setActiveProfileTab("saved")}
              className={`flex items-center gap-1.5 py-3.5 border-t-2 font-label-sm text-[10px] uppercase tracking-[0.2em] transition-all cursor-pointer ${
                activeProfileTab === "saved"
                  ? "border-white text-white font-bold"
                  : "border-transparent text-on-surface-variant/40 hover:text-white/60"
              }`}
            >
              <span className="material-symbols-outlined text-[15px]">bookmark</span>
              Saved
            </button>
          )}
        </div>

        {/* ==================== 3-COLUMN OUTLET GRID SHOWCASE ==================== */}
        {activeProfileTab === "posts" ? (
          myPosts.length === 0 ? (
            <div className="text-center py-16 px-6 glass rounded-2xl border border-white/5 select-none">
              <span className="material-symbols-outlined text-4xl text-on-surface-variant/30 mb-2">
                grid_on
              </span>
              <h4 className="font-display text-sm italic text-on-surface mb-0.5">No Posts Yet</h4>
              <p className="font-body-md text-[10px] text-on-surface-variant/50 max-w-xs mx-auto leading-relaxed">
                When you share outfit curations, they will show up here.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-2 md:gap-4 select-none">
              {myPosts.map(post => (
                <div
                  key={post.id}
                  onClick={() => navigate("/app/social/feed")}
                  className="relative aspect-square bg-black/20 border border-white/5 rounded-lg overflow-hidden cursor-pointer group shadow-md"
                >
                  <img
                    src={post.image_url}
                    alt={post.caption}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  {/* Instagram-style hover counts overlay */}
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-4 text-white font-display text-xs italic font-bold">
                    <span className="flex items-center gap-1">
                      ❤️ {post.likes_count}
                    </span>
                    <span className="flex items-center gap-1">
                      💬 {post.comments_count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )
        ) : (
          /* SAVED POSTS GRID (Tab 2) */
          savedPosts.length === 0 ? (
            <div className="text-center py-16 px-6 glass rounded-2xl border border-white/5 select-none">
              <span className="material-symbols-outlined text-4xl text-on-surface-variant/30 mb-2">
                bookmark
              </span>
              <h4 className="font-display text-sm italic text-on-surface mb-0.5">No Saved Posts</h4>
              <p className="font-body-md text-[10px] text-on-surface-variant/50 max-w-xs mx-auto leading-relaxed">
                Save outfit catalogs you love to keep a reference record in your saves tab.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-2 md:gap-4 select-none">
              {savedPosts.map(post => (
                <div
                  key={post.id}
                  onClick={() => navigate("/app/social/feed")}
                  className="relative aspect-square bg-black/20 border border-white/5 rounded-lg overflow-hidden cursor-pointer group shadow-md"
                >
                  <img
                    src={post.image_url}
                    alt={post.caption}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-4 text-white font-display text-xs italic font-bold">
                    <span className="flex items-center gap-1">
                      ❤️ {post.likes_count}
                    </span>
                    <span className="flex items-center gap-1">
                      💬 {post.comments_count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )
        )}

      </div>

      {/* ==================== FOLLOWERS MODAL PANEL ==================== */}
      {showFollowersModal && (
        <div className="fixed inset-0 z-[100] bg-background/80 backdrop-blur-sm flex justify-center items-center p-4 animate-fade-in">
          <div className="absolute inset-0 cursor-pointer" onClick={() => setShowFollowersModal(false)}></div>
          <div className="relative w-full max-w-sm bg-surface border border-white/10 rounded-2xl p-5 shadow-2xl animate-scale-up z-50">
            
            <div className="flex justify-between items-center mb-5 select-none border-b border-white/5 pb-2.5">
              <h4 className="font-display text-sm italic text-white">Followers</h4>
              <button 
                onClick={() => setShowFollowersModal(false)}
                className="material-symbols-outlined text-on-surface-variant hover:text-white cursor-pointer text-base"
              >
                close
              </button>
            </div>

            <div className="flex flex-col gap-4 overflow-y-auto max-h-72 pr-1 select-none">
              {followersList.map(item => {
                const isItemFollowing = followingList.includes(item.username);
                return (
                  <div key={item.username} className="flex items-center justify-between gap-3">
                    <div 
                      onClick={() => {
                        setShowFollowersModal(false);
                        navigate(`/app/social/profile/${item.username}`);
                      }}
                      className="flex items-center gap-2.5 cursor-pointer min-w-0"
                    >
                      <div className="w-8 h-8 rounded-full overflow-hidden border border-white/10 shrink-0">
                        <img src={item.avatar_url} alt={item.username} className="w-full h-full object-cover" />
                      </div>
                      <div className="min-w-0">
                        <span className="font-display italic text-xs text-white hover:underline block leading-none truncate">
                          {item.vanity_username}
                        </span>
                        <span className="text-[7px] text-on-surface-variant/40 tracking-wider font-semibold uppercase mt-0.5 block">
                          @{item.username}
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleModalFollowToggle(item.username)}
                      className={`px-3 py-1.5 rounded font-label-sm text-[7px] uppercase tracking-widest font-bold transition-all cursor-pointer shrink-0 ${
                        isItemFollowing
                          ? "bg-white/10 text-white border border-white/10"
                          : "bg-white text-background"
                      }`}
                    >
                      {isItemFollowing ? "Following" : "Follow"}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ==================== FOLLOWING MODAL PANEL ==================== */}
      {showFollowingModal && (
        <div className="fixed inset-0 z-[100] bg-background/80 backdrop-blur-sm flex justify-center items-center p-4 animate-fade-in">
          <div className="absolute inset-0 cursor-pointer" onClick={() => setShowFollowingModal(false)}></div>
          <div className="relative w-full max-w-sm bg-surface border border-white/10 rounded-2xl p-5 shadow-2xl animate-scale-up z-50">
            
            <div className="flex justify-between items-center mb-5 select-none border-b border-white/5 pb-2.5">
              <h4 className="font-display text-sm italic text-white">Following</h4>
              <button 
                onClick={() => setShowFollowingModal(false)}
                className="material-symbols-outlined text-on-surface-variant hover:text-white cursor-pointer text-base"
              >
                close
              </button>
            </div>

            <div className="flex flex-col gap-4 overflow-y-auto max-h-72 pr-1 select-none">
              {followingUsers.map(item => {
                const isItemFollowing = followingList.includes(item.username);
                return (
                  <div key={item.username} className="flex items-center justify-between gap-3">
                    <div 
                      onClick={() => {
                        setShowFollowingModal(false);
                        navigate(`/app/social/profile/${item.username}`);
                      }}
                      className="flex items-center gap-2.5 cursor-pointer min-w-0"
                    >
                      <div className="w-8 h-8 rounded-full overflow-hidden border border-white/10 shrink-0">
                        <img src={item.avatar_url} alt={item.username} className="w-full h-full object-cover" />
                      </div>
                      <div className="min-w-0">
                        <span className="font-display italic text-xs text-white hover:underline block leading-none truncate">
                          {item.vanity_username}
                        </span>
                        <span className="text-[7px] text-on-surface-variant/40 tracking-wider font-semibold uppercase mt-0.5 block">
                          @{item.username}
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleModalFollowToggle(item.username)}
                      className={`px-3 py-1.5 rounded font-label-sm text-[7px] uppercase tracking-widest font-bold transition-all cursor-pointer shrink-0 ${
                        isItemFollowing
                          ? "bg-white/10 text-white border border-white/10"
                          : "bg-white text-background"
                      }`}
                    >
                      {isItemFollowing ? "Following" : "Follow"}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

    </SocialLayout>
  );
};

export default SocialProfile;
