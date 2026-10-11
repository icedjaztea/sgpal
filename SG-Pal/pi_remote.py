"""SSH terminal remote for the existing Pi browser; no GPIO or new listener."""
import os
import select
import sys
import termios
import tty
from pi_online import CDP


def main():
    if not sys.stdin.isatty():
        raise SystemExit('Use ssh -t to allocate a terminal.')
    cdp = CDP()
    fd = sys.stdin.fileno()
    original = termios.tcgetattr(fd)
    print('Pi remote: arrows or A/D select; Enter confirms; Esc or B goes Back; Q quits.', flush=True)
    try:
        tty.setcbreak(fd)
        while True:
            value = os.read(fd, 1).decode(errors='ignore')
            if value.lower() == 'q':
                break
            if value == '\x1b':
                # Read bytes directly: TextIO buffering can hide an arrow suffix.
                suffix = b''
                while select.select([fd], [], [], .08)[0] and len(suffix) < 2:
                    suffix += os.read(fd, 1)
                key = {'[D': 'ArrowLeft', '[C': 'ArrowRight', '[A': 'ArrowLeft', '[B': 'ArrowRight'}.get(suffix.decode(errors='ignore'), 'Escape')
            else:
                key = {'a': 'ArrowLeft', 'd': 'ArrowRight', 'b': 'Escape', '\n': 'Enter', '\r': 'Enter', ' ': 'Enter', '\t': 'Tab'}.get(value.lower())
            if key:
                cdp.key(key)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original)
        cdp.close()
        print('\nRemote closed; the game stays running.')


if __name__ == '__main__':
    main()
