#################################################################################
# A Chat Client application. Used in the course IELEx2001 Computer networks, NTNU
#################################################################################

from socket import *

# --------------------
# Constants
# --------------------
# The states that the application can be in
states = [
    "disconnected",  # Connection to a chat server is not established
    "connected",  # Connected to a chat server, but not authorized (not logged in)
    "authorized"  # Connected and authorized (logged in)
]
TCP_PORT = 1300  # TCP port used for communication
SERVER_HOST = "datakomm.work"  # Set this to either hostname (domain) or IP address of the chat server

# --------------------
# State variables
# --------------------
current_state = "disconnected"  # The current state of the system
# When this variable will be set to false, the application will stop
must_run = True
# Use this variable to create socket connection to the chat server
# Note: the "type: socket" is a hint to PyCharm about the type of values we will assign to the variable
client_socket = None  # type: socket


def quit_application():
    """ Update the application state so that the main-loop will exit """
    # Make sure we reference the global variable here. Not the best code style,
    # but the easiest to work with without involving object-oriented code
    global must_run
    must_run = False


def send_command(command, arguments):
    global client_socket
    """
    Send one command to the chat server.
    :param command: The command to send (login, sync, msg, ...(
    :param arguments: The arguments for the command as a string, or None if no arguments are needed
        (username, message text, etc)
    :return:
    """
    command_to_send = (command + " " + arguments + "\n")  # takes the arguments and adds a \n to the end to follow
    # protocol
    client_socket.send(command_to_send.encode())  # sends encoded command to server


def read_one_line(sock):
    """
    Read one line of text from a socket
    :param sock: The socket to read from.
    :return:
    """
    newline_received = False
    message = ""
    while not newline_received:
        character = sock.recv(1).decode()
        if character == '\n':
            newline_received = True
        elif character == '\r':
            pass
        else:
            message += character
    return message


def get_servers_response():
    """
    Wait until a response command is received from the server
    :return: The response of the server, the whole line as a single string
    """
    return read_one_line(client_socket)  # returns the server response


def connect_to_server():
    # Must have these two lines, otherwise the function will not "see" the global variables that we will change here
    global client_socket
    global current_state
    client_socket = socket(AF_INET, SOCK_STREAM)  # creates socket: clinet_socket

    try:
        client_socket.connect((SERVER_HOST, TCP_PORT))  # connects client_socket to datakomm.work on port 1300
        current_state = "connected"  # changes state to connected
        print(current_state)
    except IOError as i:
        print("Error: ", i)



    client_socket.send("sync\n".encode())  # sends syncmode request
    response = get_servers_response()  # get the response from the server, we expect it to be "modeok"
    if response == "modeok":
        print(response)
        return
    else:
        print("CONNECTION NOT IMPLEMENTED!")


def disconnect_from_server():

    global client_socket
    global current_state
    client_socket.close()  # closes the socket
    current_state = "disconnected"  # changes state to disconnected
    print(current_state)


def login():
    global current_state
    username = input("Enter desired username: ")  # get username from keyboard
    send_command("login", username)  # send " login <username>\n " as specified in protocol
    current_state = "authorized"  # changes global variable current_state to "authorized"
    login_status = get_servers_response()  # get response from server if username is ok
    if login_status == "loginok":  # the expected status message from server
        print("Login OK")
    else:  # if username is taken, send server response to terminal and return to menu
        print(login_status)
        return


def send_public_message():
    public_message = input("Enter public message: ")
    send_command("msg", public_message)  # sends input from keyboard as " msg <message text>\n " as in protocol
    public_message_state = get_servers_response()  # gets answer from server when message is sent
    message_state = ""
    rc = 0  # running count for checking if we get the msgok response from the server
    for i in public_message_state:
        if rc > 4:
            break
        message_state += i
        rc += 1
    if message_state == "msgok":
        print("Message successfully sent!")  # if message is as expected, print this
    else:  # if something else, print error message
        print(public_message_state)


def get_users_list():
    # from wireshark: command "users" returns a list of every user online
    send_command("users", "")
    users = get_servers_response()
    rc = 0  # running count for changing the way the list of online users is shown for the user
    formated_list = ""
    for i in users:
        if rc > 5:
            formated_list += i
        rc += 1

    print("The users online are: ")
    print(formated_list)

    # prints the servers response from command "users"


def send_private_message():
    get_users_list()  # get the list of onlie users
    private_message_recipient = input("Write the username of the persons DM's you want to slide into: ")
    print("Write the message you want to send to " + private_message_recipient + " here:")
    private_message_input = input()
    final_private_message = str(
        private_message_recipient + " " + private_message_input)  # combine the user you want to message and the
    # message you want to send
    send_command("privmsg", final_private_message)
    private_message_state = get_servers_response()  # get server response
    if private_message_state == "msgok 1":  # if we get the response we expected, else print error message
        print("DM sent successfully")
    else:
        print(private_message_state)


def get_inbox():
    global client_socket
    """
    sends "inbox" command and server responds with "inbox N\n", where N is the number of messages
    then in the next packet
    """
    send_command("inbox", "")
    response = get_servers_response()
    rc = 0  # Running count to extract the number of items in inbox response from server "inbox N\n"
    for i in response:
        if rc > 6:  # number 7 in server response is N
            messages = i
            break
        rc += 1
    print("You have " + i + " mail(s)")
    number_of_messages = int(i)  # hardcode to get "i" to int so it will work in range
    number_of_messages = range(number_of_messages)
    for z in number_of_messages:
        print(read_one_line(client_socket))  # prints each line from packet with messages from server
    return


"""
The list of available actions that the user can perform
Each action is a dictionary with the following fields:
description: a textual description of the action
valid_states: a list specifying in which states this action is available
function: a function to call when the user chooses this particular action. The functions must be defined before
            the definition of this variable
"""
available_actions = [
    {
        "description": "Connect to a chat server",
        "valid_states": ["disconnected"],
        "function": connect_to_server
    },
    {
        "description": "Disconnect from the server",
        "valid_states": ["connected", "authorized"],
        "function": disconnect_from_server
    },
    {
        "description": "Authorize (log in)",
        "valid_states": ["connected", "authorized"],
        "function": login
    },
    {
        "description": "Send a public message",
        "valid_states": ["connected", "authorized"],
        "function": send_public_message
    },
    {
        "description": "Send a private message",
        "valid_states": ["authorized"],
        "function": send_private_message
    },
    {
        "description": "Read messages in the inbox",
        "valid_states": ["connected", "authorized"],
        "function": get_inbox
    },
    {
        "description": "See list of users",
        "valid_states": ["connected", "authorized"],
        "function": get_users_list
    },
    {
        "description": "Get a joke",
        "valid_states": ["connected", "authorized"],
        # TODO - optional step - implement the joke fetching from the server.
        # Hint: this part is not described in the protocol. But the command is simple. Try to find
        # out how it works ;)
        "function": None
    },
    {
        "description": "Quit the application",
        "valid_states": ["disconnected", "connected", "authorized"],
        "function": quit_application
    },
]


def run_chat_client():
    """ Run the chat client application loop. When this function exists, the application will stop """

    while must_run:
        print_menu()
        action = select_user_action()
        perform_user_action(action)
    print("Thanks for watching. Like and subscribe! 👍")


def print_menu():
    """ Print the menu showing the available options """
    print("==============================================")
    print("What do you want to do now? ")
    print("==============================================")
    print("Available options:")
    i = 1
    for a in available_actions:
        if current_state in a["valid_states"]:
            # Only hint about the action if the current state allows it
            print("  %i) %s" % (i, a["description"]))
        i += 1
    print()


def select_user_action():
    """
    Ask the user to choose and action by entering the index of the action
    :return: The action as an index in available_actions array or None if the input was invalid
    """
    number_of_actions = len(available_actions)
    hint = "Enter the number of your choice (1..%i):" % number_of_actions
    choice = input(hint)
    # Try to convert the input to an integer
    try:
        choice_int = int(choice)
    except ValueError:
        choice_int = -1

    if 1 <= choice_int <= number_of_actions:
        action = choice_int - 1
    else:
        action = None

    return action


def perform_user_action(action_index):
    """
    Perform the desired user action
    :param action_index: The index in available_actions array - the action to take
    :return: Desired state change as a string, None if no state change is needed
    """
    if action_index is not None:
        print()
        action = available_actions[action_index]
        if current_state in action["valid_states"]:
            function_to_run = available_actions[action_index]["function"]
            if function_to_run is not None:
                function_to_run()
            else:
                print("Internal error: NOT IMPLEMENTED (no function assigned for the action)!")
        else:
            print("This function is not allowed in the current system state (%s)" % current_state)
    else:
        print("Invalid input, please choose a valid action")
    print()
    return None


# Entrypoint for the application. In PyCharm you should see a green arrow on the left side.
# By clicking it you run the application.
if __name__ == '__main__':
    run_chat_client()
