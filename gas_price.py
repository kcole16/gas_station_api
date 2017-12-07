import operator
import collections
import math

from web3 import Web3

from cytoolz import (
    groupby,
    sliding_window,
)

from eth_utils import (
    to_tuple,
)

#w3 = Web3(Web3.IPCProvider())
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io'))


MinerData = collections.namedtuple('MinerData', ['miner', 'num_blocks', 'min_gas_price'])
Probability = collections.namedtuple('Probability', ['gas_price', 'prob'])

#SAMPLE_SIZE = 100
SAMPLE_SIZE = 10
ALLOWED_WAIT = 60
PROBABIITY = 95


def get_avg_block_time(w3, sample_size):
    latest = w3.eth.getBlock('latest')
    oldest = w3.eth.getBlock(latest.number - sample_size)
    return (latest.timestamp - oldest.timestamp) / sample_size


def get_raw_miner_data(w3, sample_size):
    latest = w3.eth.getBlock('latest', full_transactions=True)
    blocks = [latest] + [w3.eth.getBlock(latest.number - i, full_transactions=True) for i in range(sample_size - 1)]

    for block in blocks:
        for transaction in block.transactions:
            yield (block.miner, block.hash, transaction.gasPrice)


@to_tuple
def aggregate_miner_data(raw_data):
    data_by_miner = groupby(1, raw_data)

    for miner, miner_data in data_by_miner.items():
        _, block_hashes, gas_prices = map(set, zip(*miner_data))
        yield MinerData(miner, len(set(block_hashes)), min(gas_prices))


@to_tuple
def compute_probabilities(miner_data, wait_blocks, sample_size):
    """
    Computes the probabilities that a txn will be accepted at each of the gas
    prices accepted by the miners.
    """
    miner_data_by_price = tuple(sorted(
        miner_data,
        key=operator.attrgetter('min_gas_price'),
        reverse=True,
    ))
    for idx in range(len(miner_data_by_price)):
        min_gas_price = miner_data_by_price[idx].min_gas_price
        num_blocks_accepting_price = sum(m.num_blocks for m in miner_data_by_price[idx:])
        inv_prob_per_block = (sample_size - num_blocks_accepting_price) / sample_size
        probability_accepted = 1 - inv_prob_per_block ** wait_blocks
        yield Probability(min_gas_price, probability_accepted)


def compute_gas_price(probabilities, desired_probability):
    first = probabilities[0]
    last = probabilities[-1]

    if desired_probability >= first.prob:
        return first.gas_price
    elif desired_probability <= last.prob:
        return last.gas_price

    for left, right in sliding_window(2, probabilities):
        if desired_probability < right.prob:
            continue
        elif desired_probability > left.prob:
            raise Exception('Invariant')

        adj_prob = desired_probability - right.prob
        window_size = left.prob - right.prob
        position = adj_prob / window_size
        gas_window_size = left.gas_price - right.gas_price
        gas_price = int(math.ceil(right.gas_price + gas_window_size * position))
        return gas_price
    else:
        raise Exception('Invariant')


def get_gas_price(probability=PROBABIITY, allowed_wait=ALLOWED_WAIT, sample_size=SAMPLE_SIZE):
    avg_block_time = get_avg_block_time(w3, sample_size=sample_size)
    # print('AVG BLOCK TIME:', avg_block_time)
    wait_blocks = int(math.ceil(ALLOWED_WAIT / avg_block_time))
    # print('WAIT BLOCKS:', wait_blocks)

    raw_data = get_raw_miner_data(w3, sample_size=sample_size)
    miner_data = aggregate_miner_data(raw_data)

    probabilities = compute_probabilities(miner_data, wait_blocks, sample_size=sample_size)
    # print('PROBABIITIES:', probabilities)

    gas_price = compute_gas_price(probabilities, PROBABIITY / 100)
    gas_price_gwei = Web3.fromWei(gas_price, 'gwei')
    data = {
        'safe_price_in_gwei': float(gas_price_gwei),
        'avg_block_time': float(avg_block_time),
        'wait_blocks': int(wait_blocks),
    }
    return data
