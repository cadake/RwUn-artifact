import os
import json
from pathlib import Path
import matplotlib.pyplot as plt


def load_results(folder: str, wanted_fields=None):
    """
      {
        "gate": [...],
        "<field1>": [...],
        "<field2>": [...],
        ...
      }

    """
    rows = [] 
    field_union = set()

    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if not os.path.isfile(filepath):
            continue

        with open(filepath, "r") as f:
            data = json.load(f)

        config = data.get("config", {})
        gate = config.get("n_gates")
        if gate is None:
            continue

        res = data.get("results", {})
        rows.append({"gate": gate, "results": res})

        if wanted_fields is None:
            field_union.update(res.keys())

    if not rows:
        return {"gate": []}

    fields = wanted_fields if wanted_fields is not None else sorted(field_union)

    rows.sort(key=lambda r: r["gate"])

    out = {"gate": [r["gate"] for r in rows]}
    for k in fields:
        out[k] = [r["results"].get(k, None) for r in rows]

    return out


def plot_gatecount_two_curves_panels(
    folders,
    width_labels,
    tool_labels=("tool1", "tool2"),
    out_path="figures/gatecnt_two_curves_panels.pdf",
    figsize=(12.5, 2.7),
    y_builder=None,
    y_label="Metric",
    x_label="Gate count",
    title_prefix="",
    y_lim=None,
    share_y=True,
    pad_ratio=0.05,
    grid=True,
):
    assert len(folders) == 3
    assert len(width_labels) == 3
    if y_builder is None:
        raise ValueError("y_builder must be provided, e.g. lambda d: (d['s1'], d['s2']).")

    series = []
    for folder in folders:
        d = load_results(folder)  # e.g., {"gate":[...], "s1":[...], ...}
        d.setdefault("gate", [])
        series.append(d)

    def _ylim_from(values, pad_ratio=0.05):
        vals = [v for v in values if v is not None]
        if not vals:
            return None
        lo, hi = float(min(vals)), float(max(vals))
        if hi == lo:
            return lo - 1.0, hi + 1.0
        pad = (hi - lo) * pad_ratio
        return lo - pad, hi + pad

    s1_style = dict(color="#354cfe", marker="o", markersize=5.5, linewidth=1.0,
                    fillstyle="full", linestyle="solid")
    s2_style = dict(color="#d62728", marker="x", markersize=5.5, linewidth=1.0,
                    fillstyle="none", linestyle="dashed")

    fig, axes = plt.subplots(1, 3, figsize=figsize, constrained_layout=True, squeeze=False)
    axes = axes[0]

    handles = labels = None

    ys_all = []
    computed = []
    for col in range(3):
        d = series[col]
        x = d.get("gate", [])
        if not x:
            computed.append((None, None, None))
            continue

        y1, y2 = y_builder(d)
        computed.append((x, y1, y2))
        ys_all.extend([v for v in y1 if v is not None])
        ys_all.extend([v for v in y2 if v is not None])

    global_ylim = None
    if y_lim is not None:
        global_ylim = y_lim
    elif share_y and ys_all:
        global_ylim = _ylim_from(ys_all, pad_ratio=pad_ratio)

    for col in range(3):
        ax = axes[col]
        x, y1, y2 = computed[col]

        if x is None:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
            continue

        ax.plot(x, y1, label=tool_labels[0], **s1_style)
        ax.plot(x, y2, label=tool_labels[1], **s2_style)

        ax.set_title(f"{title_prefix}{width_labels[col]}")
        ax.set_xlabel(x_label)
        if grid:
            ax.grid(True, linestyle="--", alpha=0.35)

        if col == 0:
            ax.set_ylabel(y_label)
        else:
            ax.set_ylabel("")

        if global_ylim is not None:
            ax.set_ylim(*global_ylim)
        else:
            local_vals = [v for v in (list(y1) + list(y2)) if v is not None]
            local_ylim = _ylim_from(local_vals, pad_ratio=pad_ratio)
            if local_ylim is not None:
                ax.set_ylim(*local_ylim)

        if handles is None:
            handles, labels = ax.get_legend_handles_labels()

    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=2, frameon=True,
                   bbox_to_anchor=(0.35, 1.05))

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"saved: {out_path}")

