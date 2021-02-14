import unittest
import pytest
import os
import ast
import glob

from mnemocards.notegrabber import NoteParserHTML, NoteParserXML


class TestParserHTMLFiles(unittest.TestCase):

    def setUp(self):

        global colors, test_folder_path
        colors = {"vocab": "#c5e1a5",
                  "highlight": "#ffb8a1",
                  "note": "#93e3ed",
                  "golden_glow_yellow": "#fde096"}
        test_folder_path = os.path.join(os.getcwd().split(
            'mnemocards-for-play-books/')[0], 'mnemocards-for-play-books/tests/test_parser_files')

        global EXAMPLES
        examplar_file = os.path.join(
            test_folder_path, 'test_note_examples.txt')

        with open(examplar_file, 'r') as examples:
            examples = examples.read()
            EXAMPLES = ast.literal_eval(examples)

    @ pytest.mark.xml
    def test_html_parser_produces_correct_results(self):

        for test_file in glob.glob(f"{test_folder_path}/*.html"):
            file_name = test_file.split('/')[-1].split('.html')[0]

            vocab, notes, highlights = [], [], []

            with open(test_file, 'r') as note_file:
                html_src = note_file.read()

            all_notes_from_file = NoteParserHTML(
                html_src).grab_all_html_notes()

            for note in all_notes_from_file:
                note = NoteParserHTML(
                    str(note)).parse_html_note_into_types(colors)
                vocab.extend(note[0])
                notes.extend(note[1])
                highlights.extend(note[2])

            self.assertEqual([vocab, notes, highlights], [
                EXAMPLES[file_name][0], EXAMPLES[file_name][1], EXAMPLES[file_name][2]])

    @ pytest.mark.xml
    def test_docx_parser_produces_correct_results(self):

        for test_file in glob.glob(f"{test_folder_path}/*.docx"):
            file_name = test_file.split('/')[-1].split('.docx')[0]

            vocab, notes, highlights = NoteParserXML(
                test_file).grab_all_xml_notes(colors)

            # print(vocab)
            self.assertEqual([vocab, notes, highlights], [
                             EXAMPLES[file_name][0], EXAMPLES[file_name][1], EXAMPLES[file_name][2]])
