import argparse
import shutil
import logging

from photo_backuper.backuper import Backuper

logging.basicConfig(level=logging.DEBUG)


def main(args):
    
    # copy files for testing purposes
    shutil.rmtree(r"data\IMAGES", ignore_errors=True)
    shutil.copytree(r"data\IMAGES_original", r"data\IMAGES")

    backuper = Backuper(args.mode, args.utility_root, args.source_folder,
                        args.target_folder)

    backuper.perform_current_mode()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, choices=Backuper.MODES, help="Backup mode")
    parser.add_argument("--utility_root", type=str, required=True, help="Path to folder containing utility folder (typically on a desktop or a laptop)")
    parser.add_argument("--source_folder", type=str, help="Path to origin folder")
    parser.add_argument("--target_folder", type=str, help="Path to destination folder")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
