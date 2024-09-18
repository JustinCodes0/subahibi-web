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
                result = subprocess.check_output(['git', 'status', '--porcelain', '--', subdir])
            except subprocess.CalledProcessError as e:
                print("Error getting status of files:", e)
                sys.exit(1)

            lines = result.decode().splitlines()
            if not lines:
                print(f"No more files to process in {subdir}.")
                break

            files = []
            for line in lines:
                status = line[:2]
                file_path = line[3:]
                if status.strip() in ('??', 'M', 'A', 'AM', 'MM', 'D', 'R', 'C', 'U'):
                    files.append(file_path)

            if not files:
                print(f"No untracked or modified files to process in {subdir}.")
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
                if 'nothing to commit' in e.output.decode():
                    print("Nothing to commit in this batch.")
                    continue
                else:
                    print("Error committing files:", e)
                    sys.exit(1)

            try:
                subprocess.run(['git', 'push', 'origin', branch], check=True)
            except subprocess.CalledProcessError as e:
                print("Error pushing to remote:", e)
                sys.exit(1)

            print(f"Processed {len(batch_files)} files in {subdir}.")

        print(f"Finished processing subdirectory: {subdir}")

    print("All subdirectories processed.")

if __name__ == '__main__':
    main()
