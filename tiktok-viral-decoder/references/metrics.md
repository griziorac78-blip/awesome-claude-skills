# Métriques et scoring

## Ce que l'algorithme regarde (ordre d'importance approximatif)

1. **Rétention** : temps de visionnage moyen, % de visionnage complet, revisionnages. Non visible publiquement : seul le créateur le voit dans TikTok Studio. Pour les vidéos des autres, on l'estime indirectement (durée courte + boucle + beaucoup de vues = bonne rétention probable).
2. **Partages** : signal le plus fort de ceux visibles publiquement.
3. **Favoris (saves)** : le contenu a une valeur durable.
4. **Commentaires** : conversation, débat.
5. **Likes** : signal le plus faible et le plus courant.
6. **Abonnements depuis la vidéo**, visites du profil (visibles seulement par le créateur).

## Formules

```
like%   = likes        / vues × 100
comm%   = commentaires / vues × 100
save%   = favoris      / vues × 100
share%  = partages     / vues × 100

Score Outlier = vues / abonnés du compte
   (pour un audit : vues / médiane des vues du compte)
```

## Score Viral (0–100)

On pondère les actions selon leur force puis on ajoute un bonus outlier :

```
engagement_pondéré = 1×like% + 3×comm% + 4×save% + 6×share%

score_engagement = min(70, engagement_pondéré × 3)
bonus_outlier    = min(30, 10 × log10(max(1, Score Outlier)))   # ×10 → 10 pts, ×100 → 20 pts, ×1000 → 30 pts

Score Viral = score_engagement + bonus_outlier
```

- Si les abonnés sont inconnus : bonus_outlier = 0 et précise « Score sans outlier ».
- Si une métrique manque (souvent les partages ou les favoris), ne la compte pas et indique que le score est partiel.
- Ce score sert à **comparer des vidéos d'un même lot**, pas à prédire des vues. `scripts/score_videos.py` l'implémente.

## Classement

| Classe | Règle (dans un même lot) |
|--------|--------------------------|
| 🔥 Outlier | Score Outlier ≥ 10 **ou** top 20 % du Score Viral |
| ✅ Solide | Au-dessus de la médiane du lot |
| ➖ Moyenne | Sous la médiane |
| ❌ Flop | Bottom 20 % du lot |

## Repères de lecture (ordres de grandeur, à prendre avec prudence)

Ces valeurs varient fortement selon la niche, le pays, la taille du compte et l'époque. Elles servent uniquement à repérer une valeur anormalement haute ou basse quand on n'a pas encore de données de comparaison. Dès qu'on a un lot de vidéos de la niche, on compare **à l'intérieur du lot**.

| Ratio | Plutôt faible | Correct | Fort |
|-------|---------------|---------|------|
| like% | < 3 % | 3–8 % | > 8 % |
| comm% | < 0,05 % | 0,05–0,3 % | > 0,3 % |
| save% | < 0,2 % | 0,2–1 % | > 1 % |
| share% | < 0,1 % | 0,1–0,8 % | > 0,8 % |

Lecture rapide des profils :
- **save% élevé** → contenu utile / à refaire : renforcer `E-UTILE`, formats tuto/liste.
- **share% élevé** → identification ou humour : contenu « à envoyer à quelqu'un ».
- **comm% élevé avec like% bas** → polémique, parfois négative : vérifier le ton des commentaires.
- **beaucoup de vues mais ratios faibles** → bon hook, contenu décevant (ou poussé par un son tendance).
- **ratios forts mais peu de vues** → bon contenu, hook ou premier plan à retravailler, ou vidéo trop récente.

## Stats propres au créateur (mode audit, TikTok Studio)

Si l'utilisateur fournit ses analytics :
- **Temps de visionnage moyen / durée** : < 40 % = problème de rétention.
- **% visionnage complet** : principal indicateur de structure.
- **Courbe de rétention** : chute forte dans les 2–3 premières secondes = hook raté ; chute au milieu = longueur ou promesse floue.
- **Sources de trafic** : beaucoup de « Pour Toi » = l'algorithme pousse ; beaucoup de « Recherche » = bon SEO, à exploiter avec des mots-clés.
