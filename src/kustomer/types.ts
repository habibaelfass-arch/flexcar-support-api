// Raw shapes returned by https://api.kustomerapp.com/v1/kb/*
// Verified against live Kustomer responses — do not guess field names here.

export interface KustomerArticleVersion {
  _id: string;
  slug: string;
  htmlBody: string;
  title: string;
  status: string;
  scope: string;
  createdAt: string;
  updatedAt: string;
}

export interface KustomerArticleAttributes {
  title: string;
  status: string;
  scope: string;
  updatedAt: string;
  metaDescription: string;
  categories: Array<{ id: string; knowledgeBase: string }>;
  deleted?: boolean;
  langVersions?: {
    en_us?: {
      currentVersion?: {
        id?: KustomerArticleVersion;
      } | null;
    } | null;
  } | null;
}

export interface KustomerArticle {
  type: string;
  id: string;
  attributes: KustomerArticleAttributes;
}

export interface KustomerCategoryLang {
  title: string;
  slug: string;
  description: string;
  disabled: boolean;
}

export interface KustomerCategoryAttributes {
  langs: {
    en_us: KustomerCategoryLang;
  };
  published: boolean;
  root: boolean;
  updatedAt: string;
}

export interface KustomerCategory {
  type: string;
  id: string;
  attributes: KustomerCategoryAttributes;
}

export interface KustomerListResponse<T> {
  meta: { pageSize: number; page: number };
  links: { self: string; next: string | null };
  data: T[];
}
