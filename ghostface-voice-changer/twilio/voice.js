// Twilio Function « /voice » (visibilité : Protected).
// Appelée par Twilio quand l'appli lance un appel : compose le numéro demandé.
// Variable d'environnement : CALLER_ID (ton numéro Twilio, ex. +33970000000).
exports.handler = function (context, event, callback) {
  const twiml = new Twilio.twiml.VoiceResponse();
  const to = String(event.To || '').replace(/[^\d+]/g, '');

  if (!/^\+\d{8,15}$/.test(to)) {
    twiml.say({ language: 'fr-FR' }, 'Numéro invalide.');
    return callback(null, twiml);
  }

  const dial = twiml.dial({ callerId: context.CALLER_ID, timeLimit: 1800 });
  dial.number(to);
  return callback(null, twiml);
};
