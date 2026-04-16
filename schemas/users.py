from pydantic import BaseModel


class UserCreateData(BaseModel):
    """Data for creating a user."""

    qbit_host: str
    qbit_port: int
    qbit_user: str
    qbit_pass: str
    c411_key: str | None = None
    torr9_key: str | None = None
    lacale_key: str | None = None


class UserData(BaseModel):
    """Data for user."""

    id: str
    qbit_host: str
    qbit_port: int
    qbit_user: str
    qbit_pass: str
    c411_key: str | None = None
    torr9_key: str | None = None
    lacale_key: str | None = None
