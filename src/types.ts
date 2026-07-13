export interface Article {
  id: string;
  title: string;
  slug: string;
  categoryId: string;
  excerpt: string;
  bodyHtml: string;
  updatedAt: string;
}

export interface Category {
  id: string;
  slug: string;
  name: string;
  description: string;
}
