import { config } from '../config';
import type { Article, Category } from '../types';
import type {
  KustomerArticle,
  KustomerCategory,
  KustomerListResponse,
} from './types';

const KUSTOMER_BASE = 'https://api.kustomerapp.com';

async function kustomerFetch<T>(path: string): Promise<KustomerListResponse<T>> {
  const url = `${KUSTOMER_BASE}${path}`;

  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${config.kustomerApiKey}`,
      'Content-Type': 'application/json',
    },
  });

  if (!res.ok) {
    throw new Error(
      `Kustomer API responded ${res.status} ${res.statusText} for ${path}`,
    );
  }

  return res.json() as Promise<KustomerListResponse<T>>;
}

function mapArticle(item: KustomerArticle): Article {
  const version = item.attributes.langVersions?.en_us?.currentVersion?.id;
  return {
    id: item.id,
    title: item.attributes.title,
    slug: version?.slug ?? '',
    categoryId: item.attributes.categories[0]?.id ?? '',
    excerpt: item.attributes.metaDescription,
    bodyHtml: version?.htmlBody ?? '',
    updatedAt: item.attributes.updatedAt,
  };
}

function mapCategory(item: KustomerCategory): Category {
  const lang = item.attributes.langs.en_us;
  return {
    id: item.id,
    slug: lang.slug,
    name: lang.title,
    description: lang.description,
  };
}

export async function fetchAllArticles(): Promise<Article[]> {
  const res = await kustomerFetch<KustomerArticle>(
    '/v1/kb/articles?includeLang=en_us&includeBody=true&pageSize=500',
  );

  return res.data
    .filter(
      (item) =>
        item.attributes.status === 'published' &&
        item.attributes.scope === 'public' &&
        item.attributes.deleted !== true,
    )
    .map(mapArticle)
    .filter((a) => a.slug !== '');
}

export async function fetchAllCategories(): Promise<Category[]> {
  const res = await kustomerFetch<KustomerCategory>(
    '/v1/kb/categories?pageSize=200',
  );

  return res.data
    .filter(
      (item) =>
        item.attributes.published === true &&
        item.attributes.root === false &&
        item.attributes.langs.en_us.disabled === false,
    )
    .map(mapCategory);
}
