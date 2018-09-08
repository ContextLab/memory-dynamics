/*
* Example plugin template
*/

jsPsych.plugins["decode-speech"] = (function() {

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

    console.log('Decoding speech...')

    display_element.append($('<div>', {
      html: trial.stimulus,
      id: 'jspsych-decode-speech-stimulus'
    }));

    $.get("/decode_speech", {
        uniqueId: trial.data.uniqueId,
        currentListNumber: trial.data.currentListNumber})
        .done(function(data){
          processAndFinishTrial(data)
        })

    function processAndFinishTrial(data){

      console.log(data['message'])

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

    };
  }
return plugin;
})();
