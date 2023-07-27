from ...core.message import (
    MessageType,
    MessageRequest,
    MessageResponse,
    MessageBody,
)

class MessageDABase(MessageRequest):
    def __init__(self, device_protocol_version, message_type, body_type):
        super().__init__(
            device_protocol_version=device_protocol_version,
            device_type=0xDA,
            message_type=message_type,
            body_type=body_type
        )

    @property
    def _body(self):
        raise NotImplementedError


class MessageQuery(MessageDABase):
    def __init__(self, device_protocol_version):
        super().__init__(
            device_protocol_version=device_protocol_version,
            message_type=MessageType.query,
            body_type=0x03)

    @property
    def _body(self):
        return bytearray([])


class MessagePower(MessageDABase):
    def __init__(self, device_protocol_version):
        super().__init__(
            device_protocol_version=device_protocol_version,
            message_type=MessageType.set,
            body_type=0x02)
        self.power = False

    @property
    def _body(self):
        power = 0x01 if self.power else 0x00
        return bytearray([
            power, 0xFF
        ])

        
class MessageStart(MessageDABase):
    def __init__(self, device_protocol_version):
        super().__init__(
            device_protocol_version=device_protocol_version,
            message_type=MessageType.set,
            body_type=0x02)
        self.start = False
        self.washing_data = bytearray([])

    @property
    def _body(self):
        if self.start:
            return bytearray([
                0xFF, 0x01
            ]) + self.washing_data
        else:
            # Stop
            return bytearray([
                0xFF, 0x00
            ])


class DAGeneralMessageBody(MessageBody):
    def __init__(self, body):
        super().__init__(body)
        self.power = body[1] > 0
        self.start = True if body[2] in [2, 6] else False
        self.error_code = body[24]
        self.program = int(hex(body[4]),16)
        self.wash_time = body[9]
        self.soak_time = body[12]
        self.dehydration_time = '{:02x}'.format(body[10])[:1]
        self.dehydration_speed = int('{:02x}'.format(body[6])[:1],16)
        self.rinse_count = '{:02x}'.format(body[10])[1:]
        self.rinse_level = int('{:02x}'.format(body[5])[:1],16)
        self.wash_level = '{:02x}'.format(body[5])[1:]
        self.wash_strength = int('{:02x}'.format(body[6])[1:],16)
        self.softener = int('{:02x}'.format(body[8])[:1],16)
        self.detergent = int('{:02x}'.format(body[8])[1:],16)
        self.washing_data = body[3:15]
        self.progress = 0
        for i in range(1, 7):
            if (body[16] & (1 << i)) > 0:
                self.progress = i
                break
        if self.power:
            self.time_remaining = body[17] + body[18] * 60
        else:
            self.time_remaining = None


class MessageDAResponse(MessageResponse):
    def __init__(self, message):
        super().__init__(message)
        body = message[self.HEADER_LENGTH: -1]
        if self._message_type in [MessageType.query, MessageType.set] or \
                (self._message_type == MessageType.notify1 and self._body_type == 0x04):
            self._body = DAGeneralMessageBody(body)
        self.set_attr()
