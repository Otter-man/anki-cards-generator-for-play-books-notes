
from mnemocards import greet
from mnemocards._argument_parser import parse_args
from mnemocards.github import github
from mnemocards.generate import generate
from mnemocards.pull import pull
from mnemocards.push import push


def main():
    args = parse_args()

    if args.command == "generate":
        generate(args)
    elif args.command == "import":
        print("Import!!")
    elif args.command == "push":
        push()
    elif args.command == "pull":
        pull()
    elif args.command == "github":
        github(args.api_key, args.dir, args.include, args.exclude, args.gists)
    elif args.command == "clean":
        print("Clean!!")
    elif args.command == "hi":
        greet()


if __name__ == "__main__":
    main()

