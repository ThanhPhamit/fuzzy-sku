import { AuthService } from './auth-services';

async function testAuth() {
  const authService = new AuthService();
  try {
    const signInOutput = await AuthService.signIn('fuzzy-sku-poc', 'XXXX');
    console.log('Sign-in successful:', signInOutput);

    const idToken = await authService.getIdToken();
    console.log('ID Token:', idToken);
  } catch (error) {
    console.error(error);
  }
}

testAuth();
