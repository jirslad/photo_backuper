# Photo Backuper

Photo Backuper is a Python application to programatically back up photographs. Designed and used for my personal workflow needs, it does not simply mirror all photos from one device to another as usual. Instead, it requires photos to be organised into folders in a specific way. The app can back up or move the photos based of various aspects, such as file formal, folder type and others.

The goal of the app is to have a main large-storage external drive containing a folder with the whole structure and all photos. This folder can be backed up to another drive or device. The main computer, on which this app runs on, shall contain the whole structure, but not necessarily all photos for storage reasons. This app allows to store only important files and folders (typically all postprocessed JPEGs and folders with unprocessed photos).

Work in progress, new features to be included. Not recommended for public use.

![Alt text](/docs/imgs/web_showcase_new_folders.png?raw=true "Web Interface")

## Instalation

1. Create virtual environment with python>=3.10

2. Clone the repository.
```
git clone https://github.com/jirslad/photo_backuper.git
cd photo_backuper
```
3. Install photo_backuper local package.
```
pip install -e photo_backuper
```

4. Install requirements for the web interface.
```
pip install -r requirements.txt
```

5. Optionally check correctness of installation on demo data. It should back up a few folders without errors.
```
python main.py --demo --mode new_folders --utility_root data/IMAGES/source --source_folder data/IMAGES/source --target_folder data/IMAGES/target
```


## Application Description

### Glosary

**Folder structure** -- An organised structure of folders all photos are stored in.

**HDD** -- The external drive storing all files. It shall contain the root folder with the whole folder structure and all files. The folder structure gets mirrored from the main PC.

**PC** -- The computer that has the same folder structure as HDD, with the exception of not containing all RAW data.

**Raw data** -- Data to be generally stored only on HDD (such as RAW files, folders with preliminary data). Define in raw_file_types.

**Selection data** -- Data to be also stored on PC (such as folders with finished JPEGs).

**Root folder** -- A single folder containing data organised in the specific folder structure. The root folder contains several location folders. Example: Images.

**Location folder** -- A folder inside the root folder. It is supposed to organise photos into certain geographical locations or areas. Each location folder contains several project folders. Examples: The Himalayas, The Alps, Sahara Desert, Australia.

**Project folder** -- A folder inside a location folder. It is supposed to organise photos into separate photoshoots (from a single day, a single trip or a single project). The project folder contains arbitrary files, some of them are considered as raw data (usually JPEG, RAW formats - file formats defined in a settings file). The project folder may contain selection folders. A project folder should be named in this format: YYYY.MM.DD Project Name.

**Selection folder** -- A folder inside a project folder. It contains a selection of photos. The folders typically contain postprocessed JPEGs or other exported formats for futher processing (e.g. for HDR panoramas).

**Utility folder** -- A folder inside the root folder containing text files with settings of the app. It is typically named as *_photo_backuper* and is created by the app using *initialize* mode. User is supposed to operate these text files while using the app.

**Source** -- The source root folder on the device the photos are being backed up **from**. Currently it must be the main PC (containing utility folder).

**Target** -- The destination root folder on the device the photos are being backed up **to**. Currently it must be the main HDD (containing all photos).

### Required Folder Structure

The root folder shall be organised in the following structure.

```
Root Folder
│
├── Location Folder 1
│   ├── 2023-01-31 Project Folder 1
│   │   ├── image1.raw
│   │   ├── image2.raw
│   │   ├── ...
│   │   ├── Selection Folder 1
│   │       ├── best_image1.jpg
│   │       ├── best_image2.jpg
│   │       ├── ...
│   ├── 2023-01-31 Project Folder 2
│   │   ├── ...
│   ├── 2023-02-15 Project Folder 3
│   │   ├── ...
│   ├── ...
├── Location Folder 2
│   ├── 2023-01-31 Project Folder 1
│   │   ├── ...
│   ├── 2023-02-15 Project Folder 2
│   │   ├── ...
│   ├── ...
├── ...
```

### Utility Folder (= User Settings Folder)
The utility folder (typically named as *_utility_folder*) gets created inside the root folder on main PC the first time the app is run in *initialize* mode. It contains folders and files in the following structure:

```
_utility_folder
│
├── .autogen
│   ├── folders_with_raw_expected.txt
│   ├── folders_with_raw_unexpected.txt
│   ├── project_folders_list_hdd.txt
│   ├── project_folders_list_modifications.txt
│   ├── project_folders_list_pc.txt
├── settings
│   ├── raw_file_formats.txt
│   ├── raw_selection_folder_names.txt
├── project_folders_modified_hdd.txt
├── project_folders_modified_pc.txt
├── project_folders_to_be_processed.txt
├── project_folders_with_raw_on_pc.txt
```

**.autogen** -- Folder with text files automatically generated by the app. Serves for information purposes only, making it easier to spot inconsistencies.

* **folders_with_raw_expected.txt** -- List of project folders with paths relative to root folder. These project folders contain raw files on PC, which is in line with those listed in *project_folders_with_raw_on_pc.txt*.

* **folders_with_raw_unexpected.txt** -- List of project folders with paths relative to root folder. These project folders contain raw files on PC, but are not listed in *project_folders_with_raw_on_pc.txt*.

* **project_folders_list_hdd.txt** -- *to be done*

* **project_folders_list_modifications.txt** -- *to be done*

* **project_folders_list_pc.txt** -- *to be done*

**settings** -- Folder with text files with settings. ***The user should alter those files to their needs.***. Some common settings are predefined.

* **raw_file_formats.txt** -- List of file formats of raw files, separated by a comma. Files with these formats located directly inside a project folder are considered as raw data, therefore are being moved from PC to HDD (unless specified to keep them on PC, too).

* **raw_selection_folder_names.txt** -- List of selection folder names with raw data, separated by comma. Folders with these names located directly inside a project folder are considered as raw data, therefore are being moved from PC to HDD (unless specified to keep them on PC, too).

**standalone text files** -- Text files, each with list of project folders with absolute paths or relative to root folder (relative prefered). Each project folder on a new line. Example lines are for ilustration only, can be deleted. ***The user should alter those files to their needs.***

* **project_folders_modified_pc.txt** -- Project folders that have been modified on PC (photos have been postprocessed, some raw files deleted, selection folders created, ...). These project folders listed will be backed up again when *modified_folders* mode is run. After that, successfully backed up project folders will be removed from this list automatically.

* **project_folders_modified_hdd.txt** -- Same as on PC, but currently buggy behavior (raw data is moved from HDD to PC).

* **project_folders_with_raw_on_pc.txt** -- Project folders that shall keep raw data on PC (unlike normal behaviour when raw data gets moved to HDD).

* **project_folders_to_be_processed.txt** -- Project folders that have been imported to PC, but their photos have not been postprocessed yet. Behaves the same as *raw_on_pc*, therefore keeps raw data on pc. However, it acts for the user as a clear list of project folders with photos to process.


## Application Modes

The app can be run in different modes based on desired task.

### Initialize
Run ```initialize``` mode the first time the app is used on a main PC. The mode creates the *utility folder* if it does not already exist, which contains predefined settings. User shall use check these settings and alter them to their needs.

### New Folders
Run ```new_folders``` mode to back up project folders that are **not** present in the target root folder yet.

### Modified Folders
Run ```modified_folders``` mode to back up project folders that are present in the target root folder, but have been modified in the source root folder, thus shall be backed up again (backing up new and modified files and deleting files not present anymore).


## Running the App

**Command Line Arguments**
Arguments for command line interface. Inputs in web interface behave in the same way.

* **mode** -- One of supported backup modes (initialize, new_folders, modified_folders).

* **utility_root** -- Absolute path to the root folder in which the utility folder is located.

* **source_folder** -- Absolute path to the source root folder from which the photos are backed up.

* **target_folder** -- Absolute path to the target root folder to which the photos are backed up.

### Command Line Interface
Run `main.py` with command line arguments. Example:
```
python main.py --mode new_folders --utility_root D:/IMAGES --source_folder D:/IMAGES  --target_folder F:/IMAGES 
```

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jirslad/photo_backuper/blob/main/demo_notebook.ipynb)

### Web Interface
Launch the app via terminal. Then access it via web browser at `http://127.0.0.1:5000`.
```
python photo_backuper_app/app.py
``` 

Inputs work the same as in the command line interface. They are logged into a database and can be displayed by pressing `Show History`. The last log is used to prefill the inputs.


![Alt text](/docs/imgs/web_showcase_logs.png?raw=true "Logs")


## Practical Usage with Examples / Workflow

### Set Up Your Workflow
* Before using the app, organise your photos into the required structure (*Required Folder Structure*).

### Using the App for the First Time
1) Run the app with the `initialize` mode. Specify absolute path to your root folder on arbitrary drive.
```
main.py --mode initialize --utility_root C:/path/to/folder
```

2) Check the freshly created `_utility_folder` folder inside your root folder. Insert project folders paths into the text files in which you want to keep raw data on PC. Also edit the text files inside `settings` folder to specify your raw data.

### Importing Photos
Importing photos from a single project involves these steps:

1) Create a new project folder inside the appropriate location folder.

2) Import your photos into it.

3) If you plan to process the photos later and would like to keep raw files on PC also after backup, copy the project folder's path (absolute or relative to root folder) and paste it into `_photo_backuper/project_folders_to_be_processed.txt`, which also serves as TODO list for your postprocessing of photos.

4) If you want to keep the raw files on PC even after removing the project folder from the TODO list, place the project folder's path into `project_folders_with_raw_on_pc.txt`.

5) Optionally back up the freshly imported folders using `new_folders` mode. Or you can back it up later.

### Backing up New Project Folders
Simply run `main.py` in `new_folders` mode. Example:
```
python main.py --mode new_folders --utility_root D:/IMAGES --source_folder D:/IMAGES --target_folder F:/IMAGES
```

### Backing up Modified Project Folders
1) Into `_photo_backuper/project_folders_modified_pc.txt`, insert paths of project folders that have been modified since their backup.

2) Run `main.py` in `modified_folders` mode. Example:
```
python main.py --mode modified_folders --utility_root D:/IMAGES --source_folder D:/IMAGES --target_folder F:/IMAGES
```

