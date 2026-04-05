"""OCPP 1.6 enumeration types."""

from enum import StrEnum


class ChargePointStatus(StrEnum):
    """Connector/charger status values from OCPP 1.6 §7.2."""

    AVAILABLE = "Available"
    PREPARING = "Preparing"
    CHARGING = "Charging"
    SUSPENDED_EVSE = "SuspendedEVSE"
    SUSPENDED_EV = "SuspendedEV"
    FINISHING = "Finishing"
    RESERVED = "Reserved"
    UNAVAILABLE = "Unavailable"
    FAULTED = "Faulted"


class ChargePointErrorCode(StrEnum):
    """Error codes for StatusNotification."""

    NO_ERROR = "NoError"
    CONNECTOR_LOCK_FAILURE = "ConnectorLockFailure"
    EV_COMMUNICATION_ERROR = "EVCommunicationError"
    GROUND_FAILURE = "GroundFailure"
    HIGH_TEMPERATURE = "HighTemperature"
    INTERNAL_ERROR = "InternalError"
    LOCAL_LIST_CONFLICT = "LocalListConflict"
    OTHER_ERROR = "OtherError"
    OVER_CURRENT_FAILURE = "OverCurrentFailure"
    POWER_METER_FAILURE = "PowerMeterFailure"
    READER_FAILURE = "ReaderFailure"
    RESET_FAILURE = "ResetFailure"
    UNDER_VOLTAGE = "UnderVoltage"
    WEAK_SIGNAL = "WeakSignal"


class RegistrationStatus(StrEnum):
    """BootNotification response status."""

    ACCEPTED = "Accepted"
    PENDING = "Pending"
    REJECTED = "Rejected"


class AuthorizationStatus(StrEnum):
    """StartTransaction idTagInfo status."""

    ACCEPTED = "Accepted"
    BLOCKED = "Blocked"
    EXPIRED = "Expired"
    INVALID = "Invalid"
    CONCURRENT_TX = "ConcurrentTx"


class StopReason(StrEnum):
    """Reason codes for StopTransaction."""

    DE_AUTHORIZED = "DeAuthorized"
    EMERGENCY_STOP = "EmergencyStop"
    EV_DISCONNECTED = "EVDisconnected"
    HARD_RESET = "HardReset"
    LOCAL = "Local"
    OTHER = "Other"
    POWER_LOSS = "PowerLoss"
    REBOOT = "Reboot"
    REMOTE = "Remote"
    SOFT_RESET = "SoftReset"
    UNLOCK_COMMAND = "UnlockCommand"


class Measurand(StrEnum):
    """Measurand identifiers for SampledValue."""

    ENERGY_ACTIVE_IMPORT_REGISTER = "Energy.Active.Import.Register"
    POWER_ACTIVE_IMPORT = "Power.Active.Import"
    CURRENT_IMPORT = "Current.Import"
    VOLTAGE = "Voltage"
    SOC = "SoC"
    TEMPERATURE = "Temperature"


class UnitOfMeasure(StrEnum):
    """Unit-of-measure identifiers for SampledValue."""

    WH = "Wh"
    KWH = "kWh"
    W = "W"
    KW = "kW"
    A = "A"
    V = "V"
    CELSIUS = "Celsius"
    PERCENT = "Percent"


class ReadingContext(StrEnum):
    """Context in which a SampledValue was taken."""

    INTERRUPTION_BEGIN = "Interruption.Begin"
    INTERRUPTION_END = "Interruption.End"
    OTHER = "Other"
    SAMPLE_CLOCK = "Sample.Clock"
    SAMPLE_PERIODIC = "Sample.Periodic"
    TRANSACTION_BEGIN = "Transaction.Begin"
    TRANSACTION_END = "Transaction.End"
    TRIGGER = "Trigger"
