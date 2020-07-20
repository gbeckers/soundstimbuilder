import numpy as np
import time

def duration_string(seconds):
    """Converts number of seconds to human readable time string.

    """

    intervals = ((60.*60.*24.*7., 'weeks'),
                 (60.*60.*24., 'days'),
                 (60.*60., 'hours'),
                 (60., 'minutes'),
                 (1., 'seconds'),
                 (0.001, 'milliseconds'))
    for interval in intervals:
        if seconds >= interval[0]:
            amount = seconds/interval[0]
            unit = interval[1]
            if amount < 2.0:
                unit = unit[:-1] # remove 's'
            return f'{amount:.2f} {unit}'
    return f'{seconds/intervals[-1][0]:.3f} {intervals[-1][1][:-1]}'


def timeparams(nframes=None, fs=None, duration=None):
    # we need enough info from duration, fs and ntimesamples
    havents = not (nframes is None)
    havefs = not (fs is None)
    havedur = not (duration is None)
    timeparams = np.array([havents, havefs, havedur])
    if not (timeparams.sum() >= 2):
        raise ValueError(
            "at least 2 values are required for duration, ntimesamples, and fs")
    if havents:
        nframes = int(round(nframes))
    if havefs:
        fs = float(fs)
    if havedur:
        duration = float(duration)
    if timeparams.sum() == 2:
        #  now calculate what's missing
        if havents:
            if havefs:
                duration = nframes / fs
            else:  # have duration

                fs = nframes / duration
        else:  # have duration and have fs
            nframes = fs * duration
            if divmod(nframes, 1.0)[1] != 0.0:
                raise ValueError(
                    "duration and fs do not correspond to integer ntimesamples")
            else:
                nframes = int(nframes)
    return (nframes, fs, duration)

def datetimestring():
    return time.strftime('%Y%m%d%H%M%S')
