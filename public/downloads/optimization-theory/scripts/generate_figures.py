"""Generate deterministic SVG teaching figures used by the optimization notes."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "images"
OUT.mkdir(exist_ok=True)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, format="svg", bbox_inches="tight")
    plt.close(fig)


def foundations():
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    ax = axes[0]
    for p, color, label in [(1, "#2563eb", r"$\|x\|_1=1$"),
                            (2, "#059669", r"$\|x\|_2=1$")]:
        if p == 1:
            pts = np.array([[1, 0], [0, 1], [-1, 0], [0, -1], [1, 0]])
            ax.plot(pts[:, 0], pts[:, 1], color=color, label=label)
        else:
            t = np.linspace(0, 2*np.pi, 300)
            ax.plot(np.cos(t), np.sin(t), color=color, label=label)
    ax.add_patch(plt.Rectangle((-1, -1), 2, 2, fill=False,
                               color="#dc2626", label=r"$\|x\|_\infty=1$"))
    ax.set(title="Three unit balls", xlabel=r"$x_1$", ylabel=r"$x_2$",
           aspect="equal", xlim=(-1.25, 1.25), ylim=(-1.25, 1.25))
    ax.legend(fontsize=8)

    ax = axes[1]
    x = np.linspace(-2, 2, 180)
    y = np.linspace(-1.5, 1.5, 180)
    X, Y = np.meshgrid(x, y)
    # Same function as the worked example in 01:
    # f=x1^2+2*x1*x2+3*x2^2, H=[[2,2],[2,6]].
    Z = X**2 + 2*X*Y + 3*Y**2
    ax.contour(X, Y, Z, levels=[0.5, 1, 2, 4, 8], colors="#7c3aed")
    d1 = np.array([1.0, 0.0]); d2 = np.array([0.0, 1.0])
    ax.arrow(0, 0, *d1, width=.015, color="#2563eb", length_includes_head=True)
    ax.arrow(0, 0, *d2, width=.015, color="#dc2626", length_includes_head=True)
    ax.text(1.04, 0, r"$d_1^THd_1=2$")
    ax.text(.03, 1.05, r"$d_2^THd_2=6$")
    ax.set(title="Hessian records directional curvature", xlabel=r"$x_1$",
           ylabel=r"$x_2$", aspect="equal")
    save(fig, "01-norm-hessian.svg")


def simplex():
    fig, ax = plt.subplots(figsize=(5.3, 4.2))
    poly = np.array([[0, 0], [3, 0], [2, 2], [0, 4]])
    ax.fill(poly[:, 0], poly[:, 1], color="#dbeafe", edgecolor="#2563eb")
    cyc = np.vstack([poly, poly[0]])
    ax.plot(cyc[:, 0], cyc[:, 1], color="#2563eb")
    for i, (x, y) in enumerate(poly):
        ax.scatter(x, y, color="#111827", zorder=3)
        ax.text(x + .08, y + .08, f"V{i}")
    ax.annotate("simplex pivot", xy=(2, 2), xytext=(3, 0),
                arrowprops=dict(arrowstyle="->", color="#dc2626"), color="#dc2626")
    xx = np.linspace(0, 3.4, 100)
    for c in [3, 6, 9]:
        ax.plot(xx, (c - 3*xx)/2, color="#64748b", alpha=.55, linestyle="--")
    ax.set(xlim=(-.2, 3.6), ylim=(-.2, 4.4), xlabel=r"$x_1$", ylabel=r"$x_2$",
           title="Feasible polygon, vertices and objective levels")
    save(fig, "02-simplex-geometry.svg")


def line_search():
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    ax = axes[0]
    # Same golden-section example as 03: phi(t)=(t-2)^2+1 on [0,6].
    t = np.linspace(0, 6, 300)
    f = (t - 2)**2 + 1
    ax.plot(t, f, color="#2563eb")
    a, b = 0.0, 6.0
    rho = (np.sqrt(5)-1)/2
    p, q = a + (1-rho)*(b-a), a + rho*(b-a)
    ax.scatter([p, q], [(p-2)**2+1, (q-2)**2+1], color=["#059669", "#dc2626"])
    ax.axvspan(a, q, color="#dcfce7", alpha=.5)
    ax.set(title="Golden section: discard one side", xlabel=r"$\alpha$", ylabel=r"$\phi(\alpha)$")

    ax = axes[1]
    t = np.linspace(0, 1.4, 250)
    phi = (2 - 4*t)**2
    tangent = 4 - 16*t
    armijo = 4 - 1.6*t
    ax.plot(t, phi, label=r"$\phi(\alpha)$", color="#2563eb")
    ax.plot(t, tangent, label="tangent", color="#64748b", linestyle="--")
    ax.plot(t, armijo, label="Armijo bound", color="#dc2626")
    ok = phi <= armijo
    ax.fill_between(t, 0, 4.5, where=ok, color="#dcfce7", alpha=.45,
                    label="acceptable")
    ax.set(title="Armijo asks for sufficient decrease", xlabel=r"$\alpha$", ylim=(-.2, 4.5))
    ax.legend(fontsize=8)
    save(fig, "03-line-search.svg")


def trajectories():
    # Same quadratic and start as 04: f=.5*x1^2+x2^2, x0=(2,1).
    Q = np.diag([1.0, 2.0])
    x0 = np.array([2.0, 1.0])
    sd = [x0.copy()]
    x = x0.copy()
    for _ in range(8):
        g = Q @ x
        a = (g @ g) / (g @ Q @ g)
        x = x - a*g
        sd.append(x.copy())
    newton = np.vstack([x0, np.zeros(2)])
    cg = [x0.copy()]
    x = x0.copy(); g = Q @ x; d = -g
    for _ in range(2):
        a = -(g @ d)/(d @ Q @ d)
        xn = x + a*d; gn = Q @ xn
        cg.append(xn.copy())
        if np.linalg.norm(gn) < 1e-12:
            break
        beta = (gn @ gn)/(g @ g)
        d = -gn + beta*d; x, g = xn, gn
    fig, ax = plt.subplots(figsize=(6, 4.6))
    xx = np.linspace(-2.8, 2.8, 220); yy = np.linspace(-1.5, 1.5, 220)
    X, Y = np.meshgrid(xx, yy); Z = .5*(X**2 + 2*Y**2)
    ax.contour(X, Y, Z, levels=[.05, .2, .8, 2, 5, 10], colors="#cbd5e1")
    sd = np.array(sd); cg = np.array(cg)
    ax.plot(sd[:, 0], sd[:, 1], "o-", color="#dc2626", label="steepest descent")
    ax.plot(newton[:, 0], newton[:, 1], "s-", color="#059669", label="Newton")
    ax.plot(cg[:, 0], cg[:, 1], "^-", color="#2563eb", label="FR-CG")
    ax.scatter([0], [0], marker="*", s=120, color="#111827")
    ax.set(title="Same quadratic, different trajectories", xlabel=r"$x_1$", ylabel=r"$x_2$")
    ax.legend(fontsize=8)
    save(fig, "04-method-trajectories.svg")


def active_set():
    fig, ax = plt.subplots(figsize=(5.4, 4.4))
    t = np.linspace(0, 1.5, 100)
    ax.fill_between(t, 0, 1.5-t, color="#dbeafe", alpha=.8)
    ax.plot(t, 1.5-t, color="#2563eb", label=r"$x_1+x_2=1.5$")
    path = np.array([[0, 0], [1.5, 0], [1.25, .25]])
    ax.plot(path[:, 0], path[:, 1], "o-", color="#dc2626", linewidth=2)
    labels = [r"$W=\{1,2\}$", r"$W=\{2,3\}$", r"$W=\{3\}$"]
    for (x, y), label in zip(path, labels):
        ax.text(x+.03, y+.06, label, fontsize=9)
    ax.scatter([2], [1], marker="x", s=90, color="#111827", label="unconstrained minimizer")
    ax.set(xlim=(-.1, 2.25), ylim=(-.1, 1.35), xlabel=r"$x_1$", ylabel=r"$x_2$",
           title="Active-set path and working-set changes")
    ax.legend(fontsize=8)
    save(fig, "05-active-set.svg")


def active_set_flow():
    fig, ax = plt.subplots(figsize=(6.6, 7.4))
    ax.set_axis_off()

    def box(x, y, text, color="#dbeafe", width=.54, height=.075):
        patch = plt.Rectangle((x-width/2, y-height/2), width, height,
                              transform=ax.transAxes, facecolor=color,
                              edgecolor="#334155", linewidth=1.2)
        ax.add_patch(patch)
        ax.text(x, y, text, transform=ax.transAxes, ha="center", va="center",
                fontsize=9)

    def arrow(x1, y1, x2, y2, label=None):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), xycoords=ax.transAxes,
                    arrowprops=dict(arrowstyle="->", color="#334155", lw=1.2))
        if label:
            ax.text((x1+x2)/2+.012, (y1+y2)/2, label, transform=ax.transAxes,
                    fontsize=8, color="#475569")

    box(.5, .94, r"Feasible $x_0$; build $W_0$")
    box(.5, .80, r"Solve equality-QP for $p$ and $\lambda_W$")
    box(.5, .66, r"Is $\|p\|\leq\varepsilon$?", color="#fef3c7")
    box(.20, .49, r"Compute blocking $\alpha$", width=.34)
    box(.20, .34, r"$x\leftarrow x+\alpha p$", width=.34)
    box(.20, .19, r"If blocked, add constraint", width=.38)
    box(.80, .49, r"Are all $\lambda_W\geq-\varepsilon$?", color="#fef3c7", width=.38)
    box(.80, .32, "KKT stop", color="#dcfce7", width=.26)
    box(.80, .16, r"Remove most negative $\lambda_i$", color="#fee2e2", width=.40)
    arrow(.5, .90, .5, .84)
    arrow(.5, .76, .5, .70)
    arrow(.42, .63, .24, .53, "no")
    arrow(.58, .63, .76, .53, "yes")
    arrow(.20, .45, .20, .38)
    arrow(.20, .30, .20, .23)
    arrow(.24, .16, .45, .77, "repeat")
    arrow(.80, .45, .80, .36, "yes")
    arrow(.80, .45, .80, .20, "no")
    arrow(.76, .13, .55, .77, "repeat")
    ax.set_title("Feasible active-set method", fontsize=12)
    save(fig, "05-active-set-flow.svg")


if __name__ == "__main__":
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": .2})
    foundations()
    simplex()
    line_search()
    trajectories()
    active_set()
    active_set_flow()
    print(f"generated SVG files in {OUT}")
