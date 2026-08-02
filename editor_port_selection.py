from __future__ import annotations

import socket


EDITOR_PORT_SCAN_LIMIT = 64


def find_available_port(start_port: int, max_attempts: int = EDITOR_PORT_SCAN_LIMIT) -> int:
    if (
        not isinstance(start_port, int)
        or isinstance(start_port, bool)
        or not 1 <= start_port <= 65535
    ):
        raise ValueError("端口号必须是 1 到 65535 之间的整数。")
    if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or max_attempts < 1:
        raise ValueError("端口尝试次数必须是正整数。")

    end_port = min(start_port + max_attempts - 1, 65535)
    last_error: OSError | None = None
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError as error:
                last_error = error

    detail = f"（系统返回：{last_error}）" if last_error else ""
    raise RuntimeError(
        f"无法在本机端口 {start_port}-{end_port} 启动编辑器。"
        "请关闭占用这些端口的程序，或用 --port 指定其他端口。"
        f"{detail}"
    )
