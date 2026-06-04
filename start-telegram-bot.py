#!/usr/bin/env python3
"""Запускает claude --channels с PTY.
Автоматически отправляет Enter чтобы пройти first-run wizard (выбор темы)."""
import pty
import os
import select
import time

os.environ["HOME"] = os.path.expanduser("~")
os.environ["PATH"] = os.path.expanduser("~/.bun/bin") + ":/usr/local/bin:/usr/bin:/bin"
os.environ["NO_COLOR"] = "1"
os.environ["FORCE_COLOR"] = "0"
os.environ["TERM"] = "xterm-256color"

cmd = ["/usr/bin/claude", "--channels", "plugin:telegram@local-plugins"]

master_fd, slave_fd = pty.openpty()
pid = os.fork()

if pid == 0:
    # дочерний процесс
    os.close(master_fd)
    os.setsid()
    import fcntl, termios, struct
    fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)
    os.dup2(slave_fd, 0)
    os.dup2(slave_fd, 1)
    os.dup2(slave_fd, 2)
    if slave_fd > 2:
        os.close(slave_fd)
    os.execv(cmd[0], cmd)
else:
    # родительский процесс — пишем в PTY и форвардим stdout
    os.close(slave_fd)

    enter_sent = 0
    enter_delay = [2.0, 1.0, 1.0]  # секунды до отправки каждого Enter
    last_enter_time = time.time()

    while True:
        try:
            r, _, _ = select.select([master_fd], [], [], 0.5)
        except (OSError, ValueError):
            break

        if r:
            try:
                data = os.read(master_fd, 4096)
                os.write(1, data)
            except OSError:
                break

        # Отправляем несколько Enter в начале чтобы пройти wizard
        if enter_sent < len(enter_delay):
            if time.time() - last_enter_time > enter_delay[enter_sent]:
                try:
                    os.write(master_fd, b"\r\n")
                    enter_sent += 1
                    last_enter_time = time.time()
                except OSError:
                    break

        # Проверяем не завершился ли дочерний процесс
        result = os.waitpid(pid, os.WNOHANG)
        if result[0] != 0:
            break

    try:
        os.waitpid(pid, 0)
    except ChildProcessError:
        pass
