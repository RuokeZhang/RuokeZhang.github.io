# coding: utf-8
import contextlib

import ipaddress
import os
import socket
import typing

import bytedenv
from euler.protocol import TTHeaderProtocolFactory
from euler.protocol.ttheader_protocol import PROTO_TYPE_BINARY
from euler.transport import TTHeaderTransportFactory, ttheader
from thriftpy2.thrift import TClient
from thriftpy2.transport import TSocket

import bytedance.algboost.sdk as algboost_sdk


__trans_factory = TTHeaderTransportFactory()
__proto_factory = TTHeaderProtocolFactory(
    strict_read=True,
    strict_write=True,
    proto_type=PROTO_TYPE_BINARY,
    client_type=ttheader.HeaderFramedClientType
)


# copied from euler client
def _get_egress_addr() -> typing.Dict:
    egress_addr = os.environ.get('SERVICE_MESH_EGRESS_ADDR')
    if not egress_addr:
        raise ValueError("`SERVICE_MESH_EGRESS_ADDR` environment variable missing")
    if ':' in egress_addr:
        addrs = egress_addr.split(':')
        if len(addrs) != 2 or not addrs[1].isdigit():
            raise ValueError("`SERVICE_MESH_EGRESS_ADDR` `%s` not legal" % egress_addr)
        connection_args = {'host': addrs[0], 'port': int(addrs[1])}
    else:
        connection_args = {'unix_socket': egress_addr}
    return connection_args


@contextlib.contextmanager
def rpc_client_context(
    psm: str,
    thrift_service,
    cluster: str = 'default',
    timeout_ms: int = 500,
    **kwargs,
):
    connect_timeout_ms = kwargs.get('connect_timeout', timeout_ms)
    socket_kwargs = _get_egress_addr()
    socket_kwargs.update(dict(
        socket_timeout=timeout_ms,
        connect_timeout=connect_timeout_ms,
    ))

    sock = TSocket(**socket_kwargs)
    transport = __trans_factory.get_transport(sock)
    protocol = __proto_factory.get_protocol(transport)

    try:
        log_id = algboost_sdk.get_log_id()
    except Exception as e: # noqa
        log_id = '-'

    header = protocol.get_ttheader()
    header.set_int_header(ttheader.HEADER_KEY_LOG_ID, log_id)
    header.set_int_header(ttheader.HEADER_KEY_FROM_IDC, bytedenv.get_idc_name())
    header.set_int_header(ttheader.HEADER_KEY_FROM_SERVICE, bytedenv.get_psm())
    header.set_int_header(ttheader.HEADER_KEY_FROM_CLUSTER, bytedenv.get_cluster())
    header.set_int_header(ttheader.HEADER_KEY_ENV, os.environ.get('TCE_ENV', 'prod'))
    header.set_int_header(ttheader.HEADER_KEY_TO_SERVICE, psm)
    header.set_int_header(ttheader.HEADER_KEY_TO_CLUSTER, cluster)
    header.set_int_header(ttheader.HEADER_KEY_TO_METHOD, kwargs.get('method', '-'))
    header.set_int_header(ttheader.HEADER_KEY_SHORT_CONNECTION, "1")

    header.set_int_header(ttheader.HEADER_KEY_RPC_TIMEOUT, timeout_ms)
    header.set_int_header(ttheader.HEADER_KEY_CONN_TIMEOUT, connect_timeout_ms)

    to_idc = kwargs.get('to_idc')
    if to_idc:
        header.set_int_header(ttheader.HEADER_KEY_TO_IDC, to_idc)

    try:
        transport.open()
        yield TClient(thrift_service, protocol)
    finally:
        transport.close()