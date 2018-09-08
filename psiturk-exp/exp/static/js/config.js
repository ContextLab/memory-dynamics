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

// Initialize fingerprint object
var params = {
  state: 'strip-features',
  features: ['category', 'size', 'firstLetter', 'wordLength', 'location', 'color'],
  alpha: 4,
  tau: 1,
};
var fingerprint = new Fingerprint(params);

// how many lists?
var numLists = 16;

// generate fingerprint states array
var fingerprintStateArray = Array(numLists/2).fill('strip-features');
Array(numLists/2).fill('random').forEach(function(block){
  fingerprintStateArray.push(block)
})

console.log('fingerprintStateArray',fingerprintStateArray)

if (mode === 'lab') {
    // saving an array of condition labels for each list
    psiTurk.recordUnstructuredData('conditions', fingerprintStateArray)
    psiTurk.saveData({
        success: function() {
            console.log('conditions array saved!')
        }
    })
};

// create empty folder for audio files
$.post("/createaudiofolder", {
    "data": uniqueId
});
