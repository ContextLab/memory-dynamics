var Fingerprint = function(params) {

    console.log('Initializing fingerprint...')

    //////////////////////////////////////////////////////////////////////////////
    // defaults //////////////////////////////////////////////////////////////////
    //////////////////////////////////////////////////////////////////////////////

    // unless assigned, the state will be set to none
    var state = params.state || 'none';

    // features will be set automatically if not defined
    var features = params.features || ['category', 'size', 'firstLetter', 'wordLength', 'location', 'color'];

    // allows for a weights 'prior'
    var weights = params.weights || null;

    // gain parameter for feature stick
    var alpha = params.alpha || 4;

    // gain parameter for stimulus stick
    var tau = params.tau || 1;

    // if sorting by a feature, this is the feature to sort by
    var sortby = params.sortby || null;

    //////////////////////////////////////////////////////////////////////////////
    // public functions //////////////////////////////////////////////////////////
    //////////////////////////////////////////////////////////////////////////////

    // compute the fingerprint
    function computeWeights(currentList, recalledWords) {

      try {
        // get the distances
        var currentList = _computeDistance(currentList);

        // return the fingerprint
        return _computeFeatureWeights(currentList, recalledWords, features);
      } catch (e) {
        console.log('There was an error computing the fingerprint:', e)
        return _defaultFingerprint()
      }
    };

    //update the fingerprint
    // ADD IN LOGIC TO DO A WEIGHTED AVERAGE??
    function updateWeights(newWeights) {

        // loop over features and average in the new weights, if weights exists
        if (weights) {
            console.log('weights exist, updating..')
            for (feature in weights) {
                weights[feature].push(newWeights[feature]);
            }
        } else {
            weights = {};
            for (feature in newWeights) {
                weights[feature] = [];
                weights[feature].push(newWeights[feature]);
            }
        };
        console.log('updated weights: ', weights)
    };

    // return the reordered list
    function getReorderedList(nextList) {
        console.log('Reordering list according to state: ' + state)
        switch (state) {

            case 'feature-based':
                return _featurizeList(nextList)
            case 'random':
                return _randomizeList(nextList)
            case 'optimal':
                return _optimizeList(nextList)
            case 'opposite':
                return _oppositizeList(nextList)
            case 'strip-features':
                return _stripFeatures(nextList)
            case 'none':
                console.warn('Warning: No fingerprint state assigned, returning same list..')
                return nextList
        }
    };

    // function to get the current state
    function getState() {
        return state
    };

    // function to get the current weights
    function getWeights() {
        return weights
    };

    // function to get the current weights
    function getAvgWeights() {
        if (weights) {
            avgWeights = {};
            for (feature in weights) {
                avgWeights[feature] = _mean(weights[feature])
            }
        }
        return avgWeights
    };

    // function to change the fingerprint state
    function changeState(newState) {
        state = newState;
    };

    function orderByFeature(list, feature) {

        var listLocal = list.slice();

        // if distances don't exist compute them
        if (!listLocal.distances) {
            listLocal = _computeDistance(listLocal)
        }

        // pick a starting word
        var reorderedlistLocal = [];
        var stimIdx = _getRandomIntInclusive(0, listLocal.length - 1);

        // remove the word from the distance object of all stimuli
        listLocal.forEach(function(stimulus) {
            for (featuren in stimulus.distances) {
                stimulus.distances[featuren].splice(stimIdx, 1);
            }
        })
        reorderedlistLocal.push(listLocal[stimIdx]) // add this stimulus to the reordered listLocal array
        var stim = listLocal[stimIdx]
        listLocal.splice(stimIdx, 1) // remove it from the unordered listLocal

        while (listLocal.length >= 1) {

            // grab the feature vector for the current stim and sort it
            var featureVec = stim.distances[feature]
            featureVec.sort(function(a, b) {
                return a.dist - b.dist
            })

            // the next word will be...
            var nextWord = featureVec[0].word;
            var stimIdx = listLocal.map(function(stimulus) {
                return stimulus.text
            }).indexOf(nextWord);

            // remove the word from the distance object of all stimuli
            listLocal.forEach(function(stimulus) {
                for (featuren in stimulus.distances) {
                    stimulus.distances[featuren].splice(stimIdx, 1);
                }
            })

            // push to reordered listLocal
            reorderedlistLocal.push(listLocal[stimIdx]) // add this stimulus to the reordered listLocal array

            // redefine stim
            var stim = listLocal[stimIdx]

            // take that stim out of the listLocal
            listLocal.splice(stimIdx, 1) // remove it from the unordered listLocal

        };
        return reorderedlistLocal
    };

    //////////////////////////////////////////////////////////////////////////////
    // private functions /////////////////////////////////////////////////////////
    //////////////////////////////////////////////////////////////////////////////

    // return the default fingerprint
    var _defaultFingerprint = function () {
      var dfingerprint = {};
      features.forEach(function(feature){
        dfingerprint[feature] = .5;
      })
      return dfingerprint
    }

    // compute distances
    var _computeDistance = function(stimArray) {

        // initialize distance object
        stimArray.forEach(function(stimulus) {
            stimulus.distances = {};
            for (feature in stimulus.features) {
                stimulus.distances[feature] = [];
            }
        });

        // loop over the lists to create distance matrices
        for (var i = 0; i < stimArray.length; i++) {
            for (var j = 0; j < stimArray.length; j++) {

                // logic for category
                stimArray[i].distances.category.push({
                    word: stimArray[j].text,
                    dist: stimArray[i].features.category !== stimArray[j].features.category ? 1 : 0
                })

                // logic for size
                stimArray[i].distances.size.push({
                    word: stimArray[j].text,
                    dist: stimArray[i].features.size !== stimArray[j].features.size ? 1 : 0
                })

                // logic for first letter
                // DO THIS BASED ON THE NUMBER OF LETTERS APART
                stimArray[i].distances.firstLetter.push({
                    word: stimArray[j].text,
                    dist: stimArray[i].features.firstLetter !== stimArray[j].features.firstLetter ? 1 : 0
                })

                // logic for word length
                stimArray[i].distances.wordLength.push({
                    word: stimArray[j].text,
                    dist: Math.abs(stimArray[i].features.wordLength - stimArray[j].features.wordLength)
                });

                // logic for color distance
                stimArray[i].distances.color.push({
                    word: stimArray[j].text,
                    dist: Math.sqrt(Math.pow(stimArray[i].features.color.red - stimArray[j].features.color.red, 2) + Math.pow(stimArray[i].features.color.green - stimArray[j].features.color.green, 2) +
                        Math.pow(stimArray[i].features.color.blue - stimArray[j].features.color.blue, 2)).toFixed(2)
                });

                // logic for spatial distance
                stimArray[i].distances.location.push({
                    word: stimArray[j].text,
                    dist: Math.sqrt(Math.pow(stimArray[i].features.location.x - stimArray[j].features.location.x, 2) + Math.pow(stimArray[i].features.location.y - stimArray[j].features.location.y, 2)).toFixed(2)
                });
            };
        };
        return stimArray
    };

    function _computeFeatureWeights(currentList, recalledWords, features) {

        // initialize the weights object for just this list
        var listWeights = {};
        features.forEach(function(feature) {
            listWeights[feature] = [];
        })

        if (recalledWords.length <= 2) {
            console.log('Not enough recalls to compute fingerprint, returning default fingerprint.. (everything is .5)')
            features.forEach(function(feature) {
                listWeights[feature] = .5;
            })
            return listWeights
        }

        pastWords = [];

        // finger print analysis
        for (var i = 0; i < recalledWords.length - 1; i++) {

            // grab current word
            var currentWord = recalledWords[i];
            // console.log('currentWord', currentWord)

            // grab the next word
            var nextWord = recalledWords[i + 1];
            // console.log('nextWord', nextWord)

            var currentWordIdx = currentList.map(function(stimulus) {
                return stimulus.text
            }).indexOf(currentWord);

            var nextWordIdx = currentList.map(function(stimulus) {
                return stimulus.text
            }).indexOf(nextWord);

            // console.log('idx of current word',currentWordIdx)
            pastWords.push(currentWord)
                // console.log('past words',pastWords)

            if (currentWordIdx !== -1 && nextWordIdx !== -1) {

                features.forEach(function(feature) {

                    // get the distance vector for the current word
                    var distVec = currentList[currentWordIdx].distances[feature];

                    filteredDistVec = [];
                    distVec.forEach(function(word) {
                        if (word.word in pastWords) {} else {
                            filteredDistVec.push(word)
                        }
                    })

                    // sort distWords by distances
                    filteredDistVec.sort(function(a, b) {
                        return a.dist - b.dist
                    })

                    // console.log('sorted distances: ')
                    // filteredDistVec.forEach(function(word){
                    //   console.log(word)
                    // })

                    //compute the category listWeights
                    // HERE IS WHERE WE HAVE TO IMPLEMENT CORRECTION FOR THE BINARY FEATURES
                    // listWeights[feature].push(1 - distWords.map(function(word){
                    //   return word.word}).indexOf(nextWord)/distWords.length)
                    var nextWordIdx = filteredDistVec.map(function(word) {
                        return word.word
                    }).indexOf(nextWord);
                    // console.log('nextWord: ',nextWord)
                    // console.log('nextWordIdx: ',nextWordIdx)

                    idxs = [];
                    filteredDistVec.forEach(function(word, idx) {
                        if (filteredDistVec[nextWordIdx].dist === word.dist) {
                            idxs.push(idx)
                        }
                    });

                    listWeights[feature].push(1 - (idxs.reduce(function(a, b) {
                        return a + b
                    }) / idxs.length) / filteredDistVec.length);

                    // console.log('idxs',idxs)
                    // console.log('idxs length', idxs.length)
                    // console.log('dist words length',filteredDistVec.length)
                    pastWords.push(currentWord)
                })
            }
        }
        // console.log('weight array', listWeights)

        // average the distances within a feature
        for (feature in listWeights) {
            listWeights[feature] = listWeights[feature].reduce(function(a, b) {
                return a + b
            }) / listWeights[feature].length;
        }
        // console.log('averaged listWeights: ', listWeights)
        return listWeights
    };

    function _computeRecall(currentList, recalledWords) {
        listWords = [];
        currentList.forEach(function(stim) {
            listWords.push(stim.text.toUpperCase())
        })
        var recallVec = Array(listWords.length).fill(0);
        recalledWords.forEach(function(word, idx) {
            recallVec[idx] = listWords.indexOf(word);
        })
        return recallVec
    };

    // function that sorts each list by a particular stimulus feature
    function _featurizeList(stimArray) {

      var listLocal = stimArray.slice();

      // if distances don't exist compute them
      if (!listLocal.distances) {
          listLocal = _computeDistance(listLocal)
      }

      return orderByFeature(listLocal, sortby)

    };

    // function that returns optimized list
    function _optimizeList(nextList) {
        // console.log('Returning optimal list..')

        // copy the list
        var list = nextList.slice(0)

        // get the distances
        if (!list.distances) {
            list = _computeDistance(list);
        }

        // compute average weights
        var avgWeights = getAvgWeights(weights);

        // compute feature stick
        var featureStick = _computeFeatureStick(avgWeights, alpha);

        return _reorderList(list, featureStick, tau)

    };

    // function that returns list opposite of fingerprint
    function _oppositizeList(nextList) {

        // copy the list
        var list = nextList.slice(0)

        // get the distances
        if (!list.distances) {
            list = _computeDistance(list);
        }

        // compute average weights
        var avgWeights = getAvgWeights(weights);

        // mapping weights to an array to compute the min
        var arr = Object.keys(avgWeights).map(function(key) {
            return -avgWeights[key];
        });
        var min = Math.min.apply(null, arr);
        var mean = _mean(arr);

        invertedWeights = {}
        for (feature in avgWeights) {
            invertedWeights[feature] = (-avgWeights[feature] - mean - min).toFixed(2);
        };
        // console.log('weights: ', weights)
        // console.log('inverted weights: ', invertedWeights)

        var invertedFeatureStick = _computeFeatureStick(invertedWeights, alpha);

        return _reorderList(list, invertedFeatureStick, tau)
    };

    // function that returns randomized list
    function _randomizeList(nextList) {

        // copy the list
        var list = nextList.slice(0)

        // console.log('inside randomize next list', nextList)
        // get the distances
        var list = _computeDistance(list);

        var reorderedList = [];

        // starting with a random word
        while (list.length > 0) {

            var stimIdx = _getRandomIntInclusive(0, list.length - 1);
            reorderedList.push(list[stimIdx]) // add this stimulus to the reordered list array
            list.splice(stimIdx, 1) // remove it from the unordered list
        };
        return reorderedList
    };

    // function that strips features from the list
    function _stripFeatures(nextList) {

        // copy the list
        var list = nextList.slice(0)

        var reorderedList = [];

        // starting with a random word
        while (list.length > 0) {

            var stimIdx = _getRandomIntInclusive(0, list.length - 1);

            // here is where we will strip the features
            var strippedTrial = list[stimIdx]
            strippedTrial.style[4] = 'top:50%'
            strippedTrial.style[5] = 'left:50%'
            strippedTrial.style.splice(0,1)
            strippedTrial.style.push('position:absolute')
            strippedTrial.style.push('transform: translateX(-50%) translateY(-50%)')
            reorderedList.push(strippedTrial) // add this stimulus to the reordered list array
            list.splice(stimIdx, 1) // remove it from the unordered list
        };
        return reorderedList
    };

    function _computeFeatureStick(wts, alpha) {
        // creating 'stick' of feature weights
        var featureStick = [];
        for (feature in wts) {
            // console.log(Math.pow(wts[feature],alpha))
            featureStick.push(Array(Math.round(Math.pow(wts[feature], alpha) * 100)).fill(feature))
        }
        featureStick = [].concat.apply([], featureStick);
        // console.log('featureStick',featureStick)
        return featureStick
    }

    function _reorderList(nextList, featureStick, tau) {

        // starting with a random word
        var reorderedList = [];
        var stimIdx = _getRandomIntInclusive(0, nextList.length - 1);

        // console.log(nextList)

        // remove the word from the distance object of all stimuli
        nextList.forEach(function(stimulus) {
            for (feature in stimulus.distances) {
                stimulus.distances[feature].splice(stimIdx, 1);
            }
        })
        reorderedList.push(nextList[stimIdx]) // add this stimulus to the reordered list array
        nextList.splice(stimIdx, 1) // remove it from the unordered list

        // console.log('word: ',reorderedList[reorderedList.length-1])

        while (nextList.length > 0) {

            // sample from the stick
            var featureStickSample = featureStick[_getRandomIntInclusive(0, featureStick.length - 1)]
                // console.log('Feature stick sample: ', featureStickSample)

            var wordWeights = reorderedList[reorderedList.length - 1].distances[featureStickSample].map(function(distance) {
                return distance.dist
            });

            var max = Math.max.apply(null, wordWeights);
            wordWeights = wordWeights.map(function(distance) {
                if (distance === 0) {
                    return distance
                } else {
                    return distance / max
                }
            });

            var min = Math.min.apply(null, wordWeights.map(function(word) {
                return -word
            }));

            invertedWordWeights = wordWeights.map(function(weight) {
                    return -weight - min + .01
                })
                // console.log('weight', wordWeights)
                // console.log('inverted weight', invertedWordWeights)

            // create a stick representing the stimuli to chose from
            var wordStick = invertedWordWeights.map(function(weight, idx) {
                return Array(Math.round(Math.pow(weight, tau) * 100)).fill(idx)
            })

            wordStick = [].concat.apply([], wordStick);
            var wordStickSample = wordStick[_getRandomIntInclusive(0, wordStick.length - 1)]
                // console.log('word stick: ', wordStick)
                // console.log('word stick sample: ', wordStickSample)
                // console.log('chose the word:', nextList[wordStickSample])

            // remove the word from the distance object of all stimuli
            nextList.forEach(function(stimulus) {
                for (feature in stimulus.distances) {
                    stimulus.distances[feature].splice(wordStickSample, 1);
                }
            })
            reorderedList.push(nextList[wordStickSample]) // add this stimulus to the reordered list array
            nextList.splice(wordStickSample, 1) // remove it from the unordered list
        };
        // console.log('reordered list: ', reorderedList)
        return reorderedList
    }

    function _getRandomIntInclusive(min, max) {
        min = Math.ceil(min);
        max = Math.floor(max);
        return Math.floor(Math.random() * (max - min + 1)) + min;
    };

    function _mean(array) {
        var sum = array.reduce(function(a, b) {
            return a + b;
        });
        return sum / array.length;
    }

    // return the public functions
    return {
        computeWeights: computeWeights,
        updateWeights: updateWeights,
        getReorderedList: getReorderedList,
        getState: getState,
        getWeights: getWeights,
        getAvgWeights: getAvgWeights,
        changeState: changeState,
        orderByFeature: orderByFeature
    }
};
