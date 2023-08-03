from scipy.optimize import minimize_scalar
from math import erfc, log, pi, isinf, log1p, exp
from scipy.stats import norm
from ossapi.models import Score
from ossapi.mod import Mod


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


def log_sum(first_log, second_log):
    max_val = max(first_log, second_log)
    min_val = min(first_log, second_log)

    if isinf(max_val):
        return max_val

    return max_val + log(1 + exp(min_val - max_val))


def unstable_rate(
        j: Score.statistics,
        beatmap: Score.beatmap,
        mods: Mod
) -> float:
    tail_multiplier = 1.75

    note_head_portion = float(beatmap.count_circles + beatmap.count_sliders) / (
                beatmap.count_circles + beatmap.count_sliders + beatmap.count_sliders)
    tail_portion = float(beatmap.count_sliders) / (
                beatmap.count_circles + beatmap.count_sliders + beatmap.count_sliders)

    n_judgements = j.count_geki + j.count_300 + j.count_katu + j.count_100 + j.count_50 + j.count_miss

    if n_judgements == 0:
        return float('inf')

    od = beatmap.accuracy
    note_count = beatmap.count_circles
    ln_count = beatmap.count_sliders

    if Mod.HR in mods:
        window_mul = 1 / 1.4
    elif Mod.EZ in mods:
        window_mul = 1.4
    else:
        window_mul = 1

    # We need the size of every hit window in order to calculate deviation accurately.
    h_max = int(16 * window_mul)
    h_300 = int((64 - 3 * od) * window_mul)
    h_200 = int((97 - 3 * od) * window_mul)
    h_100 = int((127 - 3 * od) * window_mul)
    h_50 = int((151 - 3 * od) * window_mul)
    root2 = 2 ** 0.5

    # Returns the likelihood of any deviation resulting in the play
    def likelihood_gradient(d: float):
        if d <= 0:
            return float('inf')

        d_note = d / (note_head_portion + tail_portion * tail_multiplier ** 2) ** 0.5
        d_tail = d_note * tail_multiplier

        p_max_note = log_diff(0, log_erfc(h_max / (d_note * root2)))
        p_300_note = log_diff(log_erfc(h_max / (d_note * root2)), log_erfc(h_300 / (d_note * root2)))
        p_200_note = log_diff(log_erfc(h_300 / (d_note * root2)), log_erfc(h_200 / (d_note * root2)))
        p_100_note = log_diff(log_erfc(h_200 / (d_note * root2)), log_erfc(h_100 / (d_note * root2)))
        p_50_note = log_diff(log_erfc(h_100 / (d_note * root2)), log_erfc(h_50 / (d_note * root2)))

        def ln_prob(window: float, head_deviation: float, tail_deviation: float):
            p_head = log_erfc(window / (head_deviation * root2))

            beta = window / head_deviation
            z = norm.cdf(beta) - 0.5
            expected_value = head_deviation * (norm.pdf(0) - norm.pdf(beta)) / z

            p_tail = log_erfc((2 * window - expected_value) / (tail_deviation * root2))

            return log_diff(log_sum(p_head, p_tail), p_head + p_tail)

        p_max_ln = log_diff(0, ln_prob(h_max * 1.2, d_note, d_tail))
        p_300_ln = log_diff(ln_prob(h_max * 1.2, d_note, d_tail), ln_prob(h_300 * 1.1, d_note, d_tail))
        p_200_ln = log_diff(ln_prob(h_300 * 1.1, d_note, d_tail), ln_prob(h_200, d_note, d_tail))
        p_100_ln = log_diff(ln_prob(h_200, d_note, d_tail), ln_prob(h_100, d_note, d_tail))
        p_50_ln = log_diff(ln_prob(h_100, d_note, d_tail), ln_prob(h_50, d_note, d_tail))

        if min(note_count, ln_count > 0):
            p_max = log_sum(p_max_note + log(note_count), p_max_ln + log(ln_count)) - log(note_count + ln_count)
            p_300 = log_sum(p_300_note + log(note_count), p_300_ln + log(ln_count)) - log(note_count + ln_count)
            p_200 = log_sum(p_200_note + log(note_count), p_200_ln + log(ln_count)) - log(note_count + ln_count)
            p_100 = log_sum(p_100_note + log(note_count), p_100_ln + log(ln_count)) - log(note_count + ln_count)
            p_50 = log_sum(p_50_note + log(note_count), p_50_ln + log(ln_count)) - log(note_count + ln_count)
        elif note_count > 0:
            p_max = p_max_note
            p_300 = p_300_note
            p_200 = p_200_note
            p_100 = p_100_note
            p_50 = p_50_note
        else:
            p_max = p_max_ln
            p_300 = p_300_ln
            p_200 = p_200_ln
            p_100 = p_100_ln
            p_50 = p_50_ln

        gradient = (
                (p_max * j.count_geki +
                 p_300 * (j.count_300 + 1) +
                 p_200 * j.count_katu +
                 p_100 * j.count_100 +
                 p_50 * j.count_50) / n_judgements
        )

        return -gradient

    results = minimize_scalar(likelihood_gradient)

    return results.x * 10
