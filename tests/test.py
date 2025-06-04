from pathlib import Path

def find_model_files():
    """
    在当前工作目录（及其子目录）中查找后缀为 .pt、.onnx、.engine 的文件，
    并返回它们相对于当前工作目录的路径列表。
    """
    cwd = Path.cwd()
    extensions = {'.pt', '.onnx', '.engine'}
    result = []

    for path in cwd.rglob('*'):
        if path.is_file() and path.suffix.lower() in extensions:
            # 将绝对路径转换为相对于 cwd 的相对路径
            rel_path = path.relative_to(cwd)
            result.append("./" + str(rel_path))

    return result

if __name__ == "__main__":
    files = find_model_files()
    for f in files:
        print(f)
