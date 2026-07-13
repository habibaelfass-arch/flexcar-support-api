import { Router, Request, Response, NextFunction } from 'express';
import { getKBData } from '../cache';

const router = Router();

router.get(
  '/:slug',
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { slug } = req.params;
      const { articles } = await getKBData();

      const article = articles.find((a) => a.slug === slug);
      if (!article) {
        res.status(404).json({ error: `Article not found: ${slug}` });
        return;
      }

      res.json(article);
    } catch (err) {
      next(err);
    }
  },
);

export default router;
