"""
Quick script to use GnuPG to manage PGP keys and encrypt/decrypt messages.

Requires GnuPG to be installed on the system. On macOS, you can install it using Homebrew:
- `brew install gnupg`

Note: Still debugging several issues. This script is a work in progress.
"""

import subprocess
import sys

#################################
###     Dependency checks     ###
#################################

failed = False

# Check if GnuPG is installed
try:
    # Check if xcdoe-select is installed
    subprocess.run(['xcode-select', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

except FileNotFoundError:
    print("Xcode Command Line Tools are not installed. Please install Xcode Command Line Tools before running this script.")
    print("On macOS, you can install it using `xcode-select --install`")
    failed = True

try:
    # Check if GnuPG is installed
    subprocess.run(['gpg', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

except FileNotFoundError:
    print("GnuPG is not installed. Please install GnuPG before running this script.")
    print("On macOS, you can install it using Homebrew: `brew install gnupg`")
    failed = True

if failed:
    exit(1)

#############################
###     Configuration     ###
#############################

# Uses RSA 4096-bit keys that expire in 2 years.
KEY_TYPE = "RSA"
KEY_LENGTH = 4096
KEY_EXPIRE = "2y"

# Files to save the public key and pass phrase
PUB_KEY_FILE = "public_key.asc"
PASS_PHRASE_FILE = "pass_phrase.txt"

#####################
###     Setup     ###
#####################

# Get existing user name and email
def get_user_name_and_email():
    # Step 1: List the secret keys to ensure we only get the local user's key(s)
    result = subprocess.run(['gpg', '--list-secret-keys'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check if the command ran successfully and if any keys were listed
    if result.returncode == 0:
        output = result.stdout.decode()

        # Parse the output to find the name and email in the key list
        identities = []
        for line in output.splitlines():
            if "uid" in line:
                start_name = line.find(" ")
                start_email = line.find("<")
                end_email = line.find(">")
                if start_name != -1 and start_email != -1 and end_email != -1:
                    name = line[start_name:start_email].strip()
                    email = line[start_email+1:end_email]
                    identities.append((name, email))

        # If any identities (name, email) were found, return the first one (or list of them)
        if identities:
            # Default to the first name-email pair, could return list if needed
            return identities[0]

    else:
        print(f"Warning: error listing GPG secret keys: {result.stderr.decode()}")

    # Step 2: If no name/email was found, prompt the user to set them up
    return first_time_setup()

# First time setup (if no user name and email are found)
# Sets up private and public PGP keys + password (if wanted)
def first_time_setup():
    print("Looks like this is your first time running the tool. Let's set up your GPG key.")
    name = input("Please enter your real name:\n")
    print("Please enter your email address to configure your first GPG key:")
    email = input("(Note: this is public, but it won't be used to send you emails)\n")

    # Get or set the pass phrase
    pass_phrase = get_or_set_user_pass_phrase()

    # Command to generate the PGP key
    cmd = [
        'gpg', '--batch', '--gen-key', '--yes'
    ]

    # GPG parameters for key generation
    if pass_phrase:
        key_params = f"""
        Key-Type: {KEY_TYPE}
        Key-Length: {KEY_LENGTH}
        Subkey-Type: {KEY_TYPE}
        Subkey-Length: {KEY_LENGTH}
        Name-Real: {name}
        Name-Email: {email}
        Expire-Date: {KEY_EXPIRE}
        Passphrase: {pass_phrase}
        %commit
        """
    else:
        key_params = f"""
        Key-Type: {KEY_TYPE}
        Key-Length: {KEY_LENGTH}
        Subkey-Type: {KEY_TYPE}
        Subkey-Length: {KEY_LENGTH}
        Name-Real: {name}
        Name-Email: {email}
        Expire-Date: {KEY_EXPIRE}
        %commit
        """

    try:
        # Run the gpg command and pass the key parameters
        result = subprocess.run(
            cmd,
            input=key_params.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if result.returncode == 0:
            print("Key generation successful!")

            print_pgp_public_keys(email)

        else:
            print(f"Error generating PGP key pair: {result.stderr.decode()}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


    return name, email

# Get the pass phrase if it's loaded from a file.
def get_user_pass_phrase():

    # Check if the pass phrase is already saved in a file
    try:
        with open(PASS_PHRASE_FILE, "r") as f:
            pass_phrase = f.read().strip()
            # Pass phrased loaded from file
            if pass_phrase:
                return pass_phrase
            else:
                return None

    except FileNotFoundError:
        # No pass phrase file found; pass phrase will be entered manually
        return None

# Like get, but optionally configure the pass phrase as plain text in PASS_PHRASE_FILE.
# Warning: this is not secure, but it is safe as long as no one has read access to your filesystem.
# If you want maximum security, enter the pass phrase manually each time.
def get_or_set_user_pass_phrase():
    pass_phrase = get_user_pass_phrase()
    if pass_phrase:
        return pass_phrase

    print("Do you want to save a pass phrase as plain text?")
    print("This is less secure, but it can be convenient for testing.")
    save_pass = input("Enter 'y' to save the pass phrase, or any other key to enter it manually:\n")

    if save_pass.lower() != 'y':
        print("Got it. To change this setting later, use the `s` option to re-run setup.")
        return None

    print(f"Saving pass phrase to {PASS_PHRASE_FILE}...")
    pass_phrase = input("Enter your pass phrase (appears in plain text):\n")

    if not pass_phrase:
        print("Pass phrase cannot be empty.")
        return None

    try:
        with open("pass_phrase.txt", "w") as f:
            f.write(pass_phrase)
        print("Pass phrase saved successfully.")
        print("Make sure you keep this file safe!")
        print("To change the pass phrase, delete the pass_phrase.txt file.")
        return pass_phrase

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

# Set up PGP keys
# Also can be used to configure the user, name, or password
def setup_pgp_keys():
    print("Running setup.")
    # Step 1: call get_user_name_and_email, which will call first_time_setup if needed.
    _user, _email = get_user_name_and_email()
    # Step 2: TODO
    # A limitation is that if password was NOT saved to a file, we should really re-ask here.
    # For now, we just re-ask twice in some cases.
    _pass = get_or_set_user_pass_phrase()

# Print public key(s)
def print_pgp_public_keys(email):

    # Command to export the public key
    export_cmd = ['gpg', '--armor', '--export', email]
    export_result = subprocess.run(
        export_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    if export_result.returncode == 0:
        public_key = export_result.stdout.decode()
        print("\nPublic PGP Key (post this on your website or send it to your friend):\n")
        print(public_key)

        print("Saving public key to a file for convenient sharing...")
        with open(PUB_KEY_FILE, "w") as f:
            f.write(public_key)
        print(f"Public key saved successfully to {PUB_KEY_FILE}.")

    else:
        print(f"Error exporting PGP public key: {export_result.stderr.decode()}")

# Reset the GPG configuration
def reset_all_keys():
    # Warning: this permanently deletes all keys!
    print("Warning: this will permanently delete all GPG keys from your keyring.")
    print("Existing encryption keys or encrypted messages will be lost.")
    print("This operation cannot be undone.")
    confirm = input("Are you sure you want to continue? (y/n):\n")

    if confirm.lower() != 'y':
        print("Aborting operation.")
        return

    # Get user name
    name, _ = get_user_name_and_email()
    if not name:
        print("No user name found. Aborting operation.")
        return

    # Command to delete all keys
    cmd = ['gpg', '--delete-secret-and-public-keys', '--yes', name]

    try:
        # Step 1: Delete all secret (private) keys
        print("Deleting all secret (private) keys...")
        result_secret = subprocess.run(['gpg', '--delete-secret-keys', '--yes', '--batch'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result_secret.returncode != 0:
            print(f"Error deleting secret keys: {result_secret.stderr.decode()}")

        # Step 2: Delete all public keys
        print("Deleting all public keys...")
        result_public = subprocess.run(['gpg', '--delete-keys', '--yes', '--batch'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result_public.returncode != 0:
            print(f"Error deleting public keys: {result_public.stderr.decode()}")

        # Step 3: Clear the trust database
        print("Clearing trust database...")
        result_trust = subprocess.run(['gpg', '--delete-trustdb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result_trust.returncode != 0:
            print(f"Error clearing trust database: {result_trust.stderr.decode()}")

        print("All GPG keys have been permanently deleted.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

##########################
###     Encryption     ###
##########################

def register_recipient():
    print("Enter the recipient's public key (paste the entire key, then press Ctrl+D to finish):")

    # Read multiline input for the recipient's public key
    public_key = sys.stdin.read()

    try:
        # Import the public key into the GPG keyring
        result = subprocess.run(
            ['gpg', '--import'],
            input=public_key.encode(),  # Provide the public key as input
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if result.returncode == 0:
            print("Recipient's public key has been successfully imported.")

        else:
            print(f"Error importing public key: {result.stderr.decode()}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def list_recipients():
    # List public keys available in the keyring
    result = subprocess.run(['gpg', '--list-keys'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        print("Error listing public keys:", result.stderr.decode())
        return []

    # Decode the output and extract email addresses
    output = result.stdout.decode()
    keys = []
    for line in output.splitlines():
        if "uid" in line:
            # Extract email from the uid line (between < and >)
            start = line.find("<")
            end = line.find(">")
            if start != -1 and end != -1:
                email = line[start+1:end]
                keys.append(email)

    return sorted(set(keys))

def select_recipient():
    recipients = list_recipients()

    if not recipients:
        print("No recipients found in the keyring; let's add one.")
        register_recipient()
        # Call the function again to re-list the recipients
        return select_recipient()

    # Display the recipient list
    print("Select a recipient, or 'r' to register a new recipient:")
    for i, recipient in enumerate(recipients, start=1):
        print(f"{i}: {recipient}")

    raw_selection = input("Enter the recipient number:\n").strip().lower()

    if raw_selection == 'r':
        register_recipient()
        # Call the function again to re-list the recipients
        return select_recipient()

    try:
        selection = int(raw_selection)
        if 1 <= selection <= len(recipients):
            return recipients[selection - 1]
        else:
            print("Invalid selection.")
            return None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None

def encrypt_message():
    recipient = select_recipient()

    if recipient is None:
        return

    print(f"Selected recipient: {recipient}")
    print("Enter the message you want to encrypt (paste the message, then press Ctrl+D to finish):")

    # Read multiline input for the message to be encrypted
    message = sys.stdin.read()

    try:
        # Run the gpg command to encrypt the message
        result = subprocess.run(
            ['gpg', '--armor', '--encrypt', '--recipient', recipient],
            input=message.encode(),  # Provide the message as input
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if result.returncode == 0:
            encrypted_message = result.stdout.decode()
            print("\nEncrypted message:\n")
            print(encrypted_message)
        else:
            print(f"Error encrypting message: {result.stderr.decode()}")

    except Exception as e:
        print(f"Encryption failed or crashed: {str(e)}")

##########################
###     Decryption     ###
##########################

# Define decryption function
def decrypt_message():
    print("Enter the encrypted message (paste the entire message, then press Ctrl+D to finish):")

    # Read multiline input
    encrypted_message = sys.stdin.read()

    # Ensure the message starts and ends correctly
    if "-----BEGIN PGP MESSAGE-----" not in encrypted_message or "-----END PGP MESSAGE-----" not in encrypted_message:
        print("Error: The encrypted message format is incorrect.")
        return

    # Ensure PGP is set up by getting the user's name and email.
    _name, _email = get_user_name_and_email()

    # Get pass phrase if present (does not prompt if pass phrase is saved in a file)
    pass_phrase = get_user_pass_phrase()

    if pass_phrase:
        command = ['gpg', '--pinentry-mode', 'loopback', '--passphrase', f"{pass_phrase}", '--decrypt']
    else:
        command = ['gpg', '--pinentry-mode', 'loopback', '--decrypt']

    try:
        # Run the gpg command to decrypt the message
        result = subprocess.run(
            command,
            input=encrypted_message.encode(),  # Provide the encrypted message as input
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if result.returncode == 0:
            decrypted_message = result.stdout.decode()
            print("\nDecrypted message:\n")
            print(decrypted_message)
        else:
            print(f"Error decrypting message: {result.stderr.decode()}")

    except Exception as e:
        print(f"Decryption failed or crashed: {str(e)}")

##################################
###     Entrypoint and CLI     ###
##################################

# Main block to handle command-line interaction
if __name__ == '__main__':
    print("Welcome!")
    print("NOTE: This script is a work in progress. Please report bugs to Caleb Stanford <cdstanford@ucdavis.edu>")
    print("(No encryption necessary for bug reports :) )")
    print()

    mode_raw = input("Choose s=setup, e=encrypt, d=decrypt, r=reset, or q=quit:\n").strip().lower()
    mode = mode_raw[0] if mode_raw else ""

    if mode == 's':
        setup_pgp_keys()
    elif mode == 'e':
        encrypt_message()
    elif mode == 'd':
        decrypt_message()
    elif mode == 'r':
        reset_all_keys()
    elif mode == 'q':
        print("Quitting")
    else:
        print("Invalid mode. Please choose one of 's', 'v', 'e', or 'd'.")
        exit(1)
