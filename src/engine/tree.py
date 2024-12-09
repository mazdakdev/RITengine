import os
import argparse

def print_tree(dir_path, exclude_dirs=None, prefix=''):
    if exclude_dirs is None:
        exclude_dirs = []
    
    items = [item for item in os.listdir(dir_path) if item not in exclude_dirs]
    for index, item in enumerate(items):
        item_path = os.path.join(dir_path, item)
        connector = '└── ' if index == len(items) - 1 else '├── '
        print(prefix + connector + item)
        if os.path.isdir(item_path):
            new_prefix = '    ' if index == len(items) - 1 else '│   '
            print_tree(item_path, exclude_dirs, prefix + new_prefix)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print the tree view of a directory.")
    parser.add_argument("directory", type=str, help="The directory path to print the tree view for.")
    args = parser.parse_args()
    exclude_dirs = ['__pycache__', 'management', 'migrations']
    print_tree(args.directory, exclude_dirs)