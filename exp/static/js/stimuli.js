////////////////////////////////////////////////////////////////////////////////
// LOAD IN STIMULI AND PREPARE TRIALS //////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

// define a 'promise' to load in the data from wordpool csv
var loadData = function(){
  return new Promise(
    function(resolve, reject) {
      $.post( "/loadstim")
        .done( function(resp) {
        resolve(resp.message)
      })
    }
)};

var getFirstList = function(){
  return new Promise(
    function(resolve, reject) {
      $.get( "/nextlist", {currentListNumber: 0})
        .done(function(data) {
          console.log(data)
          parseJSON(data['message'])
          .then(function(parsed){
            formatList(parsed)
            .then(function(result){
              resolve(result)
            })
          })
      })
    }
  )};


var parseJSON = function(egg_json) {
  return new Promise(
    function(resolve, reject) {
      parsed = JSON.parse(egg_json)
      resolve(parsed)
    }
  )
}


var formatList = function(egg) {
  return new Promise(
    function(resolve, reject) {
          listArray=[]
          for (var idx = 0; idx < listLength; idx++) {

              //elements of the first row of data
              var word = egg.pres["0"][idx];
              var size = egg.features["0"][idx].size;
              var category = egg.features["0"][idx].category;

              //create a stimulus for each element of the data and push it to the stimArray
              var stim = {
                  type: "p",
                  text: word, //inserts the word from each row of csv file
                  length: word.length,
                  size: size,
                  category: category
              };

              //relative positioning specific to 5vw courier
              var height_range = Math.random() * 85;
              var width_range = Math.random() * (100 - word.length * 3);

              stim.pos = {
                  x: width_range,
                  y: height_range
              }

              // set color of the word
              var r = Math.floor(Math.random() * 255);
              var g = Math.floor(Math.random() * 255);
              var b = Math.floor(Math.random() * 255);

              stim.rgb = {
                  red: r,
                  green: g,
                  blue: b
              }

              stim.style = [
                  "color:rgb(" + r + ',' + g + ',' + b + ')',
                  "font-size:5vw",
                  "font-family:courier", // uses randomly assigned rgb, x, and y values
                  "position:absolute",
                  "top:" + height_range + "%", // relative positioning
                  "left:" + width_range + "%"
              ];

              // adding a 'features' object to each stimulus to make the organization easier
              stim.features = {
                  size: size,
                  category: category,
                  firstLetter: word[0],
                  location: {
                      x: width_range,
                      y: height_range
                  },
                  color: {
                      red: r,
                      green: g,
                      blue: b
                  },
                  wordLength: word.length
              };
              listArray.push(stim)
          };
          resolve(listArray)
      })
    }

// takes the data and organizes it into an array of stim objects
var prepareTrials = function(data) {
    return new Promise(
        function(resolve, reject) {

            // the first element is a header, not data so let's get rid of it.
            data.shift()

            //sort each element of the data and label its properties
            for (var i = 0; i < numberOfLists; i++) {

                stimArray.push([]);
                var list_array = stimArray[i];

                for (var j = 0; j < listLength; j++) {

                    var item = data[0]; //first row in data

                    //elements of the first row of data
                    var word = item[0];
                    var size = item[1];
                    var category = item[2];
                    var listid = item[3]

                    //create a stimulus for each element of the data and push it to the stimArray
                    var stim = {
                        type: "p",
                        text: word, //inserts the word from each row of csv file
                        length: word.length,
                        size: size,
                        category: category,
                        listid: listid
                    };

                    //relative positioning specific to 5vw courier
                    var height_range = Math.random() * 85;
                    var width_range = Math.random() * (100 - word.length * 3);

                    stim.pos = {
                        x: width_range,
                        y: height_range
                    }

                    // set color of the word
                    var r = Math.floor(Math.random() * 255);
                    var g = Math.floor(Math.random() * 255);
                    var b = Math.floor(Math.random() * 255);

                    stim.rgb = {
                        red: r,
                        green: g,
                        blue: b
                    }

                    stim.style = [
                        "color:rgb(" + r + ',' + g + ',' + b + ')',
                        "font-size:5vw",
                        "font-family:courier", // uses randomly assigned rgb, x, and y values
                        "position:absolute",
                        "top:" + height_range + "%", // relative positioning
                        "left:" + width_range + "%"
                    ];

                    // adding a 'features' object to each stimulus to make the organization easier
                    stim.features = {
                        size: size,
                        category: category,
                        firstLetter: word[0],
                        location: {
                            x: width_range,
                            y: height_range
                        },
                        color: {
                            red: r,
                            green: g,
                            blue: b
                        },
                        wordLength: word.length
                    }

                    list_array.push(stim)
                    data.shift();
                }
            }
            resolve(stimArray)
        })
};
