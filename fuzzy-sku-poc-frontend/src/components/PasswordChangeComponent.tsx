import React, { useState } from 'react';
import { AuthService } from '../services/AuthService';

interface PasswordChangeComponentProps {
  user: any; // CognitoUser with challenge
  authService: AuthService;
  onPasswordChanged: (user: any) => void;
  onCancel: () => void;
}

export const PasswordChangeComponent: React.FC<
  PasswordChangeComponentProps
> = ({ user, authService, onPasswordChanged, onCancel }) => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate passwords match
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    // Validate password strength
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (
      !/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/.test(
        newPassword,
      )
    ) {
      setError(
        'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character',
      );
      return;
    }

    setLoading(true);

    try {
      // Complete the NEW_PASSWORD_REQUIRED challenge using AuthService
      const completedUser = await authService.completeNewPasswordChallenge(
        user,
        newPassword,
      );
      onPasswordChanged(completedUser);
    } catch (err: any) {
      console.error('Password change error:', err);
      setError(err.message || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-green-100 to-primary-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden border-4 border-primary/20">
          {/* Header with gradient */}
          <div className="bg-gradient-to-r from-primary to-primary-400 p-8 text-center">
            <div className="inline-block bg-white/90 backdrop-blur-sm rounded-3xl p-5 shadow-2xl mb-3">
              <div className="text-6xl">🔑</div>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2 mt-3">
              Change Password
            </h1>
            <p className="text-white/90 text-lg font-lg">
              Your account requires a new password
            </p>
          </div>

          {/* Form */}
          <div className="p-8">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Set New Password
              </h2>
              <p className="text-gray-600">
                Create a secure password to continue
              </p>
            </div>

            <form onSubmit={handlePasswordChange} className="space-y-6">
              <div>
                <label
                  htmlFor="new-password"
                  className="block text-sm font-bold text-gray-700 mb-2"
                >
                  New Password
                </label>
                <input
                  id="new-password"
                  name="new-password"
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  disabled={loading}
                  placeholder="Enter your new password"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-primary focus:ring-4 focus:ring-primary/20 transition-all duration-200 outline-none"
                  autoComplete="new-password"
                />
              </div>

              <div>
                <label
                  htmlFor="confirm-password"
                  className="block text-sm font-bold text-gray-700 mb-2"
                >
                  Confirm Password
                </label>
                <input
                  id="confirm-password"
                  name="confirm-password"
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={loading}
                  placeholder="Confirm your new password"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-primary focus:ring-4 focus:ring-primary/20 transition-all duration-200 outline-none"
                  autoComplete="new-password"
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
                disabled={loading || !newPassword || !confirmPassword}
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
                    Changing Password...
                  </span>
                ) : (
                  '🔑 Change Password'
                )}
              </button>

              <button
                type="button"
                onClick={onCancel}
                disabled={loading}
                className="w-full bg-white hover:bg-gray-50 border-2 border-gray-300 hover:border-gray-400 text-gray-700 font-bold py-4 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-105 disabled:hover:scale-100 disabled:cursor-not-allowed text-lg"
              >
                ❌ Cancel
              </button>
            </form>

            {/* Password Requirements */}
            <div className="mt-8 pt-6 border-t-2 border-gray-100">
              <div className="bg-primary-50 rounded-xl p-4">
                <p className="font-bold text-primary-700 mb-3 flex items-center">
                  <span className="text-xl mr-2">📋</span>
                  Password Requirements:
                </p>
                <ul className="text-sm text-primary-600 space-y-2">
                  <li className="flex items-center">
                    <span className="text-primary-500 mr-2">✓</span>
                    At least 8 characters long
                  </li>
                  <li className="flex items-center">
                    <span className="text-primary-500 mr-2">✓</span>
                    Contains uppercase and lowercase letters
                  </li>
                  <li className="flex items-center">
                    <span className="text-primary-500 mr-2">✓</span>
                    Contains at least one number
                  </li>
                  <li className="flex items-center">
                    <span className="text-primary-500 mr-2">✓</span>
                    Contains at least one special character (@$!%*?&)
                  </li>
                </ul>
              </div>
            </div>

            <div className="mt-6 text-center">
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
