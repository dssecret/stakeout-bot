# Installation Instructions for Stakeout Bot

All commands are run on the Command Prompt unless otherwise specified. NOTE: I have not provided full details on how 
to install some of these because the Linux and Windows installation directions are different.

## Python
The bot requires Python 3.7 or greater. If the installed version is less than 3.7, the bot will not launch.

## Installing Python
Python can be installed either with the Python installer or from the Microsoft Store.

### Installer
More details can be found [here](https://docs.python.org/3/using/windows.html#installation-steps).

1. install the Python installer (for a version of 3.7 or greater) from https://www.python.org/downloads/windows/
2. Select "Install Now" if the bot is going to be run manually. If the bot is going to be set up for auto-launch, 
   select "Customize installation" a nd see the above link.
3. Remove the MAX_Path limit via https://docs.python.org/3/using/windows.html#installation-steps

### Microsoft Store (Not Recommended)
1. Open the Microsoft Store.
2. Search for Python
3. Chose a version. The version must be 3.7 or greater though (due to how the bot is coded).
4. Run `python --version` or `python3 --version` if the former does not work (if the former does not work, then all 
   `python` and `pip` commands with become `python3` and `pip3`).
5. Make sure that you have pip installed with either `pip --version` or `pip3 --version` depending on the above.

## Git
1. Check if Git is already installed on the machine with `git version`. If git is installed, this set of instructions 
   can be skipped.
2. Download the latest [Git for Windows Installer](https://gitforwindows.org/).
3. Follow the instructions provided by the installer.
4. Open Git Bash (or Command Prompt if you selected that during installation) and run `git version` to
   verify that Git is installed properly.
   
## Cloning The Project
If Git is set up to use Command Prompt, use Command Prompt; otherwise use Git Bash for this.

1. Navigate to the root directory where the project will be located with `ls` to list the current directory and `cd` 
   to change directory (e.g. to go to `Documents`, you'd do `ls Documents`).
2. Clone the project with `git clone https://github.com/dssecret/stakeout-bot.git`

## Virtual Environment
The package required for this should be installed by default. More information of setting up virtual environments 
can be found [here](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments).

1. Change your current directory to inside the stakeout-bot directory.
2. Run `python -m venv venv` (or python3 if required from above) which will create the virtual environment.
3. Activate the virtual environment by running `venv\Scripts\activate.bat`.
4. Install the required packages with `pip install -r requirements.txt`.

## Setting Up the Bot
1. Go to [Discord's Developer Page](https://discord.com/developers/applications) and create a new application. 
   Choose a name for the bot.
2. Go to the bot tab and create a bot (you can also change the name of the bot here).
3. Generate an OAUTH invite link for the bot under the OAuth2 tab. Under the URL generator, select bot for the scope 
   and then choose Send Messages, View Channels, and Manage Channels for the bot permissions (although Administrator 
   will also work fine by itself).
4. Go to the link and invite the bot to the specific server.
5. Run `python __init__.py` (or python3 if required from above)
6. If this is the first time the bot is being set up (or the `config.json` file has been deleted), the bot will ask 
   for the bot token which can be found under the bot tab in Discord Developer Applications. Once the bot token has 
   been entered, you will need to rerun the bot with the above command; this will start the bot.
7. Use the `!config` command, set up the configuartion for the bot. You can use the `!help` and `!help config` to see 
   the various options for the configuration.

## Other Setup Stuff
 - Making the bot start upon Windows start.
 - You can update the bot by running `git pull` in the directory where the bot is located.