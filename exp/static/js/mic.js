var testString = "CHECK ONE TWO"; //string for microphone test
var testPass = false; //for microphone test conditionals
var practicePass = false;

var runMicTest = function(options, cb) {
    if (options.mode==='lab') {

        var micTestTimeline = []; //create the jsPsych instructionsmicTestTimelinevariable

        // instructions for microphone test
        var micInstructions2 = {
            type: 'text',
            text: "<div class='instructions'><p> Let's test your microphone.  Please say <strong>'" + testString + "'</strong> when you see the <i style='color:red' class='fa fa-microphone'></i>.</p>" +
                "<p>Press any key to do the test.</p></div>",
            is_html: true
        }
        micTestTimeline.push(micInstructions2);

        // create the mic test
        var micTest = {
            type: 'call-function',
            func: testMic,
            timing_post_trial: 10000,
        };
        micTestTimeline.push(micTest);

        // go to this trial if the mic test fails
        var fail = {
            type: 'text',
            text: "<div class='instructions'><p>The test didn't work...</p><p>Please say <strong>'" + testString + "'</strong> clearly and close to the microphone.</p>" +
                "<p>Press any key to try again.</p></div>",
            is_html: true,
            on_finish: function() {
                if (annyang) {
                    annyang.abort();
                }
            }
        }

        // keep looping until the mic test works...maybe we want to have some cap?
        var fail_loop = {
            timeline: [fail, micTest],
            loop_function: function() {
                if (testPass === false) {
                    debug.log("Microphone test failed!")
                    return true;
                } else if (testPass === true) {
                    return false;
                }
            }
        };

        // only go into the fail loop if the mic test doesn't work
        var if_failed = {
            timeline: [fail_loop],
            conditional_function: function() {
                if (testPass === false) {
                    return true;
                } else if (testPass === true) {
                    return false;
                }
            }
        };
        micTestTimeline.push(if_failed);

        // here is where we use jspsych to run the experimentmicTestTimeline that we created above
        jsPsych.init({
            timeline: micTestTimeline,
            // fullscreen: true,
            on_finish: function() {
                $(".jspsych-display-element").remove();
                cb();
                psiTurk.saveData({
                    success: function() {
                        console.log("Mic Test Complete!");
                    }
                });
            },
            on_data_update: function(data) {
                psiTurk.recordTrialData(data);
            }
        });
    } else {
        cb();
    }
};

////////////////////////////////////////////////////////////////////////////////
// HELPER FUNCTIONS ////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

// create a function to show a plus sign at the beginning of recording
var testMic = function() {
    var $mic = $("<p class='mic' style='position:absolute;top:35%;left:47%;font-size:10vw;color:red'><i class='fa fa-microphone blink_me'></i></p>")
    $(".jspsych-display-element").append($mic);
    if (annyang) {
        var test = function(check) {
            var capTest = check.toUpperCase();
            console.log('Checked ' + capTest + '.');
            var testVal = capTest.localeCompare(testString);
            if (testVal === 0) {
                testPass = true;
                console.log('test passed');
                $(".mic").remove();
                $micSuccessMessage = $("<p id='mic-success-message' class='instructions'>That's it! Your microphone works. You will now enter fullscreen mode for the duration of the experiment.</p>")
                $(".jspsych-display-element").append($micSuccessMessage);
                annyang.abort();
                return testPass
            } else {
                testPass = false;
                return testPass
            }
        }
    }
    var abort = function() {
        annyang.abort();
    };

    // Define commands
    var commandsTest = {
        '*check': test,
        'turn off mic(rophone)': abort
    };

    annyang.debug(); // Debug info for the console
    annyang.addCommands(commandsTest); // Initialize annyang with our commands
    annyang.start();
    console.log('Microphone turned on.');
    startTimer(10000);
};
