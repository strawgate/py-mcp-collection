import subprocess
import tempfile
from pathlib import Path

import pytest
from aiofiles import open as aopen

from filesystem_operations_mcp.filesystem.file_system import FileSystem
from filesystem_operations_mcp.filesystem.nodes import BaseNode, DirectoryEntry, FileEntry, FileEntryTypeEnum, FileEntryWithMatches


# Helper function to create test files
async def create_test_file(path: Path, content: str) -> None:
    async with aopen(path, "w") as f:
        _ = await f.write(content)


# Helper function to create test directory structure
async def create_test_structure(root: Path) -> None:
    # Create some text files
    await create_test_file(root / "test_with_hello_world.txt", "Hello, World!")
    await create_test_file(root / "code_with_hello_world.py", "def hello():\n    print('Hello, World!')")
    await create_test_file(root / "data.json", '{"key": "value"}')
    await create_test_file(root / "should_be_ignored.env", "secret_key=1234567890")

    # Create a subdirectory with files
    subdir = root / "subdir"
    subdir.mkdir()
    await create_test_file(subdir / "nested.txt", "Nested content")
    await create_test_file(subdir / "script_with_hello.sh", "#!/bin/bash\necho 'Hello'")
    await create_test_file(subdir / "should_be_ignored.env", "secret_key=1234567890")

    # Create a hidden file
    await create_test_file(root / ".hidden", "Hidden content")

    # create a gitignore file
    gitdir = root / ".git"
    gitdir.mkdir()
    await create_test_file(root / ".gitignore", "*.env\n**/*.env")


@pytest.fixture
async def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        root = Path(tmpdirname)
        await create_test_structure(root)
        yield root


@pytest.fixture
async def filesystem(temp_dir: Path):
    return FileSystem(path=temp_dir)


@pytest.fixture
async def root_directory(filesystem: FileSystem):
    return DirectoryEntry(path=filesystem.path, filesystem=filesystem)


def test_base_node_properties(temp_dir: Path):
    node = BaseNode(path=temp_dir)

    assert node.name == temp_dir.name
    assert node.is_dir
    assert not node.is_file


def test_file_node_properties(root_directory: DirectoryEntry):
    node = root_directory.get_file("test_with_hello_world.txt")
    assert node.name == "test_with_hello_world.txt"
    assert node.stem == "test_with_hello_world"
    assert node.extension == ".txt"
    assert node.path == root_directory.path / "test_with_hello_world.txt"

    assert node.relative_path == Path("test_with_hello_world.txt")
    assert node.relative_path_str == "test_with_hello_world.txt"

    assert node.is_file
    assert not node.is_dir
    assert node.size == 13
    assert node.type == FileEntryTypeEnum.TEXT


class TestFileEntry:
    def test_node_properties(self, root_directory: DirectoryEntry):
        node = root_directory.get_file("test_with_hello_world.txt")
        assert node.name == "test_with_hello_world.txt"
        assert node.stem == "test_with_hello_world"
        assert node.extension == ".txt"
        assert node.path == root_directory.path / "test_with_hello_world.txt"

    def test_file_size(self, root_directory: DirectoryEntry):
        node = root_directory.get_file("test_with_hello_world.txt")
        assert node.size == 13

    def test_file_type(self, root_directory: DirectoryEntry):
        node = root_directory.get_file("test_with_hello_world.txt")
        assert node.type == FileEntryTypeEnum.TEXT

    def test_file_extension(self, root_directory: DirectoryEntry):
        node = root_directory.get_file("test_with_hello_world.txt")
        assert node.extension == ".txt"

    def test_file_stem(self, root_directory: DirectoryEntry):
        node = root_directory.get_file("test_with_hello_world.txt")
        assert node.stem == "test_with_hello_world"

    def test_file_relative_path(self, root_directory: DirectoryEntry):
        node = root_directory.get_file("test_with_hello_world.txt")
        assert node.relative_path == Path("test_with_hello_world.txt")
        assert node.relative_path_str == "test_with_hello_world.txt"

    def test_file_relative_path_str(self, root_directory: DirectoryEntry):
        node = root_directory.get_file("test_with_hello_world.txt")
        assert node.relative_path_str == "test_with_hello_world.txt"

    def test_file_is_file(self, root_directory: DirectoryEntry):
        node = root_directory.get_file("test_with_hello_world.txt")
        assert node.is_file
        assert not node.is_dir

    async def test_file_atext(self, root_directory: DirectoryEntry):
        node = root_directory.get_file("test_with_hello_world.txt")
        assert await node.atext() == "Hello, World!"

    async def test_file_alines(self, root_directory: DirectoryEntry):
        node = root_directory.get_file("test_with_hello_world.txt")
        assert await node.alines() == ["Hello, World!"]

    async def test_create_file(self, root_directory: DirectoryEntry, temp_dir: Path):
        await FileEntry.create_file(path=temp_dir / "test_with_hello_world_new.txt", content="Hello, World!")
        node = root_directory.get_file("test_with_hello_world_new.txt")
        assert await node.atext() == "Hello, World!"
        assert node.size == 13


class TestDirectoryEntry:
    def test_node_properties(self, root_directory: DirectoryEntry):
        node = root_directory.get_directory("subdir")

        assert node.name == "subdir"
        assert node.is_dir
        assert not node.is_file
        assert node.relative_path == Path("subdir")
        assert node.relative_path_str == "subdir"

    def test_get_file(self, root_directory: DirectoryEntry):
        node = root_directory.get_file("subdir/nested.txt")
        assert node.name == "nested.txt"
        assert node.relative_path == Path("subdir/nested.txt")
        assert node.relative_path_str == "subdir/nested.txt"

    def test_get_files(self, root_directory: DirectoryEntry):
        files = root_directory.get_files(["nested.txt", "script_with_hello.sh"])
        assert len(files) == 2
        assert {f.name for f in files} == {"nested.txt", "script_with_hello.sh"}

    def test_get_directory(self, root_directory: DirectoryEntry):
        node = root_directory.get_directory("subdir")
        assert node.name == "subdir"
        assert node.relative_path == Path("subdir")
        assert node.relative_path_str == "subdir"

    class TestFindFiles:
        async def test(self, root_directory: DirectoryEntry):
            descendants: list[FileEntry] = [file async for file in root_directory.afind_files()]
            assert len(descendants) == 5
            descendant_names = sorted([d.name for d in descendants])
            assert descendant_names == [
                "code_with_hello_world.py",
                "data.json",
                "nested.txt",
                "script_with_hello.sh",
                "test_with_hello_world.txt",
            ]

        async def test_depth_one(self, root_directory: DirectoryEntry):
            descendants: list[FileEntry] = [file async for file in root_directory.afind_files(max_depth=1)]
            assert len(descendants) == 3
            descendant_names = sorted([d.name for d in descendants])
            assert descendant_names == [
                "code_with_hello_world.py",
                "data.json",
                "test_with_hello_world.txt",
            ]

        async def test_depth_one_with_excludes(self, root_directory: DirectoryEntry):
            descendants: list[FileEntry] = [file async for file in root_directory.afind_files(max_depth=1, excluded_globs=["*.txt"])]
            assert len(descendants) == 2
            descendant_names = sorted([d.name for d in descendants])
            assert descendant_names == [
                "code_with_hello_world.py",
                "data.json",
            ]

        async def test_excludes_includes(self, root_directory: DirectoryEntry):
            descendants: list[FileEntry] = [
                file async for file in root_directory.afind_files(excluded_globs=["*.txt"], included_globs=["*.py"])
            ]
            assert len(descendants) == 1
            descendant_names = sorted([d.name for d in descendants])
            assert descendant_names == [
                "code_with_hello_world.py",
            ]

        async def test_includes_subdir(self, root_directory: DirectoryEntry):
            descendants: list[FileEntry] = [file async for file in root_directory.afind_files(included_globs=["subdir/*"])]
            assert len(descendants) == 3
            descendant_names = sorted([d.name for d in descendants])
            assert descendant_names == [
                "nested.txt",
                "script_with_hello.sh",
                "should_be_ignored.env",  # The user has specifically included it
            ]

        async def test_excludes_subdir(self, root_directory: DirectoryEntry):
            descendants: list[FileEntry] = [file async for file in root_directory.afind_files(excluded_globs=["subdir"])]
            assert len(descendants) == 3
            descendant_names = sorted([d.name for d in descendants])
            assert descendant_names == [
                "code_with_hello_world.py",
                "data.json",
                "test_with_hello_world.txt",
            ]

        async def test_subdir(self, root_directory: DirectoryEntry):
            descendants: list[FileEntry] = [file async for file in root_directory.get_directory("subdir").afind_files()]
            assert len(descendants) == 2
            descendant_names = sorted([d.name for d in descendants])
            assert descendant_names == [
                "nested.txt",
                "script_with_hello.sh",
            ]

    class TestSearchFiles:
        async def test(self, root_directory: DirectoryEntry):
            descendants: list[FileEntry] = [file async for file in root_directory.asearch_files(["print"])]
            assert len(descendants) == 1
            descendant_names = sorted([d.name for d in descendants])
            assert descendant_names == [
                "code_with_hello_world.py",
            ]

        async def test_two(self, root_directory: DirectoryEntry):
            descendants: list[FileEntryWithMatches] = [file async for file in root_directory.asearch_files(["hello"])]
            assert len(descendants) == 3
            descendant_names = sorted([d.name for d in descendants])
            assert descendant_names == [
                "code_with_hello_world.py",
                "script_with_hello.sh",
                "test_with_hello_world.txt",
            ]

            first_file = descendants[0]
            first_match_lines = first_file.matches.lines()
            assert len(first_match_lines) == 2
            assert first_match_lines[0] == "def hello():"
            assert first_match_lines[1] == "    print('Hello, World!')"

        async def test_case_insensitive(self, root_directory: DirectoryEntry):
            descendants: list[FileEntryWithMatches] = [file async for file in root_directory.asearch_files(["hello"], case_sensitive=False)]
            assert len(descendants) == 3
            descendant_names = sorted([d.name for d in descendants])
            assert descendant_names == [
                "code_with_hello_world.py",
                "script_with_hello.sh",
                "test_with_hello_world.txt",
            ]

        # @pytest.fixture(autouse=True)
        # def playground_beats(self):
        #     root_dir = Path("./playground/beats")
        #     if not root_dir.exists():
        #         # git clone --depth 1 --branch <branch_name> --single-branch <repo_url> <clone_path>

        #         # Clone commit 63a537a17839ef23b0cd4cd7d62e708319374b61 with depth 1 and single branch
        #         commit = "63a537a17839ef23b0cd4cd7d62e708319374b61"
        #         repo_url = "https://github.com/elastic/beats.git"
        #         clone_path = "./playground/beats"
        #         git_clone_command = f"git clone --depth 1 --branch {commit} --single-branch {repo_url} {clone_path}"
        #         _ = subprocess.run(git_clone_command, check=False, shell=True)  # noqa: S602

        #     return root_dir.resolve()

        # async def test_beats_search(self, playground_beats: Path):
        #     root_dir = DirectoryEntry(path=playground_beats, filesystem=FileSystem(path=playground_beats))
        #     async_iter = root_dir.asearch_files(["Hello"])
        #     results = [file async for file in async_iter]
        #     assert len(results) == 221

        # async def test_beats_search_wide(self, playground_beats: Path):
        #     root_dir = DirectoryEntry(path=playground_beats, filesystem=FileSystem(path=playground_beats))
        #     async_iter = root_dir.asearch_files(["l"])
        #     results = [file async for file in async_iter]
        #     assert len(results) == 7461

        # @pytest.mark.benchmark(group="search_files")
        # async def test_benchmark_search(self, playground_beats: Path, benchmark: BenchmarkFixture):
        #     root_dir = DirectoryEntry(path=playground_beats, filesystem=FileSystem(path=playground_beats))

        #     def search_pattern():
        #         async_iter = root_dir.asearch_files(["l"])
        #         return len([file async for file in results])

        #     results = benchmark(search_pattern)
        #     assert results == 401

        # @pytest.mark.benchmark(group="search_files")
        # async def test_benchmark(self, playground_beats: Path, benchmark: BenchmarkFixture):
        #     root_dir = DirectoryEntry(path=playground_beats, filesystem=FileSystem(path=playground_beats))

        #     def search_pattern():
        #         async_iter = root_dir.asearch_files(["l"])
        #         return len([file async for file in results])

        #     results = benchmark(search_pattern)
        #     assert results == 401


#     assert node.stem == "subdir"
#     assert node.extension == ""
#     assert node.is_dir

# @pytest.mark.asyncio
# async def test_file_entry_properties(temp_dir: Path):
#     file_path = temp_dir / "test_with_hello_world.txt"
#     node = FileEntry(absolute_path=file_path, root=temp_dir)

#     assert node.name == "test_with_hello_world.txt"
#     assert node.stem == "test"
#     assert node.extension == ".txt"
#     assert node.file_path == "test_with_hello_world.txt"
#     assert node.is_text
#     assert not node.is_binary
#     assert not node.is_code
#     assert not node.is_data

#     # Test file reading
#     content = await node.read_text()
#     assert content == "Hello, World!"

#     # Test binary reading
#     binary = await node.read_binary_base64()
#     assert isinstance(binary, str)  # Should be base64 encoded

#     # Test line reading
#     lines = await node.read_lines()
#     assert len(lines.lines()) == 1
#     assert lines.lines()[0] == "Hello, World!"

#     # Test line numbers
#     line_numbers = await node.read_lines()
#     assert len(line_numbers.lines()) == 1
#     assert line_numbers.line_numbers()[0] == 0
#     assert line_numbers.lines()[0] == "Hello, World!"


# @pytest.mark.asyncio
# async def test_directory_entry_properties(temp_dir: Path):
#     node = DirectoryEntry(absolute_path=temp_dir, root=temp_dir)

#     assert node.name == temp_dir.name
#     assert node.directory_path == "."

#     # Test children
#     children = await node.children()
#     assert len(children) == 4  # test_with_hello_world.txt, code_with_hello_world.py, data.json, subdir

#     # Test finding files
#     txt_files = await node.find_files("*.txt")
#     assert len(txt_files) == 2
#     assert txt_files[0].name == "test_with_hello_world.txt"
#     assert txt_files[1].name == "nested.txt"

#     # Test finding directories
#     dirs = await node.find_dirs("*")
#     assert len(dirs) == 1
#     assert dirs[0].name == "subdir"

#     # Test recursive children
#     all_children = await node._children(max_depth=1)
#     assert len(all_children) == 6  # 4 in root + 2 in subdir


# @pytest.mark.asyncio
# async def test_file_content_matching(temp_dir: Path):
#     file_path = temp_dir / "code_with_hello_world.py"
#     node = FileEntry(absolute_path=file_path, root=temp_dir)

#     # Test simple content matching
#     matches = await node.contents_match("print")
#     assert len(matches) == 1
#     assert "print" in matches[0].match.lines()[0]

#     # Test simple content matching
#     matches = await node.contents_match("print", before=1)
#     assert len(matches) == 1
#     assert "print" in matches[0].match.lines()[0]
#     assert "hello" in matches[0].before.lines()[0]

#     # Test regex matching
#     matches = await node.contents_match_regex(r"def \w+")
#     assert len(matches) == 1
#     assert "def hello" in matches[0].match.lines()[0]

#     # Test context lines
#     matches = await node.contents_match("print", before=1, after=0)
#     assert len(matches) == 1
#     assert len(matches[0].before.lines()) == 1
#     assert "def hello" in matches[0].before.lines()[0]


# @pytest.mark.asyncio
# async def test_file_type_detection(temp_dir):
#     # Test text file
#     txt_node = FileEntry(absolute_path=temp_dir / "test_with_hello_world.txt", root=temp_dir)
#     assert txt_node.is_text
#     assert not txt_node.is_binary
#     assert not txt_node.is_code

#     # Test code file
#     py_node = FileEntry(absolute_path=temp_dir / "code_with_hello_world.py", root=temp_dir)
#     assert py_node.is_code
#     assert not py_node.is_binary

#     # Test data file
#     json_node = FileEntry(absolute_path=temp_dir / "data.json", root=temp_dir)
#     assert json_node.is_data
#     assert not json_node.is_binary


# @pytest.mark.asyncio
# async def test_path_validation(temp_dir: Path):
#     # Test valid path
#     node = FileEntry(absolute_path=temp_dir / "test_with_hello_world.txt", root=temp_dir)
#     node.validate_in_root(temp_dir)

#     # Test invalid path
#     outside_path = Path("/tmp/outside")  # Insecure temporary directory

#     node = FileEntry(absolute_path=outside_path, root=temp_dir)

#     with pytest.raises(FilesystemServerOutsideRootError):
#         node.validate_in_root(temp_dir)


# @pytest.mark.asyncio
# async def test_hidden_files(temp_dir: Path):
#     # Test hidden file
#     hidden_node = FileEntry(absolute_path=temp_dir / ".hidden", root=temp_dir)
#     assert not hidden_node.passes_filters(skip_hidden=True)
#     assert hidden_node.passes_filters(skip_hidden=False)

#     # Test hidden directory
#     hidden_dir = temp_dir / ".hidden_dir"
#     hidden_dir.mkdir()
#     dir_node = DirectoryEntry(absolute_path=hidden_dir, root=temp_dir)
#     assert not dir_node.passes_filters(skip_hidden=True)
#     assert dir_node.passes_filters(skip_hidden=False)
