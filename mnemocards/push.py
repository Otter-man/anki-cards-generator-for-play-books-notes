
import os

from mnemocards.utils import read_config


COMMIT_MESSAGE = "Updating repository with mnemocards."


def commit_and_push_repo(gist_path):
    os.system(f'cd {gist_path} && git add . && '
              f'git commit -m "{COMMIT_MESSAGE}" && git push origin master')


def commit_and_push_all(repos):
    for repo, path in repos:
        commit_and_push_repo(path)


def push():
    conf = read_config()
    repos = conf.get("repos", [])
    if len(repos) == 0:
        raise Exception("No repository list in your config file")
    else:
        commit_and_push_all(conf["repos"])

