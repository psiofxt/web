'''
    Copyright (C) 2017 Gitcoin Core

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

'''

import json
import subprocess
import time

import ipfsapi
import requests
from dashboard.helpers import UnsupportedSchemaException, normalizeURL, process_bounty_changes, process_bounty_details
from dashboard.models import Bounty
from eth_utils import to_checksum_address
from hexbytes import HexBytes
from ipfsapi.exceptions import CommunicationError
from web3 import HTTPProvider, Web3
from web3.exceptions import BadFunctionCallOutput


class BountyNotFoundException(Exception):
    pass


class UnsupportedNetworkException(Exception):
    pass


class IPFSCantConnectException(Exception):
    pass


class NoBountiesException(Exception):
    pass


def startIPFS():
    print('starting IPFS')
    subp = subprocess.Popen(["ipfs", "daemon"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(10) #time for IPFS to boot


def isIPFSrunning():
    output = subprocess.check_output('pgrep -fl ipfs | wc -l', shell=True)
    is_running = output != b'       0\n'
    print(f'** ipfs is_running: {is_running}')
    return is_running


def getIPFS():
    if not isIPFSrunning():
        startIPFS()

    try:
        return ipfsapi.connect('127.0.0.1', 5001)
    except CommunicationError:
        raise IPFSCantConnectException("IPFS is not running.  try running it with `ipfs daemon` before this script")


def ipfs_cat(key):
    response = ipfs_cat_requests(key)
    if response:
        return response

    response = ipfs_cat_ipfsapi(key)
    if response:
        return response

    raise Exception("could not connect to IPFS")


def ipfs_cat_ipfsapi(key):
    ipfs = getIPFS()
    return ipfs.cat(key)


def ipfs_cat_requests(key):
    url = f'https://ipfs.infura.io:5001/api/v0/cat/{key}'
    response = requests.get(url)
    return response.text


def getWeb3(network):
    """Get a Web3 session for the provided network.

    Attributes:
        network (str): The network to establish a session with.

    Raises:
        UnsupportedNetworkException: The exception is raised if the method
            is passed an invalid network.

    Returns:
        web3.main.Web3: A web3 instance for the provided network.

    """
    if network in ['mainnet', 'rinkeby', 'ropsten']:
        return Web3(HTTPProvider(f'https://{network}.infura.io'))
    raise UnsupportedNetworkException(network)


def getStandardBountiesContractAddresss(network):
    if network == 'mainnet':
        return to_checksum_address('0x2af47a65da8cd66729b4209c22017d6a5c2d2400')
    elif network == 'rinkeby':
        return to_checksum_address('0xf209d2b723b6417cbf04c07e733bee776105a073')
    raise UnsupportedNetworkException(network)


# http://web3py.readthedocs.io/en/latest/contracts.html
def getBountyContract(network):
    web3 = getWeb3(network)
    standardbounties_abi = '[{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"}],"name":"killBounty","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_bountyId","type":"uint256"}],"name":"getBountyToken","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_data","type":"string"}],"name":"fulfillBounty","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_newDeadline","type":"uint256"}],"name":"extendDeadline","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"getNumBounties","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_fulfillmentId","type":"uint256"},{"name":"_data","type":"string"}],"name":"updateFulfillment","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_newFulfillmentAmount","type":"uint256"},{"name":"_value","type":"uint256"}],"name":"increasePayout","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_newFulfillmentAmount","type":"uint256"}],"name":"changeBountyFulfillmentAmount","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_newIssuer","type":"address"}],"name":"transferIssuer","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_value","type":"uint256"}],"name":"activateBounty","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"constant":false,"inputs":[{"name":"_issuer","type":"address"},{"name":"_deadline","type":"uint256"},{"name":"_data","type":"string"},{"name":"_fulfillmentAmount","type":"uint256"},{"name":"_arbiter","type":"address"},{"name":"_paysTokens","type":"bool"},{"name":"_tokenContract","type":"address"}],"name":"issueBounty","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_issuer","type":"address"},{"name":"_deadline","type":"uint256"},{"name":"_data","type":"string"},{"name":"_fulfillmentAmount","type":"uint256"},{"name":"_arbiter","type":"address"},{"name":"_paysTokens","type":"bool"},{"name":"_tokenContract","type":"address"},{"name":"_value","type":"uint256"}],"name":"issueAndActivateBounty","outputs":[{"name":"","type":"uint256"}],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[{"name":"_bountyId","type":"uint256"}],"name":"getBountyArbiter","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_value","type":"uint256"}],"name":"contribute","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_newPaysTokens","type":"bool"},{"name":"_newTokenContract","type":"address"}],"name":"changeBountyPaysTokens","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_bountyId","type":"uint256"}],"name":"getBountyData","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_fulfillmentId","type":"uint256"}],"name":"getFulfillment","outputs":[{"name":"","type":"bool"},{"name":"","type":"address"},{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_newArbiter","type":"address"}],"name":"changeBountyArbiter","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_newDeadline","type":"uint256"}],"name":"changeBountyDeadline","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_fulfillmentId","type":"uint256"}],"name":"acceptFulfillment","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"","type":"uint256"}],"name":"bounties","outputs":[{"name":"issuer","type":"address"},{"name":"deadline","type":"uint256"},{"name":"data","type":"string"},{"name":"fulfillmentAmount","type":"uint256"},{"name":"arbiter","type":"address"},{"name":"paysTokens","type":"bool"},{"name":"bountyStage","type":"uint8"},{"name":"balance","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_bountyId","type":"uint256"}],"name":"getBounty","outputs":[{"name":"","type":"address"},{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"bool"},{"name":"","type":"uint256"},{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_bountyId","type":"uint256"},{"name":"_newData","type":"string"}],"name":"changeBountyData","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_bountyId","type":"uint256"}],"name":"getNumFulfillments","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"inputs":[{"name":"_owner","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"name":"bountyId","type":"uint256"}],"name":"BountyIssued","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"bountyId","type":"uint256"},{"indexed":false,"name":"issuer","type":"address"}],"name":"BountyActivated","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"bountyId","type":"uint256"},{"indexed":true,"name":"fulfiller","type":"address"},{"indexed":true,"name":"_fulfillmentId","type":"uint256"}],"name":"BountyFulfilled","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"_bountyId","type":"uint256"},{"indexed":false,"name":"_fulfillmentId","type":"uint256"}],"name":"FulfillmentUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"bountyId","type":"uint256"},{"indexed":true,"name":"fulfiller","type":"address"},{"indexed":true,"name":"_fulfillmentId","type":"uint256"}],"name":"FulfillmentAccepted","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"bountyId","type":"uint256"},{"indexed":true,"name":"issuer","type":"address"}],"name":"BountyKilled","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"bountyId","type":"uint256"},{"indexed":true,"name":"contributor","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"ContributionAdded","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"bountyId","type":"uint256"},{"indexed":false,"name":"newDeadline","type":"uint256"}],"name":"DeadlineExtended","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"bountyId","type":"uint256"}],"name":"BountyChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"_bountyId","type":"uint256"},{"indexed":true,"name":"_newIssuer","type":"address"}],"name":"IssuerTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"_bountyId","type":"uint256"},{"indexed":false,"name":"_newFulfillmentAmount","type":"uint256"}],"name":"PayoutIncreased","type":"event"}]';
    standardbounties_addr = getStandardBountiesContractAddresss(network)
    bounty_abi = json.loads(standardbounties_abi)
    getBountyContract = web3.eth.contract(standardbounties_addr, abi=bounty_abi)
    return getBountyContract


def get_bounty(bounty_enum, network):
    standard_bounties = getBountyContract(network)

    try:
        issuer, deadline, fulfillmentAmount, paysTokens, bountyStage, balance = standard_bounties.functions.getBounty(bounty_enum).call()
    except BadFunctionCallOutput:
        raise BountyNotFoundException

    bountydata = standard_bounties.functions.getBountyData(bounty_enum).call()
    arbiter = standard_bounties.functions.getBountyArbiter(bounty_enum).call()
    token = standard_bounties.functions.getBountyToken(bounty_enum).call()
    numFulfillments = int(standard_bounties.functions.getNumFulfillments(bounty_enum).call())
    fulfillments = []
    for fulfill_enum in range(0, numFulfillments):
        accepted, fulfiller, data = standard_bounties.functions.getFulfillment(bounty_enum, fulfill_enum).call()
        fulfillments.append({
            'id': fulfill_enum,
            'accepted': accepted,
            'fulfiller': fulfiller,
            'data': json.loads(ipfs_cat(data)),
            })

    bounty = {
        'id': bounty_enum,
        'issuer': issuer,
        'deadline': deadline,
        'fulfillmentAmount': fulfillmentAmount,
        'paysTokens': paysTokens,
        'bountyStage': bountyStage,
        'balance': balance,
        'data': json.loads(ipfs_cat(bountydata)),
        'arbiter': arbiter,
        'token': token,
        'fulfillments': fulfillments,
        'network': network,
    }
    return bounty


# processes a bounty returned by get_bounty
def process_bounty(bounty_data):
    did_change, old_bounty, new_bounty = process_bounty_details(bounty_data)

    if did_change:
        print(f"- processing changes, {old_bounty} => {new_bounty}")
        process_bounty_changes(old_bounty, new_bounty, None)

    return did_change, old_bounty, new_bounty


def has_tx_mined(txid, network):
    web3 = getWeb3(network)
    try:
        transaction = web3.eth.getTransaction(txid)
        return transaction.blockHash != HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000')
    except Exception:
        return False


def getBountyID(issueURL, network):
    issueURL = normalizeURL(issueURL)
    bounty_id = getBountyID_from_db(issueURL, network)
    if bounty_id:
        return bounty_id

    all_known_stdbounties = Bounty.objects.filter(web3_type='bounties_network', network=network).order_by('-standard_bounties_id')

    methodology = 'start_from_web3_latest'
    try:
        highest_known_bounty_id = getHighestKnownBountyID(network)
        bounty_id = getBountyID_from_web3(issueURL, network, highest_known_bounty_id, direction='down')
    except NoBountiesException:
        methodology = 'start_from_db'
        last_known_bounty_id = 0
        if all_known_stdbounties.exists():
            last_known_bounty_id = all_known_stdbounties.first().standard_bounties_id
        bounty_id = getBountyID_from_web3(issueURL, network, last_known_bounty_id, direction='up')

    return bounty_id


def getBountyID_from_db(issueURL, network):
    issueURL = normalizeURL(issueURL)
    bounties = Bounty.objects.filter(github_url=issueURL, network=network, web3_type='bounties_network')
    if not bounties.exists():
        return None
    return bounties.first().standard_bounties_id


def getHighestKnownBountyID(network):
    standard_bounties = getBountyContract(network)
    num_bounties = int(standard_bounties.functions.getNumBounties().call())
    if num_bounties == 0:
        raise NoBountiesException()
    return num_bounties - 1


def getBountyID_from_web3(issueURL, network, start_bounty_id, direction='up'):
    issueURL = normalizeURL(issueURL)
    web3 = getWeb3(network)

    # iterate through all the bounties
    bounty_enum = start_bounty_id
    more_bounties = True
    while more_bounties:
        try:

            # pull and process each bounty
            print(f'** getBountyID_from_web3; looking at {bounty_enum}')
            bounty = get_bounty(bounty_enum, network)
            url = bounty.get('data', {}).get('payload', {}).get('webReferenceURL', False)
            if url == issueURL:
                return bounty['id']

        except BountyNotFoundException:
            more_bounties = False
        except UnsupportedSchemaException:
            pass
        finally:
            # prepare for next loop
            if direction == 'up':
                bounty_enum += 1
            else:
                bounty_enum -= 1

    return None


def build_profile_pairs(bounty):
    """Build the profile pairs list of tuples for ingestion by notifications.

    Args:
        bounty (dashboard.models.Bounty): The Bounty to build profile pairs for.

    Returns:
        list of tuples: The list of profile pair tuples.

    """
    profile_handles = []
    for fulfillment in bounty.fulfillments.select_related('profile').all().order_by('pk'):
        profile_handles.append((fulfillment.profile.handle, fulfillment.profile.absolute_url))
    return profile_handles
