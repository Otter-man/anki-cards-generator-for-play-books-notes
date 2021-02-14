import pickle
import json
import os
import zipfile
from itertools import islice
from ast import literal_eval
from subprocess import Popen
from bs4 import BeautifulSoup as bs

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


class NoteParserHTML:

    def __init__(self, html_string):
        self.html_src = html_string

    def grab_all_html_notes(self):

        soup = bs(self.html_src, 'html.parser')
        all_notes = soup.select('td[style*="width:358"]')
        return all_notes

    def parse_html_note_into_types(self, colors):
        vocab, notes, highlights = [], [], []

        soup = bs(self.html_src, 'html.parser')

        noted = soup.select_one('p:nth-of-type(3):nth-last-of-type(3) span')
        highlighted = soup.select_one('p:first-of-type span')

        if soup.select_one(f'p:first-of-type [style*="{colors["vocab"]}"]'):
            if noted:
                vocab.append(noted.text)
            elif highlighted:
                vocab.append(highlighted.text)

        elif soup.select_one(f'p:first-of-type [style*="{colors["note"]}"]'):
            if noted and highlighted:
                notes.append([highlighted.text, noted.text])
            elif highlighted and not noted:
                notes.append([highlighted.text])

        else:
            highlights.append(highlighted.text)

        return [vocab, notes, highlights]


class NoteParserXML:

    def __init__(self, docx_path):
        self.docx_src = zipfile.ZipFile(docx_path)
        self.xml_content = self.docx_src.read('word/document.xml')
        self.docx_src.close()
        self.xml_soup = bs(self.xml_content, 'html.parser')

    def grab_all_xml_notes(self, colors):
        vocab, notes, highlights = [], [], []

        all_notes = self.xml_soup.find_all('w:tbl')

        for note in all_notes:
            visible = note.find_all('w:tblind')
            if not visible:
                continue

            all_text = note.find_all('w:t')

            highlighted = all_text[0].text
            noted = all_text[1].text

            if len(all_text) == 3:
                noted = None

            if str(note).find(colors["vocab"][1:]) != -1:
                if highlighted and noted:
                    vocab.append(noted)
                else:
                    vocab.append(highlighted)

            elif str(note).find(colors["note"][1:]) != -1:
                if noted and highlighted:
                    notes.append([highlighted, noted])
                else:
                    notes.append([highlighted])

            else:
                highlights.append(highlighted)

        # two first items in highlights are always Bookname and warning.
        return vocab, notes, highlights[2:]


def download_note_file(gdriver, file_info):

    file_id = file_info["id"]
    file_name = file_info["name"]
    note_file = (
        gdriver.files()
        .export_media(fileId=file_id, mimeType="text/html")
        .execute()
    )

    # file_name_html = file_info["name"].replace("\"", "\'") + ".html"
    # with open(file_name_html, "w") as file_html:
    #     file_html.write(note_file_html.decode("utf-8"))

    note_file_html = note_file.decode("utf-8")

    return file_name, note_file_html


colors = {"vocab": "#c5e1a5",
          "highlight": "#ffb8a1",
          "note": "#93e3ed",
          "golden_glow_yellow": "#fde096"}


def notegrabber():

    downloader = GoogleDriveNoteDownloader()
    gdriver = downloader.create_gdriver()
    all_note_files = downloader.get_notes_info(gdriver)

    # We download note files for all books and scrape words marked in them.
    vocab, notes, highlights = [], [], []

    for book in all_note_files:
        file_name, note_file = download_note_file(gdriver, book)
        all_notes_from_file = NoteParserHTML(note_file).grab_all_html_notes()
        for note in all_notes_from_file:
            note = NoteParserHTML(str(note)).parse_html_note_into_types(colors)
            vocab.extend(note[0])
            notes.extend(note[1])
            highlights.extend(note[2])
        print(f"finished scraping {file_name}")

    if vocab:
        with open("result.txt", "r+") as all_words:
            old_words = [word.strip() for word in all_words.readlines()]

            with open("words.txt", "w+") as current_word_file:
                for word in vocab:
                    if word.lower() not in old_words:
                        current_word_file.write(word + "\n")
                current_word_file.seek(0)

                print(
                    "Please check all the words, script will continue after you close the file"
                )
                Popen(["gedit", "-w", current_word_file.name]).wait()

            with open("words.txt", "r") as current_word_file_edited:
                words_edited = [word.strip()
                                for word in current_word_file_edited.readlines()]
                for word in words_edited:
                    all_words.write(word + "\n")
                print('finished')
    else:
        print("No new words in your notes.")
