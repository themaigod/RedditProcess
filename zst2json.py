"""
It is a script to convert zst files to json files.
"""
import json
import os

from datetime import datetime

import zstandard
import argparse
import logging

log = logging.getLogger("bot")
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())


def read_lines_zst(file_name):
    with open(file_name, 'rb') as file_handle:
        buffer = ''
        reader = zstandard.ZstdDecompressor(max_window_size=2 ** 31).stream_reader(file_handle)
        while True:
            chunk = read_and_decode(reader, 2 ** 27, (2 ** 29) * 2)

            if not chunk:
                break
            lines = (buffer + chunk).split("\n")

            for line in lines[:-1]:
                yield line, file_handle.tell()

            buffer = lines[-1]

        reader.close()


def read_and_decode(reader, chunk_size, max_window_size, previous_chunk=None, bytes_read=0):
    chunk = reader.read(chunk_size)
    bytes_read += chunk_size
    if previous_chunk is not None:
        chunk = previous_chunk + chunk
    try:
        return chunk.decode()
    except UnicodeDecodeError:
        if bytes_read > max_window_size:
            raise UnicodeError(f"Unable to decode frame after reading {bytes_read:,} bytes")
        log.info(f"Decoding error with {bytes_read:,} bytes, reading another chunk")
        return read_and_decode(reader, chunk_size, max_window_size, chunk, bytes_read)


def zst2json(zst_file, json_file):
    """
    Convert zst file to json file.
    """
    total_lines = 0
    bad_lines = 0
    file_bytes_processed = 0
    file_size = os.path.getsize(zst_file)

    begin_time = datetime.now()
    using_time = 0
    remaining_time = 0
    # use list to store the data
    data = []
    file_bytes_processed = 0
    for line, file_bytes_processed in read_lines_zst(zst_file):
        total_lines += 1
        if total_lines % 100000 == 0:
            using_time = datetime.now() - begin_time
            remaining_time = using_time * (file_size / file_bytes_processed - 1)
            using_time = str(using_time)
            remaining_time = str(remaining_time)
            # log.info(
            #     f"{using_time:,} : {remaining_time:,} : {total_lines:,} : {bad_lines:,} : {file_bytes_processed:,}:{(file_bytes_processed / file_size) * 100:.0f}%")
            log.info(
                f"{using_time} : {remaining_time} : {total_lines} : {bad_lines} : {file_bytes_processed} : {(file_bytes_processed / file_size) * 100:.0f}%"
            )
        try:
            json_line = json.loads(line)
            data.append(json_line)
        except json.decoder.JSONDecodeError:
            bad_lines += 1

    # write the data to json file
    with open(json_file, 'w') as f:
        json.dump(data, f)

    log.info("Finished")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert zst file to json file.')
    parser.add_argument('--zst_file', type=str, default='scripts/output/XboxSeriesX_submissions.zst', help='zst file path')
    parser.add_argument('--json_file', type=str, default='json_output/XboxSeriesX_submissions.json', help='json file path')
    args = parser.parse_args()
    zst2json(args.zst_file, args.json_file)
