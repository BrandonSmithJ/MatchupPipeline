import tarfile
import os

def compress(output_tar, source_file,directory_or_contents='directory',include_tars=False):
    with tarfile.open(output_tar, "w:gz") as tar:
        if directory_or_contents == 'directory':
            tar.add(source_file, arcname=os.path.basename(source_file))
        if directory_or_contents == 'contents':
            for element in os.scandir(source_file):
                include_tar_bool = '.tar' not in element.path or include_tars
                if element.is_file and element.path:
                    tar.add(element.path,arcname=str(element.path).split('/')[-1])
