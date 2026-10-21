// Twilio Function « /token » (visibilité : Public).
// Donne à l'appli un jeton d'appel valable 1 h, seulement si le code PIN est bon.
// Variables d'environnement : API_KEY, API_SECRET, TWIML_APP_SID, APP_PIN.
exports.handler = function (context, event, callback) {
  const response = new Twilio.Response();
  response.appendHeader('Access-Control-Allow-Origin', '*');
  response.appendHeader('Content-Type', 'application/json');

  if (!context.APP_PIN || event.pin !== context.APP_PIN) {
    response.setStatusCode(401);
    response.setBody({ error: 'PIN invalide' });
    return callback(null, response);
  }

  const AccessToken = Twilio.jwt.AccessToken;
  const token = new AccessToken(context.ACCOUNT_SID, context.API_KEY, context.API_SECRET, {
    identity: 'ghostface',
    ttl: 3600
  });
  token.addGrant(new AccessToken.VoiceGrant({
    outgoingApplicationSid: context.TWIML_APP_SID,
    incomingAllow: false
  }));

  response.setBody({ token: token.toJwt() });
  return callback(null, response);
};
