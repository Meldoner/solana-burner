<div align="center">
    <img src="https://i.imgur.com/OHPxyZA.png" width="100px" />
    <h1>Solana Token Burner</h1>
</div>

## Overview

**Solana Token Burner** is a Python application designed to burn and close token accounts in order to refund storage fees. It automatically close empty token accounts and asks on which non-empty token accounts to burn the token and close the account.

## Features

- Free and open source
- Connect to custom Solana RPC endpoints.
- Retrieve and display token accounts owned by a wallet.
- Burn tokens from specified token accounts.
- Close token accounts with zero balance.
- User-friendly command-line interface for interaction.

## Installation

To get started with the Solana Token Burner, follow these steps:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/meldoner/solana-burner.git
   cd solana-burner
   ```

2. **Install the required dependencies:**

   It is recommended to use a virtual environment. You can create one using `venv`:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

   Then install the dependencies listed in `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:

```bash
python main.py
```

You will be prompted to enter your private key and select an RPC endpoint. Follow the on-screen instructions to manage your token accounts.

## Donation
If you'd like to thank me for this program, here are my wallets:
- **SOL: `CAYzFrSaogwHrsQBZLTnLf8Q5THkcAQ8GrUU1dpkc5DN`**
- **USDT TRC-20: `TW8w2gbsDGWRJwWt8NjU5FyRTm7MFMwPJv`**


## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute to this project.

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.