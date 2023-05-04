#    @Author: Justin C Presley
#    @Author-Email: justincpresley@gmail.com
#    @Project: NDN State Vector Sync Protocol
#    @Source-Code: https://github.com/justincpresley/ndn-python-svs
#    @Pip-Library: https://pypi.org/project/ndn-svs
#    @Documentation: https://ndn-python-svs.readthedocs.io

# Basic Libraries
from typing import List
import struct
# NDN Imports
from ndn.encoding import Component, TlvModel, BytesField, UintField, RepeatedField, ModelField
from ndn.encoding import get_tl_num_size, write_tl_num, parse_tl_num
# Custom Imports
from .tlv import SVSyncTlvTypes

# Class Type: an enumeration struct
# Class Purpose:
#   to hold info about a singular node within the vector.
class StateVectorComponentModel(TlvModel):
    nid = BytesField(SVSyncTlvTypes.VECTOR_KEY.value)
    seqno = UintField(SVSyncTlvTypes.VECTOR_VALUE.value)

# Class Type: an custom tlv model class
# Class Purpose:
#   to contain all the info of a state vector.
class StateVectorModel:
    value:List[StateVectorComponentModel]
    def __init__(self) -> None:
        value = []
    def encode(self) -> bytearray:
        component_wires = [v.encode() for v in self.value]
        length = sum(len(w) for w in component_wires)
        buf_len = length + get_tl_num_size(length) + get_tl_num_size(SVSyncTlvTypes.VECTOR.value)
        ret = bytearray(buf_len)
        pos = write_tl_num(SVSyncTlvTypes.VECTOR.value, ret)
        pos += write_tl_num(length, ret, pos)
        for w in component_wires:
            ret[pos:pos + len(w)] = w
            pos += len(w)
        return ret
    @staticmethod
    def parse(buf):
        # Verify the Type
        typ, pos = parse_tl_num(buf)
        if typ != SVSyncTlvTypes.VECTOR.value:
            return None
        # Check the length
        length, l = parse_tl_num(buf, pos)
        pos += l
        if pos + length != len(buf):
            return None
        # Decode components
        ret = StateVectorModel()
        ret.value = []
        while pos < len(buf):
            # Node ID
            typ, l = parse_tl_num(buf, pos)
            pos += l
            if typ != SVSyncTlvTypes.VECTOR_KEY.value:
                return None
            length, l = parse_tl_num(buf, pos)
            pos += l
            nid = buf[pos:pos + length]
            pos += length
            # Value
            typ, l = parse_tl_num(buf, pos)
            pos += l
            if typ != SVSyncTlvTypes.VECTOR_VALUE.value:
                return None
            length, l = parse_tl_num(buf, pos)
            pos += l
            if length == 1:
                seqno = struct.unpack_from('!B', buf, pos)[0]
            elif length == 2:
                seqno = struct.unpack_from('!H', buf, pos)[0]
            elif length == 4:
                seqno = struct.unpack_from('!I', buf, pos)[0]
            elif length == 8:
                seqno = struct.unpack_from('!Q', buf, pos)[0]
            else:
                return None
            pos += length
            # Append the component
            comp = StateVectorComponentModel()
            comp.nid = nid
            comp.seqno = seqno
            ret.value.append(comp)
        return ret

# Class Type: an API class
# Class Purpose:
#   to allow an easier time to interact with the StateVectorModel class.
class StateVector:
    def __init__(self, component:Component=None) -> None:
        self.vector = StateVectorModel() if not component else StateVectorModel.parse(component)
        self.vector.value = [] if not component else self.vector.value
    def set(self, nid:str, seqno:int) -> None:
        sort = True if not self.has(nid) else False
        if sort:
            svc = StateVectorComponentModel()
            svc.seqno = seqno
            svc.nid = nid.encode()
            index = len(self.vector.value)
            for i, item in enumerate(self.vector.value):
                if bytes(self.vector.value[i].nid).decode().lower() > nid.lower():
                    index = i
                    break
            self.vector.value.insert(index, svc)
        else:
            for i in self.vector.value:
                if bytes(i.nid).decode() == nid:
                    i.seqno = seqno
                    return
    def get(self, nid:str) -> int:
        for i in self.vector.value:
            if bytes(i.nid).decode() == nid:
                return i.seqno
        return 0
    def has(self, nid:str) -> bool:
        return ( nid in self.keys() )
    def to_str(self) -> str:
        stream = ""
        for i in self.vector.value:
            stream = stream + bytes(i.nid).decode() + ":" + str(i.seqno) + " "
        return stream.rstrip()
    def encode(self) -> bytes:
        return self.vector.encode()
    def keys(self) -> List[str]:
        return [bytes(i.nid).decode() for i in self.vector.value]
    def to_component(self) -> Component:
        return self.encode()