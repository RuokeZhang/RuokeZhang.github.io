from abc import ABC, abstractmethod
class Filter(ABC):
    @abstractmethod
    def matches(self, file)->bool:
        pass

class File:
    def __init__(self, name, size, is_directory, extension=""):
        self.extension=extension
        self.name=name
        self.size=size
        self.is_directory=is_directory
        self.children=[]
class SizeFilter(Filter):
    def __init__(self,min_size=0, max_size=float("inf")):
        self.min_size=min_size
        self.max_size=max_size
    def matches(self, file):
        return self.max_size>=file.size>=self.min_size
class ExtensionFilter(Filter):
    def __init__(self, extension):
        self.extension=extension
    def matches(self, file):
        return file.extension==self.extension
class AndFilter(Filter):
    def __init__(self, filters):
        self.filters=filters
    def matches(self, file):
        return all(filter.matches(file) for filter in self.filters)
class OrFilter(Filter):
    def __init__(self, filters):
        self.filters=filters
    def matches(self, file):
        return any(filter.matches(file) for filter in self.filters)
class NotFilter(Filter):
    def __init__(self, filter):
        self.filter=filter
    def matches(self, file):
        return not self.filter.matches(file)
class FileScanStrategy(ABC):
    @abstractmethod
    def scan(self, directory, filter):
        pass
class DFSFileScanStrategy(FileScanStrategy):
    def scan(self, directory, filter):
        result=[]
        def _scan_directory(directory, filter):
            if not directory:
                return 
            #在当前diretory搜索
            for file in directory.children:
                if file.is_directory:
                    _scan_directory(file, filter)
                elif filter.matches(file):
                    result.append(file)
                
        _scan_directory(directory, filter)
        return result

class FileFinder:
    def __init__(self, scan_strategy):
        self.scan_strategy=scan_strategy
    def find(self, directory, filter):
        return self.scan_strategy.scan(directory, filter)
    

def build_test_tree():
    root = File("root", 0, True)

    docs = File("docs", 0, True)
    media = File("media", 0, True)

    a = File("a.txt", 4, False, "txt")
    b = File("b.txt", 10, False, "txt")
    c = File("c.xml", 12, False, "xml")
    d = File("d.jpg", 8, False, "jpg")
    e = File("e.mp3", 20, False, "mp3")

    root.children = [docs, media]
    docs.children = [a, b, c]
    media.children = [d, e]

    return root


def test_size_filter():
    root = build_test_tree()
    finder = FileFinder(DFSFileScanStrategy())

    result = finder.find(root, SizeFilter(9))
    names = [f.name for f in result]

    assert names == ["b.txt", "c.xml", "e.mp3"]
    print("test_size_filter passed")


def test_extension_filter():
    root = build_test_tree()
    finder = FileFinder(DFSFileScanStrategy())

    result = finder.find(root, ExtensionFilter("txt"))
    names = [f.name for f in result]

    assert names == ["a.txt", "b.txt"]
    print("test_extension_filter passed")


def test_and_filter():
    root = build_test_tree()
    finder = FileFinder(DFSFileScanStrategy())

    f = AndFilter([SizeFilter(5), ExtensionFilter("txt")])
    result = finder.find(root, f)
    names = [file.name for file in result]

    assert names == ["b.txt"]
    print("test_and_filter passed")


def test_or_filter():
    root = build_test_tree()
    finder = FileFinder(DFSFileScanStrategy())

    f = OrFilter([SizeFilter(15), ExtensionFilter("jpg")])
    result = finder.find(root, f)
    names = [file.name for file in result]

    assert names == ["d.jpg", "e.mp3"]
    print("test_or_filter passed")


def test_not_filter():
    root = build_test_tree()
    finder = FileFinder(DFSFileScanStrategy())

    f = NotFilter(ExtensionFilter("txt"))
    result = finder.find(root, f)
    names = [file.name for file in result]

    assert names == ["c.xml", "d.jpg", "e.mp3"]
    print("test_not_filter passed")


if __name__ == "__main__":
    test_size_filter()
    test_extension_filter()
    test_and_filter()
    test_or_filter()
    test_not_filter()