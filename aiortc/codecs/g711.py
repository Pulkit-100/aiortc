import audioop
import fractions
from typing import List, Optional, Tuple

from av import AudioFrame

from ..jitterbuffer import JitterFrame

SAMPLE_RATE = 8000
SAMPLE_WIDTH = 2
SAMPLES_PER_FRAME = 160
TIME_BASE = fractions.Fraction(1, 8000)


class PcmDecoder:
    def decode(self, encoded_frame: JitterFrame) -> List[AudioFrame]:
        frame = AudioFrame(format="s16", layout="mono", samples=SAMPLES_PER_FRAME)
        frame.planes[0].update(self._convert(encoded_frame.data, SAMPLE_WIDTH))
        frame.pts = encoded_frame.timestamp
        frame.sample_rate = SAMPLE_RATE
        frame.time_base = TIME_BASE
        return [frame]


class PcmEncoder:
    def __init__(self) -> None:
        self.rate_state = None  # type: Optional[Tuple]

    def encode(
        self, frame: AudioFrame, force_keyframe: bool = False
    ) -> Tuple[List[bytes], int]:
        assert frame.format.name == "s16"
        assert frame.layout.name in ["mono", "stereo"]

        channels = len(frame.layout.channels)
        data = bytes(frame.planes[0])
        timestamp = frame.pts

        # resample at 8 kHz
        if frame.sample_rate != SAMPLE_RATE:
            data, self.rate_state = audioop.ratecv(
                data,
                SAMPLE_WIDTH,
                channels,
                frame.sample_rate,
                SAMPLE_RATE,
                self.rate_state,
            )
            timestamp = (timestamp * SAMPLE_RATE) // frame.sample_rate

        # convert to mono
        if channels == 2:
            data = audioop.tomono(data, SAMPLE_WIDTH, 1, 1)

        data = self._convert(data, SAMPLE_WIDTH)
        return [data], timestamp


class PcmaDecoder(PcmDecoder):
    _convert = staticmethod(audioop.alaw2lin)


class PcmaEncoder(PcmEncoder):
    _convert = staticmethod(audioop.lin2alaw)


class PcmuDecoder(PcmDecoder):
    _convert = staticmethod(audioop.ulaw2lin)


class PcmuEncoder(PcmEncoder):
    _convert = staticmethod(audioop.lin2ulaw)
