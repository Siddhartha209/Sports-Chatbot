import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import "./Navbar.css";

const Navbar = ({ collapsed, setCollapsed }) => {
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem("darkMode") === "true";
  });

  const location = useLocation();

  useEffect(() => {
    // Apply dark/light class to body
    if (darkMode) {
      document.body.classList.add("dark-mode");
      document.body.classList.remove("light-mode");
    } else {
      document.body.classList.add("light-mode");
      document.body.classList.remove("dark-mode");
    }
    localStorage.setItem("darkMode", darkMode);
  }, [darkMode]);

  useEffect(() => {
    // On mobile, collapse sidebar after navigation
    if (window.innerWidth <= 768) {
      setCollapsed(true);
    }
  }, [location, setCollapsed]);

  const toggleSidebar = () => setCollapsed(!collapsed);

  const handleToggleMode = () => setDarkMode((prev) => !prev);

  // ✅ Clear Chat handler
  const handleClearChat = () => {
    if (location.pathname === "/premier-league") {
      localStorage.removeItem("plMessages");
    } else if (location.pathname === "/ufc") {
      localStorage.removeItem("ufcMessages");
    }
    // Reload page to reflect cleared chat immediately
    window.location.reload();
  };

  return (
    <div className={`sidebar ${collapsed ? "collapsed" : "expanded"}`}>
      {/* Hamburger always visible on mobile */}
      <div className="toggle-btn" onClick={toggleSidebar}>
        ☰
      </div>
      <div className="logo">{!collapsed && "Sports"}</div>
      <ul className="nav-links">
        <li>
          <Link to="/">
            <img src="/img/home.png" alt="Home" className="nav-icon" />
            {!collapsed && <span>Home</span>}
          </Link>
        </li>
        <li>
          <Link to="/premier-league">
            <img src="/img/football_icon.png" alt="Premier League" className="nav-icon" />
            {!collapsed && <span>Premier League</span>}
          </Link>
        </li>
        <li>
          <Link to="/ufc">
            <img src="/img/ufc_logo.png" alt="UFC" className="nav-icon" />
            {!collapsed && <span>UFC</span>}
          </Link>
        </li>
      </ul>

      {/* ✅ Clear Chat button above dark/light mode */}
      {!collapsed && location.pathname !== "/" && (
        <button className="clear-chat-btn" onClick={handleClearChat}>
          Clear Chat
        </button>
      )}

      <div className="mode-toggle-container">
        <label className="mode-switch">
          <input
            type="checkbox"
            checked={darkMode}
            onChange={handleToggleMode}
          />
          <span className="slider"></span>
        </label>
        {!collapsed && (
          <span className="mode-label">
            {darkMode ? "Dark Mode" : "Light Mode"}
          </span>
        )}
      </div>
    </div>
  );
};

export default Navbar;
