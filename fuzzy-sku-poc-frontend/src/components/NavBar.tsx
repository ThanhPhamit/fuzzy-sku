import React from 'react';
import { NavLink } from 'react-router-dom';

interface NavBarProps {
  userName?: string;
}

const NavBar: React.FC<NavBarProps> = ({ userName }) => {
  return (
    <nav className="navbar">
      <div className="nav-container">
        <div className="nav-brand">
          <NavLink to="/" className="brand-link">
            🔍 Fuzzy SKU Search
          </NavLink>
        </div>

        <div className="nav-links">
          <NavLink
            to="/"
            className={({ isActive }) =>
              isActive ? 'nav-link active' : 'nav-link'
            }
          >
            🏠 Home
          </NavLink>

          {userName ? (
            <>
              <NavLink
                to="/search"
                className={({ isActive }) =>
                  isActive ? 'nav-link active' : 'nav-link'
                }
              >
                🔍 Search
              </NavLink>
              <NavLink
                to="/profile"
                className={({ isActive }) =>
                  isActive ? 'nav-link active' : 'nav-link'
                }
              >
                👤 Profile
              </NavLink>
            </>
          ) : (
            <NavLink
              to="/login"
              className={({ isActive }) =>
                isActive ? 'nav-link active' : 'nav-link'
              }
            >
              🔑 Login
            </NavLink>
          )}
        </div>

        {userName && (
          <div className="nav-user">
            <span className="user-greeting">👋 Welcome, {userName}</span>
          </div>
        )}
      </div>
    </nav>
  );
};

export default NavBar;
