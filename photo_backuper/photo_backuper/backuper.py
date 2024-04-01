from pathlib import Path
import os
import shutil
import logging

from send2trash import send2trash

logging.basicConfig(level=logging.DEBUG)


class Backuper:
    """Class to backup photographs in a folder with a specific structure.
    
    This class assumes the following treestructure:
    root_folder                 single folder containing all the contents
    |- location_folder_1        folder grouping photos by geographical locations
    |  |- project_folder_1      folder for photos from a single photoshoot
    |  |  |- selection_folder_1 selection folder for exported or preprocessed photos
    |  |  |  |- photo_1.jpg
    |  |  |- photo_1.raw
    ...

    Class with several modes to backup folder with photographs from one
    device to another device.
    
    Available modes:
        initialize -- Creates a utility folder inside root folder, which contains
          text files with settings (such as raw file formats, raw selection folders).
          User shall edit these files for the first time before running other modes.
        new_folders -- Backs up all project folders not present on the target
          (i.e. destination) device. Raw files and folders specified in settings are
          moved to the target, rest of contents is copied.
        modified_folders -- Backs up project folders modified in one root folder,
          deleting any superabundant files on the target and backing up the rest as
          in new_folders mode. These project folders must be specified in a settings
          file and are removed from it automatically after the backup.

    Args:
        mode (str): Mode to run the program in.
        utility_root (str): Absolute path to root folder that shall contain
          the utility folder.
        source_folder (str): Absolute path to source folder (currently only master PC)
        target_folder (str): Absolute path to target folder (currently only master HDD)
    """

    PROGRAM_NAME = "photo_backuper"
    MODES = ["initialize", "new_folders", "modified_folders"]
    MODES_NAMES = ["Initialize", "Backup New Folders",
                   "Backup Modified Folders"]
    
    # utility folder settings
    EXAMPLE_LINE = ( # TODO: prefer relative path
        "Example line: Himalayas\\2010.1.31 K2 climb\n"
        "Example line: D:\\Images\\Himalayas\\2010.1.31 K2 climb\n"
    )
    FILENAME_PROJECTS_MODIFIED_PC = "project_folders_modified_pc.txt"
    FILENAME_PROJECTS_MODIFIED_HDD = "project_folders_modified_hdd.txt"

    def __init__(self, mode, utility_root, source_folder=None,
                 target_folder=None):
        self.mode = mode
        self.utility_root = Path(utility_root)
        self.utility_folder = self.utility_root / ("_" + self.PROGRAM_NAME)
        self.autogen_folder = self.utility_folder / ".autogen"
        self.utility_folder_exists = self.utility_folder.exists()
        self.source_folder = source_folder # TODO: for now it is master PC
        self.target_folder = target_folder # TODO: for now it is master HDD

    @property
    def mode(self):
        return self._mode
    
    @mode.setter
    def mode(self, mode):
        if mode in self.MODES:
            self._mode = mode
        else:
            raise ValueError("Mode is not in available modes.")

    @property
    def source_folder(self):
        """Absolute path to folder 
        """
        return self._source_folder

    @source_folder.setter
    def source_folder(self, root):
        self._source_folder = self._setter_root_folder(root, "source")

    @property
    def target_folder(self):
        return self._target_folder

    @target_folder.setter
    def target_folder(self, root):
        self._target_folder = self._setter_root_folder(root, "target")

    # ------ MODES ------
    def perform_current_mode(self):
        """Performs the currectly assigned mode
        """
        match self.mode:
            case "initialize":
                message = self.mode_initialize_settings()
                logging.info(message)
            case "new_folders":
                self.mode_backup_new_folders()
            case "modified_folders":
                self.mode_backup_modified_folders()

    def mode_initialize_settings(self):
        """Performs initialization mode.
        
        Creates utility folder (_photo_backer) in the utility root folder
        (unless it already exists). User shall edit files in it to their
        needs (e.g. add raw file formats to the predefined ones, keep track
        of modified project folders, ...).
        """
        if self.utility_folder_exists:
            return ("Utility folder already exists. "
                    f"Check settings in '{self.utility_folder}' folder.")
        self._create_utility_folder()
        return ("Utility folder created. "
                f"Edit settings in '{self.utility_folder}' folder.")

    def mode_backup_new_folders(self):
        """Performs new_folders mode.
        
        Backs up all project folders from source folder not present in the
        target folder. Movev RAW data, copies the rest, keeping the file
        structure mirrored on source and target up to project folders level.
        Also generated list of existing project folders to .autogen folder
        in utility folder.
        """
        for message in self.generator_backup_new_folders():
            logging.info(message)
        logging.info("Autogenerating lists of project folders with raw files...")
        self.autogen_project_folders_with_raw()
        logging.info("Backing up finished successfully.")

    def mode_backup_modified_folders(self):
        """Performs modified_folders mode.
        
        Backs up all modified project folders (specified in a settings file)
        from source folder to target folder. Removes all superabundant files
        in target, backs up the rest as in new_folders mode.
        Also generated list of existing project folders to .autogen folder
        in utility folder.
        """
        for message in self.generator_backup_modified_folders():
            logging.info(message)
        logging.info("Autogenerating lists of project folders with raw files...")
        self.autogen_project_folders_with_raw()
        logging.info("Backing up finished successfully.")

    # ------ PUBLIC METHODS ------

    def generator_backup_new_folders(self):
        """Generator that backs up new folders while yielding progress messages.
        
        Also backs up the utility folder.

        Yields:
        A string with progess message. That is usually number of project folder
        currently being processed, total number of project folders to process,
        path of the currently processed project folder.
        """
        self._read_settings()

        # backup utility folder
        utility_target = self.target_folder / self.utility_folder.name
        shutil.copytree(self.utility_folder, utility_target, dirs_exist_ok=True)
        yield f"Utility folder from {self.source_folder} backed up."

        # backup project folders
        source_project_folders = self._get_project_folders(self.source_folder)
        target_project_folders = self._get_project_folders(self.target_folder)
        new_project_folders = self._compare_project_folders(
            source_project_folders, target_project_folders)
        n = len(new_project_folders)
        if n == 0:
            yield f"No new project folders found in {self.source_folder}."
            return None
        for i, project_folder in enumerate(new_project_folders):
            progress_msg = f"Backing up new folder {i+1:3}/{n}: {project_folder}"
            yield progress_msg

            move_raw = project_folder not in self.projects_with_raw
            self._backup_project_folder(project_folder, move_raw=move_raw)

    def generator_backup_modified_folders(self):
        """Generator that backs up modified folders while yielding progress messages.
        
        Backs up folders modified on PC, then on HDD. Also backs up the utility folder.

        Yields:
        A string with progess message. That is usually number of project folder
        currently being processed, total number of project folders to process,
        path of the currently processed project folder.
        """
        self._read_settings()

        # backup utility folder
        utility_target = self.target_folder / self.utility_folder.name
        shutil.copytree(self.utility_folder, utility_target, dirs_exist_ok=True)

        # backup modified project folders
        projects_modified_pc = set(self._read_project_folders_list(
            self.FILENAME_PROJECTS_MODIFIED_PC, self.source_folder))
        projects_modified_hdd = set(self._read_project_folders_list(
            self.FILENAME_PROJECTS_MODIFIED_HDD, self.target_folder))
        # ignore folders incorrectly listed on both lists
        intersection = projects_modified_pc & projects_modified_hdd

        projects_modified_pc = list(projects_modified_pc - intersection)
        for msg in self._subgenerator_modified_folders(
            projects_modified_pc, self.source_folder, self.target_folder):
            yield msg
        
        # TODO bug: with source and target swapped, the method moves RAW files
        # to PC instead of keeping it in HDD
        projects_modified_hdd = list(projects_modified_hdd - intersection)
        for msg in self._subgenerator_modified_folders(
            projects_modified_hdd, self.target_folder, self.source_folder):
            yield msg

    def autogen_project_folders_with_raw(self):
        """Writes two .txt files with project folders expectedly and unexpectedly
        containing raw files. Files are saved to .autogen folder in utility folder. 
        """
        expected_folders = []
        unexpected_folders = []
        project_folders = self._get_project_folders(self.source_folder)
        for project_folder in project_folders:
            if self._contains_raw(project_folder):
                if project_folder in self.projects_with_raw:
                    expected_folders.append(str(project_folder))
                else:
                    unexpected_folders.append(str(project_folder))
        with open(self.autogen_folder / "folders_with_raw_expected.txt", "w") as f: 
            f.write("\n".join(expected_folders))
        with open(self.autogen_folder / "folders_with_raw_unexpected.txt", "w") as f:
            f.write("\n".join(unexpected_folders))

    # ------ UTILITIES ------

    def _setter_root_folder(self, root, type):
        """Setter validation for source and target folders.
        """
        if self.mode == "initialize":
            return None
        if not self.utility_folder_exists:
            raise FileNotFoundError(
                f"Folder with settings '{self.utility_folder}' not found.\n"
                "Run the program with 'initialize' mode first."
                )
        if root:
            root = Path(root)
            if not root.exists():
                raise FileNotFoundError(f"'{root}' folder does not exist.")
            return root
        if type == "source":
            raise ValueError("Required parameter for this mode: source_folder")
        elif type == "target":
            raise ValueError("Required parameter for this mode: target_folder")

    def _create_utility_folder(self):
        '''Creates the utility folder with various prefilled settings files
        inside the root folder
        '''
        self.utility_folder.mkdir()
        with open(self.utility_folder / self.FILENAME_PROJECTS_MODIFIED_PC, "w") as f:
            f.write(self.EXAMPLE_LINE)
        with open(self.utility_folder / self.FILENAME_PROJECTS_MODIFIED_HDD, "w") as f:
            f.write(self.EXAMPLE_LINE)
        with open(self.utility_folder / "project_folders_to_be_processed.txt", "w") as f:
            f.write(self.EXAMPLE_LINE)
        with open(self.utility_folder / "project_folders_with_raw_on_pc.txt", "w") as f:
            f.write(self.EXAMPLE_LINE)

        self.settings_folder = self.utility_folder / "settings"
        self.settings_folder.mkdir()
        with open(self.settings_folder / "raw_selection_folder_names.txt", "w") as f:
            raw_selection_folder_names = ["tiffs", "tifs", "dng"]
            f.write(", ".join(raw_selection_folder_names))
        with open(self.settings_folder / "raw_file_formats.txt", "w") as f:
            raw_file_formats = ["raw", "orf", "rw2", "dng", "tiff", "tif",
                                "hdr", "jpg", "jpeg", "mov", "mp4"]
            f.write(", ".join(raw_file_formats))

        self.autogen_folder.mkdir()
        with open(self.autogen_folder / "project_folders_list_hdd.txt", "w") as f:
            pass
        with open(self.autogen_folder / "project_folders_list_pc.txt", "w") as f:
            pass
        with open(self.autogen_folder / "project_folders_list_modifications.txt", "w") as f:
            pass

    def _read_settings(self):
        '''Returns sets of raw file formats and raw selection folder names.
        '''
        with open(self.utility_folder / "settings" / "raw_file_formats.txt", "r") as f:
            self.raw_formats = set(x.lower().strip() for x in f.read().split(","))

        with open(self.utility_folder / "settings" / "raw_selection_folder_names.txt", "r") as f:
            self.raw_selections = set(x.lower().strip() for x in f.read().split(","))

        projects_raw = self._read_project_folders_list(
            "project_folders_with_raw_on_pc.txt", self.source_folder)
        projects_unprocessed = self._read_project_folders_list(
            "project_folders_to_be_processed.txt", self.source_folder)
        self.projects_with_raw = list(set(projects_raw) | set(projects_unprocessed))
    
    def _read_project_folders_list(self, file_name, root_folder):
        """Returns project folder paths from a file inside the utility folder.

        Args:
            file_name (str): name of the settings file located directly in the utility folder
            root_folder (pathlib.Path): absolute path to root folder the project paths are relative to
        Returns:
            list of relative project folder paths as pathlib.Path objects
        """
        with open(self.utility_folder / file_name, "r", encoding="utf-8") as f:
            project_folders = []
            for path in f.readlines():
                path = path.strip().replace("\\", "/")
                if not path or path.lower().startswith("example line"):
                    continue
                if os.path.isabs(path):
                    path = os.path.relpath(path, root_folder)
                project_folders.append(Path(path))
        return project_folders
    
    def _write_project_folders_list(self, file_name, project_folders):
        """Writes project folder paths to a file inside the utility folder.

        Args:
            file_name: name of the settings file located directly in the utility folder
            project_folders (list): list of relative project folder paths as pathlib.Path objects
        """
        lines = [f"{str(project_folder)}\n" for project_folder in project_folders]
        with open(self.utility_folder / file_name, "w") as f:
            f.write(self.EXAMPLE_LINE)
            f.writelines(lines)

    def _get_project_folders(self, root_folder):
        '''Returns list of project folders paths relative to root_folder

        Args:
            root_folder (pathlib.Path): Root folder containing location folders
                and project folders inside them.
        Returns:
            list of project folder paths as pathlib.Path objects
        '''
        project_folders = []
        for location_folder in root_folder.iterdir():
            if not location_folder.is_dir():
                continue
            if location_folder.name[0] == "_":
                continue
            for project_folder in location_folder.iterdir():
                if project_folder.is_dir():
                    project_folders.append(project_folder.relative_to(root_folder))
        return project_folders
            
    def _contains_raw(self, folder):
        """Returns True if folder contains raw data
        
        Returns True if folder contains either a file with raw file format or
        a raw selection folder. Otherwise returns False.
        
        Args:
            folder (pathlib.Path): Folder to check.
        """
        folder = self.source_folder / folder
        for file in folder.iterdir():
            if file.is_dir():
                if file.name.lower() in self.raw_selections:
                    return True
            else:
                if file.suffix.lstrip(".").lower() in self.raw_formats:
                    return True
        return False

    @staticmethod
    def _compare_project_folders(source_project_folders, target_project_folders):
        """
        Finds project folders in the source that do not exist in the target.

        Args:
            source_project_folders (list): List of project folders in the source.
            target_project_folders (list): List of project folders in the target.
        
        Returns:
            list of new project folders
        """
        return list(set(source_project_folders) - set(target_project_folders))

    def _backup_project_folder(self, project_folder, move_raw=True, source=None, target=None):
        '''Backs up single project folder

        Args:
            project_folder (pathlib.Path): Path to a project folder relative to source folder
            move_raw (bool): If True, raw files will be moved instead of copied
            source (pathlib.Path): Optional. Absolute path to source project folder
            target (pathlib.Path): Optional. Absolute path to target project folder
        '''

        if not source:
            source = self.source_folder / project_folder
        if not target:
            target = self.target_folder / project_folder

        os.makedirs(target, exist_ok=True)

        for source_item_path in source.iterdir():
            target_item_path = target.joinpath(source_item_path.name)

            if os.path.isfile(source_item_path):
                file_extension = source_item_path.suffix[1:].lower()
                if move_raw and file_extension in self.raw_formats:
                    shutil.move(source_item_path, target_item_path)
                else:
                    shutil.copy2(source_item_path, target_item_path)
            elif os.path.isdir(source_item_path):
                if move_raw and source_item_path.name.lower() in self.raw_selections:
                    shutil.move(source_item_path, target_item_path)
                else:
                    shutil.copytree(source_item_path, target_item_path)

    def _subgenerator_modified_folders(self, project_folders, source_folder, target_folder):
        """Generator that backs up modified folders in a single direction.
        
        Used as part of modified_folders mode to avoid code repetition.
        
        Backs up provided project folders modified on source to target while yielding
        progress messages.

        Args:
            project_folders (list): list of project folders' paths relative to
                a root folder.
            source_folder (pathlib.Path object): absolute path to source folder.
            target_folder (pathlib.Path object): absolute path to target folder.

        Yields:
        A string with progess message. That is usually number of project folder
        currently being processed, total number of project folders to process,
        path of the currently processed project folder.
        """
        n = len(project_folders)
        if n == 0:
            yield f"No modified project folders found in {source_folder}."
            return None
        for i, project_folder in enumerate(project_folders):
            progress_msg = f"Backing up modified folder {i+1:2}/{n}: {project_folder}"
            yield progress_msg

            source = source_folder / project_folder
            target = target_folder / project_folder
            
            # safely delete old content
            # TODO rewrite this method as described in the design document to avoid
            # unnesesarily deleting and copying files that should be kept
            if target.exists():
                send2trash(target)

            # copy new content
            move_raw = project_folder not in self.projects_with_raw
            self._backup_project_folder(project_folder, move_raw=move_raw,
                                        source=source, target=target)

            # remove project folder from list
            if source_folder == self.source_folder:
                filename = self.FILENAME_PROJECTS_MODIFIED_PC
            else:
                filename = self.FILENAME_PROJECTS_MODIFIED_HDD
            projects_modified = self._read_project_folders_list(filename, source_folder)
            projects_modified.remove(project_folder)
            self._write_project_folders_list(filename, projects_modified)                                            

    # -------------------------------------------------------------------------

    # ------ OLD METHODS TO REWRITE ------

    # # TODO: solve source/target PC/HDD ambiguity problem when they are swapped
    # # TODO: To partly solve that, call this method only when utility folder == source_folder
    # # TODO: Create also list with project folders containing raw on PC (to keep track of them even if error in manual definition occurs)
    # def write_project_folders_lists(utility_root_folder, root_folders_pc, root_folder_hdd):
    #     '''Creates lists of project folders inside the roots folder.
    #     Saves them to .autogen/project_folders_list_XXX.txt
    #     Sorted alphabetically (i.e. by date from oldest to newest).
    #     '''

    #     utility_folder = utility_root_folder / ("_" + PROGRAM_NAME)

    #     project_folders_pc = get_project_folders(utility_root_folder, root_folders_pc)
    #     project_folders_hdd = get_project_folders(utility_root_folder, root_folder_hdd)

    # # TODO: save relative paths instead of absolute
    #     with open(utility_folder / ".autogen" / "project_folders_list_pc.txt", "w") as f:
    #         f.write("\n".join([str(project_folder) for project_folder in project_folders_pc]))

    #     with open(utility_folder / ".autogen" / "project_folders_list_hdd.txt", "w") as f:
    #         f.write("\n".join([str(project_folder) for project_folder in project_folders_hdd]))

    # -------------------------------------------------------------------------
