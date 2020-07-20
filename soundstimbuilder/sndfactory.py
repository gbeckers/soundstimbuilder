"""All functions that generate sounds should go here.

"""

import numpy as np

from .snd import Snd, concatenate
from .utils import timeparams

__all__ = ['calibmark_3sweeps', 'chirp', 'harmonic', 'modfreq', 'silence', 'whitenoise']

def modfreq(freqpattern, fs, dtype='float64', peakamp=None, rmsamp=None):
    """Create a sound with provided frequency pattern.

    :param freqpattern:
    :param fs:
    :param dtype:
    :param peakamp:
    :param rmsamp:
    :return:
    """
    freqpattern = np.array(freqpattern, copy=False)
    assert freqpattern.ndim == 1, \
        "frequency pattern should be a 1-dimensional array"
    assert (freqpattern < (fs / 2.0)).all(), \
        "all frequencies should be smaller than fs / 2.0"
    fs = float(fs)
    ar = freqpattern.astype(dtype) / float(fs)
    ar = ar.cumsum()
    ar = np.unwrap(ar, discont=1)
    ar = np.sin(2 * np.pi * ar)
    return Snd(frames=ar, fs=fs).normalize(peakamp=peakamp, rmsamp=rmsamp)


def chirp(duration=None, nframes=None, fs=44100., startfreq=0., endfreq=10000., dtype='float64',
          peakamp=None, rmsamp=None):
    #print(duration,nframes, fs)
    nframes, fs, duration = timeparams(duration=duration, nframes=nframes, fs=fs)
    t = np.linspace(startfreq, endfreq, num=nframes)
    return modfreq(freqpattern=t, fs=fs, dtype=dtype, peakamp=peakamp,
                   rmsamp=rmsamp)


def silence(duration=None, nframes=None, fs=44100., nchannels=1, dtype='float64'):
    nframes, fs, duration = timeparams(duration=duration, nframes=nframes, fs=fs)
    frames = np.zeros((nframes, nchannels), dtype=dtype)
    return Snd(frames=frames, fs=fs)


def harmonic(duration=None, nframes=None, fs=44100., fundfreq=500.,
             nharmonics=1, dtype='float64',
             hweights=None, hphases=None, peakamp=None, rmsamp=None):
    """

    """
    nframes, fs, duration = timeparams(nframes=nframes, fs=fs, duration=duration)
    fundfreq = float(fundfreq)
    nharmonics = int(nharmonics)
    if hweights is None:
        hweights = np.ones(nharmonics, dtype=dtype)
    else:
        hweights = np.array(hweights, dtype=dtype)
    if hphases is None:
        hphases = (np.random.random(nharmonics) * np.pi * 2.0).astype(dtype)
    else:
        hphases = np.array(hphases, dtype=dtype)

    hsamples = np.empty((nframes, nharmonics), dtype=dtype)
    hsamples[:] = np.linspace(0., duration, nframes)[:, np.newaxis]  # time
    freqs = np.arange(fundfreq, fundfreq * (nharmonics + 1), fundfreq,
                      dtype=dtype)
    frames = (hweights[np.newaxis, :] * np.sin(
        2. * np.pi * hsamples * freqs + hphases[np.newaxis, :])).sum(1)
    snd = Snd(frames=frames, fs=fs)
    return snd.normalize(peakamp=peakamp, rmsamp=rmsamp)


def calibmark_3sweeps(fs=44100., startfreq=500., endfreq=1000., chirpduration=0.2, silenceduration=0.1,
                      rampduration=1e-3, dtype='float64'):
    c = chirp(duration=chirpduration, fs=fs, startfreq=startfreq, endfreq=endfreq, dtype=dtype)
    c = c.ramp(duration=rampduration)
    s = silence(duration=silenceduration, fs=fs, dtype=dtype)
    return concatenate([c, s, c, s, s, s, c])

def whitenoise(duration=None, nframes=None, fs=44100., nchannels=1, peakamp=None, rmsamp=None,
               dtype='float64'):
    nframes, fs, duration = timeparams(nframes=nframes, fs=fs, duration=duration)
    frames = np.random.random((nframes,nchannels)).astype(dtype)
    frames -= 0.5
    return Snd(frames=frames, fs=fs).normalize(peakamp=peakamp, rmsamp=rmsamp)

