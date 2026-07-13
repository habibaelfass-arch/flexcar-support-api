import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import { config } from './config';
import categoriesRouter from './routes/categories';
import articlesRouter from './routes/articles';
import { getKBData } from './cache';

const app = express();

// Health check registered before CORS — Railway probes send no Origin header
app.get('/health', (_req: Request, res: Response) => {
  res.json({ status: 'ok' });
});

app.use(
  cors({
    origin(origin, callback) {
      if (!origin) return callback(null, true);
      if (config.allowedOrigins.includes(origin)) return callback(null, true);
      console.warn(`[cors] Rejected origin: ${origin}`);
      callback(new Error(`CORS: origin not allowed`));
    },
    methods: ['GET'],
  }),
);

app.use(express.json());

app.use('/api/categories', categoriesRouter);
app.use('/api/articles', articlesRouter);

// eslint-disable-next-line @typescript-eslint/no-unused-vars
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  console.error('[error]', err.message);
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(config.port, () => {
  console.log(
    `[startup] flexcar-support-api on port ${config.port} (org: ${config.kustomerOrgSubdomain})`,
  );
  getKBData().catch((err: Error) => {
    console.error('[startup] Cache pre-warm failed:', err.message);
  });
});
