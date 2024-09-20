"""
Quick script to use GnuPG to manage PGP keys and encrypt/decrypt messages.

Requires GnuPG to be installed on the system. On macOS, you can install it using Homebrew:
- `brew install gnupg`

TODO: still debugging this script.
"""

import subprocess
import sys

# Configuration

# Use RSA 4096-bit keys that expire in 2 years
KEY_TYPE = "RSA"
KEY_LENGTH = 4096
KEY_EXPIRE = "2y"

# For greater security, replace with your real name and a real pass phrase
REAL_NAME = "User"
PASS_PHRASE = "passphrase"

# Optionally, replace with your own email and recipient's email
# to avoid entering them every time.
FROM_EMAIL = None
TO_EMAIL = None
# Example:
# FROM_EMAIL = "sender@domain.com"
# TO_EMAIL = "recipient@domain.com"

# Get email
def get_sender_email():
    if FROM_EMAIL:
        return FROM_EMAIL
    email = input("Enter your email address for the PGP key:\n")
    return email

def get_recipient_email():
    if TO_EMAIL:
        return TO_EMAIL
    email = input("Enter the recipient's email address:\n")
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

# Define encryption function
def encrypt_message(recipient):
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

# Define decryption function
def decrypt_message():
    print("Enter the encrypted message (paste the entire message, then press Ctrl+D to finish):")

    # Read multiline input
    encrypted_message = sys.stdin.read()

    try:
        # Ensure the message starts and ends correctly
        if "-----BEGIN PGP MESSAGE-----" not in encrypted_message or "-----END PGP MESSAGE-----" not in encrypted_message:
            print("Error: The encrypted message format is incorrect.")
            return

        # Run the gpg command to decrypt the message
        result = subprocess.run(
            ['gpg', '--decrypt'],
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

# Main block to handle command-line interaction
if __name__ == '__main__':
    mode = input("Choose s=setup, v=view public key, r=register recipient, e=encrypt, d=decrypt, or q=quit: ").strip().lower()
    mode = mode[0] if mode else ""

    if mode == 's':
        email = get_sender_email()
        setup_pgp_keys(email)
    elif mode == 'v':
        email = get_sender_email()
        print_pgp_public_keys(email)
    elif mode == 'r':
        register_recipient()
    elif mode == 'e':
        recipient = get_recipient_email()
        encrypt_message(recipient)
    elif mode == 'd':
        decrypt_message()
    elif mode == 'q':
        print("Quitting")
    else:
        print("Invalid mode. Please choose one of 's', 'v', 'e', or 'd'.")
        exit(1)
