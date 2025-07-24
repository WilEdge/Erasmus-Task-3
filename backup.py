import shutil
import os
import datetime
import logging
import zipfile

class BackupManager:
    """
    Manages all file and directory backup operations.
    Includes copying, compression, versioning, logging, and error handling.
    """
    def __init__(self, log_file="logs/backup.log"):
        """
        Initializes the backup manager.
        :param log_file: Path to the log file.
        """
        self.log_file = log_file
        self._setup_logging()
        self.logger.info("BackupManager initialized.")

    def _setup_logging(self):
        """Configures the logging system."""
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _generate_backup_folder_name(self, base_name):
        """
        Generates a backup folder name with timestamp and version.
        The version here is a simple example (v1.0.0) and could be managed more dynamically.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # For a more robust version, you could read it from a file or generate it.
        # Here, we use a static version for the example.
        version = "v1.0.0"
        return f"{base_name}_{timestamp}_{version}"

    def _count_files_in_folder(self, folder_path):
        """
        Counts the total number of files in a folder and its subfolders.
        :param folder_path: Path to the folder to analyze.
        :return: The number of files.
        """
        count = 0
        for root, _, files in os.walk(folder_path):
            count += len(files)
        return count

    def _copy_folder_contents(self, source_path, destination_path):
        """
        Recursively copies a folder and its contents.
        :param source_path: Path of the source folder.
        :param destination_path: Path of the destination folder.
        :return: True if the copy succeeds, False otherwise.
        """
        try:
            # Create the destination directory if it doesn't exist
            if not os.path.exists(destination_path):
                os.makedirs(destination_path)
                self.logger.info(f"Destination folder created: '{destination_path}'")

            # shutil.copytree is ideal for copying entire folders.
            # dirs_exist_ok=True is useful if the destination folder already exists and we want to merge,
            # but here, we remove the old backup folder first for a clean backup.
            shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
            return True
        except Exception as e:
            raise e # Re-raise the exception for finer handling in perform_backup

    def _zip_folder_contents(self, source_path, output_zip_path):
        """
        Compresses an entire folder into a ZIP file.
        :param source_path: Path of the folder to compress.
        :param output_zip_path: Full path of the output ZIP file.
        :return: True if the compression succeeds, False otherwise.
        """
        try:
            # Create the parent directory of the ZIP file if necessary
            output_dir = os.path.dirname(output_zip_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.logger.info(f"ZIP output directory created: '{output_dir}'")

            with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(source_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # arcname is the path of the file inside the ZIP archive
                        arcname = os.path.relpath(file_path, source_path)
                        zipf.write(file_path, arcname)
            return True
        except Exception as e:
            raise e # Re-raise the exception for finer handling in perform_backup

    def perform_backup(self, source_folder, base_destination_folder, compress=False):
        """
        Performs a backup of a source folder to a destination folder.
        Creates a versioned backup subfolder or a ZIP file.
        :param source_folder: Path to the source folder to back up.
        :param base_destination_folder: Path to the base destination folder for backups.
        :param compress: If True, the backup will be compressed into a ZIP.
        :return: True if the backup succeeds, False otherwise.
        """
        if not os.path.exists(source_folder):
            self.logger.error(f"Error: Source folder does not exist: '{source_folder}'")
            return False

        if not os.path.isdir(source_folder):
            self.logger.error(f"Error: Source path is not a directory: '{source_folder}'")
            return False

        # Prepare the backup folder/file name
        base_name = os.path.basename(source_folder)
        backup_name_with_version = self._generate_backup_folder_name(base_name)

        full_destination_path = os.path.join(base_destination_folder, backup_name_with_version)
        if compress:
            full_destination_path += ".zip"

        self.logger.info(f"Starting backup of '{source_folder}' to '{full_destination_path}' (Compression: {compress})")

        start_time = datetime.datetime.now()
        files_count = 0
        success = False
        error_message = ""

        try:
            # Clean up old backup if it already exists at the same path (to avoid conflicts)
            if os.path.exists(full_destination_path):
                if os.path.isdir(full_destination_path):
                    shutil.rmtree(full_destination_path)
                    self.logger.warning(f"Existing backup folder deleted: '{full_destination_path}'")
                elif os.path.isfile(full_destination_path):
                    os.remove(full_destination_path)
                    self.logger.warning(f"Existing ZIP backup file deleted: '{full_destination_path}'")

            # Perform copy or compression
            if compress:
                success = self._zip_folder_contents(source_folder, full_destination_path)
                if success:
                    self.logger.info(f"ZIP compression successful from '{source_folder}' to '{full_destination_path}'")
            else:
                success = self._copy_folder_contents(source_folder, full_destination_path)
                if success:
                    self.logger.info(f"Copy successful from '{source_folder}' to '{full_destination_path}'")

            if success:
                files_count = self._count_files_in_folder(source_folder) # Count files after success
                self.logger.info(f"Number of files backed up: {files_count}")

        except PermissionError:
            error_message = f"Permission Error: Access denied to operate on '{source_folder}' or '{full_destination_path}'"
            self.logger.error(error_message)
        except shutil.Error as e:
            error_message = f"Shutil copy error: {e}"
            self.logger.error(error_message)
        except zipfile.BadZipFile as e:
            error_message = f"ZIP file error: {e}"
            self.logger.error(error_message)
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            self.logger.error(error_message)
        finally:
            end_time = datetime.datetime.now()
            duration = end_time - start_time
            status = "SUCCESS" if success else "FAILED"

            log_message = (
                f"Backup completed for '{source_folder}' - Status: {status} - "
                f"Duration: {duration} - Files: {files_count}"
            )
            if error_message:
                log_message += f" - Error: {error_message}"

            self.logger.info(log_message)
            return success