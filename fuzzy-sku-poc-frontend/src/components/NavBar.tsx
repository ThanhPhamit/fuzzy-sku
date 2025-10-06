import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { AuthService } from '../services/AuthService';

interface NavBarProps {
  userName?: string;
  authService?: AuthService;
  setUserNameCb?: (userName: string | undefined) => void;
}

const NavBar: React.FC<NavBarProps> = ({
  userName,
  authService,
  setUserNameCb,
}) => {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    if (authService && setUserNameCb) {
      try {
        await authService.logout();
        setUserNameCb(undefined);
        setIsUserMenuOpen(false);
        navigate('/login');
      } catch (error) {
        console.error('Logout failed:', error);
      }
    }
  };

  return (
    <nav className="bg-gradient-to-r from-primary to-primary-400 shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left: Logo and Title */}
          <div className="flex items-center space-x-4">
            <NavLink
              to={userName ? '/search' : '/login'}
              className="flex items-center space-x-3 hover:opacity-90 transition-opacity"
            >
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-2 shadow-lg">
                <span className="text-4xl block">🌿</span>
              </div>
              <span className="text-white font-bold text-2xl tracking-tight">
                Fuzzy SKU POC
              </span>
            </NavLink>
          </div>

          {/* Center: Tagline */}
          <div className="hidden md:block">
            <p className="text-white/95 text-lg font-medium">
              Intelligent Japanese product search
            </p>
          </div>

          {/* Right: User Menu */}
          {userName ? (
            <div className="relative">
              <button
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="flex items-center space-x-3 bg-white/20 hover:bg-white/30 backdrop-blur-sm px-4 py-2 rounded-full transition-all duration-200 border-2 border-white/30"
              >
                <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-primary font-bold text-lg shadow-md">
                  {userName.charAt(0).toUpperCase()}
                </div>
                <span className="text-white font-semibold hidden sm:block">
                  {userName}
                </span>
                <svg
                  className={`w-4 h-4 text-white transition-transform ${
                    isUserMenuOpen ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>

              {isUserMenuOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden animate-fadeIn">
                  <div className="bg-gradient-to-br from-primary-50 to-white p-4 border-b border-gray-100">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-white font-bold text-xl shadow-lg">
                        {userName.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="font-bold text-gray-900">
                          {userName}
                        </div>
                        <div className="text-xs text-primary font-semibold flex items-center space-x-1">
                          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                          <span>Logged in</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full px-4 py-3 text-left text-red-600 hover:bg-red-50 transition-colors flex items-center space-x-2 font-semibold"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                      />
                    </svg>
                    <span>Logout</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <NavLink
              to="/login"
              className="bg-white text-primary px-6 py-2 rounded-full font-semibold hover:bg-opacity-90 transition-all duration-200 shadow-md"
            >
              🔑 Login
            </NavLink>
          )}
        </div>
      </div>
    </nav>
  );
};

export default NavBar;
