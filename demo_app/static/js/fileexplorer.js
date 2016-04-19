var fileExplorerHandler = function(result) {
  if (result.parsed.intent === '--current-path' || result.parsed.intent === '--goto' || result.parsed.intent === '--move-up' || result.parsed.intent === '--step-into' ) {
    console.log(result)
    var path = result.path
    var panel = utils.generateDiv()
    var message = $('<pre>').html('Path has been set to:')
                  .append($('<pre>').html(path))
    panel.find('.box').append(message)
    $('.holder').prepend(panel)                
  }

  else if(result.parsed.intent === '--display' || result.parsed.intent === '--hidden') {
    var path = result.path
    var panel = utils.generateDiv()
    var message = $('<pre>').html('Path:')
                  .append($('<pre>').html(path))

    var directories = $('<pre>').html('Directories:')
                      .append($('<ul>'))
    result.option_dir.forEach(function(option_dir) { 
      directories.append($('<li>').html(option_dir))
    })

    var files = $('<pre>').html('Files:')
                .append($('<ul>'))
    result.option_files.forEach(function(option_files) {
      files.append($('<li>').html(option_files))
    })

    panel.find('.box').append(message)
    panel.find('.box').append(directories)
    panel.find('.box').append(files)
    $('.holder').prepend(panel)                    
  } 
}