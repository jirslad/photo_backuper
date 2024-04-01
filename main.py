import argparse
import shutil
import logging

from photo_backuper.backuper import Backuper

logging.basicConfig(level=logging.DEBUG)


def main(args):

    # demonstration on artificial files
    if args.demo:
        shutil.rmtree("data/IMAGES", ignore_errors=True)
        shutil.copytree("data/IMAGES_original", "data/IMAGES")
        backuper = Backuper(mode=args.mode,
                            utility_root="data/IMAGES/source",
                            source_folder="data/IMAGES/source",
                            target_folder="data/IMAGES/target")

    # normal situation
    else:
        backuper = Backuper(mode=args.mode,
                            utility_root=args.utility_root,
                            source_folder=args.source_folder,
                            target_folder=args.target_folder)

    backuper.perform_current_mode()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, choices=Backuper.MODES, help="Backup mode.")
    parser.add_argument("--utility_root", type=str, required=True, help=("Absolute path to " 
                        "folder containing utility folder (typically on a desktop or a laptop)."))
    parser.add_argument("--source_folder", type=str, help="Absolute path to origin folder.")
    parser.add_argument("--target_folder", type=str, help="Absolute path to destination folder.")
    parser.add_argument("--demo", default=False, action='store_true', help="Demo mode on made up data.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
