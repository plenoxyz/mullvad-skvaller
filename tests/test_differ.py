import parent
from skvaller.differ import MullvadDiff
from json import load
with open('tests/snapshots/2022-01-01.json', encoding='utf-8') as file:
    old_data = load(file)

with open('tests/snapshots/2024-04-05.json', encoding='utf-8') as file:
    new_data = load(file)


def main():
    mv = MullvadDiff(old_data, new_data)
    changes = mv.gen_changes()
    for change in changes:
        print(change['message'], '\n')


if __name__ == '__main__':
    main()
