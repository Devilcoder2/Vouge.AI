import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

export const Header = ({ title = "VOGUE.AI", showBack = false }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path) => {
    if (path === "/app") {
      return location.pathname === "/app";
    }
    return location.pathname.startsWith(path);
  };

  const navLinks = [
    { label: "Dashboard", path: "/app" },
    { label: "Wardrobe", path: "/app/wardrobe" },
    { label: "Stylist", path: "/app/chat" },
    { label: "Planner", path: "/app/planner" },
  ];

  return (
    <>
      {/* Desktop Top Header */}
      <header className="hidden md:flex fixed top-0 left-0 w-full z-[60] glass-panel border-b border-outline-variant/10 h-24 items-center justify-between px-margin-desktop shadow-md">
        <div className="flex items-center gap-12">
          <Link
            to="/app"
            className="font-display text-2xl tracking-[0.4em] luxury-text-gradient hover:opacity-90 transition-opacity uppercase font-bold"
          >
            VOGUE.AI
          </Link>
          <nav className="flex items-center gap-8">
            {navLinks.map((link) => {
              const active = isActive(link.path);
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`font-label-sm text-[11px] uppercase tracking-[0.2em] transition-all duration-300 pb-1 ${
                    active
                      ? "text-on-surface border-b-2 border-tertiary"
                      : "text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-6">
          <button className="material-symbols-outlined text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer">
            notifications
          </button>
          <div className="flex items-center gap-3 pl-6 border-l border-outline-variant/20">
            <div className="text-right">
              <p className="font-label-sm text-[10px] text-on-surface uppercase tracking-widest font-semibold">
                Alex Thorne
              </p>
              <p className="font-label-sm text-[8px] text-tertiary uppercase tracking-widest font-semibold">
                Premium
              </p>
            </div>
            <div className="relative">
              <Link to="/app/profile" className="block">
                <img
                  alt="User Profile"
                  className="w-10 h-10 rounded-full object-cover border border-outline-variant/20 hover:border-white/40 transition-colors"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuCUhrbSCCyvL4gMnA4wJKdCIy8rVXkUi-RbzyXY0huiYdfDG1hbrZTi-unXTQtHZr7f0ylpE97bhRPNcOAuBoGKXLZ9h6MkdQTX2Ta77wOdUoQSSmQB-gtnME4J5WbRKBfLHRHGbjQ9nvppXanviB6KFDGHhH3UASuuDBy4oIWLee_5z-H844_4Mt1y2nDji5MV2TT9xd2rZAt5yi9SC4sfotZz_y65OxC_DpSb0DD2ZGoAr5G5CWtbh_ouFF8GyRaY91qgXtX9DUof"
                />
              </Link>
              <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-tertiary rounded-full border-2 border-background"></div>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Top Header */}
      <header className="md:hidden fixed top-0 left-0 w-full z-50 bg-background/80 backdrop-blur-xl border-b border-outline-variant/10 h-16 flex items-center justify-between px-margin-mobile">
        <div className="w-10 h-10 flex items-center justify-start text-on-surface">
          {showBack ? (
            <button
              onClick={() => navigate(-1)}
              className="flex items-center justify-center p-1 text-on-surface"
              aria-label="Go back"
            >
              <span className="material-symbols-outlined">arrow_back</span>
            </button>
          ) : (
            <button className="flex items-center justify-center p-1 text-on-surface" aria-label="Menu">
              <span className="material-symbols-outlined">menu</span>
            </button>
          )}
        </div>
        <div className="flex flex-col items-center">
          <Link to="/app" className="font-display text-lg tracking-[0.2em] luxury-text-gradient uppercase font-bold animate-fade-in">
            VOGUE.AI
          </Link>
          <span className="text-[10px] uppercase tracking-[0.2em] text-tertiary font-semibold -mt-1">
            Welcome back, Alex
          </span>
        </div>
        <div className="w-10 h-10 flex items-center justify-end text-on-surface">
          <button className="flex items-center justify-center p-1 text-on-surface" aria-label="Notifications">
            <span className="material-symbols-outlined">notifications</span>
          </button>
        </div>
      </header>
    </>
  );
};

export default Header;
