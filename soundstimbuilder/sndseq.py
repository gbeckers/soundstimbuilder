import numpy as np
import pandas as pd
import time
from darr.basedatadir import BaseDataDir
from .snd import Snd, wavread
from .snddict import SndDict
from .utils import duration_string, datetimestring
from .praattextgrids import TextGrid, Tier, Interval
from .sndfactory import calibmark_3sweeps

__all__ = ['SndSeq', 'SndSeqTable', 'create_sndseq']

class SndSeq(BaseDataDir):

    _classid = 'SndSeq'
    _seqfile = 'sndseq.csv'
    _infofile = 'sndseq.json'


    def __init__(self, path, tablekey=None):
        BaseDataDir.__init__(self=self, path=path)
        if tablekey is not None:
            self._seqfile = f'{self._seqfile.rsplit( ".", 1 )[0]}_{tablekey}.csv'
            self._infofile = f'{self._infofile.rsplit(".", 1)[0]}_{tablekey}.json'
        if not (self.path /self._seqfile).exists():
            raise IOError(f"cannot find table file '{self._seqfile}'")
        if not (self.path / self._infofile).exists():
            raise IOError(f"cannot find table file '{self._infofile}'")
        d = self._read_jsondict(self._infofile)
        self.fs = d['fs']
        self.nframes = d['nframes']
        self.duration = self.nframes / self.fs
        self.nsnds = d['nsnds']
        self.tablekey = tablekey


    def __str__(self):
        return f'{self._classid}: {self.path.name} <{self.nsnds} snds, {duration_string(self.duration)} >'

    __repr__ = __str__

    def seqtable(self):
        dtypes = {'snd': 'str',
                  'startframe': 'int64',
                  'endframe': 'int64',
                  'starttime': 'float64',
                  'endtime': 'float64'}
        return SndSeqTable(pd.read_csv(self.path / self._seqfile).astype(dtypes))


    def add_calibmarks_3sweeps(self, startfreq=500., endfreq=1000.,
                       chirpduration=0.2, rampduration=1e-3,
                       silentinterval=30., rms=0.2, overwrite=False):
        c = calibmark_3sweeps(startfreq=startfreq, endfreq=endfreq,
                              chirpduration=chirpduration, silenceduration=0.1,
                              rampduration=rampduration, fs=self.fs,
                              rmsamp=rms)
        snddict = SndDict(self.path)
        snddict.add('calibmark', c, overwrite=overwrite)
        seqtable = self.seqtable()
        c1 = pd.DataFrame({'startframe':[0], 'snd': ['calibmark'], 'endframe': [c.nframes]})
        nframes_silence = int(round(silentinterval * self.fs))
        seqtable['startframe'] += c.nframes + nframes_silence
        seqtable['endframe'] += c.nframes + nframes_silence
        startframe = int(seqtable['endframe'].iloc[-1]) + nframes_silence
        endframe = startframe + c.nframes
        c2 = pd.DataFrame({'startframe': [startframe], 'snd': ['calibmark'], 'endframe': [endframe]})
        seqtable = pd.concat([c1, seqtable, c2])
        seqtable['starttime'] = seqtable['startframe'] / float(self.fs)
        seqtable['endtime'] = seqtable['endframe'] / float(self.fs)
        snddict._write_jsondict(filename=self._seqfile, d={'fs': self.fs, 'nframes': endframe, 'nsnds': len(seqtable)},
                                overwrite=True)
        seqtablepath = snddict.path / self._seqfile
        time.sleep(2.) # needed for windows
        seqtablepath.unlink()
        cols = ['snd', 'startframe', 'endframe', 'starttime', 'endtime']
        additionalcols = [col for col in list(seqtable.columns) if col not in cols]
        seqtable.to_csv(seqtablepath, index=False, columns=cols + additionalcols)

    def timetransform_fromrecording(self, snd, lookduration=None):
        """Find a linear function that transforms the timing of sounds in the sequence
        to timing of the sounds in a recording of the sequence.

        We assume that there is an offset (i.e. sequence starts somewhere in the
        recording) and that there may be small differences between the provided sampling
        rates, and the actual ones in playback and recording devices. This method uses
        crosscorrelation and finds the first and the last sounds in the recording.

        """
        if not self.fs == snd.fs:
            raise ValueError("snd does not have same fs as sndseq")
        origtable = self.seqtable()
        s1name = origtable.iloc[0]['snd']
        s2name = origtable.iloc[-1]['snd']
        s1 = wavread(self.path / f'{s1name}.wav')
        s2 = wavread(self.path / f'{s2name}.wav')
        if lookduration is None:
            lookduration = 0.2 * self.duration
        looknframes = int(round(lookduration * snd.fs))
        for nframes in (s1.nframes, s2.nframes):
            if not looknframes >= nframes:
                raise ValueError("lookduration should be longer than duration target sound")
        cc = np.correlate(snd.frames[:looknframes, 0], s1.frames[:, 0], mode='valid')
        i1 = np.absolute(cc.argmax())
        t1 = i1 / float(snd.fs)
        # calibmark at end
        cc = np.correlate(snd.frames[-looknframes:, 0], s2.frames[:, 0], mode='valid')
        i2 = (np.absolute(cc.argmax()) + snd.nframes - looknframes)
        t2 = i2 / float(snd.fs)
        ot1 = origtable.iloc[0]['starttime']
        ot2 = origtable.iloc[-1]['starttime']
        slope = (t2 - t1) / (ot2 - ot1)
        offset = t1 - slope * ot1
        return slope, offset

    def seqtable_fromrecording(self, snd, lookduration=None):
        slope, offset = self.timetransform_fromrecording(snd=snd, lookduration=lookduration)
        seqtable = self.seqtable()
        seqtable['starttime'] = slope * seqtable['starttime'] + offset
        seqtable['endtime'] = slope * seqtable['endtime'] + offset
        seqtable['startframe'] = np.round(seqtable['starttime'] * self.fs).astype('int64')
        seqtable['endframe'] = (np.round(seqtable['endtime'] * self.fs)).astype('int64')
        return seqtable


    def to_snd(self, dtype='float32'):
        snddict = SndDict(self.path).read()
        seqtable = self.seqtable()
        nframes = seqtable['endframe'].iloc[-1]
        nchannels = snddict[seqtable['snd'][0]].nchannels
        fs = snddict[seqtable['snd'][0]].fs
        ar = np.zeros((nframes, nchannels), dtype=dtype)
        tier = Tier()
        for index, row in seqtable.iterrows():
            snd = snddict[row['snd']]
            startframe = row['startframe']
            endframe = row['endframe']
            ar[startframe:endframe] = snd.frames
            interval = Interval()
            interval.xmin = row['starttime']
            interval.xmax = row['endtime']
        return Snd(frames=ar, fs=fs)

    def to_textgrid(self, filepath):
        return self.seqtable().to_textgrid(filepath=filepath)


class SndSeqTable(pd.DataFrame):
    """Pandas DataFrame based table with sound sequence info.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.check_consistency()

    def to_textgrid(self, filepath):
        """Write sequence table to a Praat TextGrid file

        """
        textgrid = TextGrid()
        tier = Tier()
        lastendtime = None
        for index, row in self.iterrows():
            if (lastendtime is not None) and (lastendtime != row['starttime']):  # add a silent interval
                interval = Interval()
                interval.xmin = lastendtime
                interval.xmax = row['starttime']
                interval.text = ''
                tier.append(interval)
            interval = Interval()
            interval.xmin = row['starttime']
            interval.xmax = row['endtime']
            interval.text = row['snd']
            tier.append(interval)
            lastendtime = interval.xmax
        tier.xmin = self['starttime'].iloc[0]
        tier.xmax = self['endtime'].iloc[-1]
        textgrid['snds'] = tier
        textgrid.xmin = tier.xmin
        textgrid.xmax = tier.xmax
        textgrid.write(filename=filepath)

    def check_consistency(self):
        if not 'snd' in self.columns:
            raise KeyError(f"sequence table must contain a 'snd' column (now: {self.columns})")
        if not 'starttime' in self.columns:
            raise KeyError(f"sequence table must contain a 'starttime' column (now: {self.columns})")
        if not 'endtime' in self.columns:
            raise KeyError(f"sequence table must contain a 'endttime' column (now: {self.columns})")

def create_sndseq(snddict, seqtable, tablekey=None, overwrite=False):
    """Creates a stimulus sequence object.

    This boils down to a SndDict (i.e. wav files in a directory), with a
    table (saved in CSV format) that provides info on which sound occurs
    when in the sequence. The same sound can occur multiple times.

    The seqtable should be an object that can be converted into a Panda's
    DataFrame with at least a column named 'snd', corresponding to a key
    in snddict, and a column 'starttime', corresponding to when in the
    sequence a sound occurs. Other columns may be present as well. Note
    that the resulting start time of a sound may deviate because of
    rounding to integer sound frame timing.

    """
    if not isinstance(snddict, SndDict):
        raise TypeError(f"'snddict' is not a SndDict, but a {type(snddict)}")
    same = snddict.allsame()
    if not (same['fs'] and same['nchannels']):
        raise TypeError(f"sounds in snddict do not all have the same fs and nchannels")
    seqtable = pd.DataFrame(seqtable)
    nframes = snddict.nframes()
    startframes = []
    # looping over rows is slow but in this case we can't get around it
    endframe = 0
    startframes = []
    endframes = []
    fs = snddict.info()[seqtable['snd'][0]]['fs'] # just take fs of first sound, should all be same
    for index, row in seqtable.iterrows():
        startframe = int(round(row['starttime'] * fs))
        if not startframe >= endframe:
            raise ValueError("start time is before end time of previous sound")
        endframe = startframe + nframes[row['snd']]
        startframes.append(startframe)
        endframes.append(endframe)
    startframes = np.array(startframes, dtype='int64')
    endframes = np.array(endframes, dtype='int64')
    seqtable['startframe'] = startframes
    seqtable['endframe'] = endframes
    seqtable['starttime'] = startframes / float(fs)
    seqtable['endtime'] = endframes / float(fs)
    ds = datetimestring()
    if tablekey is None:
        tablekey = ds
    else:
        tablekey = f'{tablekey}_{ds}'
    seqpath = snddict.path / f'{SndSeq._seqfile.rsplit( ".", 1 )[0]}_{tablekey}.csv'
    infopath = f'{SndSeq._infofile.rsplit( ".", 1 )[0]}_{tablekey}.json'
    if seqpath.exists() and overwrite:
        seqpath.unlink()
    newcols = ['snd','startframe', 'endframe', 'starttime', 'endtime']
    oldcols = [col for col in list(seqtable.columns) if col not in newcols]
    seqtable.to_csv(seqpath, index=False, columns=newcols+oldcols)
    snddict._write_jsondict(filename=infopath,
                            d={'fs': fs, 'nframes': int(endframes[-1]), 'nsnds': len(seqtable)},
                            overwrite=overwrite)
    return SndSeq(snddict.path, tablekey=tablekey)





