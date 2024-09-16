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

        processed_files = set()

        while True:
            try:
                result = subprocess.check_output([
                    'git', 'ls-files', '--others', '--modified', '--exclude-standard', '--', subdir
                ])
            except subprocess.CalledProcessError as e:
                print(f"Error getting list of files in {subdir}: {e}")
                sys.exit(1)

            all_files = result.decode().splitlines()
            unprocessed_files = [f for f in all_files if f not in processed_files]
            
            if not unprocessed_files:
                print(f"No more files to process in {subdir}.")
                break

            batch_files = unprocessed_files[:batch_size]
            processed_files.update(batch_files)

            temp_filename = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
                    for f in batch_files:
                        temp.write(f + '\n')
                    temp_filename = temp.name

                subprocess.run(['git', 'add', '--pathspec-from-file=' + temp_filename], check=True)
                subprocess.run(['git', 'commit', '-m', f'Batch commit for {subdir}'], check=True)
                subprocess.run(['git', 'push', 'origin', branch], check=True)
                print(f"Processed {len(batch_files)} files in {subdir}.")
            except subprocess.CalledProcessError as e:
                print(f"Error during Git operations: {e}")
                sys.exit(1)
            finally:
                if temp_filename and os.path.exists(temp_filename):
                    os.remove(temp_filename)

    print("All subdirectories processed.")

if __name__ == '__main__':
    main()
