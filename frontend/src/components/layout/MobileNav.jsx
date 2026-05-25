import React from "react";
import { Link, useLocation } from "react-router-dom";

export const MobileNav = () => {
  const location = useLocation();

  const isActive = (path) => {
    if (path === "/app") {
      return location.pathname === "/app";
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 bg-background/90 backdrop-blur-2xl border-t border-outline-variant/10 px-margin-mobile pt-3 pb-8 flex justify-between items-center shadow-2xl">
      {/* Home / Dashboard Link */}
      <Link
        to="/app"
        className={`flex flex-col items-center gap-1 transition-all ${
          isActive("/app") ? "text-on-surface opacity-100" : "text-on-surface-variant opacity-60"
        }`}
      >
        <span className="material-symbols-outlined text-[24px]">dashboard</span>
        <span className="text-[9px] uppercase tracking-[0.1em] font-semibold">Home</span>
      </Link>

      {/* Closet / Wardrobe Link */}
      <Link
        to="/app/wardrobe"
        className={`flex flex-col items-center gap-1 transition-all ${
          isActive("/app/wardrobe") ? "text-on-surface opacity-100" : "text-on-surface-variant opacity-60"
        }`}
      >
        <span className="material-symbols-outlined text-[24px]">checkroom</span>
        <span className="text-[9px] uppercase tracking-[0.1em] font-semibold">Closet</span>
      </Link>

      {/* Centered AI Stylist Action */}
      <div className="relative -mt-10">
        <div className="absolute inset-0 bg-tertiary/20 blur-xl rounded-full"></div>
        <Link
          to="/app/chat"
          className="relative w-14 h-14 bg-on-surface text-surface rounded-full flex items-center justify-center shadow-2xl active:scale-95 transition-transform cursor-pointer"
        >
          <span className="material-symbols-outlined text-2xl font-semibold">auto_awesome</span>
        </Link>
      </div>

      {/* Discover Link */}
      <Link
        to="/app/recommendations"
        className={`flex flex-col items-center gap-1 transition-all ${
          isActive("/app/recommendations") ? "text-on-surface opacity-100" : "text-on-surface-variant opacity-60"
        }`}
      >
        <span className="material-symbols-outlined text-[24px]">explore</span>
        <span className="text-[9px] uppercase tracking-[0.1em] font-semibold">Discover</span>
      </Link>

      {/* Profile / Alex Link */}
      <Link
        to="/app/profile"
        className={`flex flex-col items-center gap-1 transition-all ${
          isActive("/app/profile") ? "text-on-surface opacity-100" : "text-on-surface-variant opacity-60"
        }`}
      >
        <span className="material-symbols-outlined text-[24px]">person</span>
        <span className="text-[9px] uppercase tracking-[0.1em] font-semibold">Alex</span>
      </Link>
    </nav>
  );
};

export default MobileNav;
