if (mode === 'debug') {
    var listLength = 3; // how long you want each list to be
    var numberOfLists = 3; // number of study/test blocks
    var recordTime = 15; //record time in s
} else {
    var listLength = 16; // how long you want each list to be
    var numberOfLists = 16; // number of study/test blocks
    var recordTime = 60; //record time in s
}

var wordsCorrect; //number of matched words for each trial


var stimArray = []; //create an array for stimuli
var experimentTimeline = []; //create the jsPsych experimentTimeline variable
var data = { //data object to keep track of recalled words
    listWords: [],
    recalledWords: [],
    correctWords: []
};

var runExperiment = function(currentStimArray, options, cb) {

    if (mode === 'lab') {
        var instructionsTimeline = setupInstructions();
        instructionsTimeline.forEach(function(instruction) {
            experimentTimeline.push(instruction)
        });
    };

    // shuffle list order across subjects
    // var shuffledLists = jsPsych.randomization.shuffle(stimArray)

    // shuffle stim within each list
    // var shuffledStimArray = [];
    // shuffledLists.forEach(function(list, idx) {
    //     shuffledStimArray.push(jsPsych.randomization.shuffle(shuffledLists[idx]))
    // })

    // initialize counter for lists and trials
    currentListNumber = 0;
    currentTrialNumber = 0;
    currentListWords = [];
    console.log(currentStimArray)

    // create the lists
    for (var listNumber = 0; listNumber <= numberOfLists - 1; listNumber++) {

        data.listWords.push([]);

        // this trial reorders a list given the fingerprint state
        var reorderList = {
          type: 'reorder-list',
          stimulus: "<p style='color:green;' class='loading'><i class='fa fa-cog fa-spin '></i></p>",
          data: {uniqueId : uniqueId,
            currentListNumber : listNumber,
            strategy : fingerprintStateArray[listNumber]},

        }
        experimentTimeline.push(reorderList)

        // reminder before starting each list
        var preList = {
            type: "text",
            text: "<div style='font-size:30px' class='instructions'><p><b>Remember:</b> You will see a list of words and then when you see the <i style='color:red' class='fa fa-microphone'></i> you will recite back as many as you can remember. Please speak clearly, slowly and about 1-2 feet from your microphone. When you are ready to see list " + (listNumber + 1) + ", press any key.</p></div>"
        }
        experimentTimeline.push(preList);

        //create block of trials
        for (var trialNumber = 0; trialNumber < listLength; trialNumber++) {
            var trial = {
                type: 'single-stim',
                // stimulus: stim,
                stimulus: function() {
                    console.log('trial number', currentTrialNumber)
                    console.log('stimulus', window.currentStimArray[currentTrialNumber % listLength])
                    return stimHTMLFormatter(window.currentStimArray[currentTrialNumber % listLength])
                },
                is_html: true,
                choices: 'none',
                timing_response: 2000,
                timing_post_trial: 2000,
                data: {
                    listNumber: listNumber,
                    trialNumber: trialNumber
                },
                on_finish: function() {
                    currentListWords.push(currentStimArray[window.currentTrialNumber % listLength].text)
                    currentTrialNumber++ // update trial number after each trial
                }
            }
            experimentTimeline.push(trial);
        };

        // pause before the recall period
        var preRecitation = {
            type: 'single-stim',
            stimulus: "<div class='instructions'><p> When you see the <i style='color:red' class='fa fa-microphone'></i>, recall as many words as you can.</p><p> Please remember to speak <strong>clearly</strong> and pause for about 2 seconds between each word.</p></div>",
            is_html: true,
            choices: 'none',
            timing_response: 3000,
        };
        experimentTimeline.push(preRecitation);

        var recall = {
              type: 'free-recall',
              stimulus: "<p class='mic'><i class='fa fa-microphone blink_me'></i></p>",
              stim_duration: recordTime * 1000,
              trial_duration: recordTime * 1000 + 2000,
              record_audio: true,
              speech_recognition: 'google',
              data: {
                  listNumber: listNumber,
                  state: fingerprintStateArray[listNumber],
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
        experimentTimeline.push(recall);

        // this trial presents spinning wheel while audio is decoded
        var decodeSpeech = {
          type: 'decode-speech',
          stimulus: "<p style='color:red;' class='loading'><i class='fa fa-cog fa-spin'></i></p>",
          data: {uniqueId : uniqueId,
            currentListNumber : listNumber},

        }
        experimentTimeline.push(decodeSpeech)

        // this trial presents spinning wheel while fingerprint is updated
        var updateFingerprint = {
          type: 'update-fingerprint',
          stimulus: "<p style='color:orange;' class='loading'><i class='fa fa-cog fa-spin '></i></p>",
          data: {uniqueId : uniqueId,
            currentListNumber : listNumber},
          on_finish : function() {
            currentList = []; // reset currentList array
            currentTrialNumber = 0; // reset trial number counter
            currentListNumber++ // add to list counter
          }
        }
        experimentTimeline.push(updateFingerprint)
    };


    console.log(experimentTimeline)

    // here is where we use jspsych to run the experimentTimeline that we created above
    jsPsych.init({
        timeline: experimentTimeline,
        fullscreen: true,
        on_finish: function() {
            if (mode === 'lab') {
                psiTurk.saveData({
                    success: function() {
                        $.get("/onfinish", {
                            uniqueId : uniqueId
                        }).done(function(result){
                          console.log(result)
                          cb();
                        });
                    }
                })
            } else {
              $.get("/onfinish", {
                  uniqueId : uniqueId
              }).done(function(result){
                console.log(result)
                cb();
              });
            }
        },
        on_data_update: function(data) {
            if (mode === 'lab') {
                psiTurk.recordTrialData(data);
            }
        }
    })
}; // closes runExperiment
