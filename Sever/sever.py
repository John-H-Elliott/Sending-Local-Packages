"""
Creates a sever that binds a socket to a given port number.
Then listens to the socket and accepts any incoming requests.

Author: John Elliott    (jel119)
Student Number:         98040483
Date:                   13/08/2021
"""
import os
import socket
import sys
from datetime import datetime


def close_socket(s):
    """
    Closes the given socket and exits the program.

    :param s:       A given socket.
    """
    s.close()
    exit()


def make_bound_socket(port):
    """
    Creates and returns a bound socket to the given port number.
    If it can do this it will print,
    the relevant information and exit() the program.

    :param port:    A valid port number to bind the socket with.
    :return s:      The new bound socket.
    """
    # Trys to create a socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:  # Expects a socket error during creation.
        print(f"Error creating socket: {e}")
        exit()
    else:
        # LocalHost is the current computer
        sever_address = ("localhost", port)

        # Trys to bind the socket with the sever address.
        try:
            s.bind(sever_address)
        except socket.gaierror as e:
            print(f"Addressing error when binding socket: {e}")
            close_socket(s)
        except socket.error as e:
            print(f"Connection issue when binding socket: {e}")
            close_socket(s)
        else:
            return s


def read_socket(s, incoming_s, buffer):
    """
    Get the request file from the client's socket.
    Also, ensures that there is no delay over 1 second or any other errors.

    :param buffer:          The number of bytes to read from the socket.
    :param s:               Sever socket.
    :param incoming_s:      Socket connected with the client.
    :return req_bytes:      The bytearray being sent from the client.
    """
    try:
        # Creates a buffer of a set number of bytes length,
        # that can be received at once.
        res = incoming_s.recv(buffer)
    except socket.timeout as e:  # The socket has timed out.
        print(f"Error due to connection timeout: {e}.\n" +
              f" Current time out set to {incoming_s.gettimeout()}.")
        incoming_s.close()
        close_socket(s)
    except socket.error as e:
        print(f"Socket error occurred during the retrieval of " +
              f"information from connected socket: {e}")
        incoming_s.close()
        close_socket(s)
    else:
        return res


def file_header_valid(header):
    """
    Checks to ensure that the header of the request file sent by,
     the sever is valid.

    :param header:      The request file header sent by the client.
    :return result:     A value representing if the header is valid.
    """
    # Checks to ensure that the file contains the header (5 Bytes of data).
    if len(header) < 5:
        print("The request file sent from the client does " +
              "not have the correct header length.")
        return False
    else:
        magic_num = int.from_bytes(header[:2], "big")
        mode_type = int.from_bytes(header[2:3], "big")
        file_length = int.from_bytes(header[3:5], "big")
        correct_size = (file_length >= 1) or (file_length <= 1024)
        return (magic_num == 0x497E) and (mode_type == 1) and correct_size


def get_data(file_name):
    """
    Gets the data from the file requested by the client and,
    converts it into a byte array.

    :param file_name:       The requested file.
    :return data:           The byte array containing the file data.
    """
    data = bytearray()
    # Gets the current path of this file and the python,
    # scripts name and replaces itself with the given file name.
    script_name = os.path.basename(__file__)
    file_path = __file__[:-len(script_name)] + file_name

    try:
        with open(file_path, "rb") as file:
            # Converts each file to a set of bytes.
            data.extend(file.read())
    except FileNotFoundError:  # Checks that the file exists.
        data = -1
    except PermissionError:  # Checks that the file can be read.
        data = -1
    except OSError:
        data = -1
    return data


def make_res_file(data):
    """
    Makes the response file that is sent back to the client.

    :param data:            The data from the requested file.
    :return res_bytes:      The response file.
    """
    res_bytes = bytearray()
    magic_num = int.to_bytes(0x497E, 2, "big")
    mode_type = int.to_bytes(2, 1, "big")
    res_bytes.extend(magic_num)
    res_bytes.extend(mode_type)
    # Data will equal -1 if there is no file with the requested name,
    # or it can't be opened.
    if data == -1:
        status_code = int.to_bytes(0, 1, "big")
        data_length = int.to_bytes(0, 4, "big")

    else:
        status_code = int.to_bytes(1, 1, "big")
        data_length = int.to_bytes(len(data), 4, "big")

    res_bytes.extend(status_code)
    res_bytes.extend(data_length)
    if data != -1:
        res_bytes.extend(data)
    return res_bytes


def send_response(incoming_s, s, file_name):
    """
    Sends the response file to the client through the connected socket.

    :param incoming_s:      Socket connected with the client.
    :param s:               Main socket of the sever.
    :param file_name:       The name of the requested file.
    """
    data = get_data(file_name)
    try:
        res_bytes = make_res_file(data)
    except OverflowError as e:
        print(f"Can't make request file as the data size is larger "
              f"than the data_length field can store. {e}")
        incoming_s.close()
        close_socket(s)
    byte_total = len(res_bytes)
    bytes_sent = 0
    # Sends the file to the client.
    # Sendall() was going to be used but it had issues were,
    # it did not always send the data before timing out.
    while bytes_sent < byte_total:
        just_sent = incoming_s.send(res_bytes)
        bytes_sent += just_sent

    # Close the connection with the client.
    incoming_s.close()
    # Data will equal -1 if there is no file with,
    # the requested name or it can't be opened.
    if data == -1:
        print("File does not exist locally. Only a File " +
              "Response message has been sent back to the client.")
    else:
        print(f"File transfer complete: Sent a total " +
              f"of {byte_total} bytes sent to client.")


def loop_requests(s):
    """
    Runs the main loop of the sever. Listening for connections,
    with the client and accepting them.
    It will then try and get a request from the client and,
    return a response with the files data.
    :param s:           The sever socket.
    """
    while True:
        # Accepts new connection with client.
        incoming_s, client_address = s.accept()
        # Sets time out to ensure request is sent,
        # without a delay of over 1 second.
        incoming_s.settimeout(1)
        # Gets the clients information from the connected socket.
        c_ip, c_port = incoming_s.getsockname()
        time = datetime.now().time().strftime("%H:%M:%S")
        print(f"{time}: Socket IP {c_ip}, Socket Port {c_port}.")
        header = read_socket(s, incoming_s, 5)

        # Checks to see if received request file is valid.
        if not file_header_valid(header):
            print("Request file sent from client does " +
                  "not have valid header values.")
            incoming_s.close()
            # As it is not a valid file it goes back into the loop.
            continue

        data_length = int.from_bytes(header[3:5], "big")
        byte_name = read_socket(s, incoming_s, data_length)
        # Checks the file name length matches the given length.
        if len(byte_name) != data_length:
            print("Request file sent filename byte length does not " +
                  "match file length value given in the header.")
            # As it is not a valid file it goes back into the loop.
            incoming_s.close()
        else:
            file_name = byte_name.decode("utf-8")
            send_response(incoming_s, s, file_name)


def main(argv):
    """
    Main function run during the deployment of the Sever side system.

    :param argv:        The arguments passed through the command line.
    """
    # Checks only one parameters is entered.
    if len(argv) != 2:
        print(f"{len(argv) - 1} parameters entered while only 1 required.")
        exit()

    # Gets the first input, port number, from the command line.
    port = int(argv[1])

    # Checks that the port number is in a range which,
    # is can be bound to a socket.
    if (port < 1024) or (port > 64000):
        print(f"Port value: {port} is out of range.")
        exit()
    s = make_bound_socket(port)

    # Trys to set socket to listening.
    try:
        # Allows only one unaccepted connection,
        # before refusing new connections.
        s.listen(1)
    except socket.error as e:
        print(f"Error when setting socket to listening: {e}")
        close_socket(s)
    
    loop_requests(s)


if __name__ == "__main__":
    main(sys.argv)
