import os
import sys
import subprocess
import tempfile
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder')
    parser.add_argument('--batch_size', type=int, default=25)
    parser.add_argument('--branch', default='master')

    args = parser.parse_args()

    folder = args.folder
    batch_size = args.batch_size
    branch = args.branch

    os.chdir(folder)

    subdirs = [d for d in os.listdir('.') if os.path.isdir(d)]

    for subdir in subdirs:
        print(f"Processing subdirectory: {subdir}")

        # Initialize a set to keep track of processed files
        processed_files = set()

        while True:
            try:
                result = subprocess.check_output([
                    'git', 'ls-files', '--others', '--modified', '--exclude-standard', '--', subdir
                ])
            except subprocess.CalledProcessError as e:
                print("Error getting list of files:", e)
                sys.exit(1)

            all_files = result.decode().splitlines()
            unprocessed_files = [f for f in all_files if f not in processed_files]
            
            if not unprocessed_files:
                print(f"No more files to process in {subdir}.")
                break

            batch_files = unprocessed_files[:batch_size]
            processed_files.update(batch_files)

            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
                for f in batch_files:
                    temp.write(f + '\n')
                temp_filename = temp.name

            try:
                subprocess.run(['git', 'add', '--pathspec-from-file=' + temp_filename], check=True)
            except subprocess.CalledProcessError as e:
                print("Error adding files:", e)
                sys.exit(1)

            try:
                subprocess.run(['git', 'commit', '-m', f'Batch commit for {subdir}'], check=True)
            except subprocess.CalledProcessError as e:
                print("Error committing files:", e)
                sys.exit(1)

            try:
                subprocess.run(['git', 'push', 'origin', branch], check=True)
            except subprocess.CalledProcessError as e:
                print("Error pushing to remote:", e)
                sys.exit(1)

            os.remove(temp_filename)

            print(f"Processed {len(batch_files)} files in {subdir}.")

    print("All subdirectories processed.")

if __name__ == '__main__':
    main()
