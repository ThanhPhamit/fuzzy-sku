import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthService } from '../services/AuthService';
import { PasswordChangeComponent } from './PasswordChangeComponent';

interface LoginComponentProps {
  authService: AuthService;
  setUserNameCb: (userName: string) => void;
}

const LoginComponent: React.FC<LoginComponentProps> = ({
  authService,
  setUserNameCb,
}) => {
  const [userName, setUserName] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userNeedingPasswordChange, setUserNeedingPasswordChange] =
    useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is already logged in - only run once on mount
    const checkAuth = () => {
      if (authService.isAuthorized()) {
        const currentUser = authService.getUserName();
        if (currentUser) {
          setUserNameCb(currentUser);
          navigate('/search', { replace: true });
        }
      }
    };
    checkAuth();
  }, []); // Empty dependency array - only run once on mount

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const user = await authService.login(userName, password);

      if (user) {
        // Check if user needs to change password
        if (user.challengeName === 'NEW_PASSWORD_REQUIRED') {
          setUserNeedingPasswordChange(user);
          setLoading(false);
          return;
        }

        // Normal successful login
        const currentUserName = authService.getUserName();
        if (currentUserName) {
          setUserNameCb(currentUserName);
          navigate('/search');
        }
      } else {
        setError('Invalid username or password');
      }
    } catch (error: any) {
      console.error('Login failed:', error);
      if (error.code === 'UserNotConfirmedException') {
        setError('Your account is not confirmed. Please check your email.');
      } else if (error.code === 'NotAuthorizedException') {
        setError('Invalid username or password');
      } else if (error.code === 'UserNotFoundException') {
        setError('User not found. Please check your username.');
      } else {
        setError('Login failed. Please check your credentials and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChanged = (user: any) => {
    // Password changed successfully, complete login
    const currentUserName = authService.getUserName();
    if (currentUserName) {
      setUserNameCb(currentUserName);
      setUserNeedingPasswordChange(null);
      navigate('/search');
    }
  };

  const handlePasswordChangeCancel = () => {
    // User cancelled password change
    setUserNeedingPasswordChange(null);
    setError('Password change cancelled. Please try again.');
  };

  // If user needs to change password, show password change component
  if (userNeedingPasswordChange) {
    return (
      <PasswordChangeComponent
        user={userNeedingPasswordChange}
        authService={authService}
        onPasswordChanged={handlePasswordChanged}
        onCancel={handlePasswordChangeCancel}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-green-100 to-primary-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden border-4 border-primary/20">
          {/* Header with gradient */}
          <div className="bg-gradient-to-r from-primary to-primary-400 p-8 text-center">
            <div className="inline-block bg-white/90 backdrop-blur-sm rounded-3xl p-5 shadow-2xl mb-3">
              <div className="text-6xl">🌿</div>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2 mt-3">
              Fuzzy SKU POC
            </h1>
            <p className="text-white/90 text-lg font-lg">
              Intelligent Japanese product search
            </p>
          </div>

          {/* Form */}
          <div className="p-8">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Welcome Back
              </h2>
              <p className="text-gray-600">
                Sign in to access the search system
              </p>
            </div>

            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <label
                  htmlFor="username"
                  className="block text-sm font-bold text-gray-700 mb-2"
                >
                  Email
                </label>
                <input
                  id="username"
                  type="text"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  required
                  disabled={loading}
                  placeholder="Enter your email"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-primary focus:ring-4 focus:ring-primary/20 transition-all duration-200 outline-none"
                  autoComplete="username email"
                />
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-bold text-gray-700 mb-2"
                >
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={loading}
                  placeholder="Enter your password"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-primary focus:ring-4 focus:ring-primary/20 transition-all duration-200 outline-none"
                  autoComplete="current-password"
                />
              </div>

              {error && (
                <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-lg">
                  <div className="flex items-center">
                    <span className="text-xl mr-2">⚠️</span>
                    <span className="font-medium">{error}</span>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !userName || !password}
                className="w-full bg-primary hover:bg-primary-600 disabled:bg-gray-300 text-white font-bold py-4 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-105 disabled:hover:scale-100 disabled:cursor-not-allowed text-lg"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Signing in...
                  </span>
                ) : (
                  '🔑 Sign In'
                )}
              </button>
            </form>

            <div className="mt-8 pt-6 border-t-2 border-gray-100 text-center">
              <p className="text-gray-600 text-sm font-medium flex items-center justify-center">
                <span className="mr-2">🔒</span>
                Secure authentication powered by AWS Cognito
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginComponent;
