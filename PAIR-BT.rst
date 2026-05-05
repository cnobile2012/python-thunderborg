**************************************************
How to Pair a Bluetooth Device on the Command Line
**************************************************

On the Raspberry Pi command line type the following.

.. code-block:: console

    $ bluetoothctl

You will get a ``[bluetooth]#`` command line, then type the following commands.

.. code-block:: console

   [bluetooth]# pairable on
   Changing pairable on succeeded
   [bluetooth]# discoverable on
   Changing discoverable on succeeded
   [bluetooth]# agent on
   Agent is already registered
   [bluetooth]# default-agent
   Default agent request successful
   [bluetooth]# scan on
   [NEW] Device 7C:C5:35:EA:6F:7E 7C-C5-35-EA-6F-7E
   [CHG] Device 7C:C5:35:EA:6F:7E RSSI: -80
   [NEW] Device 40:1B:5F:E0:4D:E2 Wireless Controller
   [CHG] Device 7C:C5:35:EA:6F:7E RSSI: -89
   [bluetooth]# pair 40:1B:5F:E0:4D:E2
   Attempting to pair with 40:1B:5F:E0:4D:E2
   [CHG] Device 40:1B:5F:E0:4D:E2 Connected: yes
   [CHG] Device 40:1B:5F:E0:4D:E2 UUIDs: 00001124-0000-1000-8000-00805f9b34fb
   [CHG] Device 40:1B:5F:E0:4D:E2 UUIDs: 00001200-0000-1000-8000-00805f9b34fb
   [CHG] Device 40:1B:5F:E0:4D:E2 ServicesResolved: yes
   [CHG] Device 40:1B:5F:E0:4D:E2 Paired: yes
   [agent] Authorize service 00001124-0000-1000-8000-00805f9b34fb (yes/no): yes
   [Wireless Controller]# quit

If any of this fails, and the first command returns:
"bluetooth.service: ConfigurationDirectory 'bluetooth' already exists but the
mode is different. (File system: 755 ConfigurationDirectoryMode: 555).
Run the second and third command.

.. code-block:: console

   $ sudo systemctl status bluetooth
   $ sudo chmod 555 /etc/bluetooth
   $ sudo systemctl restart bluetooth
   $ sudo systemctl status bluetooth  # Make sure the error is gone.

After you type ``scan on`` you will get a listing of all the pairable devices.
In the list find the one you want to pair (in our case the line with Wireless
Controller), then ``[agent]`` line shows up, type yes. The command line prompt
will change to ``[Wireless Controller]`` then type quit. You're done.

.. note::

   On the PS4 Wireless Controller you need to press the **share** button and
   the **Play Station** button at the same time to initiate pairing. You'll get
   a very rapid flashing of the light blue LED then after you type **yes** when
   asked and hit the enter key the LED will turn to a dark blue and you are
   done.
