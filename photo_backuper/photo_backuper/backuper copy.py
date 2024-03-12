from pathlib import Path
import os
import shutil
import logging

logging.basicConfig(level=logging.DEBUG)

# TODO:
# add mode and utility root as properties, check if mode is in implemented modes (set), check for utility_root existence

class Backuper:

    PROGRAM_NAME = "photo_backuper"
    MODES = ["initialize", "new_folders", "modified_folders"]
    MODES_NAMES = ["Initialize", "Backup New Folders", "Backup Modified Folders"]

    def __init__(self, mode, utility_root, source_root=None, target_root=None):

        self.mode = mode
        self.utility_root = Path(utility_root)
        self.utility_folder = self.utility_root / ("_" + self.PROGRAM_NAME)
        self.utility_folder_exists = self.utility_folder.exists()
        self.source_root = source_root
        self.target_root = target_root

    @property
    def source_root(self):
        return self._source_root

    @source_root.setter
    def source_root(self, root):
        self._source_root = self._setter_root_folder(root, "source")

    @property
    def target_root(self):
        return self._target_root

    @target_root.setter
    def target_root(self, root):
        self._target_root = self._setter_root_folder(root, "target")

    # ------ MODES ------
    def perform_current_mode(self):
        match self.mode:
            case "initialize":
                message = self.mode_initialize_settings()
                logging.info(message)
            case "new_folders":
                for message in self.generator_backup_new_folders():
                    logging.info(message)

    def mode_initialize_settings(self):
        if self.utility_folder_exists:
            # TODO: not sure, what is better to implement - error, or warning with return None
            # raise FileExistsError("Utility folder already exists."
            #                       f"Check settings in '{self.utility_folder}' folder.")
            return ("Utility folder already exists. "
                    f"Check settings in '{self.utility_folder}' folder.")
        self._create_utility_folder()
        return ("Utility folder created. "
                f"Edit settings in '{self.utility_folder}' folder.")


    def generator_backup_new_folders(self):
        self._read_settings()
        source_project_folders = self._get_project_folders(self.source_root)
        target_project_folders = self._get_project_folders(self.target_root)
        new_project_folders = self._compare_project_folders(source_project_folders, target_project_folders)
        if len(new_project_folders) == 0:
            logging.info("No new project folders found.")
            return None
        # TODO: maybe create a better way to show progress
        n = len(new_project_folders)
        for i, project_folder in enumerate(new_project_folders):
            progress_msg = f"Backing up folder {i+1:3}/{n}: {project_folder}"
            yield progress_msg

            move_raw = not project_folder in self.projects_with_raw
            self.backup_project_folder(project_folder, move_raw=move_raw)
        yield "Backing up finished successfully."

    # ------ UTILITIES ------

    def _setter_root_folder(self, root, type):
        if self.mode == "initialize":
            return None
        if not self.utility_folder_exists:
            raise FileNotFoundError(f"Folder with settings '{self.utility_folder}' not found.\n"
                                    "Run the program with 'initialize' mode first.")
        if root:
            # TODO: raise error if folder does not exist -- FileNotFoundError
            return Path(root)
        if type == "source":
            raise ValueError("The following argument is required for this mode: --source_root_folder")
        elif type == "target":
            raise ValueError("The following argument is required for this mode: --target_root_folder")

    def _create_utility_folder(self):
        '''Creates the utility folder inside the root folder
        '''
        self.utility_folder.mkdir()
        example_line = "Example line: Himalayas\\2010.1.31 K2 climb OR D:\\Images\\Himalayas\\2010.1.31 K2 climb\n"
        with open(self.utility_folder / "project_folders_modified_pc.txt", "w") as f:
            f.write(example_line)
        with open(self.utility_folder / "project_folders_modified_hdd.txt", "w") as f:
            f.write(example_line)
        with open(self.utility_folder / "project_folders_to_be_processed.txt", "w") as f:
            f.write(example_line)
        with open(self.utility_folder / "project_folders_with_raw_on_pc.txt", "w") as f:
            f.write(example_line)

        self.settings_folder = self.utility_folder / "settings"
        self.settings_folder.mkdir()
        with open(self.settings_folder / "raw_selection_folder_names.txt", "w") as f:
            raw_selection_folder_names = ["tiffs", "tifs", "dng"]
            f.write(", ".join(raw_selection_folder_names))
        with open(self.settings_folder / "raw_file_formats.txt", "w") as f:
            raw_file_formats = ["raw", "orf", "rw2", "dng", "tiff", "tif", "hdr", "jpg", "jpeg", "mov", "mp4"]
            f.write(", ".join(raw_file_formats))
        
        self.autogen_folder = self.utility_folder / ".autogen"
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
            self.raw_formats = set(f.read().split(", "))

        with open(self.utility_folder / "settings" / "raw_selection_folder_names.txt", "r") as f:
            self.raw_selections = set(f.read().split(", "))
        
        with open(self.utility_folder / "project_folders_with_raw_on_pc.txt", "r", encoding="utf-8") as f:
            self.projects_with_raw = []
            for path in f.readlines():
                if path.startswith("Example line:"):
                    continue
                path = path.rstrip()
                if os.path.isabs(path):
                    path = os.path.relpath(path, self.source_root)
                self.projects_with_raw.append(Path(path))
            

    def _get_project_folders(self, location_root):
        '''Returns list of project folders paths relative to location_root
        TODO: check if location_root exists
        '''
        project_folders = []
        for location_folder in location_root.iterdir():
            if not location_folder.is_dir():
                continue
            # ignore utility folder and other folders starting with "_"
            if location_folder.name[0] == "_":
                continue
            if location_folder.is_dir():
                for project_folder in location_folder.iterdir():
                    if project_folder.is_dir():
                        project_folders.append(project_folder.relative_to(location_root))

        return project_folders

    @staticmethod
    def _compare_project_folders(source_project_folders, target_project_folders):
        # TODO: maybe create more efficient way, but the result should be ideally also ordered (unlike with sets)
        return [path for path in source_project_folders if path not in target_project_folders]

    def backup_project_folder(self, project, move_raw=True):
        # TODO: probably treat this as public method
        '''Backup single project folder
        '''
        source = self.source_root / project
        target = self.target_root / project

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
                if move_raw and source_item_path.name in self.raw_selections:
                    shutil.move(source_item_path, target_item_path)
                else:
                    shutil.copytree(source_item_path, target_item_path)

    # ----------------------------------------------------------------------------------------

    # # TODO: solve source/target PC/HDD ambiguity problem when they are swapped
    # def write_project_folders_lists(utility_root_folder, root_folders_pc, root_folder_hdd):
    #     '''Creates lists of project folders inside the roots folder.
    #     Saves them to .autogen/project_folders_list_XXX.txt
    #     '''

    #     utility_folder = utility_root_folder / ("_" + PROGRAM_NAME)

    #     project_folders_pc = get_project_folders(utility_root_folder, root_folders_pc)
    #     project_folders_hdd = get_project_folders(utility_root_folder, root_folder_hdd)

    #     with open(utility_folder / ".autogen" / "project_folders_list_pc.txt", "w") as f:
    #         f.write("\n".join([str(project_folder) for project_folder in project_folders_pc]))

    #     with open(utility_folder / ".autogen" / "project_folders_list_hdd.txt", "w") as f:
    #         f.write("\n".join([str(project_folder) for project_folder in project_folders_hdd]))

    # ----------------------------------------------------------------------------------------
