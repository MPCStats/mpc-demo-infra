#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

def gen_env_consumer_api(
  transport: str,
  coord_host: str,
  party_hosts: list[str],
  party_ports: list[int],
):
  output = f"""\
COORDINATION_SERVER_URL={transport}://{coord_host}:8005
CERTS_PATH=certs
PARTY_HOSTS={json.dumps(party_hosts)}
PARTY_PORTS={json.dumps(party_ports)}
PRIVKEY_PEM_PATH=ssl_certs/privkey.pem
FULLCHAIN_PEM_PATH=ssl_certs/fullchain.pem
PARTY_WEB_PROTOCOL={transport}
PORT=8004
"""
  return output

def gen_env_coord(
  transport: str,
  party_hosts: list[str],
  party_ports: list[int],
):
  output = f"""\
PORT=8005
PARTY_HOSTS={json.dumps(party_hosts)}
PARTY_PORTS={json.dumps(party_ports)}
PARTY_API_KEY=81f47c24b9fbe22421ea3ae92a9cc8f6
PARTY_WEB_PROTOCOL={transport}
PROHIBIT_MULTIPLE_CONTRIBUTIONS=False
USER_QUEUE_HEAD_TIMEOUT=60
PRIVKEY_PEM_PATH=ssl_certs/privkey.pem
FULLCHAIN_PEM_PATH=ssl_certs/fullchain.pem
FREE_PORTS_START=8010
FREE_PORTS_END=8100
"""
  return output

def gen_env_party(
  transport: str,
  coord_host: str,
  party_hosts: list[str],
  party_ports: list[int], 
):
  output = f"""\
PORT=8006
PARTY_ID=0
COORDINATION_SERVER_URL={transport}://{coord_host}:8005
PARTY_API_KEY=81f47c24b9fbe22421ea3ae92a9cc8f6
PARTY_HOSTS={json.dumps(party_hosts)}
PARTY_PORTS={json.dumps(party_ports)}
PARTY_WEB_PROTOCOL={transport}
MAX_DATA_PROVIDERS=1000
PERFORM_COMMITMENT_CHECK=True
PRIVKEY_PEM_PATH=ssl_certs/privkey.pem
FULLCHAIN_PEM_PATH=ssl_certs/fullchain.pem
"""
  return output

def gen_docker_compose(notary_ip: str):
  s = f"""\
services:
  coord:
    build:
      context: .
      dockerfile: ./mpc_demo_infra/coordination_server/docker/Dockerfile
    ports:
      - "8005:8005"
    volumes:
      - coord-data:/root/mpc-demo-infra/
    stdin_open: true
    tty: true
    init: true
    extra_hosts:
      - "tlsnotaryserver.io:127.0.0.1"
    depends_on:
      - party_0
      - party_1
      - party_2
  notary:
    build:
      context: .
      dockerfile: ./mpc_demo_infra/notary_server/docker/Dockerfile
      args:
        NORTARY_IP: {notary_ip}
    ports:
      - "8003:8003"
    environment:
      - NOTARY_IP={notary_ip}
    stdin_open: true
    tty: true
    init: true
    extra_hosts:
      - "tlsnotaryserver.io:127.0.0.1"
  data_consumer_api:
    build:
      context: .
      dockerfile: ./mpc_demo_infra/data_consumer_api/docker/Dockerfile
    ports:
      - "8004:8004"
    volumes:
      - consumer_api-data:/root/mpc-demo-infra/
    stdin_open: true
    tty: true
    init: true
    extra_hosts:
      - "tlsnotaryserver.io:127.0.0.1"
    depends_on:
      - coord
  party_0:
    build:
      context: .
      dockerfile: ./mpc_demo_infra/computation_party_server/docker/Dockerfile
      args:
        PORT: 8006
        PARTY_ID: 0
        NUM_PARTIES: 3
    ports:
      - "8006:8006"
      - "8013:8013"
    environment:
      - PARTY_ID=0
    volumes:
      - party0-data:/root/MP-SPDZ/
    stdin_open: true
    tty: true
    init: true
    extra_hosts:
      - "tlsnotaryserver.io:127.0.0.1"

  party_1:
    build:
      context: .
      dockerfile: ./mpc_demo_infra/computation_party_server/docker/Dockerfile
      args:
        PORT: 8007
        PARTY_ID: 1
        NUM_PARTIES: 3
    ports:
      - "8007:8007"
      - "8014:8014"
    environment:
      - PARTY_ID=1
    volumes:
      - party1-data:/root/MP-SPDZ/
    stdin_open: true
    tty: true
    init: true
    extra_hosts:
      - "tlsnotaryserver.io:127.0.0.1"
  party_2:
    build:
      context: .
      dockerfile: ./mpc_demo_infra/computation_party_server/docker/Dockerfile
      args:
        PORT: 8008
        PARTY_ID: 2
        NUM_PARTIES: 3
    ports:
      - "8008:8008"
      - "8015:8015"
    environment:
      - PARTY_ID=2
    volumes:
      - party2-data:/root/MP-SPDZ/
    stdin_open: true
    tty: true
    init: true
    extra_hosts:
      - "tlsnotaryserver.io:127.0.0.1"
volumes:
  coord-data:
  party0-data:
  party1-data:
  party2-data:
  consumer_api-data:
"""
  return s

def parse_args():
  parser = argparse.ArgumentParser(description="config-file generation script")
  parser.add_argument(
    '--transport',
    choices=['http', 'https'],
    default='http',
    help=f"Transport to use. http is used by default",
  )
  parser.add_argument(
    '--notary-ip',
    type=str,
    default='127.0.0.1',
    help="IP address of the server on which the notary server runs",
  )
  parser.add_argument(
    '--dry-run',
    action='store_true',
    help='Print out the contents of config files',
  )
  return parser.parse_args()

args = parse_args()

def write_file(file_path: Path, content: str, args):
  if args.dry_run:
    print(f"----> {file_path}")
    print(content)
  else:
    with open(file_path, 'w') as f:
      f.write(content)
    print(f"Created {str(file_path)}")


def create_symlink(target: str, link_name: str):
  target_path = Path(target).resolve()
  link_path = Path(link_name)

  if link_path.is_symlink():
    return  # Symlink already exists, no action needed

  if link_path.exists():
    print(f"Unable to create a symbolic link {link_path} because {link_path} directory or file already exists", file=sys.stderr)
    sys.exit(1)

  print(f"Creating symbolic link: {link_path} -> {target_path}")
  try:
    link_path.symlink_to(target_path)
  except OSError as e:
    print(f"Failed to create symbolic link {link_path}: {e}", file=sys.stderr)
    sys.exit(1)

party_hosts = ["party_0", "party_1", "party_2"]
party_ports =[8006, 8007, 8008]

mpc_demo_infra = Path('mpc_demo_infra')

# write .env.consumer_api 
dot_env_consumer_api = gen_env_consumer_api(
  args.transport,
  args.notary_ip,
  party_hosts,
  party_ports,
)
write_file(mpc_demo_infra / 'data_consumer_api' / 'docker' / '.env.consumer_api', dot_env_consumer_api, args)

# write .env.coord
dot_env_coord = gen_env_coord(
  args.transport,
  party_hosts,
  party_ports,
)
write_file(mpc_demo_infra / 'coordination_server' / 'docker' / '.env.coord', dot_env_coord, args)

# write .env.party for partys
dot_env_party = gen_env_party(
  args.transport,
  args.notary_ip,
  party_hosts,
  party_ports,
)
write_file(mpc_demo_infra / 'computation_party_server' / 'docker' / '.env.party', dot_env_party, args)

# write docker-compose.yml
docker_compose_yml = gen_docker_compose(args.notary_ip)
write_file(Path('docker-compose.yml'), docker_compose_yml, args)

# create tlsn and MP-SPDZ symbolic links
create_symlink("./tlsn", "../tlsn")
create_symlink("./MP-SPDZ", "../MP-SPDZ")

