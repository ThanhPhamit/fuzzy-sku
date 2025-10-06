export interface Config {
  AWS_REGION: string;
  USER_POOL_ID: string;
  USER_POOL_CLIENT_ID: string;
  IDENTITY_POOL_ID: string;
  API_BASE_URL: string;
}

const config: Config = {
  AWS_REGION: import.meta.env.VITE_AWS_REGION || 'ap-northeast-3',
  USER_POOL_ID: import.meta.env.VITE_USER_POOL_ID || 'ap-northeast-3_2TsX1tIxD',
  USER_POOL_CLIENT_ID:
    import.meta.env.VITE_USER_POOL_CLIENT_ID || '51331lo6kcq9a2lu5r2undcpt6',
  IDENTITY_POOL_ID:
    import.meta.env.VITE_IDENTITY_POOL_ID ||
    'ap-northeast-3:a9ca4589-2a93-409b-a19d-ffe289513559',
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || '',
};

export default config;
