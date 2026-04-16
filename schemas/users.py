from pydantic import BaseModel


class UserData(BaseModel):
    """Data for user."""

    qbit_host: str
    qbit_port: int
    qbit_user: str
    qbit_pass: str
    c411_key: str | None = None
    torr9_key: str | None = None
    lacale_key: str | None = None
