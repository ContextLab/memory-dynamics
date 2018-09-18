var timeline = []
var record_time = 5


var runExperiment = function(cb) {

  // subject info
  var info = {
      type: 'survey-text',
      questions: [
        {prompt: 'Subject ID?', value: 'subid', columns: 50},
      ]
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
            "<div class='instructions'> <p>That's it!</p>" +
            "<p> <strong>When you're ready to begin the episode, press the spacebar.</strong></p></div>"
          ],
      key_forward: 32
      //show_clickable_nav: true
  };

  // video
  var video = {
    type: 'video',
    height: 640,
    width: 800,
    sources: ['/static/files/sample_video.mp4']
  };

  // recall instructions
  var recall_instructions = {
      type: "instructions",
      pages: ["<div class='instructions'><p> When you see the <i style='color:red' class='fa fa-microphone'></i>, recall the episode to the best of your ability.</p>" +
              "<p> Please remember to speak <strong>clearly</strong>.</p>" +
              "<p> <strong>When you're ready to begin recalling the episode, press the spacebar.</strong></p></div>"
            ],
      key_forward: 32
      //show_clickable_nav: true
  };

  // recall
  var recall = {
        type: "free-recall",
        stimulus: "<p class='mic' style='position:absolute;top:31%;left:43%;font-size:20vw;color:red'><i class='fa fa-microphone blink_me' style='color:red'></i></p>",
        // stimulus: "<p class='mic'><i class='fas fa-microphone></i></p>",
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
    timeline: [info, instructions, video, recall_instructions, recall, finished_message],
    fullscreen: true,
    // on_finish: function() { jsPsych.data.displayData(); }
    // on_finish: function() {
    //   psiTurk.saveData({
    //     success: function() {
    //       $.post("/onfinish", {
    //         "data": uniqueId
    //         });
    //         cb();
    //     }
    //   })
    // },
    // on_data_update: function(data) {
    //   psiTurk.recordTrialData(data);
    // }
  })

};
