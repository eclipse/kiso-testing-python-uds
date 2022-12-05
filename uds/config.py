import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class UdsConfig:
    """Encapsulate all uds communication layer parameters."""

    transport_protocol: str
    p2_can_client: int
    p2_can_server: int


@dataclass
class IsoTpConfig:
    """Encapsulate all isotp communication layer parameters."""

    req_id: int
    res_id: int
    addressing_type: str
    n_sa: int
    n_ta: int
    n_ae: int
    m_type: str
    discard_neg_resp: bool


class Config:
    """Load the different communication layer configuration and store
    them for further usage.
    """

    #: store uds configuration class container instance
    uds: UdsConfig
    #: store isotp configuration class container instance
    isotp: IsoTpConfig

    @classmethod
    def load_isotp_config(cls, config: dict) -> None:
        """Load and store isotp layer configuration parameters.

        :param config: isotp configuration parameters
        """
        cls.isotp = IsoTpConfig(**config)
        log.info(f"Loaded isotp configuration parameters : {cls.isotp}")

    @classmethod
    def load_uds_config(cls, config: dict) -> None:
        """Load and store uds layer configuration parameters.

        :param config: uds configuration parameters
        """
        cls.uds = UdsConfig(**config)
        log.info(f"Loaded uds configuration parameters : {cls.isotp}")

    @classmethod
    def load_com_layer_config(cls, tp_config: dict, uds_config: dict) -> None:
        """Load and store all configuration parameters from all
        available communication layers.

        :param tp_config: isotp configuration parameters
        :param uds_config: uds configuration parameters
        """
        cls.load_isotp_config(tp_config)
        cls.load_uds_config(uds_config)
