 function translate(cardCount, card) {
        var dict = {
  "Fill all the fields": {
    de: "Füllen Sie alle Felder aus"
  },
  "Invalid Email Address": {
    de: "Ungültige E-Mail",
  }
}

var translator = $('body').translate({
  lang: "en",
  t: dict
}); //use English
translator.lang("de");