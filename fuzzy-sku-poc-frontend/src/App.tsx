import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import NavBar from './components/NavBar';
import { useState, useEffect } from 'react';
import LoginComponent from './components/LoginComponent';
import SearchComponent from './components/SearchComponent';
import { AuthService } from './services/AuthService';
import { SearchService } from './services/SearchService';

const authService = new AuthService();
const searchService = new SearchService(authService);

// Protected route component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  if (!authService.isAuthorized()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-white">
      <BrowserRouter>
        <Routes>
          {/* Login route - no navbar */}
          <Route
            path="/login"
            element={
              userName ? (
                <Navigate to="/search" replace />
              ) : (
                <LoginComponent
                  authService={authService}
                  setUserNameCb={setUserName}
                />
              )
            }
          />

          {/* Home route */}
          <Route
            path="/"
            element={
              userName ? (
                <Navigate to="/search" replace />
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />

          {/* Search route with navbar */}
          <Route
            path="/search"
            element={
              <ProtectedRoute>
                <>
                  <NavBar
                    userName={userName}
                    authService={authService}
                    setUserNameCb={setUserName}
                  />
                  <SearchComponent searchService={searchService} />
                </>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
