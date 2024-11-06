import argparse
import asyncio
from pathlib import Path
import aiohttp
import secrets

from ..client_lib.lib import fetch_parties_certs, share_data, query_computation
from .config import settings

# project_root/certs
PROJECT_ROOT = Path(__file__).parent.parent.parent
CERTS_PATH = Path(settings.certs_path)
TLSN_EXECUTABLE_DIR = Path(settings.tlsn_project_root) / "tlsn" / "examples" / "simple"

CMD_VERIFY_TLSN_PROOF = "cargo run --release --example simple_verifier"
CMD_GEN_TLSN_PROOF = "cargo run --release --example simple_prover"

DATA_TYPE = 0

async def add_user_to_queue(access_key: str) -> None:
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{settings.coordination_server_url}/add_user_to_queue", json={
                "access_key": access_key,
            }) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["result"] == 'QUEUE_IS_FULL':
                        print("\nThe queue is currently full. Please wait for your turn.")
                    else:
                        return
        await asyncio.sleep(settings.poll_duration)


async def poll_queue_until_ready(access_key: str) -> str:
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{settings.coordination_server_url}/get_position", json={
                "access_key": access_key,
            }) as response:
                if response.status == 200:
                    data = await response.json()
                    position = data["position"] 
                    if position is None:
                        print("{access_key}: The queue is currently full. Please wait for your turn.")
                    else:
                        print(f'{access_key}: position is {position}')
                        if position == 0:
                            print(f"{access_key}: Computation servers are ready. Your requested computation will begin shortly.")
                            return data["computation_key"]
                        else:
                            print(f"{access_key}: You are currently #{position} in line.")
                else:
                    print("Server error")
        await asyncio.sleep(settings.poll_duration)


async def notarize_and_share_data(voucher_code: str):
    # Gen tlsn proofs
    proof_file = PROJECT_ROOT / f"proof.json"
    process = await asyncio.create_subprocess_shell(
        f"cd {TLSN_EXECUTABLE_DIR} && {CMD_GEN_TLSN_PROOF} {DATA_TYPE} {str(proof_file.resolve())}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise Exception(f"TLSN proof generation failed with return code {process.returncode}, {stdout=}, {stderr=}")
    secret_input_line = next((line for line in stdout.decode().splitlines() if line.startswith(f"Party {DATA_TYPE} has ")), None)
    if not secret_input_line:
        raise ValueError(f"Could not find line for secret input")
    secret_input = int(secret_input_line.split()[3])
    with open(proof_file, "r") as f:
        tlsn_proof = f.read()

    # FIXME: `nonce` shouldn't be included in the proof
    # Should be changed when we're using newer version of tlsn
    def get_nonce_from_tlsn_proof(tlsn_proof: str):
        import json
        tlsn_proof = json.loads(tlsn_proof)
        private_openings = tlsn_proof["substrings"]["private_openings"]
        if len(private_openings) != 1:
            raise Exception(f"Expected 1 private opening, got {len(private_openings)}")
        commitment_index, openings = list(private_openings.items())[0]
        commitment_info, commitment = openings
        data_commitment_hash = bytes(commitment["hash"]).hex()
        data_commitment_nonce = bytes(commitment["nonce"]).hex()
        return data_commitment_hash, data_commitment_nonce
    _, nonce = get_nonce_from_tlsn_proof(tlsn_proof)

    await add_user_to_queue(voucher_code)
    computation_key = await poll_queue_until_ready(voucher_code)

    print("Fetching party certificates...")
    await fetch_parties_certs(
        settings.party_web_protocol,
        CERTS_PATH,
        settings.party_hosts,
        settings.party_ports
    )
    print("Party certificates have been fetched and saved.")

    # Share data
    await share_data(
        CERTS_PATH,
        settings.coordination_server_url,
        settings.party_hosts,
        voucher_code,
        tlsn_proof,
        secret_input,
        nonce,
        computation_key,
    )


async def query_computation_and_verify(
    computation_index: int,
):
    access_key = secrets.token_urlsafe(16)
    await add_user_to_queue(access_key)
    computation_key = await poll_queue_until_ready(access_key)

    print("Fetching party certificates...")
    await fetch_parties_certs(
        settings.party_web_protocol,
        CERTS_PATH,
        settings.party_hosts,
        settings.party_ports
    )

    print("Party certificates have been fetched and saved.")
    results = await query_computation(
        CERTS_PATH,
        settings.coordination_server_url,
        settings.party_hosts,
        access_key,
        computation_index,
        computation_key,
    )
    print(f"{results=}")


def notarize_and_share_data_cli():
    parser = argparse.ArgumentParser(description="Notarize and share data")
    parser.add_argument("voucher_code", type=str, help="The voucher code")
    args = parser.parse_args()
    try:
        asyncio.run(notarize_and_share_data(args.voucher_code))
    except Exception as e:
        print(e)


def query_computation_and_verify_cli():
    parser = argparse.ArgumentParser(description="Query computation and verify results")
    parser.add_argument("computation_index", type=int, help="The computation index")
    args = parser.parse_args()
    try:
        asyncio.run(query_computation_and_verify(args.computation_index))
    except Exception as e:
        print(e)
