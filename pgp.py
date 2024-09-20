"""
Quick script to use GnuPG to manage PGP keys and encrypt/decrypt messages.

Requires GnuPG to be installed on the system. On macOS, you can install it using Homebrew:
- `brew install gnupg`

TODO: still debugging this script.
"""

import subprocess
import sys

# Check if GnuPG is installed
try:
    subprocess.run(['gpg', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except FileNotFoundError:
    print("GnuPG is not installed. Please install GnuPG before running this script.")
    print("On macOS, you can install it using Homebrew: `brew install gnupg`")
    exit(1)

#############################
###     Configuration     ###
#############################

# Uses RSA 4096-bit keys that expire in 2 years.
KEY_TYPE = "RSA"
KEY_LENGTH = 4096
KEY_EXPIRE = "2y"

# For greater security, replace with your real name and a real pass phrase.
REAL_NAME = "User"
PASS_PHRASE = "passphrase"

# Optionally, replace with your own email to avoid entering it every time.
EMAIL = None
# Example:
# EMAIL = "sender@domain.com"

# File for the public key
PUB_KEY_FILE = "public_key.asc"

###############################
###     Setup Functions     ###
###############################

# Get email
def get_user_email():
    if EMAIL:
        return EMAIL
    email = input("Enter your email address:\n")
    return email

# Print public key(s)
def print_pgp_public_keys(email):
    # Command to export the public key
    export_cmd = ['gpg', '--armor', '--export', email]
    export_result = subprocess.run(
        export_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    if export_result.returncode == 0:
        public_key = export_result.stdout.decode()
        print("\nPublic PGP Key (to post on your website):\n")
        print(public_key)

        print("Saving public key to a file for convenient sharing...")
        with open(PUB_KEY_FILE, "w") as f:
            f.write(public_key)
        print(f"Public key saved successfully to {PUB_KEY_FILE}.")

    else:
        print(f"Error exporting PGP public key: {export_result.stderr.decode()}")

# Set up private and public PGP keys
def setup_pgp_keys(email):
    # Command to generate the PGP key
    cmd = [
        'gpg', '--batch', '--gen-key', '--yes'
    ]

    # GPG parameters for key generation
    key_params = f"""
    Key-Type: {KEY_TYPE}
    Key-Length: {KEY_LENGTH}
    Subkey-Type: {KEY_TYPE}
    Subkey-Length: {KEY_LENGTH}
    Name-Real: {REAL_NAME}
    Name-Email: {email}
    Expire-Date: {KEY_EXPIRE}
    Passphrase: {PASS_PHRASE}
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

##########################
###     Encryption     ###
##########################

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
        print("No recipients found in the keyring.")
        print("Help: to add a recipient, use the 'r' option.")
        return None
    elif len(recipients) == 1:
        print(f"Only one recipient found, using it.")
        print("Help: to add a recipient, use the 'r' option.")
        return recipients[0]

    # Display the recipient list
    print("Select a recipient:")
    for i, recipient in enumerate(recipients, start=1):
        print(f"{i}: {recipient}")

    try:
        selection = int(input("Enter the recipient number: "))
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
        print(f"An error occurred: {str(e)}")

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

    try:
        # Run the gpg command to decrypt the message
        result = subprocess.run(
            ['gpg', '--pinentry-mode', 'loopback', '--passphrase', f"{PASS_PHRASE}", '--decrypt'],
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
        print(f"An error occurred: {str(e)}")

##################################
###     Entrypoint and CLI     ###
##################################

# Main block to handle command-line interaction
if __name__ == '__main__':
    mode = input("Choose s=setup, v=view public key, r=register recipient, e=encrypt, d=decrypt, or q=quit: ").strip().lower()
    mode = mode[0] if mode else ""

    if mode == 's':
        email = get_user_email()
        setup_pgp_keys(email)
    elif mode == 'v':
        email = get_user_email()
        print_pgp_public_keys(email)
    elif mode == 'r':
        register_recipient()
    elif mode == 'e':
        encrypt_message()
    elif mode == 'd':
        decrypt_message()
    elif mode == 'q':
        print("Quitting")
    else:
        print("Invalid mode. Please choose one of 's', 'v', 'e', or 'd'.")
        exit(1)
