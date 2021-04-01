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

def recode_keys(origkeys):
    import string, itertools
    origkeys = sorted(set(origkeys))
    tokens = string.ascii_lowercase
    ntokens = len(tokens)
    newkeylen = 1
    while (ntokens**newkeylen) / len(origkeys) < 1:
        newkeylen += 1
    keymapping = {}
    for origkey, s in zip(origkeys, itertools.permutations(string.ascii_lowercase, newkeylen)):
        keymapping[origkey] = ''.join(s)
    return keymapping


def mel_to_hz(a):
    return 700.*(np.power(10,a/2595.)-1.0)

def A_weighting(f):
    f = np.float64(f)
    r_a = (12200**2 * f**4) / ((f**2 + 20.6**2)*((f**2 + 107.7**2)*(f**2 + 737.9**2))**0.5*(f**2 + 12200**2))
    return 2.0 + 20*np.log10(r_a)