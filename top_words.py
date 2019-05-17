import ast
import os
import collections
import subprocess
import json
import csv
from nltk import pos_tag
from uuid import uuid4

FILE_LIMIT = 100
TOP_SIZE = 200


class TopWords:
    def __init__(self):
        self.word_type = 'noun'
        self.find_where = 'function'
        self.export_type = 'no'

    def export(self, words):
        if self.export_type == 'json':
            export_data = {}
            for word in words:
                export_data[word[0]] = word[1]
            with open('words.json', 'w') as json_file:
                json.dump(export_data, json_file)
                print('JSON file exported!')
        elif self.export_type == 'csv':
            with open('sales.csv', 'w') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=',')
                for word in words:
                    csv_writer.writerow(word)
                print('CSV file exported!')

    def clone_project(self, url, folder):
        code = subprocess.call('git clone ' + url + ' ' + folder)
        if code == 0:
            print("Sucess clone!")
        else:
            print("Error clone!")
        return code

    def _get_searched_objects(self, trees):
        searched = []
        inst = ast.FunctionDef if self.find_where == 'function' else ast.Name
        for tree in trees:
            for node in ast.walk(tree):
                if isinstance(node, inst):
                    if self.find_where == 'function':
                        name = node.name.lower()
                    else:
                        name = node.id.lower()
                    if not (name.startswith('__') and name.endswith('__')):
                        searched.append(name)
        return searched

    def _validate_word(self, word):
        if not word:
            return False
        pos_info = pos_tag([word])
        validate_type = 'VB' if self.word_type == 'verb' else 'NN'
        return pos_info[0][1] == validate_type

    def _get_words_from_searched_name(self, searched):
        return [word for word in searched.split('_') if self._validate_word(word)]

    def _get_words_from_searched_object(self, searched):
        words = []
        for searched_name in searched:
            for word in self._get_words_from_searched_name(searched_name):
                words.append(word)
        return words

    def _get_filenames(self, path):
        filenames = []
        for dirname, dirs, files in os.walk(path, topdown=True):
            for file in files:
                if file.endswith('.py'):
                    filenames.append(os.path.join(dirname, file))
                    if len(filenames) == FILE_LIMIT:
                        return filenames
        return filenames

    def _parse_file(self, file):
        try:
            tree = ast.parse(file)
        except SyntaxError as e:
            print("Parse error :", e)
            tree = None
        return tree

    def _get_trees(self, path, with_filenames=False, with_file_content=False):
        """
        Возвращает список распарсенных с помощью ast модуля .py файлов.
        С помощью функции os.walk рекурсивно проходится по всем директориям,
        находящимся в папке path, ищет .py файлы и заносит их в список trees
        """
        trees = []
        filenames = self._get_filenames(path)
        print('total %s files in path %s' % (len(filenames), path))
        for filename in filenames:
            with open(filename, 'r', encoding='utf-8') as attempt_handler:
                main_file_content = attempt_handler.read()
            tree = self._parse_file(main_file_content)
            if with_filenames:
                if with_file_content:
                    trees.append((filename, main_file_content, tree))
                else:
                    trees.append((filename, tree))
            else:
                trees.append(tree)
        print('trees generated')
        return trees

    def get_top_verbs_in_path(self, path, top_size=10):
        trees = [t for t in self._get_trees(path) if t]
        searched_object = self._get_searched_objects(trees)
        print(self.find_where + 's extracted')
        words = self._get_words_from_searched_object(searched_object)
        return collections.Counter(words).most_common(top_size)


def main():
    top = TopWords()
    #  1. Вводим url проекта который нужно склонировать
    while True:
        project_path = input('Enter project url to clone >> ')
        if(project_path != ""):
            break
        print('Error: Url cannot be empty!')
    temp_path = 'projects/'+str(uuid4())
    answer = top.clone_project(project_path, temp_path)
    if answer != 0:
        return
    path = os.path.join('.', temp_path)
    #  2. Искать глаголы или существительные
    while True:
        word_type = input('Enter word type (verb/noun) >> ')
        if word_type in ['noun', 'verb']:
            top.word_type = word_type
            break
        print('Error: Enter valid type!')
    #  3. Искать в функции или в именах переменных
    while True:
        find_where = input('Where to find this words (function/variable) >> ')
        if find_where in ['function', 'variable']:
            top.find_where = find_where
            break
        print('Error: Enter valid type!')

    wds = top.get_top_verbs_in_path(path)
    print('total %s words, %s unique' % (len(wds), len(set(wds))))
    for word, occurence in collections.Counter(wds).most_common(TOP_SIZE):
        print(word, occurence)
    #  4. Экспорт
    while True:
        export_type = input('Export data? (no/json/csv) >> ')
        if export_type in ['json', 'csv', 'no']:
            top.export_type = export_type
            break
        print('Error: Enter valid data type!')
    if export_type != 'no':
        top.export(wds)


main()
