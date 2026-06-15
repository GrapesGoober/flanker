import random
import time

from blessed import Terminal


def run_simple_telemetry():
    term = Terminal()

    experiments = [0, 0, 0, 0, 0]

    print(term.clear)
    # Reserve lines in the terminal so we don't scroll
    START_ROW = 2
    while any(p < 100 for p in experiments):
        for idx in range(len(experiments)):
            if experiments[idx] < 100:
                # Simulate progress
                experiments[idx] = min(100, experiments[idx] + random.randint(1, 5))

                # Jump directly to the row where the number lives
                # 'Experiment X: ' is 14 characters long, so we jump to x=14
                target_row = START_ROW + idx
                with term.location(0, target_row):
                    print(
                        f"Experiment {idx}: {experiments[idx]}%{term.clear_eol}",
                        end="",
                        flush=True,
                    )

        time.sleep(0.1)

    # Move cursor to the bottom when done
    print(term.move_xy(0, START_ROW + len(experiments) + 1) + "Done!")


if __name__ == "__main__":
    run_simple_telemetry()
