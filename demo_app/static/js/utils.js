var utils = {

  generateDiv: function() {
    var container = $('<div>').addClass('container').css('margin-top', '20px')
    var row = $('<div>').addClass('row')
    var col = $('<div>').addClass('col-xs-12')
    var box = $('<div>').addClass('box')
    col.append(box)
    row.append(col)
    container.append(row)
    return container
  },

  speech_synthesis : function(message) {
    setTimeout(function(){
      var u = new SpeechSynthesisUtterance()
      u.text = message
      u.lang = 'en-IN'
      speechSynthesis.speak(u)
    }, 1000)
  }
}  
  