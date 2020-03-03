import os.path as OS
from os import mkdir
_AbsoluteCurrentPath: str = OS.dirname(OS.abspath(__file__))
class FileFunctions:
    """
    Useful functions for file management
    """
    @staticmethod
    def makeOrGetPath(*paths) -> (bool, str):
        """
        create a file in selected directory, if it doesn't exist already
        returns:
            boolean specifying file exists or not
            full path of result file
        """
        filePath = OS.join(_AbsoluteCurrentPath, *paths)
        exists = False
        if OS.exists(filePath):
            exists = True
        else:
            try:
                mkdir(filePath)
            except:
                print(f"Error creating {filePath}")
                return None
        return (exists, filePath)
    @staticmethod
    def appendPaths(*paths):
        """
        get absolute path relative to current position
        no need to include os.path.join
        """
        return OS.join(_AbsoluteCurrentPath, *paths)
class Files:
    """
    Useful files and folders
    """
    AudioFolder: str = FileFunctions.makeOrGetPath("Audio") [1]
    DataFolder: str = FileFunctions.makeOrGetPath("Data") [1]
    TextDataJson: str = FileFunctions.makeOrGetPath(DataFolder, "eslyes.clean.json") [1]
