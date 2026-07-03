from pydantic import BaseModel, Field


class ZkEmployeeLinkRequest(BaseModel):
    zk_user_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="User ID del usuario en el reloj ZKTeco.",
    )