var timeline = []
var record_time = 5

var runExperiment = function() {

  // subject info?
  var info = {
      type: 'survey-text',
      questions: [
        {prompt: 'How old are you?', value: 'age', columns: 3},
        {prompt: 'Where were you born?', value: 'location', columns: 50},
        {prompt: 'Tell me about your day', value: 'How did it start?', rows:10, columns: 50}
      ]
  };

  // instructions
  var instructions = {
      type: "instructions",
      pages: ["add instructions here.",  "add another page here"],
      show_clickable_nav: true
  };

  // video
  var video = {
    type: 'video',
    height: 640,
    width: 800,
    sources: ['/static/files/sample_video.mp4']
  };

  // instructions
  var recall_instructions = {
      type: "instructions",
      pages: ["add instructions here.",  "add another page here"];
      show_clickable_nav: true
  };

  // recall
  var recall = {
        type: 'free-recall',
        stimulus: "<p class='mic'><i class='fa fa-microphone blink_me'></i></p>",
        stim_duration: record_time * 1000,
        trial_duration: record_time * 1000 + 2000,
        record_audio: true,
        speech_recognition: 'google',
        data: {
          listNumber: 0,
        },
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
    timeline: [info, instructions, video, recall_instructions, recall],
    on_finish: function() { jsPsych.data.displayData(); }
  });

};
