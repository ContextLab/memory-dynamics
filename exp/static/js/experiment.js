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
      type: "text",
      pages: "<div class='instructions'> <p style='font-weight:bold'> PLEASE READ THESE INSTRUCTIONS CAREFULLY </p>" +
            "<p> In this experiment, you will view a 20-25 minute episode of a TV show and recall what happened in as much detail as possible. </p>" +
            "<p> Press the NEXT to continue.</p></div>"
      show_clickable_nav: true
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
      pages: ["add instructions here.",  "add another page here"],
      show_clickable_nav: true
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
      pages: ["That's it! You're done!"],
  };


  // initialize
  jsPsych.init({
    timeline: [info, instructions, video, recall_instructions, recall, finished_message]
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
