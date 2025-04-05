import typing
import time
from pymavlink import mavutil
import dataclasses

@dataclasses.dataclass
class StreamItem:
    name: str
    fn: typing.Optional[typing.Callable]
    frequency: float
    next_send_t: typing.Optional[float] = 0
    period: typing.Optional[float] = None

    def __post_init__(self):
        self.period = 1 / self.frequency

def main():
    port = "udpout:localhost:14540"
    master = mavutil.mavlink_connection(port, source_system=255, source_component=0, dialect="custom")

    heartbeat = lambda: master.mav.heartbeat_send(0)
    balloon_report = lambda: master.mav.balloon_report_send(0, 0, 0, 0, 0, 0)

    streams = [
        StreamItem("heartbeat", heartbeat, 1),
        StreamItem("balloon_report", balloon_report, 10),
    ]

    last_status_print_time = time.time()
    msg_counter = 0
    msg_recv_counter = 0
    msg_bad_data_recv_counter = 0
    while True:
        t = time.time()
        for si in streams:
            if si.next_send_t < t:
                si.fn()
                msg_counter += 1
                si.next_send_t = t + si.period

        dt = t - last_status_print_time
        if dt > 1.0:
            msgs = msg_counter / dt
            bytes_sent = master.mav.total_bytes_sent / dt / 1024.0
            master.mav.total_bytes_sent = 0
            print(f"Transmitted {msgs:.2f} msg/s, {bytes_sent:.2f} KiB/s ")
            last_status_print_time = t
            msg_counter = 0
            print(
                f"Msgs received: {msg_recv_counter / dt:.2f} msg/s, bad data: {msg_bad_data_recv_counter / dt:.2f}/s"
            )
            msg_recv_counter = 0
            msg_bad_data_recv_counter = 0

        # On linux, the timeout needs to be tiny, on windows it can be larger
        msgs_recv = master.recv_match(timeout=0.0001)
        if msgs_recv:
            for m in msgs_recv:
                if m.get_type() == "BAD_DATA":
                    msg_bad_data_recv_counter += 1
                else:
                    msg_recv_counter += 1

if __name__ == "__main__":
    main()
