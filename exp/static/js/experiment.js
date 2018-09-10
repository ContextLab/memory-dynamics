var timeline = []
var recordTime = 60

var runExperiment = function(currentStimArray, options, cb) {

  // instructions
  var instructions = {
      type: "text",
      text: "add instructions here."
  }

  // video
  var video = {
    type: 'video',
    width: 640,
    start: 8,
    stop: 10,
    sources: ['video/sample_video.mp4']
  }

  // recall instructions
  var recall_instructions = {
      type: "text",
      text: "add instructions here."
  }

  // recall
  var recall = {
        type: 'free-recall',
        stimulus: "<p class='mic'><i class='fa fa-microphone blink_me'></i></p>",
        stim_duration: recordTime * 1000,
        trial_duration: recordTime * 1000 + 2000,
        record_audio: true,
        speech_recognition: 'google',
        on_finish: function() {
            console.log('Saving audio data...')
            psiTurk.saveData({
                success: function() {
                    console.log('Data saved!')
                }
            })
  }}

  // initialize
  jsPsych.init({
    timeline: [instructions, video, recall_instructions, recall],
    on_finish: function() { jsPsych.data.displayData(); }
  });

};
