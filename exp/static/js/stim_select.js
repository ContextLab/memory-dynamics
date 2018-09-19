infotimeline = []

var atlep1 = '/static/files/atlanta-ep1.mp4'
var atlep2 = '/static/files/atlanta-ep2.mp4'
var arrestdevep1 = '/static/files/arrested-development-ep1.mp4'

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
    on_finish: function(data){
      var returning = JSON.parse(data.responses).Q0;
      var condition = JSON.parse(data.responses).Q1;
      if (returning == 'No') {
        var videostim = atlep1
      } else if (condition == 'A') {
        var videostim = atlep2
      } else {
        var videostim = arrestdevep1
      };
      psiTurk.recordTrialData(returning);
      psiTurk.recordTrialData(condition);
      psiTurk.recordTrialData(videostim);
    }
  };

  function set_stim() {
    var qestions = jsPsych.data.getLastTrialData();
    //console.log(JSON.parse(jsPsych.data.getLastTrialData().values()[0].responses).Q0);
    var returning = JSON.parse(jsPsych.data.getLastTrialData().values()[0].responses).Q0;
    var condition = JSON.parse(jsPsych.data.getLastTrialData().values()[0].responses).Q1;
    psiTurk.recordTrialData(returning);
    psiTurk.recordTrialData(condition);
    psiTurk.recordTrialData(videostim)
    if (returning == 'No') {
      var videostim = atlep1
      } else if (condition == 'A') {
        var videostim = atlep2
      } else {
        var videostim = arrestdevep1
      };
      console.log(videostim)
      console.log(typeof videostim)
      return videostim
    };

  // initialize
  jsPsych.init({
    timeline: [info, stim_select],
    on_finish: function() {
      // psiTurk.recordTrialData(returning),
      // psiTurk.recordTrialData(condition),
      // psiTurk.recordTrialData(videostim),
      var chosen_vid = set_stim()
      console.log(chosen_vid)
      psiTurk.saveData({
        success: runExperiment(options, chosen_vid) //function() {cb();}
      })
    }
  })
};
