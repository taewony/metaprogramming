import os
from pathlib import Path
from organize import organize_files

def run_test():
    test_dir = Path("test_organize")
    test_dir.resolve()
    print("Testing organize_files on:", test_dir.absolute())
    organize_files(str(test_dir.absolute()))
    print("Test complete.")

if __name__ == "__main__":
    run_test()
