**************************************************
How to Pair a Bluetooth Device on the Command Line
**************************************************

On the Raspberry Pi command line type the following.

Try to auto pair the controllor first. Near L2 use a paper clip and insert it
in the tiny hole on the back. This will reset the controllor if it's been
previously paired to another device. Then connect the controllor via one of the
RPIs USB connectors. Then run the command below to see if it auto regestered.

.. code-block:: console

   $ bluetoothctl devices

   Device 30:EC:00:2F:8C:3B Wireless Controller

If your controllor auto registered it should return a line similar to the one
above. If not then pair using the method below.

.. code-block:: console

    $ bluetoothctl

You will get a ``[bluetooth]#`` command line, then type the following commands.

.. code-block:: console

   [bluetooth]# power on
   [bluetooth]# agent on
   [bluetooth]# default-agent
   [bluetooth]# pairable on
   [bluetooth]# scan on

   Hold the SHARE ther press and hold the PS button until the light rapidly
   flashes white. You should see something like the next line within other
   lines.

   [NEW] Device 02:34:FE:08:19:FA 02-34-FE-08-19-FA
   [NEW] Controller B8:27:EB:CF:5A:FE Discovering: yes *** THE ONE YOU WANT ***
   [CHG] Device 40:F4:C9:4E:29:ED RSSI: 0xffffffbd (-67)
   
   [bluetooth]# pair B8:27:EB:CF:5A:FE
   [bluetooth]# trust B8:27:EB:CF:5A:FE
   [bluetooth]# connect B8:27:EB:CF:5A:FE

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
