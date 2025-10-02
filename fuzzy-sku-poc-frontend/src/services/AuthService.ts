import { type CognitoUser } from '@aws-amplify/auth';
import { Amplify, Auth } from 'aws-amplify';
import { CognitoIdentityClient } from '@aws-sdk/client-cognito-identity';
import { fromCognitoIdentityPool } from '@aws-sdk/credential-providers';
import config from '../config';

// Environment variables
const { AWS_REGION, USER_POOL_ID, USER_POOL_CLIENT_ID, IDENTITY_POOL_ID } =
  config;

Amplify.configure({
  Auth: {
    mandatorySignIn: false,
    region: AWS_REGION,
    userPoolId: USER_POOL_ID,
    userPoolWebClientId: USER_POOL_CLIENT_ID,
    identityPoolId: IDENTITY_POOL_ID,
    authenticationFlowType: 'USER_PASSWORD_AUTH',
  },
});

interface AuthState {
  user: CognitoUser | null;
  jwtToken: string | null;
  accessToken: string | null;
  refreshToken: string | null;
  expirationTime: number | null;
}

export class AuthService {
  private authState: AuthState = {
    user: null,
    jwtToken: null,
    accessToken: null,
    refreshToken: null,
    expirationTime: null,
  };
  private temporaryCredentials: object | undefined;
  private refreshTimer: NodeJS.Timeout | null = null;

  constructor() {
    // Load auth state from localStorage on initialization
    this.loadAuthState();
    // Set up automatic token refresh if user is logged in
    this.setupTokenRefresh();
  }

  public isAuthorized(): boolean {
    return this.authState.user !== null && this.isTokenValid();
  }

  public isTokenValid(): boolean {
    if (!this.authState.expirationTime) return false;
    // Check if token expires in the next 5 minutes (300000 ms)
    return Date.now() < this.authState.expirationTime - 300000;
  }

  public async login(
    userName: string,
    password: string,
  ): Promise<CognitoUser | undefined> {
    try {
      const user = (await Auth.signIn(userName, password)) as CognitoUser;
      const session = user.getSignInUserSession();

      if (session) {
        this.authState = {
          user,
          jwtToken: session.getIdToken().getJwtToken(),
          accessToken: session.getAccessToken().getJwtToken(),
          refreshToken: session.getRefreshToken().getToken(),
          expirationTime: session.getAccessToken().getExpiration() * 1000, // Convert to milliseconds
        };

        // Save to localStorage
        this.saveAuthState();

        // Setup automatic token refresh
        this.setupTokenRefresh();

        return user;
      }
      return undefined;
    } catch (error) {
      console.error('Login error:', error);
      return undefined;
    }
  }

  public async logout(): Promise<void> {
    try {
      if (this.authState.user) {
        await Auth.signOut();
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear auth state regardless of signOut success
      this.clearAuthState();
    }
  }

  public getAccessToken(): string | null {
    return this.isTokenValid() ? this.authState.accessToken : null;
  }

  public getJwtToken(): string | null {
    return this.isTokenValid() ? this.authState.jwtToken : null;
  }

  public async getTemporaryCredentials() {
    if (this.temporaryCredentials && this.isTokenValid()) {
      return this.temporaryCredentials;
    }

    if (!this.isTokenValid()) {
      await this.refreshTokenIfNeeded();
    }

    this.temporaryCredentials = await this.generateTemporaryCredentials();
    return this.temporaryCredentials;
  }

  public getUserName(): string | undefined {
    return this.authState.user?.getUsername();
  }

  private async refreshTokenIfNeeded(): Promise<void> {
    if (this.isTokenValid()) return;

    try {
      if (this.authState.user && this.authState.refreshToken) {
        const user = await Auth.currentAuthenticatedUser();
        const session = user.getSignInUserSession();

        if (session) {
          this.authState = {
            ...this.authState,
            user,
            jwtToken: session.getIdToken().getJwtToken(),
            accessToken: session.getAccessToken().getJwtToken(),
            refreshToken: session.getRefreshToken().getToken(),
            expirationTime: session.getAccessToken().getExpiration() * 1000,
          };

          this.saveAuthState();
          this.setupTokenRefresh();
        }
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      // If refresh fails, logout the user
      await this.logout();
    }
  }

  private setupTokenRefresh(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    if (this.authState.expirationTime) {
      // Refresh token 5 minutes before expiration
      const refreshTime = this.authState.expirationTime - Date.now() - 300000;

      if (refreshTime > 0) {
        this.refreshTimer = setTimeout(() => {
          this.refreshTokenIfNeeded();
        }, refreshTime);
      }
    }
  }

  private saveAuthState(): void {
    try {
      const stateToSave = {
        userName: this.authState.user?.getUsername(),
        expirationTime: this.authState.expirationTime,
      };
      localStorage.setItem('authState', JSON.stringify(stateToSave));
    } catch (error) {
      console.error('Failed to save auth state:', error);
    }
  }

  private loadAuthState(): void {
    try {
      const savedState = localStorage.getItem('authState');
      if (savedState) {
        const parsed = JSON.parse(savedState);

        // Check if the saved session is still valid
        if (
          parsed.expirationTime &&
          Date.now() < parsed.expirationTime - 300000
        ) {
          // Try to restore the session
          this.restoreSession();
        } else {
          // Session expired, clear it
          localStorage.removeItem('authState');
        }
      }
    } catch (error) {
      console.error('Failed to load auth state:', error);
      localStorage.removeItem('authState');
    }
  }

  private async restoreSession(): Promise<void> {
    try {
      const user = await Auth.currentAuthenticatedUser();
      const session = user.getSignInUserSession();

      if (session) {
        this.authState = {
          user,
          jwtToken: session.getIdToken().getJwtToken(),
          accessToken: session.getAccessToken().getJwtToken(),
          refreshToken: session.getRefreshToken().getToken(),
          expirationTime: session.getAccessToken().getExpiration() * 1000,
        };
      }
    } catch (error) {
      console.error('Failed to restore session:', error);
      localStorage.removeItem('authState');
    }
  }

  private clearAuthState(): void {
    this.authState = {
      user: null,
      jwtToken: null,
      accessToken: null,
      refreshToken: null,
      expirationTime: null,
    };
    this.temporaryCredentials = undefined;

    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }

    localStorage.removeItem('authState');
  }

  private async generateTemporaryCredentials() {
    const cognitoIdentityPool = `cognito-idp.${AWS_REGION}.amazonaws.com/${USER_POOL_ID}`;
    const cognitoIdentity = new CognitoIdentityClient({
      credentials: fromCognitoIdentityPool({
        clientConfig: {
          region: AWS_REGION,
        },
        identityPoolId: IDENTITY_POOL_ID,
        logins: {
          [cognitoIdentityPool]: this.authState.jwtToken!,
        },
      }),
    });
    const credentials = await cognitoIdentity.config.credentials();
    return credentials;
  }
}
