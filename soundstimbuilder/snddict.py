import os
import warnings
from darr.datadir import DataDir, create_datadir
from .snd import wavread, Snd, DarrSnd
from .utils import datetimestring

__all__ = ['create_snddict', 'SndDict']

class SndDict:
    """Disk-based dictionary of sounds.

    Essentially all wav files in a directory. They need to have the lowercase '.wav'
    extension and we work with float32 files only. The keys are simply the filenames
    without the .wav extension, the items are Snd objects. The directory contains a
    json file that provides some info on the sounds for efficiency.

    """
    _classid = 'SndDict'
    _infofile = 'snddict.json'

    def __init__(self, path):
        self.datadir = DataDir(path=path)
        if not (self.datadir.path / self._infofile).exists():
            self._updateinfofile()

    def __getitem__(self, item):
        return wavread(self.datadir.path / f'{item}.wav')

    def __str__(self):
        return f'{self._classid}: {self.datadir.path.name} {self.keys()}'

    __repr__ = __str__

    def _updateinfofile(self):
        keys = sorted([file[:-4] for file in os.listdir(self.datadir.path) if file.endswith(".wav")])
        d = {}
        for key in keys:
            snd = self[key]
            d[key] = {}
            d[key]['fs']= snd.fs
            d[key]['nchannels'] = snd.nchannels
            d[key]['nframes'] = snd.nframes
            d[key]['duration'] = snd.duration
        self.datadir.write_jsondict(self._infofile, d, overwrite=True)

    def info(self):
        return self.datadir.read_jsondict(self._infofile)

    def add(self, key, snd, overwrite=False):
        if not isinstance(snd, (Snd, DarrSnd)):
            raise TypeError(f'cannot add object of type {type(snd)} to {self._classid}')
        if key in self.keys() and not overwrite:
            raise ValueError(f'SndDict already contains a Snd wih key {key}, use the pop method to remove first')
        snd.to_wav(self.datadir.path / f'{key}.wav', dtype='float32', overwrite=overwrite)
        d = self.datadir.read_jsondict(self._infofile)
        d[key] = {}
        d[key]['fs'] = snd.fs
        d[key]['nchannels'] = snd.nchannels
        d[key]['nframes'] = snd.nframes
        d[key]['duration'] = snd.duration
        self.datadir.write_jsondict(self._infofile, d, overwrite=True)

    def keys(self):
        return sorted(self.info().keys())

    def items(self):
        for key in self.keys():
            yield key, self[key]

    def pop(self, key):
        if not key in self.keys():
            raise ValueError(f"Snd {key} does not exist in SndDict")
        (self.datadir.path / f'{key}.wav').unlink()
        d = self.datadir.read_jsondict(self._infofile)
        d.pop(key)
        self.datadir.write_jsondict(self._infofile, d, overwrite=True)

    def allsame(self):
        """Tests if attributes of all sounds are the same (fs, nchannels, nframes, duration).

        """
        d = {'fs': [],
             'nchannels': [],
             'nframes': [],
             'duration': []}

        for sndkey, values in self.info().items():
            d['fs'].append(values['fs'])
            d['nchannels'].append(values['nchannels'])
            d['nframes'].append(values['nframes'])
            d['duration'].append(values['duration'])
        s = {}
        for key, values in d.items():
            s[key] = all(val == values[0] for val in values)
        return s

    def nframes(self):
        return {key: snd.nframes for key,snd in self.items()}

    def read(self):
        """reads every in memory and returns a dictionary with Snd objects"""
        return {key: snd for (key, snd) in self.items()}




def create_snddict(path, d, overwrite=False, datetime=None, warnexistingfiles=True):
    if datetime is None:
        path = str(path) + '_' + datetimestring()
    else:
        path = str(path) + '_' + datetime
    bd = create_datadir(path=path, overwrite=overwrite)
    if warnexistingfiles:
        for path in bd.path.iterdir():
            warnings.warn(f'"{bd.path}" already contains "{path.parts[-1]}"')
    for key, snd in d.items():
        snd.to_wav(bd.path / f'{key}.wav', dtype='float32', overwrite=overwrite)
    return SndDict(bd.path)