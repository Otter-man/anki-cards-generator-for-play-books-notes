import pickle
import json
import os
from itertools import islice
from ast import literal_eval
from subprocess import Popen

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload


class GoogleDriveNoteDownloader:
    def create_gdriver(self):

        SCOPES = [
            "https://www.googleapis.com/auth/drive.metadata.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

        gdriver = build("drive", "v3", credentials=creds)
        return gdriver

    def get_notes_info(self, gdriver):

        with open("settings.json", "a+") as setting_file:

            setting_file.seek(0)
            if setting_file.read() == "":
                print(
                    f"Setting file not found, creating new setting file for tracking note files"
                )
                setting_file.write("{}")

            setting_file.seek(0)
            all_notes = literal_eval(setting_file.read())

        notes_folder_search = (
            gdriver.files()
            .list(
                q="mimeType='application/vnd.google-apps.folder' and name='Play Books Notes' and trashed=False",
                spaces="drive",
                fields="files(name,id,mimeType,trashed)",
            )
            .execute()
        )
        notes_folder_id = notes_folder_search.get("files")[0]["id"]

        page_token = None
        notes_files = []
        while True:
            notes_files_search = (
                gdriver.files()
                .list(
                    q=f"'{notes_folder_id}' in parents and name contains 'note' and trashed=False",
                    spaces="drive",
                    fields="nextPageToken, files(id, name, version)",
                    pageToken=page_token,
                )
                .execute()
            )
            for file_info in notes_files_search.get("files", []):
                file_id = file_info["id"]
                file_name = file_info["name"]
                file_version = file_info["version"]
                if all_notes.get(file_id) != [file_name, file_version]:
                    all_notes[file_id] = [file_name, file_version]
                    notes_files.append(file_info)
                else:
                    continue

            page_token = notes_files_search.get("nextPageToken", None)
            if page_token is None:
                break

        with open("settings.json", "w") as setting_file:
            setting_file.write(json.dumps(all_notes, indent=4))

        return notes_files


class NoteScrapper:
    def download_note_file(self, gdriver, file_info):

        file_id = file_info["id"]
        file_name = file_info["name"] + ".txt"

        note_file = (
            gdriver.files()
            .export_media(fileId=file_id, mimeType="text/plain")
            .execute()
        )

        # To download file as HTML for easier parsing.
        # note_file_html = (
        #     gdriver.files()
        #     .export_media(fileId=file_id, mimeType="text/html")
        #     .execute()
        # )
        # # with open(
        # #     f'{" ".join(file_info["name"].split())}.html', "w"
        # # ) as file_html:
        # #     file_html.write(note_file_html.decode("utf-8"))

        note_file = note_file.decode("utf-8").split("\n")

        return file_name, note_file

    def grab_notes(self, book, words_list):

        exceptions = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
            "Introduction",
            "Notes",
            "they",
        ]

        with open("result.txt", "r") as old_words:
            old_words = [word.strip() for word in old_words.readlines()]

            for line in islice(book, 15, None):
                line = str(line)
                if (line[0] != "\t") and (line[0] != "w"):
                    continue

                line = line.strip()
                line = line.split()

                if not line:
                    continue

                try:
                    line[0] = int(line[0])
                    continue
                except (ValueError, IndexError):

                    if line[0] == "w":
                        line.pop(0)

                    word_in_card = " ".join(line)
                    if (word_in_card in old_words) or (
                        word_in_card.lower() in old_words
                    ):
                        continue
                    elif (len(line) == 1) and (len(line[0]) <= 2):
                        continue
                    elif line[0] not in exceptions and 0 < len(line) <= 4:
                        words_list.append(" ".join(line))


def notegrabber():

    downloader = GoogleDriveNoteDownloader()
    scrapper = NoteScrapper()
    gdriver = downloader.create_gdriver()
    all_notes = downloader.get_notes_info(gdriver)

    # We download note files for all books and scrape words marked in them.
    words_list = []
    for book in all_notes:
        file_name, note_file = scrapper.download_note_file(gdriver, book)
        scrapper.grab_notes(note_file, words_list)
        print(f"finished scraping {file_name}")

    if words_list:
        with open("current_words.txt", "w+") as current_word_file:
            for word in words_list:
                current_word_file.write(word + "\n")
            current_word_file.seek(0)

            print(
                "Please check all the words, script will continue after you close the file"
            )
            Popen(["gedit", "-w", current_word_file.name]).wait()

        with open("result.txt", "a+") as word_library:
            with open("current_words.txt", "r") as current_word_file_edited:
                words_edited = [word.strip()
                                for word in current_word_file_edited.readlines()]
                for word in words_edited:
                    word_library.write(word + "\n")
                print('finished')
