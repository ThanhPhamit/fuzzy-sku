import './App.css';
import {
  Outlet,
  RouterProvider,
  createBrowserRouter,
  NavLink,
  Navigate,
} from 'react-router-dom';
import NavBar from './components/NavBar';
import { useState, useEffect } from 'react';
import LoginComponent from './components/LoginComponent';
import SearchComponent from './components/SearchComponent';
import { AuthService } from './services/AuthService';
import { SearchService } from './services/SearchService';

const authService = new AuthService();
const searchService = new SearchService(authService);

function App() {
  const [userName, setUserName] = useState<string | undefined>(undefined);

  useEffect(() => {
    // Check if user is already logged in on app start
    if (authService.isAuthorized()) {
      const currentUser = authService.getUserName();
      if (currentUser) {
        setUserName(currentUser);
      }
    }
  }, []);

  // Protected route component
  const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    if (!authService.isAuthorized()) {
      return <Navigate to="/login" replace />;
    }
    return <>{children}</>;
  };

  const router = createBrowserRouter([
    {
      element: (
        <>
          <NavBar userName={userName} />
          <Outlet />
        </>
      ),
      children: [
        {
          path: '/',
          element: (
            <div className="home-page">
              <div className="page-header">
                <h1 className="page-title">🔍 Welcome to Fuzzy SKU Search</h1>
                <p className="page-subtitle">
                  Advanced Japanese product search with fuzzy matching
                  capabilities
                </p>
              </div>
              <div className="home-actions">
                {userName ? (
                  <NavLink to="/search" className="btn-primary home-btn">
                    🔍 Start Searching
                  </NavLink>
                ) : (
                  <NavLink to="/login" className="btn-primary home-btn">
                    🔑 Login to Search
                  </NavLink>
                )}
              </div>
              <div className="home-features">
                <div className="feature-card">
                  <h3>🎯 Fuzzy Matching</h3>
                  <p>
                    Find products even with partial or approximate Japanese text
                  </p>
                </div>
                <div className="feature-card">
                  <h3>⚡ Fast Search</h3>
                  <p>Powered by OpenSearch for lightning-fast results</p>
                </div>
                <div className="feature-card">
                  <h3>🔒 Secure Access</h3>
                  <p>AWS Cognito authentication for secure access</p>
                </div>
              </div>
            </div>
          ),
        },
        {
          path: '/login',
          element: (
            <LoginComponent
              authService={authService}
              setUserNameCb={setUserName}
              onLoginSuccess={() => {
                // Redirect to search page after successful login
                window.location.href = '/search';
              }}
            />
          ),
        },
        {
          path: '/search',
          element: (
            <ProtectedRoute>
              <SearchComponent searchService={searchService} />
            </ProtectedRoute>
          ),
        },
        {
          path: '/profile',
          element: (
            <ProtectedRoute>
              <div className="profile-page">
                <div className="page-header">
                  <h1 className="page-title">👤 Profile</h1>
                  <p className="page-subtitle">
                    {userName ? `Welcome, ${userName}!` : 'User Profile'}
                  </p>
                </div>
                <div className="form-container">
                  <div className="profile-info">
                    <h3>Account Information</h3>
                    <div className="info-item">
                      <strong>Username:</strong> {userName}
                    </div>
                    <div className="info-item">
                      <strong>Authentication Status:</strong>
                      <span className="status-badge active">✅ Active</span>
                    </div>
                  </div>

                  <div className="profile-actions">
                    <button
                      onClick={() =>
                        authService.logout().then(() => {
                          setUserName(undefined);
                          window.location.href = '/login';
                        })
                      }
                      className="btn-secondary"
                    >
                      🚪 Logout
                    </button>
                  </div>
                </div>
              </div>
            </ProtectedRoute>
          ),
        },
      ],
    },
  ]);

  return (
    <div className="wrapper">
      <RouterProvider router={router} />
    </div>
  );
}

export default App;
