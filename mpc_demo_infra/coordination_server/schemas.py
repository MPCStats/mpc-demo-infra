from pydantic import BaseModel
from typing import Optional
from .user_queue import AddResult


class RequestHasAddressSharedDataRequest(BaseModel):
    eth_address: str

class RequestHasAddressSharedDataResponse(BaseModel):
    has_shared_data: bool

class RequestSharingDataRequest(BaseModel):
    eth_address: str
    tlsn_proof: str
    client_id: int
    client_cert_file: str
    access_key: str
    computation_key: str

class RequestSharingDataResponse(BaseModel):
    client_port_base: int

class RequestQueryComputationRequest(BaseModel):
    client_id: int
    client_cert_file: str
    access_key: str
    computation_key: str

class RequestQueryComputationResponse(BaseModel):
    client_port_base: int

class RequestAddUserToQueueRequest(BaseModel):
    access_key: str

class RequestAddUserToQueueResponse(BaseModel):
    result: AddResult

class RequestGetPositionRequest(BaseModel):
    access_key: str

class RequestGetPositionResponse(BaseModel):
    position: Optional[int]
    computation_key: Optional[str]

class RequestValidateComputationKeyRequest(BaseModel):
    access_key: str
    computation_key: str

class RequestValidateComputationKeyResponse(BaseModel):
    is_valid: bool

class RequestFinishComputationRequest(BaseModel):
    access_key: str
    computation_key: str

class RequestFinishComputationResponse(BaseModel):
    is_finished: bool
