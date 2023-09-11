import tarfile
import os

def compress(output_tar, source,directory_or_contents='directory'):
    with tarfile.open(output_tar, "w:gz") as tar:
        if directory_or_contents == 'directory':
            tar.add(source, arcname=os.path.basename(source))
        if directory_or_contents == 'contents':
            for element in os.scandir(source):
                if element.is_file:
                    tar.add(element.path,arcname=str(element.path).split('/')[-1])
