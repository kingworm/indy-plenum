import json
from collections import OrderedDict
from copy import deepcopy

from ledger.genesis_txn.genesis_txn_file_util import create_genesis_txn_init_ledger
from plenum.common.constants import TXN_TIME, TXN_TYPE, TARGET_NYM, ROLE, \
    ALIAS, VERKEY, FORCE, TXN_PAYLOAD, TXN_PAYLOAD_METADATA, TXN_SIGNATURE, TXN_METADATA, TXN_SIGNATURE_TYPE, ED25515, \
    TXN_SIGNATURE_FROM, TXN_SIGNATURE_VALUE, TXN_SIGNATURE_VALUES, TXN_PAYLOAD_DATA, TXN_PAYLOAD_METADATA_REQ_ID, \
    TXN_PAYLOAD_METADATA_FROM, TXN_PAYLOAD_PROTOCOL_VERSION, TXN_PAYLOAD_TYPE, TXN_METADATA_SEQ_NO, TXN_METADATA_TIME, \
    TXN_METADATA_ID, TXN_VERSION, CURRENT_PROTOCOL_VERSION
from plenum.common.request import Request
from plenum.common.types import f, OPERATION
from stp_core.common.log import getlogger

logger = getlogger()


def getTxnOrderedFields():
    return OrderedDict([
        (f.IDENTIFIER.nm, (str, str)),
        (f.REQ_ID.nm, (str, int)),
        (f.SIG.nm, (str, str)),
        (TXN_TIME, (str, int)),
        (TXN_TYPE, (str, str)),
        (TARGET_NYM, (str, str)),
        (VERKEY, (str, str)),
        (ROLE, (str, str)),
        (ALIAS, (str, str)),
        (f.SIGS.nm, (str, str)),
    ])


def createGenesisTxnFile(genesisTxns, targetDir, fileName, fieldOrdering,
                         reset=True):
    ledger = create_genesis_txn_init_ledger(targetDir, fileName)

    if reset:
        ledger.reset()

    reqIds = {}
    for txn in genesisTxns:
        identifier = get_from(txn)
        if identifier not in reqIds:
            reqIds[identifier] = 0
        reqIds[identifier] += 1
        append_payload_metadata(txn,
                                frm=identifier,
                                req_id=reqIds[identifier])
        ledger.add(txn)
    ledger.stop()


def idr_from_req_data(data):
    if data.get(f.IDENTIFIER.nm):
        return data[f.IDENTIFIER.nm]
    else:
        return Request.gen_idr_from_sigs(data.get(f.SIGS.nm, {}))


# TODO: remove after old client deprecation or uniforming read and write respnse formats
def get_reply_itentifier(result):
    if f.IDENTIFIER.nm in result:
        return result[f.IDENTIFIER.nm]
    elif TXN_PAYLOAD in result and TXN_PAYLOAD_METADATA in result[TXN_PAYLOAD] and \
            TXN_PAYLOAD_METADATA_FROM in result[TXN_PAYLOAD][TXN_PAYLOAD_METADATA]:
        return result[TXN_PAYLOAD][TXN_PAYLOAD_METADATA][TXN_PAYLOAD_METADATA_FROM]
    else:
        return Request.gen_idr_from_sigs(result.get(f.SIGS.nm, {}))


# TODO: remove after old client deprecation or uniforming read and write respnse formats
def get_reply_reqId(result):
    if f.REQ_ID.nm in result:
        return result[f.REQ_ID.nm]
    elif TXN_PAYLOAD in result and TXN_PAYLOAD_METADATA in result[TXN_PAYLOAD] and \
            TXN_PAYLOAD_METADATA_REQ_ID in result[TXN_PAYLOAD][TXN_PAYLOAD_METADATA]:
        return result[TXN_PAYLOAD][TXN_PAYLOAD_METADATA][TXN_PAYLOAD_METADATA_REQ_ID]
    assert False


# TODO: remove after old client deprecation or uniforming read and write respnse formats
def get_reply_txntype(result):
    if TXN_TYPE in result:
        return result[TXN_TYPE]
    elif TXN_PAYLOAD in result and TXN_TYPE in result[TXN_PAYLOAD]:
        return result[TXN_PAYLOAD][TXN_TYPE]


# TODO: remove after old client deprecation or uniforming read and write respnse formats
def get_reply_nym(result):
    if TARGET_NYM in result:
        return result[TARGET_NYM]
    elif TXN_PAYLOAD in result and TXN_PAYLOAD_DATA in result[TXN_PAYLOAD] and\
            TARGET_NYM in result[TXN_PAYLOAD][TXN_PAYLOAD_DATA]:
        return result[TXN_PAYLOAD][TXN_PAYLOAD_DATA][TARGET_NYM]

# TODO: Support real strategies and Data Class for transactions
# instead of util functions


def get_type(txn):
    return txn[TXN_PAYLOAD][TXN_PAYLOAD_TYPE]


def set_type(txn, txn_type):
    txn[TXN_PAYLOAD][TXN_PAYLOAD_TYPE] = txn_type
    return txn


def get_payload_data(txn):
    return txn[TXN_PAYLOAD][TXN_PAYLOAD_DATA]


def get_from(txn):
    return txn[TXN_PAYLOAD][TXN_PAYLOAD_METADATA].get(TXN_PAYLOAD_METADATA_FROM, None)


def get_req_id(txn):
    return txn[TXN_PAYLOAD][TXN_PAYLOAD_METADATA].get(TXN_PAYLOAD_METADATA_REQ_ID, None)


def get_seq_no(txn):
    return txn[TXN_METADATA].get(TXN_METADATA_SEQ_NO, None)


def get_txn_time(txn):
    return txn[TXN_METADATA].get(TXN_METADATA_TIME, None)


def get_txn_id(txn):
    return txn[TXN_METADATA].get(TXN_METADATA_ID, None)


def is_forced(txn):
    force = get_payload_data(txn).get(FORCE, None)
    if force is None:
        return False
    return str(force) == 'True'


def init_empty_txn(txn_type, protocol_version=None):
    result = {}
    result[TXN_PAYLOAD] = {}
    result[TXN_METADATA] = {}
    result[TXN_SIGNATURE] = {}
    result[TXN_VERSION] = "1"

    set_type(result, txn_type)
    result[TXN_PAYLOAD][TXN_PAYLOAD_DATA] = {}
    if protocol_version:
        result[TXN_PAYLOAD][TXN_PAYLOAD_PROTOCOL_VERSION] = protocol_version

    result[TXN_PAYLOAD][TXN_PAYLOAD_METADATA] = {}
    # result[TXN_PAYLOAD][TXN_PAYLOAD_METADATA][TXN_PAYLOAD_METADATA_FROM] = None
    # result[TXN_PAYLOAD][TXN_PAYLOAD_METADATA][TXN_PAYLOAD_METADATA_REQ_ID] = None

    # result[TXN_METADATA][TXN_METADATA_SEQ_NO] = None
    # result[TXN_METADATA][TXN_METADATA_TIME] = None
    # result[TXN_METADATA][TXN_METADATA_ID] = None

    return result


def set_payload_data(txn, data):
    txn[TXN_PAYLOAD][TXN_PAYLOAD_DATA] = data
    return txn


def append_payload_metadata(txn, frm=None, req_id=None):
    if frm is not None:
        txn[TXN_PAYLOAD][TXN_PAYLOAD_METADATA][TXN_PAYLOAD_METADATA_FROM] = frm
    if req_id is not None:
        txn[TXN_PAYLOAD][TXN_PAYLOAD_METADATA][TXN_PAYLOAD_METADATA_REQ_ID] = req_id
    return txn


def append_txn_metadata(txn, seq_no=None, txn_time=None, txn_id=None):
    if seq_no is not None:
        txn[TXN_METADATA][TXN_METADATA_SEQ_NO] = seq_no
    if txn_time is not None:
        txn[TXN_METADATA][TXN_METADATA_TIME] = txn_time
    if txn_id is not None:
        txn[TXN_METADATA][TXN_METADATA_ID] = txn_id
    return txn


def reqToTxn(req, txn_time=None):
    """
    Transform a client request such that it can be stored in the ledger.
    Also this is what will be returned to the client in the reply
    :param req:
    :return:
    """

    if isinstance(req, dict):
        req_data = req
    elif isinstance(req, str):
        req_data = json.loads(req)
    elif isinstance(req, Request):
        req_data = req.as_dict
    else:
        raise TypeError(
            "Expected dict or str as input, but got: {}".format(type(req)))

    req_data = deepcopy(req_data)
    return do_req_to_txn(req_data=req_data,
                         req_op=req_data[OPERATION],
                         txn_time=txn_time)


def transform_to_new_format(txn, seq_no):
    t = deepcopy(txn)
    txn_time = t.pop(TXN_TIME, None)
    txn = do_req_to_txn(req_data=t,
                        req_op=t,
                        txn_time=txn_time)
    append_txn_metadata(txn, seq_no=seq_no)
    return txn


def do_req_to_txn(req_data, req_op, txn_time=None):
    # 1. init new txn
    result = init_empty_txn(txn_type=req_op.pop(TXN_TYPE, None),
                            protocol_version=req_data.pop(f.PROTOCOL_VERSION.nm, None))

    # 2. Fill txn metadata (txnTime)
    # more metadata will be added by the Ledger
    if txn_time:
        append_txn_metadata(result, txn_time=txn_time)

    # 3. Fill Signature
    if (f.SIG.nm in req_data) or (f.SIGS.nm in req_data):
        result[TXN_SIGNATURE][TXN_SIGNATURE_TYPE] = ED25515
        signatures = {req_data.get(f.IDENTIFIER.nm, None): req_data.get(f.SIG.nm, None)} \
            if req_data.get(f.SIG.nm, None) is not None \
            else req_data.get(f.SIGS.nm, {})
        result[TXN_SIGNATURE][TXN_SIGNATURE_VALUES] = [
            {
                TXN_SIGNATURE_FROM: frm,
                TXN_SIGNATURE_VALUE: sign,
            }
            for frm, sign in signatures.items()
        ]
        req_data.pop(f.SIG.nm, None)
        req_data.pop(f.SIGS.nm, None)

    # 4. Fill Payload metadata

    append_payload_metadata(result,
                            frm=req_data.pop(f.IDENTIFIER.nm, None),
                            req_id=req_data.pop(f.REQ_ID.nm, None))

    # 5. Fill Payload data
    set_payload_data(result, req_op)

    return result
