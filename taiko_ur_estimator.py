from scipy.optimize import minimize_scalar
from math import erfc, log, pi, isinf, log1p, exp
from ossapi.models import Score


def log_erfc(x):
    if x < 5:
        return log(erfc(x))
    else:
        return -x ** 2 - log(x * pi ** 0.5)


def log_diff(first_log, second_log):
    max_val = max(first_log, second_log)

    if isinf(max_val):
        return max_val

    return first_log + log1p(-exp(-(first_log - second_log)))


def unstable_rate(
        j: Score.statistics,
        beatmap: Score.beatmap,
        mods: str
) -> float:
    n_judgements = j.count_300 + j.count_100

    if n_judgements == 0:
        return float('inf')

    od = beatmap.accuracy

    if "HR" in mods:
        od = min(od * 1.4, 10)
    elif "EZ" in mods:
        od = od * 0.5

    multiplier = 1

    if "DT" in mods:
        multiplier = 2 / 3.0
    elif "HT" in mods:
        multiplier = 4 / 3.0

    # We need the size of every hit window in order to calculate deviation accurately.
    h_300 = (50 - 3 * od) * multiplier

    if od < 5:
        h_100 = (120 - 6 * od) * multiplier
    else:
        h_100 = (80 - 8 * (od - 5)) * multiplier

    root2 = 2 ** 0.5

    # Returns the likelihood of any deviation resulting in the play
    def likelihood_gradient(d: float):
        if d <= 0:
            return float('inf')

        p_300 = log_diff(0, log_erfc(h_300 / (d * root2)))
        p_100 = log_diff(log_erfc(h_300 / (d * root2)), log_erfc(h_100 / (d * root2)))

        gradient = exp(
            (p_300 * j.count_300 +
             p_100 * (j.count_100 + 0.5)) / n_judgements
        )

        return -gradient

    results = minimize_scalar(likelihood_gradient)

    return results.x * 10
