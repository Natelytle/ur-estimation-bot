from scipy.special import erfinv
from ossapi.models import Score


def unstable_rate(
        j: Score.statistics,
        beatmap: Score.beatmap,
        mods: str
) -> float:
    n_judgements = j.count_300 + j.count_100 + j.count_50

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
    h_300 = (80 - 6 * od) * multiplier
    h_50 = (200 - 10 * od) * multiplier

    count_300_circles = beatmap.count_circles - j.count_100 - j.count_50 - j.count_miss
    great_prob_circles = max(0, count_300_circles / (beatmap.count_circles + 1.0))

    if count_300_circles < 0:
        non_circle_misses = -count_300_circles
        great_prob_sliders = max(0, (beatmap.count_sliders - non_circle_misses) / (beatmap.count_sliders + 1.0))
    else:
        great_prob_sliders = beatmap.count_sliders / (beatmap.count_sliders + 1.0)

    if great_prob_circles + great_prob_sliders == 0:
        return float('inf')

    root2 = 2**0.5

    deviation_on_circles = h_300 / (root2 * erfinv(great_prob_circles))
    deviation_on_sliders = h_50 / (root2 * erfinv(great_prob_sliders))

    return min(deviation_on_circles, deviation_on_sliders) * 10
