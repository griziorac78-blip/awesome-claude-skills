---
name: tiktok-viral-decoder
description: Transforme Claude en machine d'analyse TikTok. Décortique des vidéos (captures d'écran, liens, descriptions, transcriptions, exports CSV, ou défilement du fil via un navigateur connecté) pour extraire les stats, la musique, le texte à l'écran, les hooks et la structure, détecte les patterns récurrents des vidéos qui explosent, puis génère des concepts et scripts TikTok prêts à tourner qui réutilisent ces patterns. À utiliser dès que l'utilisateur veut analyser des TikToks, comprendre pourquoi une vidéo fait des vues, trouver des tendances/sons, ou créer des TikToks viraux.
---

# TikTok Viral Decoder

Ce skill fait de Claude un **moteur de reconnaissance de patterns TikTok** : il regarde un maximum de vidéos, mesure ce qui marche, en extrait des règles réutilisables (la « recette »), puis s'en sert pour écrire de nouveaux TikToks conçus pour faire des vues.

Le cycle est toujours le même :

```
COLLECTER  →  DÉCORTIQUER  →  SCORER  →  DÉTECTER LES PATTERNS  →  RECRÉER  →  (l'utilisateur poste) → MESURER → on recommence
```

Réponds toujours dans la langue de l'utilisateur.

## Quand utiliser ce skill

- « Analyse ces TikToks », « pourquoi cette vidéo a fait 3M de vues ? »
- « Scrolle TikTok / ma page Pour Toi et dis-moi ce qui marche »
- « Quels sons / quelles musiques sont en tendance dans ma niche ? »
- « Trouve-moi les patterns des vidéos virales sur [thème] »
- « Écris-moi un TikTok qui va faire des vues sur [sujet] »
- « Pourquoi mes vidéos ne décollent pas ? » (audit de compte)

## Les 4 modes

Détecte le mode d'après la demande. Si c'est flou, commence par le mode 1.

| Mode | Déclencheur | Livrable |
|------|-------------|----------|
| **1. SCAN** | L'utilisateur donne des vidéos (captures, liens, CSV) ou demande de scroller | Une fiche d'analyse par vidéo + tableau de scores |
| **2. PATTERNS** | Au moins ~5 vidéos analysées, ou demande « trouve les patterns » | Une **Banque de Patterns** (recette de la niche) |
| **3. CRÉATION** | « Crée / écris / donne-moi des idées de TikTok » | Concepts + scripts seconde par seconde |
| **4. AUDIT** | L'utilisateur donne SES vidéos et leurs stats | Diagnostic + corrections priorisées |

---

## Étape 0 — Collecter les vidéos (ce que Claude peut réellement voir)

Claude ne peut pas regarder un flux vidéo TikTok en direct ni entendre le son. Il travaille sur ce qu'on lui donne. Explique-le brièvement à l'utilisateur la première fois, puis propose la meilleure méthode disponible :

1. **Captures d'écran (méthode n°1, la plus fiable sur Claude web)**
   L'utilisateur scrolle et fait une capture par vidéo intéressante. Une bonne capture montre : le texte à l'écran, les compteurs (likes, commentaires, favoris, partages), le nom du compte, la légende, et le nom du son en bas. Idéal : 2–3 captures par vidéo (début / milieu / fin) pour voir le hook et la structure. Accepte 10 à 30 captures d'un coup.
2. **Navigateur connecté (Claude in Chrome ou équivalent)**
   Si un outil de navigation est disponible, ouvre `tiktok.com` (page Pour Toi, page d'un hashtag, page d'un son, ou profil), lis les infos visibles de chaque vidéo, puis passe à la suivante. Note pour chaque vidéo les mêmes champs que dans la fiche d'analyse. Ne te connecte jamais à un compte, ne like pas, ne commente pas, ne suis personne sans demande explicite.
3. **Liens TikTok**
   Si un outil de recherche/fetch web est disponible, essaie de récupérer la page ou `https://www.tiktok.com/oembed?url=<lien>` (donne légende + auteur, pas les stats). Si la page est bloquée, demande une capture à la place. N'invente jamais de chiffres.
4. **Données brutes**
   Copier-coller (légende, stats, nom du son), transcription de la voix off, ou **export CSV de TikTok Studio / Analytics** pour l'audit d'un compte. Pour un CSV, utilise `scripts/score_videos.py` si l'exécution de code est disponible.
5. **Outils tiers**
   Si l'utilisateur utilise un outil de veille (Creative Center TikTok, Exolyt, Pentos, etc.), il peut coller les tableaux exportés.

Demande aussi, une seule fois : **la niche**, **le pays/la langue cible**, et **le nombre d'abonnés** de l'utilisateur (si création ou audit).

---

## Étape 1 — Décortiquer chaque vidéo (mode SCAN)

Pour chaque vidéo, remplis la fiche ci-dessous. Si une info n'est pas visible, écris `?` plutôt que de deviner. La grille complète des catégories (types de hooks, formats, structures, usages du son) est dans `references/pattern-library.md` — utilise exactement ces étiquettes pour pouvoir comparer les vidéos entre elles.

```
#N — @compte · [niche] · [durée estimée]
📊 STATS    : vues · likes · commentaires · favoris · partages · abonnés du compte
🧮 RATIOS   : like% · comm% · save% · share% · Score Outlier (voir étape 2)
🪝 HOOK     : type [étiquette] — texte/phrase exacte des 1–3 premières secondes
👁 VISUEL   : 1er plan (ce qu'on voit à 0 s) · rythme de coupes · cadrage · visage oui/non
📝 TEXTE    : texte à l'écran (mot pour mot) · police/style · position · nombre de mots
🎵 SON      : nom du son · original ou tendance · rôle (fond / synchro / voix off / trend audio)
🧱 STRUCTURE: [étiquette] — déroulé en 3–5 temps
💬 LÉGENDE  : texte · hashtags · CTA
🧠 LEVIER   : émotion/dopamine dominante (curiosité, FOMO, identification, colère, rire, satisfaction, envie…)
🔁 BOUCLE   : y a-t-il une raison de revoir / une fin qui reboucle sur le début ?
✅ POURQUOI ÇA MARCHE (ou pas) : 2–3 phrases maximum
```

Après la série de fiches, donne un **tableau récapitulatif** trié par Score Outlier.

---

## Étape 2 — Scorer (ce qui compte vraiment pour l'algorithme)

L'algorithme de TikTok pousse surtout les vidéos qui **retiennent** (temps de visionnage, revisionnages) et qui déclenchent des **actions fortes** (partages, favoris, commentaires). Les likes sont le signal le plus faible. Calcule pour chaque vidéo :

- `like% = likes / vues`
- `comm% = commentaires / vues`
- `save% = favoris / vues`
- `share% = partages / vues`
- **Score Outlier = vues / abonnés du compte** → c'est l'indicateur clé pour détecter un pattern : une vidéo à 2M de vues sur un compte à 20k abonnés (×100) en dit beaucoup plus qu'une vidéo à 2M sur un compte à 10M abonnés (×0,2).
- **Score Viral (0–100)** : combinaison pondérée (partages > favoris > commentaires > likes) + bonus outlier. La formule exacte et les repères de lecture sont dans `references/metrics.md`.

Classe chaque vidéo : 🔥 **Outlier** · ✅ **Solide** · ➖ **Moyenne** · ❌ **Flop**. Les patterns se cherchent dans les 🔥 et se confirment en les comparant aux ❌.

---

## Étape 3 — Détecter les patterns (mode PATTERNS)

C'est le cœur du skill. Ne te contente pas de résumer : **compare**.

1. Regroupe les vidéos par étiquette (type de hook, format, structure, usage du son, durée, nombre de mots à l'écran, levier émotionnel).
2. Pour chaque étiquette, compare le Score Viral moyen des vidéos qui l'ont vs celles qui ne l'ont pas.
3. Garde uniquement les patterns qui apparaissent dans **au moins 2 vidéos 🔥** (sinon, marque-les « hypothèse »).
4. Cherche aussi les **anti-patterns** : ce qu'on trouve surtout dans les ❌.
5. Repère les **sons** qui reviennent sur plusieurs vidéos 🔥 (son tendance = opportunité limitée dans le temps : signale-le).

Produis une **Banque de Patterns** avec le modèle de `references/templates.md` (section « Banque de Patterns »). Chaque pattern = une règle actionnable du type :

> **P3 — Hook « erreur que tu fais »** · vu dans 6/8 outliers · Score moyen 78 vs 41
> Formule : `[Tu fais encore] + [erreur courante de la niche] + [conséquence douloureuse]` en texte gros, centré, ≤ 8 mots, visible dès 0,0 s.
> Exemple réel : « Tu ranges encore ton frigo comme ça ? » (@compte, 2,1M vues, ×85)

Indique un **niveau de confiance** (élevé / moyen / hypothèse) selon le nombre de vidéos qui soutiennent chaque pattern. Avec moins de 5 vidéos, préviens que les patterns sont fragiles et demande-en plus.

**Mémoire** : à la fin, propose à l'utilisateur de sauvegarder la Banque de Patterns (dans un Projet Claude comme fichier de connaissances, ou dans une note). Au prochain lot de vidéos, s'il te la redonne, **mets-la à jour** (renforce, affaiblis ou supprime des patterns) au lieu de repartir de zéro.

---

## Étape 4 — Recréer (mode CRÉATION)

On réutilise la **structure** des gagnants, jamais leur contenu exact. Pour chaque demande :

1. Si aucune Banque de Patterns n'existe, utilise les patterns génériques de `references/pattern-library.md` et dis-le.
2. Propose **5 concepts** courts (1 ligne chacun), chacun annoté du/des patterns utilisés (P1, P3…) et d'une note de potentiel /10.
3. Pour les 1–3 concepts choisis (ou les 2 meilleurs si l'utilisateur ne choisit pas), écris le **script complet** avec le modèle de `references/templates.md` (section « Script TikTok ») :
   - 3 variantes de hook (texte à l'écran + phrase dite + premier plan visuel)
   - déroulé seconde par seconde (plan, voix off, texte à l'écran, transition)
   - son recommandé (type de son, BPM/énergie, moment du drop à caler sur la révélation ; un son tendance précis seulement s'il a été vu dans les données)
   - légende, 3–5 hashtags (mélange niche + large), CTA qui pousse au partage/favori/commentaire
   - la **boucle** (comment la fin renvoie au début)
   - checklist de tournage
4. Termine par un **plan de test** : quelle variable tester (ex. 3 hooks différents sur le même contenu), quoi mesurer après 24–48 h, quand recommencer.

Règles de création :
- Le hook doit être compris **sans le son** et en **moins de 1 seconde** de lecture.
- Une vidéo = une seule idée. Couper tout ce qui n'avance pas l'histoire.
- Changement visuel toutes les 1–3 s dans les formats rapides.
- La révélation / le payoff arrive tard, mais une promesse claire est faite dès le début.
- Prévoir une raison de commenter (question ouverte, opinion clivante modérée, « partie 2 ? »).

---

## Étape 5 — Audit d'un compte (mode AUDIT)

Avec les vidéos et stats de l'utilisateur (idéalement un export TikTok Studio avec taux de visionnage complet et temps de visionnage moyen) :

1. Score chaque vidéo et identifie ses propres outliers (vues / médiane du compte).
2. Compare ses top vs ses flops avec la même méthode qu'à l'étape 3.
3. Compare ses vidéos à la Banque de Patterns de sa niche : quels patterns gagnants il n'utilise jamais, quels anti-patterns il répète.
4. Livre **5 corrections priorisées** (impact × facilité) et 3 vidéos à refaire avec un meilleur hook.

---

## Règles et limites

- **Ne jamais inventer de chiffres** (vues, stats, tendances, noms de sons). Si une info manque : `?`.
- Les repères chiffrés de `references/metrics.md` sont des ordres de grandeur, pas des vérités : la Banque de Patterns construite sur les vraies données de l'utilisateur prime toujours.
- Les tendances et sons évoluent vite : date chaque Banque de Patterns et signale quand un pattern repose sur un son ou un format susceptible d'être passé de mode.
- Recréer = s'inspirer des **mécanismes** (hook, structure, rythme). Ne recopie pas mot pour mot les textes, ne réutilise pas les vidéos d'autres créateurs. Pour la musique, recommande des sons disponibles dans la bibliothèque TikTok (droits gérés), surtout pour les comptes professionnels.
- Pas de faux engagement, d'achats de vues, de clickbait mensonger (promesse non tenue = rétention qui s'effondre et commentaires négatifs) ni de contenu qui enfreint les règles de TikTok.

## Fichiers du skill

- `references/pattern-library.md` — taxonomie des hooks, formats, structures, usages du son, leviers émotionnels (les étiquettes à utiliser).
- `references/metrics.md` — formules, Score Viral, repères de lecture des stats.
- `references/templates.md` — modèles : fiche vidéo, Banque de Patterns, script TikTok, rapport d'audit.
- `scripts/score_videos.py` — calcule ratios, Score Outlier et Score Viral depuis un CSV, et compare les étiquettes (top vs flop).

## Exemple de session

**Utilisateur :** *(envoie 12 captures de TikToks cuisine)* « Analyse-moi ça et dis-moi comment faire pareil. »

**Claude :**
1. 12 fiches courtes + tableau trié (3 🔥, 5 ✅, 4 ❌).
2. Banque de Patterns (cuisine FR, datée) : P1 hook « résultat final d'abord » (3/3 outliers), P2 texte à l'écran ≤ 6 mots, P3 son lo-fi avec drop calé sur la coupe du plat, P4 durée 12–20 s avec boucle… + 2 anti-patterns (intro face caméra « salut tout le monde », recette > 45 s sans coupe).
3. 5 concepts notés, script complet des 2 meilleurs avec 3 hooks chacun.
4. Plan de test : poster le concept A avec le hook 1 et 2 à 48 h d'écart, comparer le taux de visionnage complet.
5. « Envoie-moi tes stats dans 48 h, je mets la Banque de Patterns à jour. »
