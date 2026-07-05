"""
Credit-risk metrics (pure stdlib). We deliberately lead with AUC-ROC / KS / Gini
and precision-recall — NOT raw accuracy, which is meaningless on an imbalanced
default book (a model predicting 'never defaults' scores ~90% accuracy and is useless).
"""


def auc_roc(y, p):
    """Area under ROC via the Mann-Whitney U statistic (rank-based, exact)."""
    pairs = sorted(zip(p, y))
    # assign average ranks (handle ties)
    ranks = [0.0] * len(pairs)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    n_pos = sum(y)
    n_neg = len(y) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    sum_ranks_pos = sum(rk for rk, (_, yi) in zip(ranks, pairs) if yi == 1)
    return (sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def ks_stat(y, p, bins=100):
    """Kolmogorov-Smirnov: max separation between good/bad cumulative distributions."""
    pos = sorted(pi for pi, yi in zip(p, y) if yi == 1)
    neg = sorted(pi for pi, yi in zip(p, y) if yi == 0)
    if not pos or not neg:
        return 0.0, 0.5
    best, at = 0.0, 0.5
    for t in [k / bins for k in range(bins + 1)]:
        cdf_pos = sum(1 for x in pos if x <= t) / len(pos)
        cdf_neg = sum(1 for x in neg if x <= t) / len(neg)
        d = abs(cdf_pos - cdf_neg)
        if d > best:
            best, at = d, t
    return best, at


def confusion(y, p, threshold):
    tp = fp = tn = fn = 0
    for yi, pi in zip(y, p):
        pred = 1 if pi >= threshold else 0
        if pred == 1 and yi == 1:
            tp += 1
        elif pred == 1 and yi == 0:
            fp += 1
        elif pred == 0 and yi == 0:
            tn += 1
        else:
            fn += 1
    return tp, fp, tn, fn


def prf(y, p, threshold):
    tp, fp, tn, fn = confusion(y, p, threshold)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    acc = (tp + tn) / max(len(y), 1)
    return {"precision": prec, "recall": rec, "f1": f1, "accuracy": acc,
            "tp": tp, "fp": fp, "tn": tn, "fn": fn}


def best_f1_threshold(y, p):
    thr = sorted(set(round(pi, 3) for pi in p))
    best_t, best_f1 = 0.5, -1.0
    for t in thr:
        f1 = prf(y, p, t)["f1"]
        if f1 > best_f1:
            best_f1, best_t = f1, t
    return best_t


def calibration(y, p, deciles=10):
    """Mean predicted vs actual default rate per predicted-probability decile."""
    order = sorted(range(len(p)), key=lambda i: p[i])
    n = len(order)
    out = []
    for d in range(deciles):
        idx = order[d * n // deciles:(d + 1) * n // deciles]
        if not idx:
            continue
        mp = sum(p[i] for i in idx) / len(idx)
        ma = sum(y[i] for i in idx) / len(idx)
        out.append({"decile": d + 1, "n": len(idx), "mean_pred": mp, "actual": ma})
    return out


def report(y, p, threshold=None):
    auc = auc_roc(y, p)
    ks, ks_at = ks_stat(y, p)
    t = threshold if threshold is not None else best_f1_threshold(y, p)
    m = prf(y, p, t)
    return {
        "n": len(y), "positives": sum(y), "base_rate": sum(y) / max(len(y), 1),
        "auc_roc": auc, "gini": 2 * auc - 1, "ks": ks, "ks_threshold": ks_at,
        "op_threshold": t, **m,
    }


def print_report(name, rep, calib=None):
    print(f"\n=== {name} ===")
    print(f"  n={rep['n']}  positives={rep['positives']}  base default rate={rep['base_rate']:.2%}")
    print(f"  AUC-ROC : {rep['auc_roc']:.4f}   Gini: {rep['gini']:.4f}   KS: {rep['ks']:.4f} (@p={rep['ks_threshold']:.2f})")
    print(f"  Operating threshold: {rep['op_threshold']:.3f}")
    print(f"  Precision: {rep['precision']:.3f}  Recall: {rep['recall']:.3f}  F1: {rep['f1']:.3f}")
    print(f"  Confusion  TP={rep['tp']} FP={rep['fp']} TN={rep['tn']} FN={rep['fn']}")
    print(f"  (accuracy {rep['accuracy']:.3f} — shown for reference only; not a valid headline on imbalanced data)")
    if calib:
        print("  Calibration (decile: mean_pred vs actual):")
        for c in calib:
            print(f"    D{c['decile']:2d}  n={c['n']:4d}  pred={c['mean_pred']:.3f}  actual={c['actual']:.3f}")
