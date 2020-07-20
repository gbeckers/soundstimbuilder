import numpy as np
import scipy.io.wavfile
import scipy.signal
import matplotlib.pyplot as plt
import darr

from pathlib import Path

from .utils import duration_string

__all__ = ['concatenate', 'wavread', 'Snd']


class BaseSnd():
    """A base sound object without frames but with some useful
    general attributes and methods.

    To be used as a parent class for sound objects with frames

    Parameters
    ----------
    nframes: int
    nchannels: int
    fs: float
      Sampling frequency in Hz.
    dtype: numpy dtype

    """

    _classid = "BaseSnd"

    def __init__(self, nframes, nchannels, fs):

        self.nframes = nframes
        self.nchannels = nchannels
        self.fs = fs
        self.dt = 1 / self.fs
        self.duration = self.nframes / self.fs
        self.frames = None # this should be set by the child class, an object with frames


    def samplingtimes(self):
        """
        Returns the times of *sample centers*, relative to origin time.

        To get the sampling times relative to starttime add the starttime and
        origintime to the result of this method (e.g. signal.samplingtimes +
        signal.starttime + signal.origintime). But if you do this, note that
        the samplingtimes property is a float array of 64-bit precision. If
        starttime is a large number (e.g. Epoch) you may want to upcast to
        higher-precision floats first (96- or 128-bit float) if possible on
        your platform, at least if you want to retain precision.

        """
        return ((np.arange(self.nframes, dtype=np.float64) + 0.5)
                / self.fs)

    def samplingboundarytimes(self):
        """
        Returns the times of *sample boundaries*, relative to origin time.

        Note that the size of the return array is ntimesamples + 1

        """
        return (np.arange(self.nframes + 1, dtype=np.float64) / self.fs)

    def time_to_index(self, time, nearest_boundary=False):
        """
        Converts a time, or array of times, to their corresponding sample
        indices.

        Note that the default is to return to which *sample center* the given
        time is closest. When nearest_boundary is True, this will be to which
        *sample start* the time is closest.

        Parameter
        ---------

        time: <float, float sequence>
        nearest_boundary: bool
            Determines whether or not the the sample index is given of which
            the *center* is closest to the parameter time. If True, this will
            be the closest sample *start*.

        Example: if the time parameter is [t0, t1, t2],

        |    s0    |    s1    |    s2    |    s3    |    s4    | ...
                     ^       ^  ^
                     t0      t1 t2

        then the result will be the sample of indices [s1, s1, s2] if
        nearest_boundary is False (default) or [s1, s2, s2] if nearest_boundary
        is True.

        Note that it is possible to get an index number of ntimesamples
        if the time is endtime.

        """
        time = np.asarray(time, dtype=np.float64)
        outsiderange = (time < 0) | (time > self.duration)
        if outsiderange.any():
            offendingtimes = time[outsiderange]
            raise ValueError(
                "%s s. are outside range of possible times (%f,%f)" \
                % (offendingtimes, 0, self.duration))
        # calculate
        if nearest_boundary:
            index = np.floor((time + self.dt / 2.0) * self.fs).astype(np.int64)
        else:
            index = np.floor(time * self.fs).astype(np.int64)
        if index.size == 1:
            return index.item()
        else:
            return index

    def index_to_time(self, index):
        """
        Converts a sample index, or array of indices, to their
        corresponding times. Note that the *time of sample center*
        is given, not the time of the sample start.

        Parameter
        ---------
        index: an integer or array of integers

        Note
        ----
        Center of samples define their time of occurrence

        |    0    |    1    |    2    |    3    |    4    | ...
             ^         ^         ^         ^         ^
             t0        t1        t2        t3        t4

        """
        index = np.asarray(index, np.int64)
        if ((index < 0) | (index >= self.nframes)).any():
            raise ValueError("index (%s) cannot be smaller than zero or higher"
                             " than nframes - 1 (%d)" \
                             % (index, self.nframes - 1))
        result = ((index + 0.5) / self.fs)
        if result.size == 1:
            return result.item()
        else:
            return result

    def to_darrsnd(self, path, accessmode='r', dtype='float32', metadata=None, overwrite=False):
        ds = darr.asarray(array=self.frames, dtype=dtype, accessmode=accessmode, metadata=metadata,
                          overwrite=overwrite)
        ds.metadata['fs'] = self.fs
        return DarrSnd(path=path, accessmode=accessmode)

    def to_wav(self, filepath, dtype='float32', overwrite=False):
        #TODO warn if rounding has consequences. wav can only have int fs
        fs = int(round(self.fs))
        filepath = Path(filepath)
        if not filepath.exists() or overwrite:
            scipy.io.wavfile.write(filename=filepath, rate=fs, data=self.frames.astype(dtype))
        else:
            raise IOError(f'{filepath} exists, use `overwrite` parameter to overwrite')

    def rms(self):
        return ((self.frames - self.frames.mean(axis=0))**2.0).mean(0)**0.5

    def absmax(self):
        return np.absolute(self.frames).max(axis=0)

    def plot(self, starttime=None, endtime=None, fig=None):
        if starttime is None:
            starttime = 0.0
        if endtime is None:
            endtime = self.duration
        starti, endi = self.time_to_index((starttime,endtime))
        if fig is None:
            plt.figure(figsize=(16, 3))
        # next could be lot more efficient
        t = self.samplingtimes()[starti:endi]
        ax = []
        for channel in range(self.nchannels):
            plt.subplot(self.nchannels,1,channel+1)
            plt.plot(t, self.frames[starti:endi,channel])

    # TODO for no we only use the first channel
    # FIXME scaling is not OK yet
    def specgram(self, nperseg=512, noverlap=496, nfft=None, detrend='constant',
                 return_onesided=True, scaling='density',  mode='psd', db=True, imshow=True, freqrange=(0,8000.),
                 dynrange=50, fig=None):
        if fig is None:
            plt.figure(figsize=(16, 3))
        window =  scipy.signal.windows.gaussian(nperseg, int(nperseg/8), sym=True)
        powers = []
        for channel in range(self.nchannels):
            plt.subplot(self.nchannels,1,channel+1)
            f, t, p = scipy.signal.spectrogram(self.frames[:,channel], fs=self.fs, window=window, nperseg=nperseg, noverlap=noverlap,
                                               nfft=nfft, detrend=detrend, return_onesided=return_onesided,
                                               scaling=scaling, mode=mode)
            if db:
                p = 10 * np.log10(p + np.finfo(p.dtype).resolution)
                m = p.max()
                clim = (m-dynrange,m)
            else:
                clim = None
            if imshow:
                plt.imshow(p,extent=(t[0], t[-1], f[0], f[-1]), aspect='auto',origin='lower',clim=clim)
                plt.ylim(freqrange)
            powers.append(p)
        return f, t, powers

class Snd(BaseSnd):

    _classid = 'Snd'

    def __init__(self, frames, fs, dtype=None):
        frames = np.asarray(frames, dtype=dtype)
        if frames.ndim == 1:
            frames = frames.reshape((-1,1))
        elif frames.ndim > 2:
            raise TypeError("'frames' cannot have more than 2 dimensions")
        self.frames = frames
        nframes = frames.shape[0]
        nchannels = frames.shape[1]
        BaseSnd.__init__(self=self,nframes=nframes, nchannels=nchannels, fs=fs)
        self.frames = frames


    def __str__(self):
        totdur = duration_string(self.nframes * self.dt)
        return f'{self._classid} <{totdur}, {self.fs} Hz, {self.nframes} frames, {self.frames.dtype}>'

    __repr__ = __str__

    def toaudiofloat(self, dtype='float64'):
        """Converts the sound to an audio compatible floating point format.

        If the frames are in a (unsigned) integer format, values will be scaled
        to fit between -1.0 and 1.0. If the frames are already in float format,
        they will be scaled if there are values smaller than -1.0 or larger than 1.0.

        Returns
        -------
        A new Snd object with floating dtype.

        """
        if np.issubdtype(self.frames.dtype, np.integer):
            minval = np.iinfo(self.frames.dtype).min
            maxval = np.iinfo(self.frames.dtype).max
            valrange = maxval - minval
            if minval == 0: # unsigned int
                frames = (self.frames.astype(dtype) / (2 * maxval)) - 0.5
            else: # signed int
                frames = self.frames.astype(dtype) / -minval
        else:
            frames = self.frames.astype(dtype)
            absmax = max(abs(frames.min()),frames.max())
            if absmax > 1.0:
                frames /= absmax
        return Snd(frames=frames, fs=self.fs)

    def normalize(self, peakamp=1.0, rmsamp=None):
        peakamp, rmsamp = _check_amp(peakamp=peakamp,
                                     rmsamp=rmsamp)
        if rmsamp is None:
            frames = self.frames / (np.max(np.abs(self.frames)) / peakamp)
        else:
            rms = (self.frames ** 2.0).mean() ** 0.5
            frames = self.frames * rmsamp / rms
        return Snd(frames=frames, fs=self.fs)

    def ramp(self, duration, window=np.hanning):
        frames = np.array(self.frames).copy()
        ntimebins = int(np.round(duration * self.fs))
        w = window(ntimebins * 2)
        w1 = w[-ntimebins:].reshape(-1,1)
        w2 = w[:ntimebins].reshape(-1,1)
        frames[:ntimebins] *= w2
        frames[-ntimebins:] *= w1
        return Snd(frames=frames, fs=self.fs)

    def scale(self, factor):
        frames = self.frames * factor
        return Snd(frames=frames, fs=self.fs)

class DarrSnd(BaseSnd):

    """A simple sound object that is disk based (darr array) with some useful attributes and methods.

        Parameters
        ----------
        path : str or pathlib.Path
          File system path to which the sound will be saved. Note that this will
          be a directory containing multiple files.
        accessmode : {`r`, `r+`}, optional
          File access mode of the sound that is returned. `r` means
          read-only, `r+` means read-write. In the latter case, data can be
          changed. Default `r`.

        """

    _classid = "DarrSnd"

    def __init__(self, path, accessmode='r'):
        frames = darr.Array(path=path, accessmode=accessmode)
        self.metadata = frames.metadata
        fs = frames.metadata['fs']
        BaseSnd.__init__(self=self, nframes=frames.shape[0], nchannels=frames.shape[1], fs=fs)
        self.frames = frames


def wavread(filepath, tofloat=False):
    """Reads a wave file.

    Note we use scipy although pysoundfile would generally be better, as it supports 24-bit files. But that package
    currently has installation problems, and we are not using 24 bit anyway.

    Params
    -----
    filepath
    tofloat : bool
      If wav file in in PCM integer format (16 bits only), data will be scaled down to floating point between -1.0 and
      1.0

    """
    fs, data = scipy.io.wavfile.read(filename=filepath)
    snd = Snd(frames=data, fs=fs)
    if tofloat:
        snd = snd.toaudiofloat()
    return snd


def _check_amp(peakamp, rmsamp):
    if (peakamp is None) and (rmsamp is None):
        peakamp = 0.99
    if (not peakamp is None) and (not rmsamp is None):
        raise ValueError(
            "you can only set either peakamp or rmsamp, but not both")
    if not peakamp is None:
        peakamp = float(peakamp)
    if not rmsamp is None:
        rmsamp = float(rmsamp)
    return peakamp, rmsamp


def concatenate(snds):
    if not all(snd.fs==snds[0].fs for snd in snds):
        raise TypeError("not all snds have the same fs")
    if not all(snd.nchannels==snds[0].nchannels for snd in snds):
        raise TypeError("not all snds have the same nchannels")
    nframes = sum(snd.nframes for snd in snds)
    nchannels = snds[0].nchannels
    frames = np.empty((nframes, nchannels), dtype=snds[0].frames.dtype)
    startframe = 0
    for snd in snds:
        endframe = startframe + snd.nframes
        frames[startframe:endframe] = snd.frames
        startframe = endframe
    return Snd(frames=frames, fs=snds[0].fs)