import parent
from src.differ import MullvadDiffer
from json import load
with open('tests/snapshots/2022-01-01.json', encoding='utf-8') as file:
    old_data = load(file)

with open('tests/snapshots/2024-04-05.json', encoding='utf-8') as file:
    new_data = load(file)


def main():
    mv = MullvadDiffer(old_data, new_data)
    changes = mv.get_changes()
    for change in changes:
        print(change['message'], '\n')


if __name__ == '__main__':
    main()
