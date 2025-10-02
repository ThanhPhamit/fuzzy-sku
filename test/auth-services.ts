import { Amplify } from 'aws-amplify';
import { SignInOutput, fetchAuthSession, signIn } from '@aws-amplify/auth';

const awsRegion = process.env.AWS_REGION;

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: 'ap-northeast-3_2TsX1tIxD',
      userPoolClientId: '51331lo6kcq9a2lu5r2undcpt6',
      identityPoolId: 'ap-northeast-3:a9ca4589-2a93-409b-a19d-ffe289513559',
    },
  },
});

export class AuthService {
  static async signIn(
    username: string,
    password: string,
  ): Promise<SignInOutput> {
    try {
      const signInOutput: SignInOutput = await signIn({
        username,
        password,
        options: {
          authFlowType: 'USER_PASSWORD_AUTH',
        },
      });
      return signInOutput;
    } catch (error) {
      throw new Error(`Sign-in failed: ${error}`);
    }
  }

  public async getIdToken(): Promise<string | undefined> {
    try {
      const session = await fetchAuthSession();
      return session.tokens?.idToken?.toString();
    } catch (error) {
      throw new Error(`Failed to get ID token: ${error}`);
    }
  }
}
