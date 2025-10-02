import React, { useState, useEffect } from 'react';
import { AuthService } from '../services/AuthService';

interface LoginComponentProps {
  authService: AuthService;
  setUserNameCb: (userName: string) => void;
  onLoginSuccess?: () => void;
}

const LoginComponent: React.FC<LoginComponentProps> = ({
  authService,
  setUserNameCb,
  onLoginSuccess,
}) => {
  const [userName, setUserName] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // Check if user is already logged in
    if (authService.isAuthorized()) {
      const currentUser = authService.getUserName();
      if (currentUser) {
        setUserNameCb(currentUser);
        setIsLoggedIn(true);
      }
    }
  }, [authService, setUserNameCb]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const user = await authService.login(userName, password);

      if (user) {
        const currentUserName = authService.getUserName();
        if (currentUserName) {
          setUserNameCb(currentUserName);
          setIsLoggedIn(true);

          // Clear form
          setUserName('');
          setPassword('');

          // Call success callback
          if (onLoginSuccess) {
            onLoginSuccess();
          }
        }
      } else {
        setError('Invalid username or password');
      }
    } catch (error) {
      console.error('Login failed:', error);
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    setLoading(true);
    try {
      await authService.logout();
      setUserNameCb('');
      setIsLoggedIn(false);
      setUserName('');
      setPassword('');
      setError(null);
    } catch (error) {
      console.error('Logout failed:', error);
      setError('Logout failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (isLoggedIn) {
    const currentUser = authService.getUserName();
    return (
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <h2>👤 Welcome!</h2>
            <p>
              You are logged in as <strong>{currentUser}</strong>
            </p>
          </div>

          <div className="login-actions">
            <button
              type="button"
              onClick={handleLogout}
              disabled={loading}
              className="btn-secondary logout-btn"
            >
              {loading ? 'Logging out...' : '🚪 Logout'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h2>🔐 Login</h2>
          <p>Sign in to your account to access the fuzzy search</p>
        </div>

        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              required
              disabled={loading}
              placeholder="Enter your username"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
              placeholder="Enter your password"
              className="form-input"
            />
          </div>

          {error && <div className="error-message">⚠️ {error}</div>}

          <button
            type="submit"
            disabled={loading || !userName || !password}
            className="btn-primary login-btn"
          >
            {loading ? '🔄 Signing in...' : '🔑 Sign In'}
          </button>
        </form>

        <div className="login-footer">
          <p>Don't have an account? Contact your administrator.</p>
        </div>
      </div>
    </div>
  );
};

export default LoginComponent;
