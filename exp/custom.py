"""
Custom Flask routes for the memory-dynamics experiment server.

The two routes below handle the audio recordings of participants'
recalls. The jspsych-free-recall plugin records audio in the browser and
POSTs it to /save_audio when each recall trial ends.
/createaudiofolder is called once at the start of each session to create
the directory those files go in.
"""

import re
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request


custom_code = Blueprint('custom_code',
                        __name__,
                        template_folder='templates',
                        static_folder='static')

AUDIO_DIR = Path(__file__).resolve().parent.parent.joinpath('data',
                                                            'raw',
                                                            'recall-audio')

# psiTurk unique IDs are of the form "<workerId>:<assignmentId>". Only
# IDs matching this pattern are accepted, so that a malformed (or
# malicious) request can't write outside AUDIO_DIR.
UNIQUE_ID_PATTERN = re.compile(r'^[\w-]+:[\w-]+$')

# recall types set by the jspsych-free-recall plugin's "recall_type"
# parameter (see exp/static/js/experiment.js)
FILENAME_PATTERN = re.compile(r'^[\w-]+:[\w-]+-(?:delayed|recall|prediction)\.wav$')


@custom_code.route('/createaudiofolder', methods=['POST'])
def create_audio_folder():
    """Create the directory that a participant's recordings are saved to."""
    unique_id = request.form['data']
    if UNIQUE_ID_PATTERN.match(unique_id) is None:
        return jsonify(folderCreated='failure',
                       message=f"Invalid participant ID: {unique_id}"), 400

    participant_dir = AUDIO_DIR.joinpath(unique_id)
    participant_dir.mkdir(parents=True, exist_ok=True)
    current_app.logger.info(f"Created audio folder: {participant_dir}")
    return jsonify(folderCreated='success')


@custom_code.route('/save_audio', methods=['POST'])
def save_audio():
    """Save the audio recording of a single recall trial."""
    filename = request.form['audio-filename']
    foldername = request.form['audio-foldername']
    if (FILENAME_PATTERN.match(filename) is None
            or UNIQUE_ID_PATTERN.match(foldername) is None):
        return jsonify(message=f"Invalid audio filename: {foldername}/{filename}"), 400

    filepath = AUDIO_DIR.joinpath(foldername, filename)
    try:
        request.files['audio-blob'].save(str(filepath))
    except Exception:
        current_app.logger.exception(f"Failed to save audio file: {filepath}")
        return jsonify(message=f"There was an error saving the audio file: {filepath}"), 500

    current_app.logger.info(f"Saved audio file: {filepath}")
    return jsonify(message=f"Successfully saved audio file: {filepath}",
                   fname=str(filepath))
