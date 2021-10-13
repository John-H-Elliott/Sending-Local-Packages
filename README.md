# **Sending-Local-Packages**

## To start the **Sever**

---

1.
    First open the console to the location of the **["sever.py"](Sever/sever.py)** file.

2.
    Next, run the code;

    ```Console
    sever.py {port_number}
    ```

    Where {_port_number_} is between **1024** and **64000**.

If any errors occur they should be printed out to the console for further diagnostics.

## To start the **Client**

---

1.
    First open the console to the location of the **["client.py"](client.py)** file.

2.
    Next, run the code;

    ```Console
    client.py localhost {port_number} {file_name}
    ```

    Where {_port_number_} is the same as the sever and {_file_name_} is the name of the file being downloaded. Which must also be in the [sever location](Sever/).

If any errors occur they should be printed out to the console for further diagnostics.

---

### Result

After this the file from [Sever directory](Sever/), if it existed, should be generated in the location of the [client](client.py).
