from langchain.tools import tool


@tool
def read_test_file(file_path: str) -> str:
    """
    读取测试文件的内容。

    参数:
    - file_path: 文件路径，如 "output/test_login.py"

    返回: 文件内容
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"文件不存在: {file_path}"
    except Exception as e:
        return f"读取文件失败: {str(e)}"


@tool
def write_test_file(file_path: str, content: str) -> str:
    """
    写入/覆盖测试文件。

    参数:
    - file_path: 文件路径
    - content: 要写入的完整内容

    返回: 操作结果
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"文件已成功写入: {file_path}"
    except Exception as e:
        return f"写入文件失败: {str(e)}"