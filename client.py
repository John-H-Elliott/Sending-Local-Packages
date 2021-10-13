"""
Creates a client that access a given sever through a IP/DNS address and port number.
It then requests a file from the sever after ensuring its information is correct.
It also ensures that the requested file doesn't already locally exist.

Author: John Elliott    (jel119)
Student Number:         98040483
Date:                   13/08/2021
"""
import socket
import sys
import os


def close_socket(s):
    """
    Closes the given socket and exits the program.

    :param s:       A given socket.
    """
    s.close()
    exit()


def get_ip_and_socket(s_address):
    """
    Ensures IP is correct and sets up the socket used by the client.

    :param s_address:   The address of the sever.
    :return s_ip, s:    Returns the sever address and clients socket.
    """
    # Trys to convert a sever address if given as hostname to IPv4.
    try:
        # Returns an IPv4 address if given a hostname else returns any IPv4
        # address given unchanged.
        s_ip = socket.gethostbyname(s_address)
    except socket.error as e:  # Expects a error when converting address.
        print(f"Issues getting a valid IPv4 address: {e}")
        exit()
    else:
        # Trys to create a socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)  # sets a timeout of one second.
        except socket.error as e:  # Expects a error during creation.
            print(f"Error creating socket: {e}")
            exit()
        else:
            return s_ip, s


def sever_connect(s_ip, s_port, s):
    """
    Connects from the client socket to the sever socket.

    :param s_ip:        The IPv4 address of the sever.
    :param s_port:      The port of the sever.
    :param s:           The clients socket.
    """
    sever_address = (s_ip, s_port)
    # Trys to connect to sever
    try:
        s.connect(sever_address)
    except socket.error as e:  # Expects a socket error during connection.
        print(f"Error connecting to sever: {e}")
        close_socket(s)


def make_request_file(file):
    """
    Turns a file name into a bytearray request for the file.

    :param file:            Name of the file being requested.
    :return req_bytes:      The bytearray request being sent to the sever.
    """
    req_bytes = bytearray()
    magic_num = int.to_bytes(0x497E, 2, "big")
    mode_type = int.to_bytes(1, 1, "big")
    req_bytes.extend(magic_num)
    req_bytes.extend(mode_type)

    # Checks that the file is of a valid size.
    file_bytes = bytes(file, 'utf-8')
    file_size = len(file_bytes)
    if (file_size < 1) or (file_size > 1024):
        print(f"Filename contains: {file_size} bytes long.\n" +
              "It must be between the byte range 1 to 1024 to be valid.")
        exit()
    req_bytes.extend(int.to_bytes(file_size, 2, "big"))
    req_bytes.extend(file_bytes)

    return req_bytes


def read_socket(s, buffer):
    """
    Gets the response file sent from the sever.

    :param buffer:          The number of bytes to read from the socket.
    :param s:               The clients socket.
    :return res:            The data attend from the socket.
    """
    try:
        # Creates a buffer of a set number of bytes length,
        # that can be received at once.
        res = s.recv(buffer)
    except socket.timeout as e:  # The socket has timed out.
        print(f"Error due to connection timeout: {e}\n" +
              f"Current time out set to {s.gettimeout()}.")
        close_socket(s)
    except socket.error as e:
        print(f"Socket error occurred during the retrieval of " +
              f"information from connected socket: {e}")
        close_socket(s)
    else:
        return res


def file_checker(header, s):
    """
    Checks to ensure that the response file is valid.
    It will print any errors and close the client socket if they occur.

    :param header:          The header of the file sent from the sever.
    :param s:               The clients socket.
    """
    # Checks to ensure that the file has a header of the correct length.
    if len(header) < 8:
        print("The response file sent from the sever does " +
              "not have the correct header length.")
        close_socket(s)
    magic_num = int.from_bytes(header[:2], "big")
    mode_type = int.from_bytes(header[2:3], "big")
    status_code = int.from_bytes(header[3:4], "big")
    valid_status = (status_code == 0) or (status_code == 1)
    if not ((magic_num == 0x497E) and (mode_type == 2) and valid_status):
        print("Response file sent from sever does not have valid header.")
        close_socket(s)
    # If the statues code is zero the is no file to save so the,
    # client closes the socket and exits the program.
    if status_code == 0:
        print("No file exists with that name on the sever.")
        close_socket(s)


def save_data(name, data_length, s):
    """
    Saves data given by the response file to a file with the same
    name as the one being requested.

    :param name:                The name of the file to store the data.
    :param data_length:         The length of the data (N/o of Bytes).
    :param s:                   The clients socket.
    """
    data = bytearray()
    transfer_running = True
    # Loops until the number of bytes transferred,
    # is at least the data_length.
    while transfer_running:
        data_block = read_socket(s, 4096)
        # Used to determine when no more bytes have come in.
        if len(data_block) == 0:
            transfer_running = False
        else:
            data.extend(data_block)
    if not (len(data) == data_length):
        print("The header value for data length does not match " +
              "the number of bytes received as data.")
        close_socket(s)

    try:
        with open(name, "wb+") as file:  # Creates a new writeable file.
            file.write(data)
    except OSError as e:
        print(f"Error when creating {name}: {e}")
        close_socket(s)
    return len(data)


def resolve_response(header, s, name):
    """
    Will try and resolve the response file given by the sever
    and save any given file data if possible.

    :param header:          The response file header from the sever.
    :param s:               The clients socket
    :param name:            The requested file name.
    """
    file_checker(header, s)

    # Checks that the header value of data length,
    # matches the given length of data.
    data_length = int.from_bytes(header[4:8], "big")
    data_saved = save_data(name, data_length, s)
    # Give a write out of the total number of saved bytes,
    # and close the clients socket.
    print(f"File {name} saved. Number of bytes transferred " +
          f"were {data_saved + len(header)}.")
    close_socket(s)


def main(argv):
    """
    Main function that runs during when a client
    wishes to connect to the sever.

    :param argv:        The arguments passed through the command line.
    """
    # Checks exactly three parameters are entered.
    if len(sys.argv) != 4:
        print(f"{len(argv) - 1} parameters entered while only 3 required.")
        exit()

    # Gets the first input, port number, from the command line.
    s_address = sys.argv[1]
    s_port = int(sys.argv[2])
    file_name = sys.argv[3]

    # Gets the current path of this file and,
    # replaces itself with the given file name.
    script_name = os.path.basename(__file__)
    file_path = __file__[:-len(script_name)] + file_name
    # Checks to see if a file with the same name current exists locally.
    if os.path.isfile(file_path):
        print("File exist locally. To avoid overwriting " +
              "files no connection made.")
        exit()

    # Checks that the port number is in a range,
    # which is can be bound to a socket.
    if (s_port < 1024) or (s_port > 64000):
        print(f"Port value: {s_port} is out of range.")
        exit()

    # Gets key socket parts ready
    s_ip, s = get_ip_and_socket(s_address)
    sever_connect(s_ip, s_port, s)
    # Send file request.
    s.sendall(make_request_file(file_name))
    header = read_socket(s, 8)  # Reads the header.
    if len(header) == 0:
        print("No response file received, probably an error " +
              "in the request file sent.")
    else:
        resolve_response(header, s, file_name)


if __name__ == "__main__":
    main(sys.argv)
