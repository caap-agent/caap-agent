def read_text_file(file_path):
    content = None
    for encoding in ['cp949', 'utf-16', 'utf-8']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
        except Exception:
            pass

    if content is None:
        raise RuntimeError(f"Failed to read {file_path}")
    return content
