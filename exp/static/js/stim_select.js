// Note: The TV episodes used in the experiment are copyrighted, so they aren't
// distributed with this repo and the experiment will load an example video file
// instead.
// To adapt the experiment to use "real" stimuli, add your video files to
// exp/static/files/, update the paths below, and set use_sample_video to false.

var use_sample_video = true
var sample_video = '/static/files/sample_video.mp4'

var atlep1 = use_sample_video ? sample_video : '/static/files/atlanta-ep1.mp4'
var atlep2 = use_sample_video ? sample_video : '/static/files/atlanta-ep2.mp4'
var arrestdevep1 = use_sample_video ? sample_video : '/static/files/arrested-development-ep1.mp4'

var runStim_select = function(options) {

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
  };

  function set_conditions() {
    var questions = jsPsych.data.getLastTrialData();
    var returning = JSON.parse(questions.values()[0].responses).Q0;
    var condition = JSON.parse(questions.values()[0].responses).Q1;
    if (returning == 'No') {
      var second_run = false;
      var videostim = atlep1;
      } else if (condition == 'A') {
        var second_run = true;
        var videostim = atlep2
      } else {
        var second_run = true;
        var videostim = arrestdevep1
      };
    console.log(videostim)
    psiTurk.recordTrialData(returning)
    psiTurk.recordTrialData(condition)
    psiTurk.recordTrialData(videostim)
    return {second_run : second_run, videostim : videostim}
  };

  // initialize
  jsPsych.init({
    timeline: [info, stim_select],
    on_finish: function() {
      var conditions = set_conditions()
      psiTurk.saveData({
        success: runExperiment(options, conditions),
      })
    }
  })
};
