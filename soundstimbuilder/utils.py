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

eps = np.power(2.0, -52.0)

def round_nextradix2(number):
    return int(pow(2, np.ceil(np.log2(number))))


def round_nearestradix2(number):
    return int(pow(2, np.round(np.log2(number))))


def round_nearestodd(number):
    n = int(np.round(number))  # nearest int
    if n % 2 == 0:  # n is even
        if n - number < 0:
            n += 1
        else:
            n -= 1
    return n


def round_nearesteven(number):
    n = int(np.round(number))  # nearest int
    if n % 2 == 1:  # n is odd
        if n - number < 0:
            n += 1
        else:
            n -= 1
    return n


def iseven(number):
    return (number % 2.0) == 0.0


def isodd(number):
    return (number % 2.0) == 1.0


def alleven(numbers):
    return np.all((np.asarray(numbers) % 2.0) == 0.0)


def allodd(numbers):
    return np.all((np.asarray(numbers) % 2.0) == 1.0)

def isradix2(number):
    if not (number & (number - 1)):
        return True
    else:
        return False

def allradix2(numbers):
    numbers = np.asarray(numbers)
    if not (numbers & (numbers- 1)).any():
        return True
    else:
        return False