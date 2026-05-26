import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import SocialLayout from "../components/layout/SocialLayout";
import {
  apiListCommunities, apiGetMyCommunities, apiCreateCommunity,
  apiToggleCommunityMembership, apiGetCommunityDetails, apiListCommunityPosts,
  apiListCommunityMembers
} from "../utils/socialStore";

export const Communities = () => {
  const navigate = useNavigate();

  // Navigation states
  const [activeTab, setActiveTab] = useState("joined"); // joined, explore
  const [communitiesList, setCommunitiesList] = useState([]);
  const [loading, setLoading] = useState(true);

  // Community Details states (when a user clicks on a community card)
  const [selectedCommunity, setSelectedCommunity] = useState(null);
  const [commPosts, setCommPosts] = useState([]);
  const [commMembers, setCommMembers] = useState([]);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [activeDetailsTab, setActiveDetailsTab] = useState("feed"); // feed, info, members

  // Community Creation modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newRules, setNewRules] = useState("");
  const [newCover, setNewCover] = useState("");

  const MOCK_COVERS = [
    "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1516257984-b1b4d707412e?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?auto=format&fit=crop&w=800&q=80"
  ];

  // Load Communities lists
  const loadCommunities = async () => {
    setLoading(true);
    try {
      if (activeTab === "joined") {
        const list = await apiGetMyCommunities();
        setCommunitiesList(list);
      } else {
        const list = await apiListCommunities();
        setCommunitiesList(list);
      }
    } catch (e) {
      console.error("Error loading communities:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCommunities();
  }, [activeTab]);

  // Load details when a community is selected
  const handleSelectCommunity = async (comm) => {
    setSelectedCommunity(comm);
    setLoadingDetails(true);
    setActiveDetailsTab("feed");
    try {
      // Fetch details, posts, and members
      const [details, postsList, membersList] = await Promise.all([
        apiGetCommunityDetails(comm.slug),
        apiListCommunityPosts(comm.id),
        apiListCommunityMembers(comm.id)
      ]);
      setSelectedCommunity(details);
      setCommPosts(postsList);
      setCommMembers(membersList);
    } catch (e) {
      console.error("Error loading community details:", e);
    } finally {
      setLoadingDetails(false);
    }
  };

  // Toggle Join/Leave membership
  const handleToggleMembership = async (e, comm) => {
    e.stopPropagation(); // Avoid triggering card details click
    try {
      await apiToggleCommunityMembership(comm.id, comm.is_joined);
      
      // Update state in lists
      setCommunitiesList(prev => prev.map(c => {
        if (c.id === comm.id) {
          const nextState = !c.is_joined;
          return {
            ...c,
            is_joined: nextState,
            members_count: c.members_count + (nextState ? 1 : -1)
          };
        }
        return c;
      }));

      // Update details view in-place if active
      if (selectedCommunity?.id === comm.id) {
        setSelectedCommunity(prev => {
          if (!prev) return null;
          const nextState = !prev.is_joined;
          return {
            ...prev,
            is_joined: nextState,
            members_count: prev.members_count + (nextState ? 1 : -1)
          };
        });
        
        // Refresh members roster
        const membersList = await apiListCommunityMembers(comm.id);
        setCommMembers(membersList);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Create custom community
  const handleCreateCommunitySubmit = async (e) => {
    e.preventDefault();
    if (!newName.trim() || !newDesc.trim()) return;

    const payload = {
      name: newName,
      description: newDesc,
      rules: newRules || "1. Focus on fashion aesthetics.\n2. Respect styled creators.",
      cover_image_url: newCover || MOCK_COVERS[0]
    };

    try {
      const created = await apiCreateCommunity(payload);
      setShowCreateModal(false);
      setNewName("");
      setNewDesc("");
      setNewRules("");
      setNewCover("");
      
      // Notify user
      const toast = document.createElement("div");
      toast.className = "fixed bottom-36 left-1/2 -translate-x-1/2 bg-on-surface text-background px-6 py-3 rounded-full font-label-sm text-[11px] uppercase tracking-[0.2em] shadow-2xl z-[99] border border-white/10 animate-fade-in flex items-center gap-2";
      toast.innerHTML = `<span class="material-symbols-outlined text-sm font-bold text-tertiary">check_circle</span> Community Created`;
      document.body.appendChild(toast);
      setTimeout(() => {
        toast.classList.add("animate-fade-out");
        setTimeout(() => toast.remove(), 400);
      }, 2000);

      // Reload
      setActiveTab("joined");
      loadCommunities();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <SocialLayout title="Fashion Communities">
      <div className="w-full relative pb-20 select-text">
        
        {/* Title Header */}
        {!selectedCommunity && (
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8 select-none">
            <div>
              <h2 className="font-display text-2xl italic luxury-text-gradient mb-1">Fashion Communities</h2>
              <p className="text-[7px] uppercase tracking-[0.2em] text-on-surface-variant/40 font-semibold">
                Explore dedicated stylistic tribes, capsule discussions, and sub-group feeds
              </p>
            </div>
            
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-5 py-2.5 bg-white text-background font-label-sm text-[8px] uppercase tracking-widest rounded-lg font-bold hover:bg-tertiary hover:text-on-tertiary transition-all active:scale-[0.97] cursor-pointer shadow-md flex items-center gap-1.5"
            >
              <span className="material-symbols-outlined text-xs">add</span>
              Create Tribe
            </button>
          </div>
        )}

        {/* ==================== COMM DETAILS PANEL VIEW ==================== */}
        {selectedCommunity ? (
          <div className="animate-fade-in">
            {/* Back to feed button */}
            <button
              onClick={() => setSelectedCommunity(null)}
              className="mb-6 flex items-center gap-1 text-[9px] uppercase tracking-widest text-on-surface-variant/70 hover:text-white font-bold cursor-pointer"
            >
              <span className="material-symbols-outlined text-sm">arrow_back</span>
              Back to communities list
            </button>

            {/* Cover Banner Card */}
            <div className="relative h-44 rounded-2xl border border-white/[0.08] overflow-hidden shadow-2xl mb-8 flex items-end p-6 select-none">
              <img
                src={selectedCommunity.cover_image_url}
                alt={selectedCommunity.name}
                className="absolute inset-0 w-full h-full object-cover opacity-35"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background via-background/45 to-transparent"></div>
              
              <div className="relative w-full flex flex-col sm:flex-row sm:items-end justify-between gap-4 z-10">
                <div>
                  <span className="text-[7px] text-tertiary uppercase tracking-widest block font-bold mb-1">
                    c/{selectedCommunity.slug}
                  </span>
                  <h2 className="font-display text-xl md:text-2xl italic text-white leading-none mb-1.5">
                    {selectedCommunity.name}
                  </h2>
                  <p className="font-body-md text-[10px] text-on-surface-variant/70 font-light max-w-lg truncate">
                    {selectedCommunity.description}
                  </p>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <div className="text-right sm:text-left">
                    <p className="text-xs font-display italic font-semibold text-white leading-none">
                      {selectedCommunity.members_count}
                    </p>
                    <p className="text-[7px] uppercase tracking-wider text-on-surface-variant/40 font-semibold mt-0.5">
                      Members
                    </p>
                  </div>
                  
                  <button
                    onClick={(e) => handleToggleMembership(e, selectedCommunity)}
                    className={`px-5 py-2 rounded-full font-label-sm text-[8px] uppercase tracking-widest font-bold transition-all shadow-md cursor-pointer ${
                      selectedCommunity.is_joined
                        ? "bg-white/10 text-white border border-white/10 hover:bg-error/15 hover:border-error/25 hover:text-error"
                        : "bg-white text-background"
                    }`}
                  >
                    {selectedCommunity.is_joined ? "Joined" : "Join Tribe"}
                  </button>
                </div>
              </div>
            </div>

            {/* Sub details tabs switch */}
            <div className="flex gap-2 border-b border-white/5 pb-2 mb-6 select-none">
              {[
                { id: "feed", label: "Tribe Feed", icon: "style" },
                { id: "members", label: "Roster", icon: "groups" },
                { id: "info", label: "Rules & Coordinates", icon: "info" }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveDetailsTab(tab.id)}
                  className={`px-5 py-2 rounded-lg font-label-sm text-[9px] uppercase tracking-[0.15em] transition-all flex items-center gap-1.5 cursor-pointer ${
                    activeDetailsTab === tab.id
                      ? "bg-white/10 text-white font-bold border border-white/10"
                      : "text-on-surface-variant/60 hover:text-white"
                  }`}
                >
                  <span className="material-symbols-outlined text-[14px]">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Sub pages loading */}
            {loadingDetails ? (
              <div className="text-center py-12">
                <span className="material-symbols-outlined text-2xl text-tertiary animate-spin mb-2">
                  sync
                </span>
                <p className="font-body-md text-[10px] text-on-surface-variant/50 uppercase tracking-widest">
                  Syncing tribe database...
                </p>
              </div>
            ) : (
              <div>
                
                {/* 1. Tribe Feed */}
                {activeDetailsTab === "feed" && (
                  <div className="max-w-xl mx-auto w-full flex flex-col gap-6">
                    {selectedCommunity.is_joined && (
                      <div className="glass rounded-xl border border-white/5 p-4 flex justify-between items-center select-none shadow-md">
                        <p className="font-body-md text-[10.5px] text-on-surface-variant/75 font-light">
                          Wearing a {selectedCommunity.name.toLowerCase()} aesthetic look?
                        </p>
                        <button
                          onClick={() => navigate("/app/social/post/new")}
                          className="px-4 py-2 bg-white/15 hover:bg-white text-white hover:text-background font-label-sm text-[8px] uppercase tracking-widest rounded-lg font-bold transition-all shadow-md cursor-pointer border border-white/5"
                        >
                          Tag Outfit Look
                        </button>
                      </div>
                    )}

                    {commPosts.length === 0 ? (
                      <div className="text-center py-16 px-6 glass rounded-2xl border border-white/5 select-none">
                        <span className="material-symbols-outlined text-4xl text-on-surface-variant/30 mb-3">
                          style
                        </span>
                        <h4 className="font-display text-sm italic text-on-surface mb-0.5">Feed is empty</h4>
                        <p className="font-body-md text-[10px] text-on-surface-variant/50 max-w-xs mx-auto leading-relaxed">
                          Be the first to share your digitized outfits in c/{selectedCommunity.slug}!
                        </p>
                      </div>
                    ) : (
                      commPosts.map(post => (
                        <div
                          key={post.id}
                          onClick={() => navigate("/app/social/feed")}
                          className="glass rounded-2xl border border-white/[0.08] overflow-hidden flex flex-col shadow-2xl cursor-pointer hover:border-white/15 transition-all duration-300"
                        >
                          <div className="relative aspect-[4/5] bg-black/20 overflow-hidden select-none">
                            <img src={post.image_url} alt={post.caption} className="w-full h-full object-cover" />
                          </div>
                          <div className="p-4">
                            <p className="font-body-md text-xs text-on-surface-variant/90 leading-relaxed font-light mb-3 select-text">
                              <span className="font-display italic text-white mr-1.5">@{post.username}</span>
                              {post.caption}
                            </p>
                            <div className="flex justify-between items-center text-[8px] text-on-surface-variant/40 uppercase tracking-widest font-semibold pt-2 border-t border-white/5 select-none">
                              <span>❤️ {post.likes_count} likes</span>
                              <span>💬 {post.comments_count} comments</span>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* 2. Roster (Members) */}
                {activeDetailsTab === "members" && (
                  <div className="max-w-md mx-auto w-full bg-white/[0.01] border border-white/5 rounded-2xl p-5 shadow-xl select-none">
                    <h4 className="font-display text-xs italic text-white mb-4">Tribe Members Registry</h4>
                    <div className="flex flex-col gap-4">
                      {commMembers.map(member => (
                        <div key={member.user_id} className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-full overflow-hidden border border-white/10 shrink-0">
                              <img src={member.avatar_url} alt={member.username} className="w-full h-full object-cover" />
                            </div>
                            <div>
                              <span className="font-display italic text-xs text-white hover:underline cursor-pointer block leading-none">
                                @{member.username}
                              </span>
                              <span className="text-[7px] text-on-surface-variant/40 tracking-wider font-semibold uppercase mt-1 block">
                                Joined {new Date(member.joined_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>

                          <span className={`px-2 py-0.5 rounded-full font-label-sm text-[5.5px] uppercase tracking-wider font-semibold ${
                            member.role === "admin"
                              ? "bg-tertiary/20 text-tertiary border border-tertiary/30"
                              : "bg-white/5 text-on-surface-variant/80 border border-white/5"
                          }`}>
                            {member.role}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 3. Info & Rules */}
                {activeDetailsTab === "info" && (
                  <div className="max-w-lg mx-auto w-full flex flex-col gap-5 select-text">
                    <div className="glass rounded-xl border border-white/5 p-5 shadow-lg">
                      <h4 className="font-display text-xs italic text-white mb-2 select-none">Tribal Guidelines</h4>
                      <p className="font-body-md text-xs text-on-surface-variant/80 leading-relaxed font-light whitespace-pre-line">
                        {selectedCommunity.rules}
                      </p>
                    </div>
                    
                    <div className="glass rounded-xl border border-white/5 p-5 shadow-lg select-none">
                      <h4 className="font-display text-xs italic text-white mb-1.5">Aesthetic Specs</h4>
                      <div className="flex items-center justify-between text-[8px] uppercase tracking-widest text-on-surface-variant font-bold border-b border-white/5 py-2">
                        <span>Creation Sync Date</span>
                        <span className="font-mono text-white">
                          {new Date(selectedCommunity.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[8px] uppercase tracking-widest text-on-surface-variant font-bold py-2">
                        <span>Moderation Mode</span>
                        <span className="font-mono text-tertiary">Verified Members Only</span>
                      </div>
                    </div>
                  </div>
                )}

              </div>
            )}

          </div>
        ) : (
          /* ==================== COMMUNITIES LIST PANELS ==================== */
          <div className="animate-fade-in">
            {/* List Navigation Tabs */}
            <div className="flex gap-2 border-b border-white/5 pb-2 mb-8 select-none">
              {["joined", "explore"].map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-2.5 rounded-lg font-label-sm text-[10px] uppercase tracking-[0.2em] transition-all duration-300 cursor-pointer ${
                    activeTab === tab
                      ? "bg-white/10 text-white font-bold border border-white/10"
                      : "text-on-surface-variant/60 hover:text-white"
                  }`}
                >
                  {tab === "joined" ? "My Tribes" : "Discover Tribes"}
                </button>
              ))}
            </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <span className="material-symbols-outlined text-4xl text-tertiary animate-spin mb-4">
                  auto_awesome
                </span>
                <p className="font-body-md text-xs text-on-surface-variant/60 tracking-wider">
                  Syncing fashion communities...
                </p>
              </div>
            ) : communitiesList.length === 0 ? (
              <div className="text-center py-16 px-6 glass rounded-2xl border border-white/5 select-none">
                <span className="material-symbols-outlined text-4xl text-on-surface-variant/30 mb-3">
                  forum
                </span>
                <h4 className="font-display text-sm italic text-on-surface mb-1">No Communities Found</h4>
                <p className="font-body-md text-xs text-on-surface-variant/60 mb-6 max-w-sm mx-auto leading-relaxed">
                  {activeTab === "joined"
                    ? "You haven't joined any fashion communities yet. Head over to Discover Tribes to join style communities!"
                    : "No communities are currently registered in the style directory."}
                </p>
                {activeTab === "joined" && (
                  <button
                    onClick={() => setActiveTab("explore")}
                    className="px-6 py-3 bg-white text-background font-label-sm text-[9px] uppercase tracking-widest rounded hover:bg-tertiary hover:text-on-tertiary transition-all duration-300 font-bold shadow-md cursor-pointer"
                  >
                    Discover Aesthetics
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 select-none">
                {communitiesList.map(comm => (
                  <div
                    key={comm.id}
                    onClick={() => handleSelectCommunity(comm)}
                    className="glass rounded-2xl border border-white/[0.08] overflow-hidden cursor-pointer hover:border-white/15 hover:scale-[1.01] transition-all duration-300 flex flex-col shadow-xl"
                  >
                    {/* Cover image header */}
                    <div className="relative h-28 bg-black/20">
                      <img src={comm.cover_image_url} alt={comm.name} className="w-full h-full object-cover opacity-45 pointer-events-none" />
                      <div className="absolute inset-0 bg-gradient-to-t from-surface via-surface/40 to-transparent"></div>
                      <div className="absolute bottom-3 left-4">
                        <span className="text-[7px] text-tertiary uppercase tracking-widest font-bold block mb-0.5">
                          c/{comm.slug}
                        </span>
                        <h4 className="font-display text-base italic text-white truncate max-w-[280px]">
                          {comm.name}
                        </h4>
                      </div>
                    </div>

                    <div className="p-4 flex-1 flex flex-col justify-between">
                      <p className="font-body-md text-[10px] text-on-surface-variant/80 font-light leading-relaxed mb-4 line-clamp-2">
                        {comm.description}
                      </p>

                      <div className="flex justify-between items-center pt-3.5 border-t border-white/5">
                        <div className="flex gap-3 text-[8.5px] text-on-surface-variant/40 tracking-wider font-semibold uppercase">
                          <span>👥 {comm.members_count} Members</span>
                          <span>📦 {comm.posts_count || 0} Fits</span>
                        </div>
                        
                        <button
                          onClick={(e) => handleToggleMembership(e, comm)}
                          className={`px-4 py-1.5 rounded-full font-label-sm text-[7px] uppercase tracking-widest font-bold transition-all shadow-md cursor-pointer ${
                            comm.is_joined
                              ? "bg-white/10 text-white border border-white/10 hover:bg-error/15 hover:border-error/25 hover:text-error"
                              : "bg-white text-background"
                          }`}
                        >
                          {comm.is_joined ? "Leave" : "Join"}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ==================== TRIBAL CREATION MODAL ==================== */}
        {showCreateModal && (
          <div className="fixed inset-0 z-[100] bg-background/80 backdrop-blur-sm flex justify-center items-center p-4 animate-fade-in">
            <div className="absolute inset-0 cursor-pointer" onClick={() => setShowCreateModal(false)}></div>
            <div className="relative w-full max-w-md bg-surface border border-white/10 rounded-2xl p-6 shadow-2xl animate-scale-up z-50">
              
              <div className="flex justify-between items-center mb-6 select-none border-b border-white/5 pb-3">
                <div>
                  <h3 className="font-display text-base italic text-white">Create Style Tribe</h3>
                  <p className="text-[7px] text-on-surface-variant/40 uppercase tracking-[0.2em] font-semibold">
                    Set up styling community guidelines
                  </p>
                </div>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="w-7 h-7 rounded-full bg-white/5 border border-white/5 flex items-center justify-center text-primary hover:bg-white/10 transition-all cursor-pointer"
                >
                  <span className="material-symbols-outlined text-sm">close</span>
                </button>
              </div>

              <form onSubmit={handleCreateCommunitySubmit} className="flex flex-col gap-4">
                
                <div className="flex flex-col gap-1.5">
                  <label className="font-label-sm text-[8px] uppercase tracking-widest text-on-surface-variant font-bold select-none">
                    Tribe Name
                  </label>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="e.g. Minimalist Monochrome"
                    required
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-xs text-white placeholder-on-surface-variant/30 focus:outline-none focus:border-white/20 font-light"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-label-sm text-[8px] uppercase tracking-widest text-on-surface-variant font-bold select-none">
                    Styling Philosophy Description
                  </label>
                  <textarea
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    placeholder="Brief description of the aesthetic silhouette, color coordinates, or guidelines..."
                    rows={2}
                    required
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-xs text-white placeholder-on-surface-variant/30 focus:outline-none focus:border-white/20 font-light resize-none"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-label-sm text-[8px] uppercase tracking-widest text-on-surface-variant font-bold select-none">
                    Tribal Guidelines (Rules)
                  </label>
                  <textarea
                    value={newRules}
                    onChange={(e) => setNewRules(e.target.value)}
                    placeholder="1. Focus on fabric textiles.&#10;2. Only neutral colors."
                    rows={2}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-xs text-white placeholder-on-surface-variant/30 focus:outline-none focus:border-white/20 font-light resize-none"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-label-sm text-[8px] uppercase tracking-widest text-on-surface-variant font-bold select-none">
                    Cover Banner Image URL
                  </label>
                  <input
                    type="url"
                    value={newCover}
                    onChange={(e) => setNewCover(e.target.value)}
                    placeholder="https://images.unsplash.com/photo..."
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-xs text-white placeholder-on-surface-variant/30 focus:outline-none focus:border-white/20 font-light"
                  />
                  <div className="flex items-center gap-1.5 mt-1 select-none">
                    <span className="text-[7px] text-on-surface-variant/40 uppercase tracking-widest font-bold">
                      Banner Presets:
                    </span>
                    <div className="flex gap-2">
                      {MOCK_COVERS.map((cover, idx) => (
                        <div
                          key={idx}
                          onClick={() => setNewCover(cover)}
                          className="w-8 h-8 rounded border border-white/10 cursor-pointer overflow-hidden hover:border-tertiary"
                        >
                          <img src={cover} className="w-full h-full object-cover" />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={!newName.trim() || !newDesc.trim()}
                  className="w-full py-3 bg-white text-background font-label-sm text-[9px] uppercase tracking-widest rounded-lg font-bold hover:bg-tertiary hover:text-on-tertiary transition-all active:scale-[0.98] disabled:opacity-40 cursor-pointer mt-2 shadow-lg"
                >
                  Register Tribe
                </button>
              </form>
            </div>
          </div>
        )}

      </div>
    </SocialLayout>
  );
};

export default Communities;
