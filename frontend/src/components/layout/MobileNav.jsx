import React from "react";
import { Link, useLocation } from "react-router-dom";

export const MobileNav = () => {
  const location = useLocation();
  const isActive = (path) =>
    location.pathname === path
      ? "text-primary opacity-100"
      : "text-on-surface-variant opacity-50 hover:opacity-100";

  return (
    <nav className="md:hidden fixed bottom-0 w-full z-50 flex justify-around items-end pb-6 pt-2 px-4 bg-surface/90 backdrop-blur-2xl border-t border-white/10 shadow-2xl">
      <Link
        to="/app"
        className={`flex flex-col items-center justify-center transition-all ${isActive(
          "/app"
        )}`}
      >
        <span className="material-symbols-outlined mb-1 text-2xl">home</span>
        <span className="text-[10px] uppercase tracking-widest">Home</span>
      </Link>
      <Link
        to="/app/wardrobe"
        className={`flex flex-col items-center justify-center transition-all ${isActive(
          "/app/wardrobe"
        )}`}
      >
        <span className="material-symbols-outlined mb-1 text-2xl">
          checkroom
        </span>
        <span className="text-[10px] uppercase tracking-widest">Wardrobe</span>
      </Link>
      <Link
        to="/app/chat"
        className="flex flex-col items-center justify-center group"
      >
        <div className="bg-primary text-background rounded-full p-3.5 -mt-8 shadow-2xl transition-transform group-active:scale-90 flex items-center justify-center">
          <span className="material-symbols-outlined text-2xl">
            auto_awesome
          </span>
        </div>
        <span
          className={`mt-1 text-[10px] uppercase tracking-widest ${isActive(
            "/app/chat"
          )}`}
        >
          AI Stylist
        </span>
      </Link>
      <Link
        to="/app/discover"
        className={`flex flex-col items-center justify-center transition-all ${isActive(
          "/app/discover"
        )}`}
      >
        <span className="material-symbols-outlined mb-1 text-2xl flex items-center justify-center">
          explore
        </span>
        <span className="text-[10px] uppercase tracking-widest">Discovery</span>
      </Link>
      <Link
        to="/app/profile"
        className={`flex flex-col items-center justify-center transition-all ${isActive(
          "/app/profile"
        )}`}
      >
        <span className="material-symbols-outlined mb-1 text-2xl">person</span>
        <span className="text-[10px] uppercase tracking-widest">Profile</span>
      </Link>
    </nav>
  );
};

export default MobileNav;
