from pydantic import BaseModel

class GetPartyCertResponse(BaseModel):
    party_id: int
    cert_file: str

class RequestSharingDataMPCRequest(BaseModel):
    tlsn_proof: str
    mpc_port_base: int
    secret_index: int
    client_id: int
    client_port_base: int
    client_cert_file: str
    input_bytes: int

class RequestSharingDataMPCResponse(BaseModel):
    data_commitment: str

class RequestQueryComputationMPCRequest(BaseModel):
    mpc_port_base: int
    client_id: int
    client_port_base: int
    client_cert_file: str

class RequestQueryComputationMPCResponse(BaseModel):
    pass
