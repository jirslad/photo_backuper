from pathlib import Path
import sys
import os
import threading
import time
import shutil # TODO: for testing
from datetime import datetime

from flask import Flask, render_template, request
from flask_socketio import SocketIO
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import InputRequired
import sqlite3
from dotenv import load_dotenv

from photo_backuper.backuper import Backuper

# TODO: remove, but make it work even without photo_backuper package installed
folder_path = Path(__file__).parents[0]
sys.path.append(folder_path)

app = Flask(__name__)
load_dotenv()
app.config['SECRET_KEY'] = os.environ.get('APP_KEY')
socketio = SocketIO(app)

# copy files for demonstration purposes
demo_data = folder_path.parents[0] / r"data\IMAGES"
demo_data_original = folder_path.parents[0] / r"data\IMAGES_original"
shutil.rmtree(demo_data, ignore_errors=True)
shutil.copytree(demo_data_original, demo_data)
# shutil.rmtree(r"D:/initial_state" , ignore_errors=True)
# shutil.copytree(r"D:/initial_state_original", r"D:/initial_state")

class InputForm(FlaskForm):
    mode_choices = [x for x in zip(Backuper.MODES, Backuper.MODES_NAMES)]
    mode = SelectField("Mode label", choices=mode_choices, coerce=str,
                       validators=[InputRequired("Mode required")])
    utility_folder = StringField("Utility Folder", validators=[InputRequired("Utility folder required")])
    source_folder = StringField("Source Folder")
    target_folder = StringField("Target Folder")
    run_button = SubmitField("Run Mode")

def execute_query(db_path, query, *args):
    '''Connect to database and execute query.
    Args:
        db_path: path-like object
    '''
    try:
        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            cur.execute(query, args)
            con.commit()
            if query.strip().upper().startswith("SELECT"):
                rows = cur.fetchall()
                column_names = [desc[0] for desc in cur.description]
                return [dict(zip(column_names, row)) for row in rows]
            return None
    except sqlite3.Error as e:
         print(e)

# create database
db_path = folder_path / "logs.db"
query = """
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    mode TEXT NOT NULL,
    utility_folder TEXT NOT NULL,
    source_folder TEXT NOT NULL,
    target_folder TEXT NOT NULL
)
"""
execute_query(db_path, query)


@app.route("/", methods=["GET", "POST"])
def index():

    log_count = execute_query(db_path, "SELECT COUNT() FROM logs")[0]["COUNT()"]
    if log_count:
        last_log = execute_query(db_path, "SELECT * FROM logs WHERE id = (SELECT MAX(id) FROM logs) ")[0]
        input_form = InputForm(
            mode=last_log["mode"],
            utility_folder=last_log["utility_folder"],
            source_folder=last_log["source_folder"],
            target_folder=last_log["target_folder"]
        )
    else:
        input_form = InputForm()

    validation_message = ""
    if input_form.validate_on_submit():
        mode = input_form.mode.data
        utility_folder = input_form.utility_folder.data # D:/initial_state/source   'C:/Python_notebooks/photo_backuper/data/IMAGES/source'
        source_folder = input_form.source_folder.data   # D:/initial_state/source   'C:/Python_notebooks/photo_backuper/data/IMAGES/source'
        target_folder = input_form.target_folder.data   # D:/initial_state/target   'C:/Python_notebooks/photo_backuper/data/IMAGES/target'
        
        # mode-specific validation
        if mode != Backuper.MODES[0] and not (source_folder and target_folder):
            validation_message += "For selected mode, both source and target folders must be specified.\n"
        else:
            # log history to database
            timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            query = """
            INSERT INTO logs (timestamp, mode, utility_folder, source_folder, target_folder)
            VALUES (?, ?, ?, ?, ?)
            """
            execute_query(db_path, query, timestamp, mode, utility_folder, source_folder, target_folder)

            # define backuper
            def run_backuper():
                time.sleep(0.5) # delay to render template before logging any messages

                backuper = Backuper(mode, utility_folder, source_folder, target_folder)
                match mode:
                    case "initialize":
                        message = backuper.mode_initialize_settings()
                        socketio.emit('backup_message', {'message': message})
                    case "new_folders":
                        for message in backuper.generator_backup_new_folders():
                            socketio.emit('backup_message', {'message': message})
                        socketio.emit('backup_message',
                                      {'message':"Autogenerating lists of project folders with raw files..."})   
                        backuper.autogen_project_folders_with_raw()
                        socketio.emit('backup_message', {'message': "Backing up finished successfully."})
                    case "modified_folders":
                        for message in backuper.generator_backup_modified_folders():
                            socketio.emit('backup_message', {'message': message})
                        socketio.emit('backup_message',
                                      {'message':"Autogenerating lists of project folders with raw files..."})   
                        backuper.autogen_project_folders_with_raw()
                        socketio.emit('backup_message', {'message': "Backing up finished successfully."})

            # call backuper and continuously log results
            thread = threading.Thread(target=run_backuper)
            thread.start()
    # validation errors
    if input_form.errors:
        for var, msgs in input_form.errors.items():
            validation_message += f"{var}: {msgs[0]}\n"

    return render_template("index.html", input_form=input_form, validation_message=validation_message)


@app.route("/logs", methods=["GET", "POST"])
def show_logs():
    if request.method == "POST":
        log_id = request.form.get("log_id")
        delete_all = bool(request.form.get("delete_all"))
        if log_id:
            execute_query(db_path, "DELETE FROM logs WHERE id = ?", log_id)
        elif delete_all:
            execute_query(db_path, "DELETE FROM logs")

    logs = execute_query(db_path, "SELECT * FROM logs")
    
    return render_template("logs.html", logs=logs)


if __name__ == "__main__":
    app.run(debug=True)

