////////////////////////////////////////////////////////////////////////////////
// RUN THE EXPERIMENT //////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
var options = {
  show: true,
  mode: mode
};
runInfo(options, function() {
  runDemographics(options, function() {
    loadData.then(function(loadedFileData) {
      prepareTrials(loadedFileData).then(function(trials) {
        runExperiment(trials, options, function() {
          runPostQuestionnaire(options);
        });
      });
    });
  });
});
