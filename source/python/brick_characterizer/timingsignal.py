
class TimingSignal():
    def __init__(self,signal,related):
        self._signal_name = signal
        self._clock_signal = related[0]
        self._stimulus = related[1]
        self._unateness = related[2]

    def clock(self):
        return self._clock_signal

    def stimulus(self):
        return self._stimulus

    def unateness(self):
        return self._unateness

    def name(self):
        return self._signal_name

class SetupHoldTimingSignal(TimingSignal):
    def __init__(self,signal,related,delay,stepsize,direction):
        TimingSignal.__init__(self,signal,related)
        self._delay =  delay
        self._stepsize = stepsize
        self._direction = direction

    def delay(self):
        return self._delay

    def stepsize(self):
        return self._stepsize

    def direction(self):
        return self._direction

