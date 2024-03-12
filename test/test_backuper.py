'''
Run with $ python -m unittest test/test_backuper.py
'''

import unittest
import tempfile
import os
import shutil

from photo_backuper.backuper import Backuper

class TestModeSelection(unittest.TestCase):
    
    def test_invalid_mode(self):
        """Selection of an invalid mode"""
        with self.assertRaises(ValueError):
            backuper = Backuper("invalid_mode", "")


class TestModeInitializeSettings(unittest.TestCase):

    def setUp(self):
        self.mode = Backuper.MODES[0] # "initialize"
        self.utility_root = tempfile.mkdtemp()
        self.utility_folder = os.path.join(self.utility_root, "_" + Backuper.PROGRAM_NAME)

    def tearDown(self):
        shutil.rmtree(self.utility_root)

    def test_create_utility_folder(self):
        '''Creation of utility folder under normal circumstance'''
        # run mode_initialize_settings
        backuper = Backuper(self.mode, self.utility_root)
        backuper.mode_initialize_settings()

        # test creation of utility folder with proper name
        self.assertTrue(os.path.exists(self.utility_folder))

        # test creation of contents of the utility folder
        expected_utility_folder = os.path.join(os.path.dirname(__file__), "data_utility_folder", "_photo_backuper")
        self.assertTrue(_compare_folders(expected_utility_folder, self.utility_folder))

    def test_utility_folder_already_exists(self):
        '''Creation of utility folder when it already exists'''
        os.mkdir(self.utility_folder)
        expected_message = ("Utility folder already exists. "
                            f"Check settings in '{self.utility_folder}' folder.")

        backuper = Backuper(self.mode, self.utility_root)
        message = backuper.mode_initialize_settings()
        self.assertEqual(message, expected_message)


class TestModeBackupNewFolders(unittest.TestCase):

    def setUp(self):
        self.mode = Backuper.MODES[1] # "new_folders"
        self.tempdir = tempfile.mkdtemp()
        self.initial_state = os.path.join(os.path.dirname(__file__), "data_backup_new", "initial_state")
        shutil.copytree(self.initial_state, self.tempdir, dirs_exist_ok=True)
        self.expected_final_state = os.path.join(os.path.dirname(__file__), "data_backup_new", "final_state")

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_backup_new_folders(self):
        '''Backing up new folders under normal circumstance'''
        # run mode backup new folders
        utility_root = os.path.join(self.tempdir, "source")
        source_folder= os.path.join(self.tempdir, "source")
        target_folder = os.path.join(self.tempdir, "target")
        backuper = Backuper(self.mode, utility_root, source_folder, target_folder)
        backuper.perform_current_mode()

        # test both source and target folders are as expected
        self.assertTrue(_compare_folders(self.expected_final_state, self.tempdir))

    # TODO: add edge cases:
    # - source and target does not exist
    # - no new project folders


class TestModeBackupModifiedFolders(unittest.TestCase):

    def setUp(self):
        self.mode = Backuper.MODES[2] # "modified_folders"
        self.tempdir = tempfile.mkdtemp()
        self.initial_state = os.path.join(os.path.dirname(__file__), "data_backup_modified", "initial_state")
        shutil.copytree(self.initial_state, self.tempdir, dirs_exist_ok=True)
        self.expected_final_state = os.path.join(os.path.dirname(__file__), "data_backup_modified", "final_state")

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_backup_modified_folders(self):
        '''Backing up modified folders under normal circumstance'''
        # run mode backup modified folders
        utility_root = os.path.join(self.tempdir, "source")
        source_folder= os.path.join(self.tempdir, "source")
        target_folder = os.path.join(self.tempdir, "target")
        backuper = Backuper(self.mode, utility_root, source_folder, target_folder)
        backuper.perform_current_mode()

        # test both source and target folders are as expected
        self.assertTrue(_compare_folders(self.expected_final_state, self.tempdir))


# TODO test autogen methods


def _compare_folders(folder1, folder2):
        """Compare the contents of two folders.
        
        Returns True if their contents are the same, False otherwise.

        Args:
            folder1 (str): path to the first folder
            folder2 (str): path to the second folder
        """
        contents1 = os.listdir(folder1)
        contents2 = os.listdir(folder2)

        contents1.sort()
        contents2.sort()

        if contents1 != contents2:
            print("Contents are different")
            print(f" 1) {contents1}\n 2) {contents2}")
            return False

        # Check if the contents of subdirectories are the same
        for item1, item2 in zip(contents1, contents2):
            path1 = os.path.join(folder1, item1)
            path2 = os.path.join(folder2, item2)

            # Recursively compare subdirectories
            if os.path.isdir(path1) and os.path.isdir(path2):
                if not _compare_folders(path1, path2):
                    print("Subdirectories are different")
                    print(f" 1) {path1}\n 2) {path2}")
                    return False

            # Compare files
            elif os.path.isfile(path1) and os.path.isfile(path2):
                # filecmp.cmp() to compare content of two files
                # compare file names
                if not item1 == item2:
                    print("File names are different")
                    print(f" 1) {item1}\n 2) {item2}")
                    return False

            # If one is a file and the other is a directory, they are different
            else:
                print("One is a file and the other is a directory")
                print(f" 1) {path1}\n 2) {path2}")
                return False

        # All contents are the same
        return True

            
if __name__ == "__main__":
    unittest.main()
