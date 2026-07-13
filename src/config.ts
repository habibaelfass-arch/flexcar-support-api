import 'dotenv/config';

function requireEnv(name: string): string {
  const val = process.env[name];
  if (!val) {
    console.error(`[startup] Missing required environment variable: ${name}`);
    process.exit(1);
  }
  return val;
}

export const config = {
  port: parseInt(process.env.PORT ?? '3000', 10),
  kustomerApiKey: requireEnv('KUSTOMER_API_KEY'),
  kustomerOrgSubdomain: requireEnv('KUSTOMER_ORG_SUBDOMAIN'),
  allowedOrigins: requireEnv('ALLOWED_ORIGIN')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean),
} as const;
