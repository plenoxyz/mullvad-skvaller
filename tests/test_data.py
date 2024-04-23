import parent
from src.data import MullvadData
from json import load
from differ import MullvadDiff


class TestMullvadData(MullvadData):
    def __load_test_data(self):
        with open('tests/snapshots/2022-01-01.json', 'r') as f:
            return load(f)

    def test_update(self):
        old_data = self.data
        self.data = self.__load_test_data()
        differential = MullvadDiff(old_data, self.data)
        return differential.gen_changes()

def main():
    mv = TestMullvadData('https://api.mullvad.net/www/relays/all/')
    changes = mv.test_update()
    for change in changes:
        print(change)


if __name__ == '__main__':
    main()
