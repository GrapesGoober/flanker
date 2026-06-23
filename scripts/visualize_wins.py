import matplotlib.pyplot as plt

win_rates = [
    [0.55, 0.42, 0.70],
    [0.38, 0.50, 0.45],
    [0.62, 0.58, 0.49],
]

plt.imshow(win_rates)  # type: ignore
plt.colorbar(label="Win Rate")  # type: ignore
plt.show()  # type: ignore
