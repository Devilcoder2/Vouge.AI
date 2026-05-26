import React from "react";
import { Link, useLocation } from "react-router-dom";
import Header from "./Header";
import MobileNav from "./MobileNav";
import Breadcrumbs from "./Breadcrumbs";

export const SocialLayout = ({ children, title = "Vogue.AI Social" }) => {
  const location = useLocation();

  const socialLinks = [
    { label: "Home", path: "/app/social/feed", icon: "home" },
    { label: "Explore", path: "/app/social/explore", icon: "search" },
    { label: "Create Post", path: "/app/social/post/new", icon: "add_box" },
    { label: "Profile", path: "/app/social/profile", icon: "account_circle" },
    { label: "Recreate Fit", path: "/app/social/recreate", icon: "auto_awesome" },
  ];

  const isActive = (path) => {
    if (path === "/app/social/feed") {
      return location.pathname === "/app/social/feed" || location.pathname === "/app/social";
    }
    if (path === "/app/social/profile") {
      return location.pathname.startsWith("/app/social/profile");
    }
    if (path === "/app/social/recreate") {
      return location.pathname.startsWith("/app/social/recreate");
    }
    return location.pathname.startsWith(path);
  };

  return (
    /* Outer wrapper: full viewport height, flex-col so header is on top */
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      {/* Fixed Header — renders above everything */}
      <Header title={title} />

      {/* Body row: fills remaining height below header */}
      <div className="flex flex-1 overflow-hidden pt-24">

        {/* ── Desktop Left Sidebar ── fixed height, never scrolls */}
        <aside className="hidden md:flex flex-col gap-2 w-64 shrink-0 h-full overflow-y-auto border-r border-white/[0.06] px-4 py-6 select-none">
          {/* Ambient glows inside sidebar */}
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-0 left-0 w-48 h-48 bg-primary/20 rounded-full blur-[80px]" />
          </div>

          {/* Branding */}
          <div className="px-3 py-2 mb-4 relative z-10">
            <h4 className="font-display text-sm italic text-white mb-0.5">Style Portal</h4>
            <p className="text-[8px] uppercase tracking-[0.25em] text-on-surface-variant/40 font-semibold">
              Social styling network
            </p>
          </div>

          {/* Nav Links */}
          <nav className="flex flex-col gap-1 relative z-10">
            {socialLinks.map((link) => {
              const active = isActive(link.path);
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`flex items-center gap-3.5 px-4 py-3 rounded-xl transition-all duration-300 ${
                    active
                      ? "bg-white/10 text-white font-bold border border-white/10 shadow-lg scale-[1.02]"
                      : "text-on-surface-variant/70 hover:text-white hover:bg-white/5"
                  }`}
                >
                  <span className={`material-symbols-outlined text-[18px] ${active ? "text-tertiary" : ""}`}>
                    {link.icon}
                  </span>
                  <span className="font-label-sm text-[10px] uppercase tracking-[0.15em] font-semibold">
                    {link.label}
                  </span>
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* ── Mobile Top Nav Bar (horizontal scroll) ── */}
        {/* Rendered inside a sticky banner above the content on mobile */}

        {/* ── Main content column: this is the ONLY thing that scrolls ── */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Mobile horizontal nav */}
          <div className="md:hidden flex items-center gap-2 overflow-x-auto px-4 py-3 border-b border-white/5 scrollbar-none shrink-0 bg-background/60 backdrop-blur-md">
            {socialLinks.map((link) => {
              const active = isActive(link.path);
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-lg font-label-sm text-[10px] uppercase tracking-wider shrink-0 transition-all ${
                    active
                      ? "bg-white/10 text-white font-bold border border-white/10"
                      : "text-on-surface-variant/60 hover:text-white"
                  }`}
                >
                  <span className="material-symbols-outlined text-[14px]">{link.icon}</span>
                  {link.label.split(" ")[0]}
                </Link>
              );
            })}
          </div>

          {/* Scrollable page content */}
          <main className="flex-1 overflow-y-auto px-4 md:px-8 py-6 pb-28 md:pb-12 animate-fade-in relative">
            {/* Ambient glows in content area */}
            <div className="absolute inset-0 z-0 opacity-10 pointer-events-none select-none">
              <div className="absolute top-10 right-10 w-96 h-96 bg-primary rounded-full blur-[140px]" />
              <div className="absolute bottom-10 left-10 w-96 h-96 bg-tertiary-fixed-dim rounded-full blur-[140px]" />
            </div>

            <div className="relative z-10 max-w-4xl mx-auto w-full">
              <Breadcrumbs />
              {children}
            </div>
          </main>
        </div>
      </div>

      {/* Mobile bottom nav */}
      <MobileNav />
    </div>
  );
};

export default SocialLayout;
