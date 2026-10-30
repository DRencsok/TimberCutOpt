from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from run import TIME_LIMIT

RESULTS = Path(__file__).parent / "results"

# Load data
df = pd.read_csv(RESULTS / "results.csv")

summary = df.groupby(["size", "solver"])[["waste_percent", "runtime_s"]].median().reset_index()

solvers = {
    "cp_sat": "CP-SAT",
    "greedy": "Greedy",
}

# Waste chart

fig_waste, ax_waste = plt.subplots()

unique = summary["solver"].unique()
sizes = summary["size"].unique()

for name in unique:
    rows = summary[summary["solver"] == name]
    ax_waste.plot(rows["size"], rows["waste_percent"], marker="o", label=solvers[name])

ax_waste.legend()
ax_waste.set_xlabel("Problem size (pieces)")
ax_waste.set_ylabel("Median waste (%)")
ax_waste.set_title("Material waste: greedy vs CP-SAT")
ax_waste.set_xscale("log")
ax_waste.set_ylim(bottom=0)
ax_waste.set_xticks(sizes, sizes)
ax_waste.minorticks_off()
fig_waste.savefig(RESULTS / "waste.png", dpi=150, bbox_inches="tight")


# Runtime chart

fig_runtime, ax_runtime = plt.subplots()

for name in unique:
    rows = summary[summary["solver"] == name]
    ax_runtime.plot(rows["size"], rows["runtime_s"], marker="o", label=solvers[name])

ax_runtime.axhline(TIME_LIMIT, linestyle="--", color="grey", label="CP-SAT time limit")
ax_runtime.legend()
ax_runtime.set_xlabel("Problem size (pieces)")
ax_runtime.set_ylabel("Runtime (seconds)")
ax_runtime.set_title("Runtime: greedy vs CP-SAT")
ax_runtime.set_yscale("log")
ax_runtime.set_xscale("log")
ax_runtime.set_xticks(sizes, sizes)
ax_runtime.minorticks_off()

fig_runtime.savefig(RESULTS / "runtime.png", dpi=150, bbox_inches="tight")
