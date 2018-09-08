var runInfo = function(options, cb) {
    infoTimeline = [];
    if (options.mode === 'lab') {
        // defining groups of questions that will go together.
        var subjectID = {
            type: 'survey-text',
            questions: ["Subject ID: ", "Subject Number: ", "Experimenter Name: "],
        };
        infoTimeline.push(subjectID)

        jsPsych.init({
            timeline: infoTimeline,
            // fullscreen: true,
            on_finish: function() {
                $('.jspsych-display-element').remove();
                psiTurk.saveData({
                    success: function() {
                        console.log("Info Collected!");
                        var subnum = parseInt(JSON.parse(jsPsych.data.getLastTrialData().responses).Q1); // getting the recalled words
                        console.log('subnum', subnum)

                        var listOrder = []
                        counterbalance[subnum % 6].forEach(function(condition){
                          for (i = 0; i < 4; i++) {
                            listOrder.push(condition)
                          }
                        })

                        // generate fingerprint states array
                        fingerprintStateArray = Array(4).fill('random').concat(listOrder);

                        console.log(fingerprintStateArray)

                        if (mode === 'lab') {
                            // saving an array of condition labels for each list
                            psiTurk.recordUnstructuredData('conditions', fingerprintStateArray)
                            psiTurk.saveData({
                                success: function() {
                                    console.log('conditions array saved!')
                                }
                            })
                        };
                        cb();
                    }
                });
            },
            on_data_update: function(data) {
                psiTurk.recordTrialData(data);
            }
        })
    } else {
        cb();
    }
};
