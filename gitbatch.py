import os
import sys
import subprocess
import argparse
import tempfile

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

        while True:
            try:
                result = subprocess.check_output([
                    'git', 'ls-files', '--others', '--modified', '--exclude-standard', '--', subdir
                ])
            except subprocess.CalledProcessError as e:
                print("Error getting list of files:", e)
                sys.exit(1)

            files = result.decode().splitlines()
            if not files:
                print(f"No more files to process in {subdir}.")
                break

            batch_files = files[:batch_size]

            try:
                subprocess.run(['git', 'add', '--'] + batch_files, check=True)
            except subprocess.CalledProcessError as e:
                print("Error adding files:", e)
                sys.exit(1)
            except OSError as e:
                print("Error with command length, switching to temporary file method.")
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
                    for f in batch_files:
                        temp.write(f + '\n')
                    temp_filename = temp.name
                try:
                    subprocess.run(['git', 'add', '--pathspec-from-file=' + temp_filename], check=True)
                except subprocess.CalledProcessError as e:
                    print("Error adding files via temporary file:", e)
                    sys.exit(1)
                finally:
                    os.remove(temp_filename)

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

            print(f"Processed {len(batch_files)} files in {subdir}.")

    print("All subdirectories processed.")

if __name__ == '__main__':
    main()
