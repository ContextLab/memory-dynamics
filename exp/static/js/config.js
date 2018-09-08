////////////////////////////////////////////////////////////////////////////////
// INITIALIZE EXPERIMENT VARIABLES /////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

// collects custom ID and experimenter name if run in the lab
mode = 'lab';

// Initalize psiturk object
var psiTurk = new PsiTurk(uniqueId, adServerLoc, mode);

////////////////////////////////////////////////////////////////////////////////
// CONFIGURE FINGERPRINT ///////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

// how many lists?
var numLists = 16;

// define counterbalances
var counterbalance =  [["random", "stabilize", "destabilize"],
                      ["random", "destabilize", "stabilize"],
                      ["stabilize", "random", "destabilize"],
                      ["stabilize", "destabilize", "random"],
                      ["destabilize", "stabilize", "random"],
                      ["destabilize", "random", "stabilize"]]

if (mode === 'debug') {

  var subnum=3

  var listOrder = []
  counterbalance[subnum % 6].forEach(function(condition){
    for (i = 0; i < 4; i++) {
      listOrder.push(condition)
    }
  })

  // generate fingerprint states array
  var fingerprintStateArray = Array(4).fill('random').concat(listOrder);
  console.log(fingerprintStateArray)
}

// create empty folder for audio files
$.post("/createaudiofolder", {
    "data": uniqueId
});

annyang.start({ autoRestart: false });
