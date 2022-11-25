from uds.uds_communications.TransportProtocols.Can.CanTp import CanTp
from uds.interfaces import TpInterface


class TpFactory:
    """Transport protocol factory class."""

    #: store all available protocols
    protocols: dict = {"can": CanTp}

    @classmethod
    def select_transport_protocol(cls, protocol: str, **kwargs) -> TpInterface:
        """Select a protocol and instaciate it.

        :param protocol: protocol's name
        :param kwargs: named arguments

        :return: the selected protocol instance

        :raises ValueError: if the given protocol doesn't exist
        """
        protocol_instance = cls.protocols.get(protocol.lower())

        if protocol_instance is None:
            raise ValueError(f"protocol {protocol} is not supported!")

        return protocol_instance(**kwargs)

    @classmethod
    def add_protocol(cls, name: str, obj: TpInterface) -> None:
        """Add a protocol to the available protocols dictionary.

        :param name: protocol's name
        :param obj: protocol object reference

        :raises ValueError: if the given protocol's name already exists
            in protocols dictionary
        """
        if name in cls.protocols:
            raise ValueError(f"protocol {name} already exist!")

        cls.protocols[name] = obj

    @classmethod
    def remove_protocol(cls, name: str) -> None:
        """Remove a protocol from the available protocols dictionary.

        :param name: protocol's name

        :raises ValueError: if the given protocol's name doesn't exist
            in the protocols dictionary
        """
        if name in cls.protocols:
            raise ValueError(f"protocol {name} is not referenced!")

        del cls.protocols[name]
