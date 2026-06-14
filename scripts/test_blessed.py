import time

from blessed import Terminal

term = Terminal()

print(term.move_down)

for i in range(1, 100):
    # term.clear_eol clears any leftover characters from the previous print
    print(term.move_up + f"Current number: {i}" + term.clear_eos)

    # Small delay so humans can actually see it increment
    time.sleep(0.02)

print("Done!")
