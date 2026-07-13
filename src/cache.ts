import { fetchAllArticles, fetchAllCategories } from './kustomer/client';
import type { Article, Category } from './types';

const CACHE_TTL_MS = 10 * 60 * 1000; // 10 minutes

interface KBSnapshot {
  articles: Article[];
  categories: Category[];
  fetchedAt: number;
}

let snapshot: KBSnapshot | null = null;
let isFetching = false;

async function refresh(): Promise<void> {
  if (isFetching) return;
  isFetching = true;

  try {
    const [articles, categories] = await Promise.all([
      fetchAllArticles(),
      fetchAllCategories(),
    ]);
    snapshot = { articles, categories, fetchedAt: Date.now() };
    console.log(
      `[cache] Refreshed — ${articles.length} articles, ${categories.length} categories`,
    );
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`[cache] Refresh failed — serving stale data if available. ${msg}`);
  } finally {
    isFetching = false;
  }
}

function isStale(): boolean {
  return snapshot !== null && Date.now() - snapshot.fetchedAt > CACHE_TTL_MS;
}

export async function getKBData(): Promise<KBSnapshot> {
  if (snapshot === null) {
    // First request — must block until data is loaded
    await refresh();
    if (snapshot === null) {
      throw new Error(
        'Knowledge base data unavailable — initial Kustomer fetch failed',
      );
    }
    return snapshot;
  }

  if (isStale() && !isFetching) {
    // Serve stale immediately, refresh in background
    refresh().catch(() => {
      // errors already logged inside refresh()
    });
  }

  return snapshot;
}
