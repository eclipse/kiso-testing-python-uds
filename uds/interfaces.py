import abc


class TpInterface(abc.ABC):
    @abc.abstractmethod
    def send(self, payload):
        """ """

    @abc.abstractmethod
    def recv(self, timeout_ms):
        """ """
