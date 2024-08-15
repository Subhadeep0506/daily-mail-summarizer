import os


def clean_temp():
    for dirpath, _, filenames in os.walk("temp"):
        for filename in filenames:
            if filename.endswith(".txt"):
                file_path = os.path.join(dirpath, filename)
                os.remove(file_path)
