# Scanner Snapchat Web avec un navigateur connecté

Pour les environnements où Claude pilote un navigateur (Claude in Chrome, computer use, Playwright local…). Sinon, demande des captures d'écran.

## Règles de sécurité

- **Seulement à la demande**, pour la conversation nommée par l'utilisateur. Pas de scan de toutes les convs, pas de surveillance en continu.
- **L'utilisateur se connecte lui-même** sur https://web.snapchat.com (identifiant, mot de passe, code 2FA ou validation dans l'app). Ne saisis, ne lis et ne stocke jamais ses identifiants.
- **Lecture seule par défaut** : n'envoie aucun message, ne clique pas sur « Appel », n'ouvre pas de snaps non vus (ça les marque comme vus pour l'autre) sauf demande explicite.
- Si l'utilisateur veut que tu envoies une réponse : affiche le texte exact, attends un « oui, envoie » pour **ce** message précis.
- Ne fais jamais de capture/exportation des snaps photo/vidéo de l'autre.

## Déroulé

1. Ouvre `https://web.snapchat.com`. Si l'écran de connexion apparaît, demande à l'utilisateur de se connecter puis de te prévenir.
2. Dans la liste des discussions (colonne de gauche), clique sur la conversation demandée (cherche par prénom avec la barre de recherche si besoin).
3. Lis les messages visibles. Fais défiler vers le haut pour charger l'historique jusqu'à ~30 messages ou au début de l'échange en cours (s'arrêter dès que le contexte est suffisant).
4. Pour chaque message, note : **auteur** (utilisateur = « Moi », généralement en rouge ; l'autre = son nom, en bleu/violet), **texte**, **type** (chat, snap, réponse à une story, média), **horodatage** visible.
5. Repère les indicateurs d'état si visibles : « Ouvert », « Reçu », « Vu », « en train d'écrire ».
6. Passe à l'étape 1 du skill (Décoder) avec cette transcription.

## Si l'interface a changé

Snapchat Web évolue souvent. Si un élément n'est pas trouvé, décris ce que tu vois à l'utilisateur et propose le repli : captures d'écran ou copier-coller.
