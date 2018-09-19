var timeline = []
var record_time = 5
atlep1 = '/static/files/atlanta-ep1.mp4'
atlep2 = '/static/files/atlanta-ep2.mp4'
arrestdevep1 = '/static/files/arrested-development-ep1.mp4'

var runExperiment = function(options, cb) {

  // subject info
  var info = {
      type: 'survey-text',
      questions: [
        {prompt: 'Subject ID?', value: '', columns: 50}
      ]
  };

  var stim_select = {
    type: 'survey-multi-choice',
    questions: [
      {prompt: 'Returning subject?', options: ['No','Yes'], required: true},
      {prompt: 'Condition', options: ['A','B'], required: true}
    ],
    on_finish: function(data){
      var returning = JSON.parse(data.responses).Q0;
      var condition = JSON.parse(data.responses).Q1;
      if (returning == 'No') {
        videostim = atlep1
      } else if (condition == 'A') {
        videostim = atlep2
      } else {
        videostim = arrestdevep1
      }
    }
  };

  // instructions
  var instructions = {
      type: "instructions",
      pages: ["<div class='instructions'> <p style='font-weight:bold'> PLEASE READ THESE INSTRUCTIONS CAREFULLY </p>" +
            "<p> In this experiment, you will view a 20-25 minute episode of a TV show and recall what happened in as much detail as possible. </p>" +
            "<p> Press the spacebar to continue.</p></div>",
            "<div class='instructions'> <p> When the episode ends, you will see the microphone icon (<i style='color:red' class='fa fa-microphone'></i>).  This indicates that the computer has started recording. </p>" +
            "<p> From that point on, you will have <strong>10 minutes</strong> to recall the episode as fully as you can.</p> <p> Press the spacebar to continue.</p></div>",
            "<div class='instructions'> <p> Do your best to recall the events of the video in order using the characters' names, but if you realize you skipped something, feel free to go back and describe it.</p>" +
            "<p> Press the spacebar to continue.</p></div>",
            "<div class='instructions'> <p>Okay that's everything. Ready to start?</p>" +
            "<p> <strong>When you're ready to begin the episode, press the spacebar.</strong></p></div>"
          ],
      key_forward: 32
  };

  // video
  var video = {
    type: 'video',
    height: $(window).height(),
    width: $(window).width(),
    sources: [videostim]
  };

  // recall instructions
  var recall_instructions = {
      type: "instructions",
      pages: ["<div class='instructions'><p> When you see the <i style='color:red' class='fa fa-microphone'></i>, recall the episode to the best of your ability.</p>" +
              "<p> Please remember to speak <strong>clearly</strong>.</p>" +
              "<p> <strong>When you're ready to begin recalling the episode, press the spacebar.</strong></p></div>"
            ],
      key_forward: 32
  };

  // recall
  var recall = {
        type: "free-recall",
        stimulus: "<p class='mic' style='position:absolute;top:31%;left:43%;font-size:20vw;color:red'><i class='fa fa-microphone blink_me' style='color:red'></i></p>",
        stim_duration: record_time * 1000,
        trial_duration: record_time * 1000 + 2000,
        record_audio: true,
        speech_recognition: 'google',
        data: {
          listNumber: 0
        },
        on_finish: function() {
            console.log('Saving audio data...')
            psiTurk.saveData({
                success: function() {
                    console.log('Data saved!')
                }
            })
    }
  };

  // finished message
  var finished_message = {
      type: "instructions",
      pages: ["<div class='instructions'><p>You're almost done!</p>" +
      "<p>Please go get your experimter.</p>" +
      "<p> Prese the spacebar for the post-experiment questionnaire.</div>"],
      key_forward: 32
  };


  // initialize
  jsPsych.init({
    timeline: [info, stim_select, instructions, video, recall_instructions, recall, finished_message],
    on_finish: function() {
      psiTurk.recordTrialData(uniqueId),
      psiTurk.saveData({
        success: function() {cb();}
      })
    }
  })
};
