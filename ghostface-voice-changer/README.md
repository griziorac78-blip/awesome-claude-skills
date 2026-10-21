# Ghostface Voice

Changeur de voix Ghostface en direct, dans le navigateur (Safari sur iPhone, Chrome ou Edge sur ordinateur).

- `index.html` : l'appli (un seul fichier).
- `twilio/token.js` et `twilio/voice.js` : les deux fonctions Twilio qui permettent d'appeler un vrai numéro de téléphone depuis l'iPhone, avec la voix transformée.

## Appeler depuis l'iPhone seul (Twilio)

Tout se fait depuis Safari sur l'iPhone, sur console.twilio.com (zoome si besoin). Compte environ 20 minutes la première fois.

### 1. Compte et numéro
1. Crée un compte sur twilio.com et vérifie ton numéro.
2. **Phone Numbers › Buy a number** : achète un numéro avec l'option *Voice*. Un numéro américain s'achète tout de suite. Un numéro français demande d'envoyer une pièce d'identité et une adresse (*Regulatory bundle*). C'est ce numéro que verra la personne que tu appelles.
3. **Voice › Settings › Geo permissions** : coche **France** (et les autres pays que tu veux appeler).

> Compte d'essai : tu ne peux appeler que les numéros ajoutés dans *Verified Caller IDs*, et un message Twilio est lu au début de l'appel. Ajoute du crédit (*Upgrade*) pour enlever ces limites.

### 2. Clé d'API
**Account › API keys & tokens › Create API key** (type *Standard*). Note le **SID** (commence par `SK`) et le **Secret** (affiché une seule fois).

### 3. Le service (fonctions + page)
1. **Functions and Assets › Services › Create Service**, nomme-le `ghostface`.
2. **Add › Add Function**, chemin `/token`, visibilité **Public**. Colle le contenu de `twilio/token.js`.
3. **Add › Add Function**, chemin `/voice`, visibilité **Protected**. Colle le contenu de `twilio/voice.js`.
4. **Add › Upload File** : envoie `index.html`, visibilité **Public**. Comme ça, l'appli est hébergée en https à la même adresse.
5. **Settings › Environment Variables**, ajoute :
   | Clé | Valeur |
   |---|---|
   | `API_KEY` | le SID de la clé (`SK…`) |
   | `API_SECRET` | le secret de la clé |
   | `CALLER_ID` | ton numéro Twilio au format `+1…` ou `+33…` |
   | `APP_PIN` | un code à toi, par exemple `4817` |
   | `TWIML_APP_SID` | à remplir à l'étape 4 |
6. **Deploy All**. L'adresse du service s'affiche en bas, par exemple `https://ghostface-1234.twil.io`.

### 4. L'application d'appel (TwiML App)
1. **Voice › TwiML › TwiML Apps › Create new TwiML App**, nom `Ghostface`.
2. **Voice Request URL** : `https://ghostface-1234.twil.io/voice` (ton adresse), méthode **POST**. Enregistre.
3. Copie son SID (commence par `AP`) dans la variable `TWIML_APP_SID` du service, puis **Deploy All** de nouveau.

### 5. Appeler
1. Sur l'iPhone, ouvre `https://ghostface-1234.twil.io/index.html` dans Safari. Partager › *Sur l'écran d'accueil* pour l'avoir comme une appli.
2. Dans « Réglages du service d'appel », mets ton code PIN (l'adresse se remplit toute seule).
3. Tape le numéro, touche **Appeler**, autorise le micro. La personne entend directement la voix Ghostface.

Garde l'appli au premier plan pendant l'appel : iOS coupe le micro de Safari en arrière-plan.

### Coût
Environ 1 à 2 € par mois pour le numéro, plus quelques centimes par minute d'appel vers la France (voir twilio.com/voice/pricing).

### Sécurité
Le code PIN empêche quelqu'un d'autre de passer des appels avec ton compte. Choisis-en un qui n'est pas évident, et ne partage pas l'adresse de l'appli avec le PIN.

## Limites
Snapchat, Instagram et WhatsApp : impossible sur le même iPhone, Apple interdit à toute appli de modifier le son de leurs appels. Sur ordinateur, voir le guide dans l'appli (câble audio virtuel).

Pour les blagues entre potes uniquement. Les appels malveillants (menaces, appels répétés pour faire peur) sont punis par la loi, et Twilio ferme les comptes qui en abusent.
