import React from "react";
import Header from "./Header";
import MobileNav from "./MobileNav";
import Breadcrumbs from "./Breadcrumbs";

export const Layout = ({ children, title, showBack, hideNav = false }) => {
  return (
    <div className="flex flex-col min-h-screen">
      <Header title={title} showBack={showBack} />
      <div className="flex-1 flex flex-col w-full relative">
        <main className="flex-1 overflow-y-auto pt-20 md:pt-32 pb-28 md:pb-12 px-4 md:px-8 max-w-7xl mx-auto w-full animate-fade-in">
          <Breadcrumbs />
          {children}
        </main>
        {!hideNav && <MobileNav />}
      </div>
    </div>
  );
};

export default Layout;
