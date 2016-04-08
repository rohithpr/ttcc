$(document).ready(function() {
  /* Constants, global variables and clock controllers
   */

  var CLOCK_INTERVAL = 1000 // Clock will be called every second (1000 ms)
  var SESSION_DURATION = 120 // Active for this long without any activity

  var newCommand // Will be sent to server
  var oldResult // Will be sent to server

  var sessionDuration // Time left before the session expires
  var currentSession // If a front end app wants to own the session it can tag itself

  var clearSession = function() {
    newCommand = true
    oldResult = {}
    sessionDuration = 0
    currentSession = ''
  };

  var clock = function() {
    if (sessionDuration > 0) {
      sessionDuration -= 1
      if (sessionDuration === 0) {
        clearSession()
        console.log('Session ended')
      }
    }
    else {
      sessionDuration = 0
    }
  }

  var interval = setInterval(clock, CLOCK_INTERVAL)

  /* Utils and front end controllers
   */

  var speech_synthesis = function(message) {
    setTimeout(function(){
      var u = new SpeechSynthesisUtterance()
      u.text = message
      u.lang = 'en-IN'
      speechSynthesis.speak(u)
    }, 1000)
  }

  var tetrisHandler = function(inputContent) {
    var messageTetris = function(message) {
      var tetris = $('.tetris')[0]
      tetris.contentWindow.postMessage(message, '*')
    }

    var getCommands = function(inputContent) {
      var start = ['start', 'tart', 'stat']
      var stop = ['stop', 'top', 'step', 'stoup']
      var left = ['left', 'cleft', 'lift']
      var right = ['right', 'wright', 'bright', 'tight', 'try']
      var rotate = ['rotate', 'rooted', 'routed', 'rote', 'protect']
      var drop = ['drop', 'dropped']
      var sets = [start, stop, left, right, rotate, drop]
      var sets_results = ['start', 'stop', 'left', 'right', 'rotate', 'drop']

      var result = inputContent.split(' ')

      var commands = []
      outer: for(var i = 0; i < result.length; i++) {
        for(var k = 0; k < sets.length; k++) {
          if (sets[k].indexOf(result[i]) !== -1) {
            commands.push(sets_results[k])
            continue outer
          }
        }
      }
      return commands
    }

    var gameCommands = {
                    'start': 32,
                    'stop': 27,
                    'left': 37,
                    'right': 39,
                    'rotate': 38,
                    'drop': 40,
                    'tetris': 32,
                  }
    var commands = getCommands(inputContent)
    if (commands.length === 0) {
      if (inputContent.search('quit session') !== -1 || inputContent.search('stop session') !== -1) {
        // The session itself is stopped
        var panel = utils.generateDiv()
        var message = $('<pre>').html('Tetris closed and session terminated')
        panel.find('.box').append(message)
        $('.holder').prepend(panel)

        clearSession()
        messageTetris(gameCommands['stop'])
        $('.tetris').remove()
      }
      else if (inputContent.search('quit') !== -1) {
        // Exit only from the game, session is still active
        var panel = utils.generateDiv()
        var message = $('<pre>').html('Tetris closed')
        panel.find('.box').append(message)
        $('.holder').prepend(panel)

        sessionDuration = SESSION_DURATION
        currentSession = ''
        messageTetris(gameCommands['stop'])
        $('.tetris').remove()
      }
      return
    }
    sessionDuration = 600
    commands.forEach(function(command) {
      messageTetris(gameCommands[command])
    })
  }


  //Handles SoundCloud specific operations
  var soundcloud_handler = function(inputContent) {
    var player = SC.Widget(document.querySelector('.soundcloud'))

    if (inputContent.search('soundcloud') != -1) {
      var search_term = inputContent.substring(inputContent.search('soundcloud')+11, inputContent.length)
      console.log(search_term)

        SC.initialize({
          client_id : 'CLIENT-ID'
        })

        SC.get('/tracks', {
            q: search_term,
            license: 'cc-by-sa',
            limit: 50
        })
        .then(function(tracks) {
          var track_url = tracks[3].uri
          console.log(track_url)
          player.load(track_url, {auto_play: true})

          (function(){
            player.bind(SC.Widget.Events.READY, function () { //Fired when the widget has loaded its data
              console.log('Ready');                         //and is ready to accept external calls
              player.bind(SC.Widget.Events.FINISH, function () { //Fired when the sound finishes.
                console.log("Song finished")
                var panel = utils.generateDiv()
                var message = $('<pre>').html('Soundcloud closed and session terminated')
                panel.find('.box').append(message)
                $('.holder').prepend(panel)
                $('.soundcloud').remove()
                clearSession()
              });
            });
          }());
        });
    }        

    else {
      if(inputContent == 'pause') {
        console.log("Paused")
        player.pause()
      }

      else if(inputContent == 'play') {
        console.log("Play")
        player.play()
      }

      else if(inputContent == 'toggle') {
        console.log("Toggle")
        player.toggle()
      }
      else if (inputContent.search('quit session') !== -1 || inputContent.search('stop session') !== -1) {
        //To close soundcloud and the session
        var panel = utils.generateDiv()
        var message = $('<pre>').html('Soundcloud closed and session terminated')
        panel.find('.box').append(message)
        $('.holder').prepend(panel)

        clearSession()
        $('.soundcloud').remove()
      }

      else if (inputContent.search('quit') !== -1) {
        // Exit only from the SoundCloud, session is still active
        console.log("SoundCloud quiting")
        var panel = utils.generateDiv()
        var message = $('<pre>').html('Soundcloud closed')
        panel.find('.box').append(message)
        $('.holder').prepend(panel)

        sessionDuration = SESSION_DURATION
        currentSession = ''
        $('.soundcloud').remove()
      }

      return
      sessionDuration = 300
    }    
  }



  /* Speech and server controllers
   */
  if (typeof webkitSpeechRecognition === 'function') {
    var streamer = new webkitSpeechRecognition()
  }

  var setupStreamer = function () {
    if (typeof webkitSpeechRecognition !== 'function') {
       return
    }
    streamer.lang = 'en-IN'
    streamer.continuous = true
    streamer.interimResults = false

    streamer.onresult = function(event) {
      var inputContent = ''
      for (var i = event.resultIndex; i < event.results.length; i++) {
           inputContent += event.results[i][0].transcript
      }
      inputContent = inputContent.toLowerCase()
      console.log('inputContent: ', inputContent)
      inputContent = inputContent.trim()

      // Check if the command is to start a new session
      // Display a message saying that the system can now receive commands
      var isStartSession = inputContent.search('start session')
      if (isStartSession !== -1) {
        // Saying start session even when a session is active will set it to SESSION_DURATION
        sessionDuration = SESSION_DURATION
        var panel = utils.generateDiv()
        var message = $('<pre>').html('Session started')
        panel.find('.box').append(message)
        $('.holder').prepend(panel)
        console.log('Session started')
        return
      }


      var isStopSession = inputContent.search('stop session')
      if (isStopSession !== -1) {
        sessionDuration = 0
        var panel = utils.generateDiv()
        var message = $('<pre>').html('Session stopped')
        panel.find('.box').append(message)
        $('.holder').prepend(panel)
        console.log('Session stopped')
        return
      }


      console.log('session time left:', sessionDuration)
      // If the message is not related to session (de)activation AND a session is active send input to server
      if (sessionDuration > 0) {
        $('input[name=command_text]').val(inputContent)
        $('#main-submit').click()
      }
     }


      streamer.onend = function(event) {
        streamer.start()
     }
   };


  // This will be executed when the page is loaded
  (function() {
    clearSession()
    setupStreamer()
    if (typeof webkitSpeechRecognition === 'function') {
      streamer.start()
    }
    $('#result').hide().parent().hide()
  })()


   // Handles voice input
  $('#main-speech').click(function() {
    // var record = function() {
    // if (typeof webkitSpeechRecognition !== 'function') {
    //   alert('Please use Google Chrome for voice input')
    //   return
    // }
    // var recording = new webkitSpeechRecognition()
    //    recording.lang = 'en-IN'
    //    recording.onresult = function(event) {
    //      $('input[name=command_text]').val(event.results[0][0].transcript)
    //      // console.log(event.results[0][0])
    //      // Optional
    //      // $('#command_form').submit()
    //    }
    //    recording.start()
    //  }
    //  record()
    $('input[name=command_text]').val("soundcloud")
    $('#main-submit').click()
  })


   // Submits form using AJAX
  $('#main-submit').click(function(e) {
    e.preventDefault()

    var inputContent = $('input[name=command_text]').val()

    // All front end apps should have their code before the 'quit' check
    if (currentSession === 'tetris') {
      tetrisHandler(inputContent)
      return
    }

    if (currentSession === 'soundcloud') {
      soundcloud_handler(inputContent)
      return
    }    

    if (inputContent === 'quit session' || inputContent === 'quit') {
      clearSession()
      var panel = utils.generateDiv()
      return
    }

    var submit = function() {
      var data = {}
      data.input = inputContent
      data.newCommand = newCommand // Global variable
      data.oldResult = JSON.stringify(oldResult)
      // console.log(command)
      $.ajax({
        url: '/command',
        method: 'POST',
        data: data,
        success: function(result) {
          console.log(result)
          if (result.error === true) {
            // Handle error
             oldResult = {}
             newCommand = true
            // return
           }
          if (result.final === true) { // Current command has been executed completely, start new session
            oldResult = {}
            newCommand = true
            var parsed = JSON.stringify(result.parsed, null, 2)
            var panel = utils.generateDiv()
            var parsed = $('<pre>').html(parsed)
            var message = $('<pre>').html(result.message)
            panel.find('.box').append(message)
            panel.find('.box').append(parsed)
            $('.holder').prepend(panel)

            if (result.tweet) {
              var panel = utils.generateDiv()
              var message = $('<pre>').html('Tweets found:')
              var tweets = $('<ul>')
              result.tweet.forEach(function(tweet) {
                tweets.append($('<li>').html(tweet))
              })
              panel.find('.box').append(message)
              panel.find('.box').append(tweets)
              $('.holder').prepend(panel)
            }

            // If tetris
            if (result.parsed && result.parsed.device === 'tetris') {
              var container = utils.generateDiv()
              var iframe = $('<iframe>')
                            .attr('src', 'tetris')
                            .attr('width', '100%')
                            .attr('height', '270px')
                            .addClass('tetris')
                            .append($('<div>').addClass('holder'))
              container.find('.box').append(iframe).removeClass('box')
              // container.insertAfter('#voiceForm')
              $('.holder').prepend(container)
              currentSession = 'tetris'
              sessionDuration = 600 // Game will be active for ten minutes without any input
            }

            /*If soundcloud then it creates an iframe where the soundcloud widget
              is loaded and a function call is made to soundcloud_handler()              
            */
            if (result.parsed && result.parsed.device === 'soundcloud') {
              var container = utils.generateDiv()
              var iframe = $('<iframe>')
                            // .attr('src','static/img/soundcloud.png')
                            .attr('src','https://w.soundcloud.com/player/?url=http%3A%2F%2Fapi.soundlcoud.com%2Ftracks%2F1848538&show_artwork=true')
                            .attr('width', '100%')
                            .attr('height', '150px')
                            .addClass('soundcloud')
                            .append($('<div>').addClass('holder'))
              container.find('.box').append(iframe).removeClass('box')
              $('.holder').prepend(container)
              currentSession = 'soundcloud'
              soundcloud_handler(inputContent)
              sessionDuration = 300 // Soundcloud will be active for five minutes without any input
            }

          }
          // // the below code is only for twitter delete after the interaction is made proper
          // if (result.final === 'twitter_False') {
          //   var parsed = JSON.stringify(result.parsed, null, 2)
          //   oldResult = {}
          //   newCommand = true
          //   $('#result').html(parsed).show().parent().show()
          //   $('#message').html(result.message)
          //   if (result.options !== undefined) {
          //     var options = $('<ol>')
          //     result.options.forEach(function(option) {
          //       options.append($('<li>').html(option))
          //     })
          //     $('#options').html(options)
          //     $('#tweet').hide()
          //   }
          // }

          else if (result.final === false) { // Needs confirmation or more information
            var parsed = JSON.stringify(result.parsed, null, 2)
            oldResult = result
            newCommand = false
            var panel = utils.generateDiv()
            var message = $('<pre>').html(result.message)
            var parsed = $('<pre>').html(parsed)
            panel.find('.box').append(message)
            $('.holder').prepend(panel)
            if (result.options !== undefined) {
              var optionsPre = $('<pre>')
              var options = $('<ol>')
              result.options.forEach(function(option) {
                options.append($('<li>').html(option))
              })
              optionsPre.append(options)
              panel.find('.box').append(optionsPre)
            }
            panel.find('.box').append(parsed)

          }
          if (typeof webkitSpeechRecognition === 'function') {
            streamer.stop()
          }
         },
        error: function(a, b, c) {
          console.log(a, b, c)
          $('#message').html('Something went wrong. Please try again.').show().parent().show()
        }
      })

    }
    submit()
  })
})