import { Router, Request, Response, NextFunction } from 'express';
import { getKBData } from '../cache';

const router = Router();

router.get('/', async (_req: Request, res: Response, next: NextFunction) => {
  try {
    const { categories } = await getKBData();
    res.json(categories);
  } catch (err) {
    next(err);
  }
});

router.get(
  '/:categorySlug/articles',
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { categorySlug } = req.params;
      const { categories, articles } = await getKBData();

      const category = categories.find((c) => c.slug === categorySlug);
      if (!category) {
        res.status(404).json({ error: `Category not found: ${categorySlug}` });
        return;
      }

      res.json(articles.filter((a) => a.categoryId === category.id));
    } catch (err) {
      next(err);
    }
  },
);

export default router;
