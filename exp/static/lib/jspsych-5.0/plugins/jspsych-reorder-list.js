/*
* Example plugin template
*/

jsPsych.plugins["reorder-list"] = (function() {

  var plugin = {};

  plugin.trial = function(display_element, trial) {

    // set default values for parameters
    // trial.trial_duration = trial.trial_duration || 60;
    // trial.stim_duration = trial.stim_duration || 60;

    // allow variables as functions
    // this allows any trial variable to be specified as a function
    // that will be evaluated when the trial runs. this allows users
    // to dynamically adjust the contents of a trial as a result
    // of other trials, among other uses. you can leave this out,
    // but in general it should be included
    trial = jsPsych.pluginAPI.evaluateFunctionParameters(trial);

    var setTimeoutHandlers = [];

    console.log('Reordering list with ' + trial.data.strategy + ' strategy.')

    display_element.append($('<div>', {
      html: trial.stimulus,
      id: 'jspsych-reorder-list-stimulus'
    }));

    $.get("/reorder_list_init", {
        uniqueId : trial.data.uniqueId,
        currentListNumber : trial.data.currentListNumber,
        strategy : trial.data.strategy})
        .done(function(result){
          console.log(result)
          function check_status() {
            $.get("/return_reordered_list")
                .done(function(result){
                if(!result.finished) {
                  console.log('Checking..')
                  setTimeout(check_status, 2000);
                } else {
		    console.log('Done! Parsing data and finishing trial...')
                    processAndFinishTrial(result)
		}
		})
            }
	check_status()
        })

    function processAndFinishTrial(result){
      parseJSON(result['data'])
      .then(function(parsed){
	console.log('Done parsing!  Formatting the list...')
        formatList(parsed)
        .then(function(result){

          console.log(result)
          window.currentStimArray = result


          // kill any remaining setTimeout handlers
          for (var i = 0; i < setTimeoutHandlers.length; i++) {
            clearTimeout(setTimeoutHandlers[i]);
          }

          // kill keyboard listeners
          if (typeof keyboardListener !== 'undefined') {
            jsPsych.pluginAPI.cancelKeyboardResponse(keyboardListener);
          }

          // gather the data to store for the trial
          var trial_data = {
            "stimulus": trial.stimulus,
          };

          jsPsych.data.write(trial_data);

          // clear the display
          display_element.html('');

          // move on to the next trial
          jsPsych.finishTrial(trial_data);
        })
      })

    };
  }
return plugin;
})();
