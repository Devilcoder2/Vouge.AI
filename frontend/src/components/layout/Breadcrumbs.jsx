import React from "react";
import { Link, useLocation } from "react-router-dom";

export const Breadcrumbs = () => {
  const location = useLocation();
  const { pathname } = location;

  // Don't show breadcrumbs on landing page or the core app home dashboard
  if (pathname === "/" || pathname === "/app") return null;

  // Map route segments to readable breadcrumb labels and links
  const getBreadcrumbs = (path) => {
    // Strip "/app" prefix if it exists for clean breadcrumbs matching
    const relativePath = path.startsWith("/app") ? path.slice(4) : path;
    const segments = relativePath.split("/").filter(Boolean);
    const crumbs = [{ label: "Home", url: "/app" }];

    if (segments.length === 0) return crumbs;

    if (segments[0] === "wardrobe") {
      crumbs.push({ label: "Wardrobe", url: null });
    } else if (segments[0] === "chat") {
      crumbs.push({ label: "AI Stylist", url: null });
    } else if (segments[0] === "planner") {
      crumbs.push({ label: "Planner", url: null });
    } else if (segments[0] === "discover") {
      crumbs.push({ label: "Discovery Feed", url: null });
    } else if (segments[0] === "profile") {
      crumbs.push({ label: "Profile", url: null });
    } else if (segments[0] === "inventory") {
      crumbs.push({ label: "Wardrobe", url: "/app/wardrobe" });
      if (segments[1]) {
        const categoryLabel =
          segments[1].charAt(0).toUpperCase() + segments[1].slice(1);
        crumbs.push({ label: categoryLabel, url: null });
      }
    } else if (segments[0] === "item") {
      crumbs.push({ label: "Wardrobe", url: "/app/wardrobe" });
      if (segments[1]) {
        const categoryLabel =
          segments[1].charAt(0).toUpperCase() + segments[1].slice(1);
        crumbs.push({ label: categoryLabel, url: `/app/inventory/${segments[1]}` });
      }
      if (segments[2]) {
        crumbs.push({ label: "Item Details", url: null });
      }
    } else if (segments[0] === "category" && segments[1] === "new") {
      crumbs.push({ label: "Wardrobe", url: "/app/wardrobe" });
      crumbs.push({ label: "New Category", url: null });
    } else if (segments[0] === "outfit") {
      crumbs.push({ label: "Recommended Outfits", url: "/app/recommendations" });
      crumbs.push({ label: "Curation Manifest", url: null });
    } else if (segments[0] === "recommendations") {
      crumbs.push({ label: "Recommended Outfits", url: null });
    } else if (segments[0] === "analysis") {
      crumbs.push({ label: "Wardrobe", url: "/app/wardrobe" });
      crumbs.push({ label: "Analysis", url: null });
    } else {
      // General dynamic fallback
      segments.forEach((seg, index) => {
        const label = seg.charAt(0).toUpperCase() + seg.slice(1);
        const url = "/app/" + segments.slice(0, index + 1).join("/");
        const isLast = index === segments.length - 1;
        crumbs.push({ label, url: isLast ? null : url });
      });
    }

    return crumbs;
  };

  const crumbs = getBreadcrumbs(pathname);

  return (
    <nav className="flex items-center gap-1 text-[11px] text-on-surface-variant/70 mb-6 font-medium tracking-wider uppercase select-none">
      {crumbs.map((crumb, index) => {
        const isLast = index === crumbs.length - 1;
        return (
          <React.Fragment key={index}>
            {index > 0 && (
              <span className="material-symbols-outlined text-[16px] opacity-40 mx-1">
                chevron_right
              </span>
            )}
            {crumb.url && !isLast ? (
              <Link
                to={crumb.url}
                className="hover:text-primary transition-colors flex items-center gap-1"
              >
                {crumb.label === "Home" && (
                  <span className="material-symbols-outlined text-[13px] -mt-[1px]">
                    home
                  </span>
                )}
                <span>{crumb.label}</span>
              </Link>
            ) : (
              <span className={isLast ? "text-on-surface font-semibold" : ""}>
                {crumb.label}
              </span>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};

export default Breadcrumbs;
