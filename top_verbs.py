import ast
import os
import collections

from nltk import pos_tag


FILE_LIMIT = 100

# def flat(_list) после рефакторинга стала ненужной


def is_verb(word):
    if not word:
        return False
    pos_info = pos_tag([word])
    return pos_info[0][1] == 'VB'


def get_filenames(path):
    filenames = []
    for dirname, dirs, files in os.walk(path, topdown=True):
        for file in files:
            if file.endswith('.py'):
                filenames.append(os.path.join(dirname, file))
                if len(filenames) == FILE_LIMIT:
                    return filenames
    return filenames


def parse_file(file):
    try:
        tree = ast.parse(file)
    except SyntaxError as e:
        print("Parse error :", e)
        tree = None
    return tree


def get_trees(path, with_filenames=False, with_file_content=False):
    """
    Возвращает список распарсенных с помощью ast модуля .py файлов.
    С помощью функции os.walk рекурсивно проходится по всем директориям,
    находящимся в папке path, ищет .py файлы и заносит их в список trees
    """
    trees = []
    filenames = get_filenames(path)
    print('total %s files in path %s' % (len(filenames), path))
    for filename in filenames:
        with open(filename, 'r', encoding='utf-8') as attempt_handler:
            main_file_content = attempt_handler.read()
        tree = parse_file(main_file_content)
        if with_filenames:
            if with_file_content:
                trees.append((filename, main_file_content, tree))
            else:
                trees.append((filename, tree))
        else:
            trees.append(tree)
    print('trees generated')
    return trees


# def get_all_names(tree) использовалась в get_all_words_in_path


def get_verbs_from_function_name(function_name):
    return [word for word in function_name.split('_') if is_verb(word)]


def get_verbs_from_functions(functions):
    verbs = []
    for function_name in functions:
        for verb in get_verbs_from_function_name(function_name):
            verbs.append(verb)
    return verbs


# def get_all_words_in_path(path) нигде не используется

def get_functions(trees):
    functions = []
    for tree in trees:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                name = node.name.lower()
                if not (name.startswith('__') and name.endswith('__')):
                    functions.append(name)
    return functions


def get_top_verbs_in_path(path, top_size=10):
    trees = [t for t in get_trees(path) if t]
    fncs = get_functions(trees)
    print('functions extracted')
    verbs = get_verbs_from_functions(fncs)
    return collections.Counter(verbs).most_common(top_size)

# def get_top_functions_names_in_path нигде не используется


wds = []
projects = [
    'django',
    'flask',
    'pyramid',
    'reddit',
    'requests',
    'sqlalchemy',
]
TOP_SIZE = 200

for project in projects:
    path = os.path.join('.', project)
    wds += get_top_verbs_in_path(path)

print('total %s words, %s unique' % (len(wds), len(set(wds))))
for word, occurence in collections.Counter(wds).most_common(TOP_SIZE):
    print(word, occurence)
